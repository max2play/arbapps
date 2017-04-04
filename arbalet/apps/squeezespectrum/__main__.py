import argparse
from .squeezespectrum import SqueezeSpectrumAnalyser

parser = argparse.ArgumentParser(description='Musical spectrum display for the default system audio input with control for Squeezeplayer')
parser.add_argument('-v', '--vertical',
                    action='store_const',
                    const=True,
                    default=False,
                    help='The spectrum must be vertical (less bands, more bins)')
SqueezeSpectrumAnalyser(parser).start()

