import argparse
import sys
import fileinput
import qrcode


class Qrcode(object):

    def __init__(self, invert_flag, print_flag, out_file):
        self.qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,
                                box_size=1,
                                border=2,)

        self.invert_flag = invert_flag
        self.print_flag = print_flag
        self.out_file = out_file
        self.count = 1

    def add_data(self, data):
        if len(data) > 0:
            self.qr.add_data(data)

    def print_png(self):
        if self.print_flag:
            self.qr.print_tty()
            self.qr.clear()

    def gen_qrcode(self):
        self.print_png()


def get_flags(args):
    """
    Returns:
    args.input: string     return the path of your input file
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-p", "--p", dest="print_flag",
                        action="store_true", help="print qrcode image file")
    parser.add_argument("-o", "--o", dest="out_file", help="out file")
    parser.add_argument("-t", "--t", dest="input_text", help="Your input text")
    parser.add_argument("-f", "--f", dest="file", help="Your input file")
    parser.add_argument("-i", "--i", dest="invert_flag", action="store_false",
                        help="invert the ASCII characters (solid <-> transparent)")
    parser.add_argument("-d", "--d", dest="divide", type=int,
                        help="divides file into several png")

    args = parser.parse_args()
    return args


def showQr(text):
    qr = Qrcode(invert_flag=True,
                print_flag=True, out_file=None)
    qr.add_data(text)
    qr.gen_qrcode()

if __name__ == "__main__":
    args = sys.argv[1:]
    params = get_flags(args)

    qr = Qrcode(invert_flag=params.invert_flag,
                print_flag=params.print_flag, out_file=params.out_file)

    if params.input_text:
        qr.add_data(params.input_text)
        qr.gen_qrcode()

    elif params.file:
        count = 0
        # with open(params.file, 'r') as f:
        for line in fileinput.input(params.file):
            qr.add_data(line)
            count += 1
            if params.divide and count % params.divide == 0:
                qr.gen_qrcode()
        if not params.divide or count % params.divide != 0:
            qr.gen_qrcode()
