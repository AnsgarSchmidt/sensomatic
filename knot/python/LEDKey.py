import TM1638

DIO = 17
CLK = 27
STB = 22

display = TM1638.TM1638(DIO, CLK, STB)
display.enable(1)
