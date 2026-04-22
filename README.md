# pyvalon

Python library for configuring Valon Synthesizer devices.
Supports V5015, V5007, and V5008. The V5007/V5008 protocol implementation
is a Python port of [ValonSynth](https://github.com/nrao/ValonSynth).

This repo is shipped as part of the
[eigsep-field](https://github.com/EIGSEP/eigsep-field) release and pinned
in its `manifest.toml`.

## Install

```
pip install pyvalon
```

Or from a checkout, for development:

```
git clone https://github.com/EIGSEP/pyvalon
cd pyvalon
pip install -e .[dev]
```

## Python API

```python
from pyvalon import V5008

synth = V5008("/dev/ttyUSB0", baud=9600)
synth.SetRefSelect("external")
synth.SetFreq("A", 500.0)      # MHz
synth.SetRFLevel("A", 5)       # dBm
synth.Flash()                  # persist to NVM
synth.close()
```

`V5007` and `V5015` have analogous interfaces.

## Command-line tools

Installing the package puts two console scripts on your `PATH`.

### V5007 / V5008 — `v5008`

```
v5008 [--dev DEV] [--baud BAUD] [--synth {A,B}] [--freq FREQ]
      [--amp {-4,-1,2,5}] [--ref {external,internal}] [--label [LABEL]]
      [--status] [--flash] [--eigsep]
```

### V5015 — `v5015`

```
v5015 [--dev DEV] [--baud BAUD] [--freq FREQ] [--amp AMP] [--ref REF]
      [--rfout RFOUT] [--pwr PWR] [--v]
```

Run either with `-h` for full argument help.

## EIGSEP defaults

The V5008 CLI ships with an `--eigsep` shortcut that applies the
experiment's standard configuration in one shot: external reference,
synth A at 500 MHz, synth B at 250 MHz, 5 dBm output on both, then
flashes to non-volatile memory:

```
v5008 --dev /dev/ttyUSB0 --eigsep
```

The defaults live in `EIGSEP_DEFAULTS` at the top of `pyvalon.v5008` —
edit there if the field configuration changes.

## Development

```
pip install -e .[dev]
pytest
```

Releases are managed by
[release-please](https://github.com/googleapis/release-please): merging
conventional-commit PRs to `master` opens a release PR that bumps the
version in `pyproject.toml` and `.release-please-manifest.json`, and
publishes to PyPI once merged.
