import RPi.GPIO as GPIO

class TM1638(object):

    FONT = [0b00111111,
            0b00000110,
            0b01011011,
            0b01001111,
            0b01100110,
            0b01101101,
            0b01111100,
            0b00000111,
            0b01111111,
            0b01100111,
            0b00000000]

    def __init__(self, dio, clk, stb):
        self.dio = dio
        self.clk = clk
        self.stb = stb
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.dio,  GPIO.OUT)
        GPIO.setup(self.clk,  GPIO.OUT)
        GPIO.setup(self.stb,  GPIO.OUT)
        GPIO.output(self.stb, True)
        GPIO.output(self.clk, True)
        self.clearDisplay()

    def clearDisplay(self):
        GPIO.output(self.stb, False)
        self.send_byte(0xC0)
        for i in range(16):
            self.send_byte(0x00)
        GPIO.output(self.stb, True)

    def enable(self, intensity=7):
        self.send_command(0x40)                         # Normale mode, Auto Address, write data
        self.send_command(0x80 | 8 | min(7, intensity)) # 80 = 0b10000000, 8 = 0b00001000

    def disable(self):
        self.send_command(0x40)  # Normale mode, Auto Address, write data
        self.send_command(0x80)  # 80 = 0b10000000

    def send_command(self, cmd):
        GPIO.output(self.stb, False)
        self.send_byte(cmd)
        GPIO.output(self.stb, True)

    def send_byte(self, data):
        for i in range(8):
            GPIO.output(self.clk, False)
            GPIO.output(self.dio, (data & 1) == 1)
            data >>= 1
            GPIO.output(self.clk, True)

    def send_data(self, addr, data):
        self.send_command(0x44)       # Fixed data
        GPIO.output(self.stb, False)
        self.send_byte(0xC0 | addr)   # Write to address
        self.send_byte(data)
        GPIO.output(self.stb, True)

    def set_led(self, n, color):
        self.send_data((n << 1) + 1, color)

    def set_segment(self, pos, val, dot = False):
        self.send_data(pos * 2, TM1638.FONT[val] | (128 if dot else 0))

    def set_text(self, text):
        for i in range(8):
            self.set_segment(i,int(text[i]))

    def receive(self):
        temp = 0
        GPIO.setup(self.dio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        for i in range(8):
            temp >>= 1
            GPIO.output(self.clk, False)
            if GPIO.input(self.dio):
                temp |= 0x80
            GPIO.output(self.clk, True)
        GPIO.setup(self.dio, GPIO.OUT)
        return temp

    def get_buttons(self):
        keys = 0
        GPIO.output(self.stb, False)
        self.send_byte(0x42)
        for i in range(4):
            keys |= self.receive() << i
        GPIO.output(self.stb, True)
        return keys
