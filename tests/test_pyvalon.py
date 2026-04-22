"""Tests for pyvalon.

The V500X/V5015 driver classes talk over pyserial, so we monkeypatch
``serial.Serial`` with an in-memory fake. This lets us exercise the
checksum + pack/unpack helpers and a few full command round-trips
without hardware.
"""

import struct

import pytest

from pyvalon import V500X, V5007, V5008, V5015, Valon
from pyvalon import valon as valon_mod


class FakeSerial:
    """In-memory stand-in for ``serial.Serial``.

    ``queue(data)`` stages bytes the driver will later read back.
    ``sent`` accumulates everything the driver writes.
    """

    def __init__(self, *args, **kwargs):
        self.sent = bytearray()
        self._replies = bytearray()

    def queue(self, data):
        self._replies += bytes(data)

    def write(self, data):
        self.sent += bytes(data)

    def read(self, n):
        out = bytes(self._replies[:n])
        del self._replies[:n]
        return out

    def close(self):
        pass


@pytest.fixture
def fake_v500x(monkeypatch):
    fake = FakeSerial()
    monkeypatch.setattr(
        valon_mod.serial, "Serial", lambda *a, **kw: fake
    )
    synth = V500X("/dev/null", 9600)
    return synth, fake


def test_package_exports():
    assert issubclass(V5007, V500X)
    assert issubclass(V5008, V500X)
    assert V5015.__mro__[1] is Valon


def test_generate_checksum(fake_v500x):
    synth, _ = fake_v500x
    assert synth._generate_checksum(b"\x00\x01\x02") == 0x03
    assert synth._generate_checksum(b"\xff\x01") == 0x00
    assert synth._generate_checksum(b"") == 0


def test_pack_unpack_int_roundtrip(fake_v500x):
    synth, _ = fake_v500x
    buf = bytearray(8)
    synth._pack_int(0x11223344, buf, 0)
    synth._pack_int(-1, buf, 4)
    assert bytes(buf[:4]) == b"\x11\x22\x33\x44"
    assert synth._unpack_int(buf, 0) == 0x11223344
    assert synth._unpack_int(buf, 4) == -1


def test_pack_unpack_short_roundtrip(fake_v500x):
    synth, _ = fake_v500x
    buf = bytearray(4)
    synth._pack_short(0x1234, buf, 0)
    synth._pack_short(100, buf, 2)
    assert synth._unpack_short(buf, 0) == 0x1234
    assert synth._unpack_short(buf, 2) == 100


def test_freq_registers_roundtrip(fake_v500x):
    synth, _ = fake_v500x
    buf = bytearray(24)
    regs = {"ncount": 100, "frac": 500, "mod": 4095, "dbf": 4}
    synth._pack_freq_registers(regs, buf, 0)
    assert synth._unpack_freq_registers(buf) == regs


def test_verify_checksum(fake_v500x):
    synth, _ = fake_v500x
    data = b"\xaa\xbb\xcc"
    cs = synth._generate_checksum(data)
    assert synth._verify_checksum(data, bytes([cs])) is True
    assert synth._verify_checksum(data, bytes([cs ^ 1])) is False


def test_get_reference(fake_v500x):
    synth, fake = fake_v500x
    payload = struct.pack(">I", 10_000_000)
    fake.queue(payload + bytes([synth._generate_checksum(payload)]))
    assert synth.GetReference() == 10_000_000
    assert bytes(fake.sent) == bytes([0x81])


def test_set_reference_ack(fake_v500x):
    synth, fake = fake_v500x
    fake.queue(bytes([V500X.REPLY["ACK"]]))
    assert synth.SetReference(10_000_000) is True
    expected = struct.pack(">BI", 0x01, 10_000_000)
    cs = synth._generate_checksum(expected)
    assert bytes(fake.sent) == expected + bytes([cs])


def test_set_reference_nack(fake_v500x):
    synth, fake = fake_v500x
    fake.queue(bytes([V500X.REPLY["NACK"]]))
    assert synth.SetReference(10_000_000) is False


def test_flash_ack(fake_v500x):
    synth, fake = fake_v500x
    fake.queue(bytes([V500X.REPLY["ACK"]]))
    assert synth.Flash() is True
    assert bytes(fake.sent[:1]) == bytes([0x40])


def test_eigsep_defaults_shape():
    from pyvalon.v5008 import EIGSEP_DEFAULTS

    assert set(EIGSEP_DEFAULTS) == {"A", "B", "ref"}
    assert EIGSEP_DEFAULTS["ref"] == "external"
    assert EIGSEP_DEFAULTS["A"]["freq"] == 500.0
    assert EIGSEP_DEFAULTS["B"]["freq"] == 250.0
    assert EIGSEP_DEFAULTS["A"]["amp"] == 5
    assert EIGSEP_DEFAULTS["B"]["amp"] == 5
