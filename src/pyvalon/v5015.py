#! /usr/bin/env python
"""
usage: v5015.py [-h] [--dev DEV] [--baud BAUD] [--freq FREQ] [--amp AMP] [--ref REF] [--rfout RFOUT] [--pwr PWR] [--v]

Usage for Setting V5015.

optional arguments:
  -h, --help     show this help message and exit
  --dev DEV      Serial port for V5015.
  --baud BAUD    Baud rate.
  --freq FREQ    The frequency in MHz.
  --amp AMP      The amplitude in dBm.
  --ref REF      The reference source('internal' or 'external' or 'status')
  --rfout RFOUT  The rfout status('on' or 'off' or 'status')
  --pwr PWR      The power status('on' or 'off' or 'status')
  --v            Verbose
"""
from pyvalon.valon import V5015
from argparse import ArgumentParser

JUST_LEN = 8

def main():
    parser = ArgumentParser(description="Usage for Setting V5015.")
    parser.add_argument('--dev',dest='dev', type=str, default='/dev/ttyUSB0',help='Serial port for V5015.')
    parser.add_argument('--baud',dest='baud', type=int, default=9600, help='Baud rate.')
    parser.add_argument('--freq', dest='freq', type=float, help='The frequency in MHz.')
    parser.add_argument('--amp', dest='amp', type=float, default=-999, help='The amplitude in dBm.')
    parser.add_argument('--ref',dest='ref',type=str, default='', help='The reference source(\'internal\' or \'external\' or \'status\')')
    parser.add_argument('--rfout', dest='rfout', type=str, default='', help='The rfout status(\'on\' or \'off\'  or \'status\')')
    parser.add_argument('--pwr', dest='pwr', type=str, default='', help='The power status(\'on\' or \'off\'  or \'status\')')
    parser.add_argument('--v', dest='verbose', default=False, action='store_true', help='Verbose')
    args = parser.parse_args()
    
    print('%s: %s'%('Dev'.ljust(JUST_LEN),args.dev))
    print('%s: %s'%('Baud'.ljust(JUST_LEN),args.baud))
    synth = V5015(args.dev, args.baud)
    if args.freq :
        r = synth.SetFreq(args.freq,'MHz',verbose=args.verbose)
        print('%s: %s'%('Freq'.ljust(JUST_LEN),r))
    if args.amp > -999:
        r = synth.SetAmp(args.amp,verbose=args.verbose)
        print('%s: %s'%('Freq'.ljust(JUST_LEN),r))
    if args.ref:
        if args.ref == 'status':
            r = synth.SetRef(verbose=args.verbose)
        else:
            r = synth.SetRef(args.ref,verbose=args.verbose)
        print('%s: %s'%('Ref'.ljust(JUST_LEN),r))
    if args.rfout:
        if args.rfout == 'status':
            r = synth.RFout(verbose=args.verbose)
        else:
            r = synth.RFout(args.rfout,verbose=args.verbose)
        print('%s: %s'%('Rfout'.ljust(JUST_LEN),r))
    if args.pwr:
        if args.pwr == 'status':
            r = synth.PWRout(verbose=args.verbose)
        else:
            r = synth.PWRout(args.pwr,verbose=args.verbose)
        print('%s: %s'%('Pwr'.ljust(JUST_LEN),r))
    synth.close()

if __name__=='__main__':
    main()
