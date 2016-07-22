import fcntl

def decrypt(key, data):
    cstate = [0x48,  0x74,  0x65,  0x6D,  0x70,  0x39,  0x39,  0x65]

    shuffle = [2, 4, 0, 7, 1, 6, 5, 3]

    phase1 = [0] * 8
    for i, o in enumerate(shuffle):
        phase1[o] = data[i]

    phase2 = [0] * 8
    for i in range(8):
        phase2[i] = phase1[i] ^ key[i]

    phase3 = [0] * 8
    for i in range(8):
        phase3[i] = ( (phase2[i] >> 3) | (phase2[ (i-1+8)%8 ] << 5) ) & 0xff

    ctmp = [0] * 8
    for i in range(8):
        ctmp[i] = ( (cstate[i] >> 4) | (cstate[i]<<4) ) & 0xff

    out = [0] * 8
    for i in range(8):
        out[i] = (0x100 + phase3[i] - ctmp[i]) & 0xff

    return out

if __name__ == "__main__":

    values     = {}
    key        = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]
    set_report = "\x00" + "".join(chr(e) for e in key)
    fp         = open("/dev/hidraw0", "a+b",  0)
    fcntl.ioctl(fp, 0xC0094806, set_report)

    while True:

        data      = list(ord(e) for e in fp.read(8))
        decrypted = decrypt(key, data)

        if decrypted[4] != 0x0d or (sum(decrypted[:3]) & 0xff) != decrypted[3]:
            print "Checksum error"
        else:
            op         = decrypted[0]
            val        = decrypted[1] << 8 | decrypted[2]
            values[op] = val

            if (0x50 in values) and (0x42 in values):
                co2 = values[0x50]
                tmp = values[0x42] / 16.0-273.15

                if (co2 > 5000 or co2 < 0):
                    continue

                print "CO2: %4i TMP: %3.1f" % (co2, tmp)
