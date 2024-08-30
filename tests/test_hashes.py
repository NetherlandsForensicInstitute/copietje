from copietje import HASH_FUNCTIONS

import pytest


s = HASH_FUNCTIONS['sha1']
m = HASH_FUNCTIONS['mmh3']
c = HASH_FUNCTIONS['crc32']


@pytest.mark.parametrize(
    ('data', 'hash_func', 'value'),
    (
        (b'', s, 4003674586),
        (b'', m, 0),
        (b'', c, 0),
        # binary data chosen so mmh3 will produce a negative value unless forced to use unsigned values
        (b'abcd1234efgh5678', s, 3767009287),
        (b'abcd1234efgh5678', m, 3336711770),
        (b'abcd1234efgh5678', c, 864535597),
        (b'\x04\x03\x02\x01', s, 883442974),
        (b'\x04\x03\x02\x01', m, 1165084099),
        (b'\x04\x03\x02\x01', c, 3914441734),
    )
)
def test_hash_values(data, hash_func, value):
    assert hash_func(data) == value
