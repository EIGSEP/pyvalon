#! /usr/bin/env python
"""
usage: v5008.py [-h] [--dev DEV] [--baud BAUD] [--synth {A,B}] [--freq FREQ] [--amp {-4,-1,2,5}] [--ref {external,internal}] [--status] [--flash]

Usage for Setting V5007/V5008.

optional arguments:
  -h, --help            show this help message and exit
  --dev DEV             Serial port for V5007/V5008.
  --baud BAUD           Baud rate.
  --synth {A,B}         A - synthesizer 1; B - synthesizer 2.
  --freq FREQ           The frequency in MHz.
  --amp {-4,-1,2,5}     The amplitude level.
  --ref {external,internal}
                        The reference source('internal' or 'external')
  --status              Check the synthesizer status
  --flash               Write the parameters into flash
"""
from Valon import V500X
from argparse import ArgumentParser

JUST_LEN = 12

# EIGSEP default configuration
EIGSEP_DEFAULTS = {
    'A': {'freq': 500.0, 'amp': 5},
    'B': {'freq': 250.0, 'amp': 5},
    'ref': 'external',
}

def CheckStatus(synth, s):
    print('%s: %s'%('synthesizer'.ljust(JUST_LEN), s))
    label = synth.GetLabel(s)
    print('%s: %s'%('Label'.ljust(JUST_LEN), label))
    freq = synth.GetFreq(s)
    print('%s: %.02f'%('Freq(MHz)'.ljust(JUST_LEN), freq))
    rf_level = synth.GetRFLevel(s)
    print('%s: %d'%('RF Level'.ljust(JUST_LEN), rf_level))
    ref = synth.GetRefSelect()
    print('%s: %s'%('Reference'.ljust(JUST_LEN), ref))
    lock = synth.GetPhaseLock(s)
    if lock == True:
        print('%s: %s'%('Lock'.ljust(JUST_LEN), 'Locked'))
    else:
        print('%s: %s'%('Lock'.ljust(JUST_LEN), 'Unlocked'))  

def GetSynth(args):
    if args.synth == None:
        print('Please specify which synthesizer you want to use: A - synthesizer 1; B - synthesizer 2.')
    else:
        return args.synth

def main():
    parser = ArgumentParser(description="Usage for Setting V5008.")
    parser.add_argument('--dev',dest='dev', type=str, default='/dev/ttyUSB0',help='Serial port for V5008.')
    parser.add_argument('--baud',dest='baud', type=int, default=9600, help='Baud rate.')
    parser.add_argument('--synth',dest='synth', type=str, choices=['A', 'B'], default=None, help='A - synthesizer 1; B - synthesizer 2.')
    parser.add_argument('--freq', dest='freq', type=float, help='The frequency in MHz.')
    parser.add_argument('--amp', dest='amp', type=int, choices=[-4, -1, 2, 5], default=-999, help='The amplitude level.')
    parser.add_argument('--ref',dest='ref',type=str, choices=['external', 'internal'], default='', help='The reference source(\'internal\' or \'external\')')
    parser.add_argument('--label', dest='label', type=str, default=None, help='Set or get the synthesizer label (omit value to get)')
    parser.add_argument('--status', dest='status', default=False, action='store_true', help='Check the synthesizer status')
    parser.add_argument('--flash', dest='flash', default=False, action='store_true', help='Write the parameters into flash')
    args = parser.parse_args()
    
    print('%s: %s'%('Dev'.ljust(JUST_LEN),args.dev))
    print('%s: %s'%('Baud'.ljust(JUST_LEN),args.baud))

    synth = V500X(args.dev, args.baud)

    # If no configuration arguments provided, apply EIGSEP defaults
    no_config = (args.freq is None and args.amp == -999 and args.ref == ''
                 and args.label is None and not args.status and not args.flash)
    if no_config:
        print('\nApplying EIGSEP defaults...')
        # Set external reference
        r = synth.SetRefSelect(EIGSEP_DEFAULTS['ref'])
        if not r:
            print('Reference set failed.')
        else:
            print('%s: %s'%('Reference'.ljust(JUST_LEN), synth.GetRefSelect()))
        # Configure both synthesizers
        for s in ('A', 'B'):
            cfg = EIGSEP_DEFAULTS[s]
            r = synth.SetFreq(s, cfg['freq'])
            if not r:
                print('Frequency set failed for synth %s.' % s)
            r = synth.SetRFLevel(s, cfg['amp'])
            if not r:
                print('RF level set failed for synth %s.' % s)
        # Flash and show status
        synth.Flash()
        print('')
        CheckStatus(synth, 'A')
        print('')
        CheckStatus(synth, 'B')
        print('\nSettings flashed.')
        synth.close()
        return

    # set freq
    if args.freq:
        s = GetSynth(args)
        r = synth.SetFreq(s, args.freq)
        if r == False:
            print('Frequency set failed.')
        else:
            freq = synth.GetFreq(s)
            print('%s: %s'%('synthesizer'.ljust(JUST_LEN), s))
            print('%s: %.02f'%('Freq(MHz)'.ljust(JUST_LEN), freq))
    # set RF level
    if args.amp != -999:
        s = GetSynth(args)
        r = synth.SetRFLevel(s, args.amp)
        if r == False:
            print('RF level set failed.')
        else:
            rf_level = synth.GetRFLevel(s)
            print('%s: %s'%('synthesizer'.ljust(JUST_LEN), s))
            print('%s: %d'%('RF Level'.ljust(JUST_LEN), rf_level))
    # set ref
    if args.ref != '':
            r = synth.SetRefSelect(args.ref)
            if r == False:
                print('Reference set failed.')
            else:
                ref = synth.GetRefSelect()
                print('%s: %s'%('Reference'.ljust(JUST_LEN), ref))
    # set or get label
    if args.label is not None:
        s = GetSynth(args)
        if args.label == '':
            label = synth.GetLabel(s)
            print('%s: %s'%('Label'.ljust(JUST_LEN), label))
        else:
            r = synth.SetLabel(s, args.label)
            if r == False:
                print('Label set failed.')
            else:
                label = synth.GetLabel(s)
                print('%s: %s'%('synthesizer'.ljust(JUST_LEN), s))
                print('%s: %s'%('Label'.ljust(JUST_LEN), label))
    if args.status:
        print('')
        CheckStatus(synth, 'A')
        print('')
        CheckStatus(synth, 'B')
    if args.flash:
        if args.status == False:
            print('')
            CheckStatus(synth, 'A')
            print('')
            CheckStatus(synth, 'B')
        synth.Flash()
        print('')
        print('The parameters have been written into flash!')
    synth.close()

if __name__=='__main__':
    main()
