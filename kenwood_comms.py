import serial
from serial.tools import list_ports
from kenwood_constants import *
import time
import numpy as np


class KenwoodInterface(object):

    def __init__(self):

        ##########################################
        #   get port device info from device available
        port = self.select_active_port()
        print('TK serial port found: ', port)
        if port is None:
            print('could not find Prolific USB-to-Serial converter')
            raise Exception

        ##########################################
        #   create serial connection
        self.ser = serial.Serial(port=port, baudrate=9600, bytesize=8,
                                 parity='N', stopbits=2, timeout=5)

        print('comm name: ', self.ser.name)

    def select_active_port(self):
        """returns a valid COM port if found"""

        ports = list_ports.comports()
        for port in ports:
            if "Prolific" in port.manufacturer:
                return port.device

    def end_comms(self, message='no message'):
        """terminate communication with transceiver"""

        print('ending TK transmit session: ', message)
        end_message = (END ^ CRYPT2).tobytes()

        self.ser.write(end_message)
        self.check_conf(CRYPT2)
        self.ser.close()

    def convert_decimal_to_channel(self):
        """order is reversed (index 5, 4, 3, 2)
        each value bit shifted right by 4
        then logical AND 0x0f for next digit
        decimal place after third digit (e.g. after shifting second value)"""
        pass

    def tk_read_all(self, save=True):
        """read entire memory of transceiver"""

        self.init_comms()

        blocks = np.zeros((16, 32), dtype='uint8')

        for channel_index, x in enumerate(range(0x12C0, 0x14C0, 0x20)):
            MSB = x >> 8
            LSB = x & 0xff
            addr_len = 0x20
            self.ref_add_send(R, MSB, LSB, addr_len)
            self.ref_add_read(W, MSB, LSB, addr_len)

            data_in = self.ser.read(size=addr_len)
            data_in = np.array(list(data_in), dtype='uint8') ^ CRYPT2
            # print('channel data: ', data_in)

            self.write_conf(CRYPT2)

            blocks[channel_index] = data_in

        self.end_comms(message='nominal')

        if save:
            np.save('tk_dump', blocks)

        return blocks

    def tk_read(self):

        self.init_comms()

        channels_binary = np.zeros((16, 32), dtype='uint8')
        channels_binary.fill(0xff)

        print('READ from TK2404')
        for channel_index, x in enumerate(range(0x12C0, 0x14C0, 0x20)):
            MSB = x >> 8
            LSB = x & 0xff
            addr_len = 0x20
            self.ref_add_send(R, MSB, LSB, addr_len)
            self.ref_add_read(W, MSB, LSB, addr_len)

            data_in = self.ser.read(size=addr_len)
            data_in = np.array(list(data_in), dtype='uint8') ^ CRYPT2
            print('channel data: ', data_in)

            self.write_conf(CRYPT2)

            channels_binary[channel_index] = data_in

        self.end_comms(message='nominal')

        return channels_binary

    def checksum_send(self, vals):
        """vals: uint8 values to be summed with overflow"""

        checksum = np.sum(vals, dtype='uint8')
        # print('sending checksum: ', checksum)
        self.ser.write((checksum ^ CRYPT2).tobytes())
        time.sleep(0.01)
        self.check_conf(CRYPT2)

    def tk_write(self, channels, channel_data):
        """enumerates and writes channel data to transceiver"""

        print("SEND to TK2402")

        self.init_comms()
        self.ref_add_send(Y, 0x00, 0x70, 0x10)
        prog_write = P2402 ^ CRYPT2
        self.ser.write(bytes(list(prog_write)))
        self.checksum_send(P2402)
        self.set_scan_button_1()
        self.chan_enum(channels)
        self.write_channel_blocks(channel_data)
        self.end_comms(message='nominal')

    def set_scan_button_1(self):
        """
        assign button 1 to toggle scan mode of all scan-enabled channels
        address = 0x0f 0xd0
        value = "0x0d
        """

        self.ref_add_send(Y, 0x0f, 0xd0, 0x01)
        scan_toggle = np.uint8(0x0d)

        self.ser.write((scan_toggle ^ CRYPT2).tobytes())
        self.checksum_send(scan_toggle)

    def ref_add_send(self, command, MSB, LSB, addr_len):

        args = (command, MSB, LSB, addr_len)
        for arg in args:
            ref_send_bytes = bytes([arg ^ CRYPT2])
            self.ser.write(ref_send_bytes)
            time.sleep(0.01)

    def ref_add_read(self, command, MSB, LSB, addr_len):

        address_in = np.array(list(self.ser.read(size=0x04))) ^ CRYPT2
        pass

    def chan_enum(self, channels):
        """form bit register representation of active channels
        e.g. channels[1,2,4,7] = 0b01001011"""

        chanEnum = np.array([0xff, 0xff], dtype='uint8')  # Channel enumeration bytes for #1-8, and #9-16

        for channel in channels:
            if channel < 9:
                # enumerate channels #1-8
                chanEnum[0] = chanEnum[0] - (1 << (channel - 1))
            else:
                # enumerate channels #9-16
                chanEnum[1] = chanEnum[1] - (1 << (channel - 9))

        #   send enumeration bytes
        self.ref_add_send(Y, 0x10, 0x00, 0x02)
        # print('sending chanEnum: ', chanEnum)
        self.ser.write((chanEnum ^ CRYPT2).tobytes())
        self.checksum_send(chanEnum)

    def write_channel_blocks(self, channel_data):

        for i, x in enumerate(range(0x12C0, 0x14C0, 0x20)):
            self.ref_add_send(Y, (x >> 8), (x & 0xff), 0x20)
            print(channel_data[i])
            self.ser.write((channel_data[i] ^ CRYPT2).tobytes())
            self.checksum_send(channel_data[i])

    def init_comms(self):
        """initiate communications with TK2402 through handshake sequence
        baud rate ramping, and passing encryption key bytes"""

        print('initiating communications')
        time.sleep(0.01)
        # send serial programming request
        self.ser.write(PROGRAM.tobytes())
        time.sleep(0.01)

        incoming_byte = self.ser.read(size=1)

        # increase baudrate if response is correct, else terminate
        if ord(incoming_byte) == LISTENING:
            self.ser.baudrate = 19200
        else:
            self.end_comms()

        # get confirmation byte
        self.check_conf(CRYPT1)

        #  Send version request
        self.ser.write(VERSION.tobytes())

        # collect identification data
        ident_data = self.ser.read(size=40)
        print('Kenwood identity:', ident_data)
        time.sleep(0.01)

        ##############################################
        #   comms beyond this point are XOR encrypted
        self.ser.write(CRYPT1.tobytes())

        self.write_conf(CRYPT1)  # send first XOR encryption byte
        time.sleep(0.01)

        self.ser.write(bytes([P ^ CRYPT2]))  # send 'P' encrypted with second encryption
        self.ser.read(size=10)
        self.write_conf(CRYPT2)

    def write_conf(self, crypt):
        """write confirmation byte to transceiver"""

        self.ser.write((CONF ^ crypt).tobytes())  # XOR encrypted 0xbb
        time.sleep(0.01)
        self.check_conf(crypt)

    def check_conf(self, crypt):
        """check that confirmation byte has been received"""

        incoming_byte = self.ser.read(size=1)
        if (ord(incoming_byte) ^ crypt) != CONF:
            self.end_comms(message='failed confirmation')


if __name__ == '__main__':
    tk = KenwoodInterface()
    tk.tk_read_all()
