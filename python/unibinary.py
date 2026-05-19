#!/usr/bin/env python3
# Nicolas Seriot, 2013-01-17

"""
UniBinary, or "Base64 for Unicode".

Encodes and decodes data into printable Unicode characters.

2 ASCII characters -> 1 unicode character
3 arbitrary bytes  -> 2 unicode characters
[3, 0xFFF] repeats -> 2 unicode characters

The encoded text can be copied / pasted / posted on Twitter and stored as UTF-8 text files.

http://github.com/nst/UniBinary/

$ python3 unibinary.py -h

$ python3 unibinary.py -e /bin/date > /tmp/date.txt
$ file /tmp/date.txt
/tmp/date.txt: UTF-8 Unicode text, with very long lines, with no line terminators

$ python3 unibinary.py -d /tmp/date.txt > /tmp/date
"""

import sys
import argparse

__author__ = "Nicolas Seriot"
__license__ = "BSD"

# http://docs.python.org/3/howto/unicode.html
# http://unicode.org/Public/UNIDATA/Blocks.txt

# encodes ascii characters (7 bits)
U12a_0_0_start = 0x5E00  # CJK Unified Ideographs (subset) - encodes 12 bits (2 ascii) - MSB 0,0
U12a_0_1_start = 0x6E00  # CJK Unified Ideographs (subset) - encodes 12 bits (2 ascii) - MSB 0,1
U12a_1_0_start = 0x7E00  # CJK Unified Ideographs (subset) - encodes 12 bits (2 ascii) - MSB 1,0
U12a_1_1_start = 0x8E00  # CJK Unified Ideographs (subset) - encodes 12 bits (2 ascii) - MSB 1,1
U12a_length = 0x1000

# encodes arbitrary bits
U12b_start = 0x4E00  # CJK Unified Ideographs (subset) - encodes 12 bits
U12b_length = 0x1000
U8_start = 0x0400    # Cyrillic                        - encodes 8 bits
U8_length = 0x100


def two_unichr_to_repeat_byte_ntimes(b, n):
    if n > 0xFFF:
        raise ValueError

    if b > 0xFF:
        raise ValueError

    return (chr(U8_start + b), chr(U12b_start + n))


def unichr_12a_from_two_ascii(a1, a2):
    i1 = a1 if isinstance(a1, int) else ord(a1)
    i2 = a2 if isinstance(a2, int) else ord(a2)

    unicode_start = None

    if i1 < 64 and i2 < 64:
        unicode_start = U12a_0_0_start
    elif i1 < 64 and i2 >= 64:
        i2 -= 64
        unicode_start = U12a_0_1_start
    elif i1 >= 64 and i2 < 64:
        i1 -= 64
        unicode_start = U12a_1_0_start
    elif i1 >= 64 and i2 >= 64:
        i1 -= 64
        i2 -= 64
        unicode_start = U12a_1_1_start

    return chr(unicode_start + (i1 << 6) + i2)


def unichr_08_from_int(i):
    if i > (U8_start + U8_length):
        print("-- unichr_08_from_int: 0x%x" % i)
        raise ValueError

    return chr(U8_start + i)


def unichr_12_from_int(i):
    if i > (U12b_start + U12b_length):
        print("-- unichr_12_from_int: 0x%x" % i)
        raise ValueError

    return chr(U12b_start + i)


def int_from_u08b(u):
    i = ord(u)

    if i < U8_start or i > (U8_start + U8_length):
        print("-- int_from_u08b: %s" % u)
        raise ValueError

    return i - U8_start


