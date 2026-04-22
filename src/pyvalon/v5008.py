#! /usr/bin/env python
"""
usage: v5008.py [-h] [--dev DEV] [--baud BAUD] [--synth {A,B}] [--freq FREQ] [--amp {-4,-1,2,5}] [--ref {external,internal}] [--label [LABEL]] [--status] [--flash] [--eigsep]

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
  --label [LABEL]       Set the synthesizer label; omit value to get the current label.
  --status              Check the synthesizer status
  --flash               Write the parameters into flash
  --eigsep              Apply EIGSEP default configuration
"""
from pyvalon.valon import V500X
from argparse import ArgumentParser

JUST_LEN = 12

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

def set_freq(synth, s, freq):
    if synth.SetFreq(s, freq) == False:
        print('Frequency set failed for synth %s.' % s)
        return False
    print('%s: %s'%('synthesizer'.ljust(JUST_LEN), s))
    print('%s: %.02f'%('Freq(MHz)'.ljust(JUST_LEN), synth.GetFreq(s)))
    return True

def set_amp(synth, s, amp):
    if synth.SetRFLevel(s, amp) == False:
        print('RF level set failed for synth %s.' % s)
        return False
    print('%s: %s'%('synthesizer'.ljust(JUST_LEN), s))
    print('%s: %d'%('RF Level'.ljust(JUST_LEN), synth.GetRFLevel(s)))
    return True

def set_ref(synth, ref):
    if synth.SetRefSelect(ref) == False:
        print('Reference set failed.')
        return False
    print('%s: %s'%('Reference'.ljust(JUST_LEN), synth.GetRefSelect()))
    return True

def set_label(synth, s, label):
    if synth.SetLabel(s, label) == False:
        print('Label set failed.')
        return False
    print('%s: %s'%('synthesizer'.ljust(JUST_LEN), s))
    print('%s: %s'%('Label'.ljust(JUST_LEN), synth.GetLabel(s)))
    return True

def configure_synth(synth, s, freq=None, amp=None):
    if freq is not None:
        set_freq(synth, s, freq)
    if amp is not None:
        set_amp(synth, s, amp)

def apply_eigsep_defaults(synth):
    print('\nApplying EIGSEP defaults...')
    set_ref(synth, EIGSEP_DEFAULTS['ref'])
    for s in ('A', 'B'):
        cfg = EIGSEP_DEFAULTS[s]
        configure_synth(synth, s, freq=cfg['freq'], amp=cfg['amp'])
    synth.Flash()
    print('')
    CheckStatus(synth, 'A')
    print('')
    CheckStatus(synth, 'B')
    print('\nSettings flashed.')

def main():
    parser = ArgumentParser(description="Usage for Setting V5008.")
    parser.add_argument('--dev',dest='dev', type=str, default='/dev/ttyUSB0',help='Serial port for V5008.')
    parser.add_argument('--baud',dest='baud', type=int, default=9600, help='Baud rate.')
    parser.add_argument('--synth',dest='synth', type=str, choices=['A', 'B'], default=None, help='A - synthesizer 1; B - synthesizer 2.')
    parser.add_argument('--freq', dest='freq', type=float, help='The frequency in MHz.')
    parser.add_argument('--amp', dest='amp', type=int, choices=[-4, -1, 2, 5], default=None, help='The amplitude level.')
    parser.add_argument('--ref',dest='ref',type=str, choices=['external', 'internal'], default=None, help='The reference source(\'internal\' or \'external\')')
    parser.add_argument('--label', dest='label', type=str, nargs='?', const='', default=None, help='Set the synthesizer label; omit value to get the current label.')
    parser.add_argument('--status', dest='status', default=False, action='store_true', help='Check the synthesizer status')
    parser.add_argument('--flash', dest='flash', default=False, action='store_true', help='Write the parameters into flash')
    parser.add_argument('--eigsep', dest='eigsep', default=False, action='store_true', help='Apply EIGSEP default configuration (A=500 MHz, B=250 MHz, external ref, 5 dBm, flash)')
    args = parser.parse_args()

    print('%s: %s'%('Dev'.ljust(JUST_LEN),args.dev))
    print('%s: %s'%('Baud'.ljust(JUST_LEN),args.baud))

    synth = V500X(args.dev, args.baud)

    if args.eigsep:
        apply_eigsep_defaults(synth)
        synth.close()
        return

    if args.freq is not None:
        s = GetSynth(args)
        if s is not None:
            set_freq(synth, s, args.freq)
    if args.amp is not None:
        s = GetSynth(args)
        if s is not None:
            set_amp(synth, s, args.amp)
    if args.ref is not None:
        set_ref(synth, args.ref)
    if args.label is not None:
        s = GetSynth(args)
        if s is not None:
            if args.label == '':
                print('%s: %s'%('Label'.ljust(JUST_LEN), synth.GetLabel(s)))
            else:
                set_label(synth, s, args.label)
    if args.status:
        print('')
        CheckStatus(synth, 'A')
        print('')
        CheckStatus(synth, 'B')
    if args.flash:
        if not args.status:
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
