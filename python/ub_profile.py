#!/usr/bin/env python3
# Nicolas Seriot, 2013-01-17

"""
UniBinary profiling

$ python3 ub_profile.py
"""

import cProfile
import pstats

from unibinary import gen_encode_unichars_from_bytes, gen_decode_bytes_from_string


def profile_encode_file():
    with open("/Users/nst/Desktop/sc.png", "rb") as f:  # any file ~ 800 KB
        data = f.read()

    with open("/tmp/tmp.txt", 'w', encoding='utf-16') as f:
        for unichars in gen_encode_unichars_from_bytes(data):
            if isinstance(unichars, str):
                f.write(unichars)
            else:
                for u in unichars:
                    f.write(u)


def profile_decode_file():
    with open("/tmp/tmp.txt", "r", encoding='utf-16') as f:
        s = f.read()

    with open("/tmp/tmp.bin", 'wb') as f:
        for chunk in gen_decode_bytes_from_string(s):
            f.write(bytes(chunk))


if __name__ == '__main__':

    for f in [profile_encode_file, profile_decode_file]:

        prof = cProfile.Profile()
        prof.runcall(f)

        s = pstats.Stats(prof)
        s.strip_dirs()
        s.sort_stats('time', 'calls')
        s.print_stats(20)
