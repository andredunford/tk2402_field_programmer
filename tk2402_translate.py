import numpy as np

from kenwood_constants import *


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
            if channels_dict[key]['freq_rx'] not in exclusions:
                #   receive frequency (bare minimum)
                channels_binary[ind] = CHAN_INIT
                channels_binary[ind][0] = ind + 1
                channels_binary[ind][2:6] = self.freq_float_to_hex(float(channels_dict[key]['freq_rx']))
                channels_binary[ind][10] = self.calc_freq_step(float(channels_dict[key]['freq_rx']))
                channels_binary[ind][12:14] = self.qt_float_to_hex(float(channels_dict[key]['qt_rx']))

                #   transmit frequency
                if channels_dict[key]['freq_tx'] not in exclusions:
                    channels_binary[ind][6:10] = self.freq_float_to_hex(float(channels_dict[key]['freq_tx']))
                    channels_binary[ind][11] = self.calc_freq_step(float(channels_dict[key]['freq_tx']))
                    channels_binary[ind][14:16] = self.qt_float_to_hex(float(channels_dict[key]['qt_tx']))

                #   channel power, width, and scan enabling
                channels_binary[ind][17] = self.psw_bool_to_hex(
                    int(channels_dict[key]['power']),
                    int(channels_dict[key]['width']),
                    int(channels_dict[key]['scan'])
                )
                #   add channels with scan flag as active
                if channels_dict[key]['scan']:
                    channels_active.append(ind + 1)

        # channels_active = self.list_active_channels(channels_binary)

        return channels_binary, channels_active

    def binary_to_dict(self, channels_binary):
        """translate hex data from Kenwood Radio into human-readable data for display in app"""

        data_dict = {
            i: {'freq_rx': None, 'freq_tx': None, 'qt_rx': 0.0, 'qt_tx': 0.0,
                                     'power': 1, 'scan': 1, 'width': 0} for i in range(1, 17, 1)
        }

        for index, channel in enumerate(channels_binary):
            if channel[0] == 0xff or channel[5] == 0xff:
                continue
            else:

                data_dict[index + 1]['freq_rx'] = self.freq_hex_to_float(channel[2:6])
                data_dict[index + 1]['freq_tx'] = self.freq_hex_to_float(channel[6:10])

                data_dict[index + 1]['qt_rx'] = self.qt_hex_to_float(channel[12:14])
                data_dict[index + 1]['qt_tx'] = self.qt_hex_to_float(channel[14:16])

                data_dict[index + 1]['power'], \
                data_dict[index + 1]['scan'], \
                data_dict[index + 1]['width'],  = self.psw_hex_to_bool(channel[17])

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

    def freq_float_to_hex(self, freq):
        """convert float value frequency into hex value bytes"""

        #   represent value as 8-character string with decimal point removed
        freq_str = str(freq).replace('.', '').ljust(8, '0')
        #   split string into 2-character strings
        freq_bytes_str = [freq_str[i:i + 2] for i in range(0, len(freq_str), 2)]
        #   convert split strings into integer values with base-16
        freq_hex_array = np.array([int(i, 16) for i in freq_bytes_str], dtype='uint8')
        #   flip array to reverse order
        freq_hex_array = np.reshape(np.flip(freq_hex_array), (1, -1))

        return freq_hex_array

    def freq_hex_to_float(self, freq_hex_array):

        if freq_hex_array[0] == 0xff:
            return None
        #   reverse order to standard
        freq_hex_array = np.flip(freq_hex_array)
        freq_string = np.array([[str(i >> 4), str(i & 0x0f)] for i in freq_hex_array])
        freq_string = freq_string.flatten()
        #   insert decimal point in third position
        freq_string = np.insert(freq_string, 3, '.')
        freq_string = ''.join(freq_string)
        freq_float = float(freq_string)

        return freq_float

    def qt_float_to_hex(self, qt_freq):
        """lookup bytes cooresponding to frequency given in QT_mask"""

        #   find frequency index
        qt_index = np.where(QT_MASK == qt_freq)
        qt_bytes = np.array([QT_B1[qt_index], QT_B2[qt_index]], dtype='uint8')
        qt_bytes = qt_bytes.reshape((1, -1))

        return qt_bytes

    def qt_hex_to_float(self, qt_hex):
        """lookup float value in QT_b1 and QT_b2"""

        qt1_index = np.where(QT_B1 == qt_hex[0])
        qt2_index = np.where(QT_B2 == qt_hex[1])

        qt_float = float(QT_MASK[np.intersect1d(qt1_index, qt2_index)][0])

        return qt_float

    def psw_bool_to_hex(self, power, width, scan):
        """create single byte indicating power, width, scan settings
        Power/Scan (HIGH nibble): 0xC(Low/Yes), 0xD (Low/No), 0xE (High/Yes), 0xF (High/No)
        Channel Width (LOW nibble): 0xC(Narrow)/0xD(Wide)
        """

        power_nibble = (power * 2) + 0xC  # either 0xC or 0xE from bool values 0, 1
        scan_nibble = int(not bool(scan))  # take inverse of boolean value: scan on = 0 off = 1
        width_nibble = width + 0xC

        #   combine high and low nibbles into byte
        psw_byte = ((power_nibble + scan_nibble) << 4) + width_nibble

        return psw_byte

    def psw_hex_to_bool(self, psw_hex):
        """translate boolean values from single byte indicator"""

        power = int((psw_hex >> 4) >= 0xE)
        scan = int(not bool((psw_hex >> 4) % 2))
        width = int((psw_hex & 0x0f) - 0xC)

        return power, scan, width

    def list_active_channels(self, channels_binary):

        channels_active = [i for i in channels_binary[:, 0] if i != 0xff]

        return channels_active


if __name__ == "__main__":
    TKTranslate(None)