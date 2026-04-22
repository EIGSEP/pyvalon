# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```
pip install -e .[dev]           # install + dev extras (ruff, pytest, build, twine)
pytest                          # full suite (uses pyproject [tool.pytest.ini_options])
pytest -k test_flash_ack        # run a single test by name
ruff check . && ruff format .   # lint + format (not currently enforced in CI)
python -m build                 # build sdist + wheel locally
```

No dev servers or long-running processes — this is a driver library plus CLI scripts.

## Release flow

Releases are managed by release-please on push to `master`. Writing a conventional-commit message (`feat:`, `fix:`, `feat!:`) causes release-please to open/update a release PR that bumps the version in `pyproject.toml` and `.release-please-manifest.json`. Merging that PR cuts a GitHub release and auto-publishes to PyPI via trusted publishing (`environment: pypi` in `.github/workflows/release-please.yml`). Do not hand-edit `version` in `pyproject.toml`; let release-please manage it.

pyvalon is pinned in `eigsep-field`'s `manifest.toml`. A new PyPI release is the signal for eigsep-field to bump the pin and refresh its lockfile.

## Architecture

All driver code lives in `src/pyvalon/valon.py`. There are two fundamentally different protocols behind a superficially similar class hierarchy:

- **`Valon` / `V5015`** — ASCII string protocol. Commands are text (`"F 500 MHz\r"`, `"PWR 5\r"`, `"REFS 1\r"`), and responses are parsed by splitting on `;` and `\r`. Brittle to firmware wording changes; no checksums.

- **`V500X` / `V5007` / `V5008`** — binary protocol ported from [nrao/ValonSynth](https://github.com/nrao/ValonSynth). Commands are opcode bytes; synth A/B is selected by OR-ing `0x08` into the opcode (see `V500X.SYNTH`). The high bit distinguishes reads (`0x80 | s`) from writes (`0x00 | s`). Reads come back as a fixed-size payload followed by a 1-byte modulo-256 checksum that `CheckReadBack` validates; writes come back as a single ACK (`0x06`) or NACK (`0x15`) byte. Frequency state lives in 24 bytes of device registers — `_pack_freq_registers` / `_unpack_freq_registers` marshal the `ncount` / `frac` / `mod` / `dbf` fields into/out of `reg0`, `reg1`, `reg4` with specific bit masks; if you touch frequency logic, roundtrip the two functions.

`v5008.py` and `v5015.py` are thin CLI wrappers over the driver classes. The V5008 CLI has an `--eigsep` shortcut that applies `EIGSEP_DEFAULTS` (A=500 MHz, B=250 MHz, 5 dBm, external ref) and flashes — this is the path eigsep-field deployments actually use. Changing the field configuration means editing that dict, not passing flags through the CLI.

## Testing

Tests monkeypatch `pyvalon.valon.serial.Serial` with an in-memory `FakeSerial` (see `tests/test_pyvalon.py`) so driver round-trips run without hardware. When adding coverage for a new V500X command, the pattern is: queue the expected reply bytes + checksum onto the fake, invoke the method, then assert both the return value and `fake.sent`. The V5015 string-protocol paths are not covered and would need scripted ASCII reply fixtures.
