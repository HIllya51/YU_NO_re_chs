from ai5win_gui import AI5WINArcToolGUI

debug = False


def test(mode: str):
    from ai5win_arc import AI5WINArc
    """modes: unpack, pack, hackerman"""
    if mode == "unpack":
        test_arc = AI5WINArc("mes.ARC", "MES", integrity_check=True)
        test_arc.unpack()
    elif mode == "pack":
        test_arc = AI5WINArc("mes.ARC", "MES", integrity_check=True,
                             first_key=0x3, second_key=0x33656755, third_key=0x68820811,
                             name_bytes=20)
        test_arc.pack()
    elif mode == "hackerman":
        import struct
        key = 0x55
        with open("mes.ARC", 'rb') as inf, open('mes.ARC.tryhack', 'wb') as ouf:
            while True:
                new_byte = inf.read(1)
                if new_byte == b'':
                    break
                new_byte = new_byte[0] ^ key
                ouf.write(struct.pack('B', new_byte))


def main():
    gui = AI5WINArcToolGUI()  # Crutch. Otherwise at exit will be shown error.


if __name__ == '__main__':
    if debug:
        test("unpack")
    else:
        main()
