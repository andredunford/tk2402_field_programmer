import struct

from tk2402_constants import *


class TKTranslate(object):

    def __init__(self):

        pass

    def dict_to_binary(self, channels_dict):
        """translate dictionary of channel parameters into hex data formatted for Kenwood Radio"""

        channels_binary = np.zeros((16, 32), dtype='uint8')
        channels_binary.fill(0xff)
        channels_active = []

        exclusions = ['', None, 0, 'null']

        for ind, key in enumerate(channels_dict):
            channels_binary[ind] = CHAN_INIT
            channels_binary[ind][0] = ind + 1

            if channels_dict[key]['freq_rx'] not in exclusions:
                #   receive frequency (bare minimum)
                channels_binary[ind][2:6] = self.float_to_bcd(float(channels_dict[key]['freq_rx']))
                channels_binary[ind][10] = self.calc_freq_step(float(channels_dict[key]['freq_rx']))
                channels_binary[ind][12:14] = self.qt_float_to_byte(float(channels_dict[key]['qt_rx']))

                #   transmit frequency
                if channels_dict[key]['freq_tx'] not in exclusions:
                    channels_binary[ind][6:10] = self.float_to_bcd(float(channels_dict[key]['freq_tx']))
                    channels_binary[ind][11] = self.calc_freq_step(float(channels_dict[key]['freq_tx']))
                    channels_binary[ind][14:16] = self.qt_float_to_byte(float(channels_dict[key]['qt_tx']))

                #   channel power, width, and scan enabling
                channels_binary[ind][17] = self.psw_bool_to_byte(
                    int(channels_dict[key]['power']),
                    int(channels_dict[key]['width']),
                    int(channels_dict[key]['scan'])
                )
                #   add channels with scan flag as active
                if channels_dict[key]['scan']:
                    channels_active.append(ind + 1)

        return channels_binary, channels_active

    def binary_to_dict(self, channels_binary):
        """translate hex data from Kenwood Radio into human-readable data for display in app"""

        data_dict = {
            i: {
                'freq_rx': None,
                'freq_tx': None,
                'qt_rx': 0.0,
                'qt_tx': 0.0,
                'power': 1,
                'scan': 1,
                'width': 0
            } for i in range(1, 17)
        }

        for index, channel in enumerate(channels_binary):
            if channel[0] == 0xff or channel[5] == 0xff:
                continue
            else:
                data_dict[index + 1]['freq_rx'] = self.bcd_to_float(channel[2:6])
                data_dict[index + 1]['freq_tx'] = self.bcd_to_float(channel[6:10])

                data_dict[index + 1]['qt_rx'] = self.qt_byte_to_float(channel[12:14])
                data_dict[index + 1]['qt_tx'] = self.qt_byte_to_float(channel[14:16])

                data_dict[index + 1]['power'], \
                data_dict[index + 1]['scan'], \
                data_dict[index + 1]['width'],  = self.psw_byte_to_bool(channel[17])

        return data_dict

    def calc_freq_step(self, freq):
        """find frequency step flag by mysterious kenwood method
        TODO: still can't reproduce higher precision frequencies with 100% accuracy (rare) """

        #  take 5 significant digits after decimal place as integer
        freq_int = int(round((freq - np.floor(freq)) * 1e5))
        #   find indices of freq_steps which are equally divisible into freq_int
        zero_modulo_indices = np.where(freq_int % FREQ_STEPS[:, 1] == 0)
        #   retrieve flag value from first zero modulo index in freq_steps
        step_flag = FREQ_STEPS[zero_modulo_indices][0, 0]

        return step_flag

    def float_to_bcd(self, val_float):
        """convert frequency float value to Binary Coded Decimal byte array"""

        val_kHz = int(val_float * 1000)
        bcd_vals = [0] * 4

        for idx in range(len(bcd_vals) - 1):
            chunk = val_kHz % 100
            val_kHz //= 100
            tens = chunk // 10
            ones = chunk % 10
            bcd_vals[idx + 1] = (tens << 4) | ones

        return bcd_vals

    def bcd_to_float(self, val_bytes):
        """convert Binary Coded Decimal byte array to frequency float value"""
        if val_bytes[0] == 0xff:
            return None

        output = 0
        for idx, val in enumerate(val_bytes[1:]):
            high = (val >> 4) & 0x0f
            low = val & 0x0f
            digits = int((high * 10) + low)
            output += digits * 10**(idx * 2)

        return output / 1000

    def qt_float_to_byte(self, qt_freq):
        """lookup bytes corresponding to frequency given in QT_mask"""

        qt_freq_int = int(qt_freq * 10)
        qt_bytes = np.array([list(struct.pack('<H', qt_freq_int))], dtype='uint8')

        return qt_bytes

    def qt_byte_to_float(self, qt_hex):
        """convert CTCSS byte values to frequency float value"""

        qt_int = struct.unpack('<H', qt_hex)[0]
        qt_float = qt_int / 10

        return qt_float

    def psw_bool_to_byte(self, power, width, scan):
        """create single byte indicating power, width, scan settings
        Power/Scan (HIGH nibble): 0xC(Low/Yes), 0xD (Low/No), 0xE (High/Yes), 0xF (High/No)
        Channel Width (LOW nibble): 0xC(Narrow)/0xD(Wide)
        power:  bit 5 (0x20)
        scan:   bit 4 (0x10)
        width:  bit 0 (0x01)
        """

        psw_byte = 0xCC + (power * 0x20) + (int(not scan) * 0x10) + (width * 0x01)

        return psw_byte

    def psw_byte_to_bool(self, psw_hex):
        """translate boolean values from single byte indicator
        power:  bit 5 (0x20)
        scan:   bit 4 (0x10)
        width:  bit 0 (0x01)
        """

        power = (psw_hex & 0x20) >> 5
        scan = int(not (psw_hex & 0x10) >> 4)
        width = (psw_hex & 0x01) >> 0

        return power, scan, width

    def list_active_channels(self, channels_binary):

        channels_active = [i for i in channels_binary[:, 0] if i != 0xff]

        return channels_active


if __name__ == "__main__":
    TKTranslate(None)