def two_bytes_from_u12a(u):
    unicode_start = None

    i = ord(u)
    for start in (U12a_0_0_start, U12a_0_1_start, U12a_1_0_start, U12a_1_1_start):
        if i >= start and i < (start + U12a_length):
            unicode_start = start
            break

    if not unicode_start:
        print("-- two_bytes_from_u12a ord=0x%02x" % ord(u))
        raise ValueError

    value = i - unicode_start
    b0 = (value & 0xFC0) >> 6
    b1 = i & 0x3F

    if unicode_start == U12a_0_0_start:
        pass
    elif unicode_start == U12a_0_1_start:
        b1 += 64
    elif unicode_start == U12a_1_0_start:
        b0 += 64
    elif unicode_start == U12a_1_1_start:
        b0 += 64
        b1 += 64

    return (b0, b1)


def int_from_u12b(u):
    i = ord(u)

    if i < U12b_start or i > (U12b_start + U12b_length):
        print("-- int_from_u12b: %s" % u)
        raise ValueError

    return i - U12b_start


def two_twelve_bits_values_from_three_bytes(a, b, c):
    # (0x12, 0x34, 0x56) -> (0x123, 0x456)

    if a > 0xFF or b > 0xFF or c > 0xFF:
        raise ValueError

    s1 = (a << 4) + (b >> 4)
    s2 = ((b & 0xF) << 8) + c

    return (s1, s2)


def three_bytes_from_two_twelve_bits_values(i1, i2):
    # (0x123, 0x456) -> (0x12, 0x34, 0x56)

    if i1 > 0xFFF or i2 > 0xFFF:
        raise ValueError

    b1 = i1 >> 4
    b2 = ((i1 & 0xF) << 4) + ((i2 & 0xF00) >> 8)
    b3 = i2 & 0x0FF

    return (b1, b2, b3)


def number_of_left_instances_from_index(l, index):
    i = index
    c = 0
    x = l[i]
    while i < len(l):
        if l[i] == x:
            c += 1
        else:
            break
        i += 1

    return c


def three_bytes_from_unichars(u1, u2):
    i1 = int_from_u12b(u1)
    i2 = int_from_u12b(u2)
    return three_bytes_from_two_twelve_bits_values(i1, i2)


def repeated_bytes_from_unichars(u1, u2):
    b = int_from_u08b(u1)
    n = int_from_u12b(u2)
    return [b] * n


def two_bytes_from_unichars(u1, u2):
    b1 = int_from_u08b(u1)
    b2 = int_from_u08b(u2)
    return (b1, b2)


def is_in_U12a(u):
    i = ord(u)

    for unicode_start in (U12a_0_0_start, U12a_0_1_start, U12a_1_0_start, U12a_1_1_start):
        if i >= unicode_start and i < (unicode_start + U12a_length):
            return True

    return False


def is_in_U8b(u):
    i = ord(u)
    return i >= U8_start and i < (U8_start + U8_length)


def is_in_U12b(u):
    i = ord(u)
    return i >= U12b_start and i < (U12b_start + U12b_length)


def bytes_from_u1_u2(u1, u2):

    u1_in_U12 = is_in_U12b(u1)
    u2_in_U12 = is_in_U12b(u2)

    u1_in_U8 = is_in_U8b(u1)
    u2_in_U8 = is_in_U8b(u2)

    if u1_in_U12 and u2_in_U12:
        return three_bytes_from_unichars(u1, u2)
    elif u1_in_U8 and u2_in_U12:
        return repeated_bytes_from_unichars(u1, u2)
    elif u1_in_U8 and u2_in_U8:
        return two_bytes_from_unichars(u1, u2)
    else:
        print("-- %s %s 0x%x 0x%x" % (u1, u2, ord(u1), ord(u2)))
        raise ValueError


def _coerce_to_bytes(data):
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, str):
        return data.encode('latin-1')
    if isinstance(data, list):
        if not data:
            return b''
        if isinstance(data[0], str):
            return bytes(ord(c) for c in data)
        return bytes(data)
    return bytes(data)


