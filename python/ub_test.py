#!/usr/bin/env python3
# Nicolas Seriot, 2013-01-17

"""
UniBinary tests

$ python3 ub_test.py
"""

import hashlib
import unittest

from unibinary import *


def shasum(filename):
    m = hashlib.sha1()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * m.block_size), b''):
            m.update(chunk)
    return m.hexdigest()


class TestUnidata(unittest.TestCase):

    def test_unichr_12_encoding_decoding(self):

        for i in [0x0, 0x1, 0xAB, 0x123, 0xABC, 0xF, 0xFF, 0xFFF]:

            u = unichr_12_from_int(i)
            self.assertNotEqual(i, u)

            i2 = int_from_u12b(u)
            self.assertEqual(i, i2)

    def test_3_to_2_bytes(self):

        (a, b) = two_twelve_bits_values_from_three_bytes(0x12, 0x34, 0x56)

        self.assertEqual(a, 0x123, "0x%x" % a)
        self.assertEqual(b, 0x456, "0x%x" % b)

    def test_2_to_3_bytes(self):

        (a, b, c) = three_bytes_from_two_twelve_bits_values(0x123, 0x456)

        self.assertEqual(a, 0x12, "0x%x" % a)
        self.assertEqual(b, 0x34, "0x%x" % b)
        self.assertEqual(c, 0x56, "0x%x" % c)

    def test_encode_3_bytes(self):
        data = b"\xab\xcd\xef"

        gen = gen_encode_unichars_from_bytes(data)

        (u1, u2) = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(u1, chr(U12b_start + 0xABC))
        self.assertEqual(u2, chr(U12b_start + 0xDEF))

    def test_encode_bytes(self):
        data = b"\xab\xcd\xef\xff"

        gen = gen_encode_unichars_from_bytes(data)

        (u1, u2) = next(gen)
        u3 = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(u1, chr(U12b_start + 0xABC))
        self.assertEqual(u2, chr(U12b_start + 0xDEF))
        self.assertEqual(u3, chr(U8_start + 0xFF))

    def test_decode_unichars(self):

        u1 = chr(U12b_start + 0xABC)
        u2 = chr(U12b_start + 0xDEF)

        s = ''
        s += u1
        s += u2

        gen = gen_decode_bytes_from_string(s)

        (a, b, c) = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(a, 0xAB)
        self.assertEqual(b, 0xCD)
        self.assertEqual(c, 0xEF)

    def test_is_in_U8b(self):
        self.assertFalse(is_in_U8b("Ͽ"))

        self.assertTrue(is_in_U8b("Ѐ"))
        self.assertTrue(is_in_U8b("ӿ"))

        self.assertFalse(is_in_U8b("Ԁ"))

    def test_encoding_decoding_utf16_file(self):

        src = "/usr/bin/true"
        tmp = "/tmp/true.txt"
        cpy = "/tmp/true"

        import os
        if not os.path.exists(src):
            print("-- WARNING: cannot test %s, file does not exist" % src)
            return

        for e in ['utf-8', 'utf-16']:

            with open(src, "rb") as f:
                data = f.read()

            with open(tmp, 'w', encoding=e) as f:
                for unichars in gen_encode_unichars_from_bytes(data):
                    if isinstance(unichars, str):
                        f.write(unichars)
                    else:
                        for u in unichars:
                            f.write(u)

            ##

            with open(tmp, 'r', encoding=e) as f:
                s = f.read()

            with open(cpy, 'wb') as f:
                for chunk in gen_decode_bytes_from_string(s):
                    f.write(bytes(chunk))

            shasum_src = shasum(src)
            shasum_cpy = shasum(cpy)

            self.assertEqual(shasum_src, shasum_cpy)

    def test_unichr_12a_from_two_ascii(self):
        u = unichr_12a_from_two_ascii('Z', 'E')
        self.assertEqual(u, "钅")

        u = unichr_12a_from_two_ascii('z', ',')
        self.assertEqual(u, "責")

    def test_ascii_characters_encoding(self):
        s = b"abc"

        gen = gen_encode_unichars_from_bytes(s)

        u0 = next(gen)
        u1 = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(u0, "院")
        self.assertEqual(u1, "ѣ")

    def test_ascii_characters_encoding_2(self):

        s = b"ZE"

        gen = gen_encode_unichars_from_bytes(s)

        u0 = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(u0, unichr_12a_from_two_ascii('Z', 'E'))

    def test_two_unichr_to_repeat_byte_ntimes_aaa(self):
        (uni_b, uni_r) = two_unichr_to_repeat_byte_ntimes(ord('a'), 10)

        self.assertEqual(ord(uni_b), 0x0461)
        self.assertEqual(ord(uni_r), 0x4E0A)

    def test_two_unichr_to_repeat_byte_ntimes_xxx(self):
        (uni_b, uni_r) = two_unichr_to_repeat_byte_ntimes(ord('x'), 3)

        self.assertEqual(ord(uni_b), 0x0478)
        self.assertEqual(ord(uni_r), 0x4E03)

    def test_repeat(self):

        s = b"xxx"

        gen = gen_encode_unichars_from_bytes(s)

        (u0, u1) = next(gen)

        self.assertFalse(list(gen))

        print("%x %x" % (ord(u0), ord(u1)))

        self.assertEqual(ord(u0), 0x0478)
        self.assertEqual(ord(u1), 0x4E03)

    def test_ascii_characters_decoding(self):

        s = ["院", "ѣ"]

        s2 = []
        for chunks in gen_decode_bytes_from_string(s):
            for b in chunks:
                s2.append(b)

        self.assertEqual(s2[0], ord('a'))
        self.assertEqual(s2[1], ord('b'))
        self.assertEqual(s2[2], ord('c'))

    def test_ascii_characters_decoding_2(self):

        s = ["钅"]

        s2 = []
        for chunks in gen_decode_bytes_from_string(s):
            for b in chunks:
                s2.append(b)

        self.assertEqual(s2[0], ord('Z'))
        self.assertEqual(s2[1], ord('E'))

    def test_five_bytes_encoding(self):
        data = b"\xab\xcd\xef\xab\xcd"
        gen = gen_encode_unichars_from_bytes(data)

        (u1, u2) = next(gen)
        u3 = next(gen)
        u4 = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(u1, chr(U12b_start + 0xABC))
        self.assertEqual(u2, chr(U12b_start + 0xDEF))
        self.assertEqual(u3, unichr_08_from_int(0xAB))
        self.assertEqual(u4, unichr_08_from_int(0xCD))

    def test_ascii_and_bytes_encoding(self):
        data = b"\xab\xcd\xef"
        data += b"\x61\x62\x63\x64\x65"  # abcde

        gen = gen_encode_unichars_from_bytes(data)

        (u1, u2) = next(gen)
        u3 = next(gen)
        u4 = next(gen)
        u5 = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(u1, chr(U12b_start + 0xABC))
        self.assertEqual(u2, chr(U12b_start + 0xDEF))
        self.assertEqual(u3, unichr_12a_from_two_ascii('a', 'b'))
        self.assertEqual(u4, unichr_12a_from_two_ascii('c', 'd'))
        self.assertEqual(u5, unichr_08_from_int(ord('e')))

    def test_ascii_and_bytes_decoding(self):

        u1 = chr(U12b_start + 0xABC)
        u2 = chr(U12b_start + 0xDEF)
        u3 = unichr_12a_from_two_ascii('a', 'b')
        u4 = unichr_12a_from_two_ascii('c', 'd')
        u5 = unichr_08_from_int(ord('e'))

        s = ''
        s += u1
        s += u2
        s += u3
        s += u4
        s += u5

        gen = gen_decode_bytes_from_string(s)

        (a, b, c) = next(gen)
        (d, e) = next(gen)
        (f, g) = next(gen)
        h = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(a, 0xAB)
        self.assertEqual(b, 0xCD)
        self.assertEqual(c, 0xEF)

    def test_repeats(self):

        l = [1, 1, 1, 2, 1]

        n = number_of_left_instances_from_index(l, 0)

        self.assertEqual(n, 3)

    def test_empty_string(self):

        data = b""

        gen = gen_encode_unichars_from_bytes(data)

        self.assertFalse(list(gen))

    def test_one_char(self):

        data = b"a"

        gen = gen_encode_unichars_from_bytes(data)

        u1 = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(ord(u1), 0x0461)

    def test_repeats_2(self):

        data = b"\xAB\xCD\xEF\xFF\xFF\xFF\xFF\x00"

        gen = gen_encode_unichars_from_bytes(data)

        (u1, u2) = next(gen)
        (u3, u4) = next(gen)
        u5 = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(ord(u1), 0x58BC)
        self.assertEqual(ord(u2), 0x5bEF)
        self.assertEqual(ord(u3), 0x04FF)
        self.assertEqual(ord(u4), 0x4E04)
        self.assertEqual(ord(u5), 0x0400)

    def test_encode_macho_header(self):

        data = b"\xCF\xFA\xED\xFE\x07\x00\x00\x01"

        gen = gen_encode_unichars_from_bytes(data)

        (u1, u2) = next(gen)
        (u3, u4) = next(gen)
        u5 = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(ord(u1), 0x5AFF)
        self.assertEqual(ord(u2), 0x58ED)
        self.assertEqual(ord(u3), 0x5DE0)
        self.assertEqual(ord(u4), 0x5500)
        self.assertEqual(ord(u5), 0x5E01)

    def test_big_repeats_2000_minus_2(self):

        data = b"\xAA" * (0x2000 - 2)

        gen = gen_encode_unichars_from_bytes(data)

        (u1, u2) = next(gen)
        (u3, u4) = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(ord(u1), 0x04AA)
        self.assertEqual(ord(u2), 0x5DFF)
        self.assertEqual(ord(u3), 0x04AA)
        self.assertEqual(ord(u4), 0x5DFF)

    def test_big_repeats_2000(self):

        data = b"\xAA" * 0x2000

        gen = gen_encode_unichars_from_bytes(data)

        (u1, u2) = next(gen)
        (u3, u4) = next(gen)
        u5 = next(gen)
        u6 = next(gen)

        self.assertFalse(list(gen))

        self.assertEqual(ord(u1), 0x04AA)
        self.assertEqual(ord(u2), 0x5DFF)
        self.assertEqual(ord(u3), 0x04AA)
        self.assertEqual(ord(u4), 0x5DFF)
        self.assertEqual(ord(u5), 0x04AA)
        self.assertEqual(ord(u6), 0x04AA)

    def test_ascii_text_encoding_decoding(self):

        s = (b"if I'd listened everything that they said to me, "
             b"took the time to bleed from all the tiny little arrows "
             b"shot my way, I wouldn't be here! the ones who don't do "
             b"anything are always the ones who try to put you down. "
             b"I'm talking to you: hero time starts right now! time to shine!")

        encode_gen = gen_encode_unichars_from_bytes(s)

        e = [b for b in encode_gen]

        s2 = b''.join(bytes(chunk) for chunk in gen_decode_bytes_from_string(e))

        self.assertEqual(s, s2)

    def test_ascii_text_encoding_decoding_2(self):

        s = bytes(range(32, 128))

        encode_gen = gen_encode_unichars_from_bytes(s)

        e = [b for b in encode_gen]

        self.assertTrue(len(e) * 2 == len(s))

        s2 = b''.join(bytes(chunk) for chunk in gen_decode_bytes_from_string(e))

        self.assertEqual(s, s2)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnidata)
    unittest.TextTestRunner(verbosity=2).run(suite)
