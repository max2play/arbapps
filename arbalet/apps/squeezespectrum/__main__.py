import argparse
from .squeezespectrum import SqueezeSpectrumAnalyser

parser = argparse.ArgumentParser(description='Musical spectrum display for the default system audio input with control for Squeezeplayer')
parser.add_argument('-v', '--vertical',
                    action='store_const',
                    const=True,
                    default=False,
                    help='The spectrum must be vertical (less bands, more bins)')
parser.add_argument('--squeezebox_server',
                    type=str,
                    nargs='?',
                    const='127.0.0.1',
                    default='',
                    help='IP of Squeezebox Server')
parser.add_argument('--squeezeplayer_mac',
                    type=str,
                    nargs='?',
                    default='',
                    help='MAC Address of Squeezebox Player to control')
SqueezeSpectrumAnalyser(parser).start()