def gen_encode_unichars_from_bytes(data):

    data = _coerce_to_bytes(data)

    i = 0

    while i < len(data):
        r = number_of_left_instances_from_index(data, i)

        if r >= 3:
            # read N bytes | N >= 3 and N < 0x1000, encode as 2 unichar

            if r >= 0x1000:
                r = 0xFFF

            (uni_b, uni_n) = two_unichr_to_repeat_byte_ntimes(data[i], r)
            i += r
            yield (uni_b, uni_n)

        else:

            two_ascii_chars_available = (len(data) >= i + 2
                                         and data[i] < 128
                                         and data[i + 1] < 128)

            if two_ascii_chars_available:
                # read 2 x 7 bits, encode 1 unichar
                a1 = data[i]
                a2 = data[i + 1]
                i += 2
                yield unichr_12a_from_two_ascii(a1, a2)

            elif len(data) >= i + 3:
                # read 3 bytes, encode 2 unichars
                (s1, s2) = two_twelve_bits_values_from_three_bytes(
                    data[i], data[i + 1], data[i + 2])
                i += 3
                yield (unichr_12_from_int(s1), unichr_12_from_int(s2))

            else:
                # read 1 byte, encode 1 unichar
                b = data[i]
                i += 1
                yield unichr_08_from_int(b)


def gen_decode_bytes_from_string(s):

    if isinstance(s, list):
        s = ''.join(s)

    i = 0

    while i < len(s):

        if s[i] == '\n':
            i += 1
            continue

        if is_in_U12a(s[i]):
            # 1 U12a -> read 2 ascii characters
            data = two_bytes_from_u12a(s[i])
            i += 1
            yield data
        elif i + 1 < len(s):
            # (U12b, U12b) -> read 3 bytes
            # (U8b, U12b) -> read repetition
            # (U8b, U8b) -> read 1 byte, 1 byte
            u1 = s[i]
            i += 1

            while i < len(s) and s[i] == '\n':
                i += 1

            if i >= len(s):
                if is_in_U8b(u1):
                    yield (int_from_u08b(u1),)
                    return
                print("-- cannot decode", s)
                sys.exit(1)

            u2 = s[i]
            i += 1

            yield bytes_from_u1_u2(u1, u2)
        elif is_in_U8b(s[i]):
            # 1 U8b -> read 1 byte
            b = int_from_u08b(s[i])
            i += 1
            yield (b,)
        else:
            print("-- cannot decode", s)
            sys.exit(1)


def _unichars_to_str(unichars):
    if isinstance(unichars, str):
        return unichars
    return ''.join(unichars)


def print_decoded_string(s):
    out = sys.stdout.buffer
    for chunk in gen_decode_bytes_from_string(s):
        out.write(bytes(chunk))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='UniBinary encodes and decodes data into printable Unicode characters.')
    parser.add_argument('-e', '--encode', help='file to encode')
    parser.add_argument('-d', '--decode', help='file to decode')
    parser.add_argument('-es', '--encode_string', help='utf-8 string to encode')
    parser.add_argument('-ds', '--decode_string', help='utf-8 string to decode')
    args = vars(parser.parse_args())

    if args['encode']:
        with open(args['encode'], "rb") as f:
            data = f.read()

        for unichars in gen_encode_unichars_from_bytes(data):
            sys.stdout.write(_unichars_to_str(unichars))

        sys.stdout.flush()
        sys.stderr.write('\n')

    elif args['decode']:
        with open(args['decode'], "r", encoding='utf-8') as f:
            s = f.read()

        print_decoded_string(s)

        sys.stdout.flush()
        sys.stderr.write('\n')

    elif args['encode_string']:
        data = args['encode_string'].encode('utf-8')
        for unichars in gen_encode_unichars_from_bytes(data):
            sys.stdout.write(_unichars_to_str(unichars))

        sys.stdout.flush()
        sys.stderr.write('\n')

    elif args['decode_string']:
        print_decoded_string(args['decode_string'])

        sys.stdout.flush()
        sys.stderr.write('\n')

    else:
        parser.print_help()
