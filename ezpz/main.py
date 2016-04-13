#!/usr/bin/env python

'''
ezpz.py: Pan-Zoom across all the pictures in a directory.
Good for timelapse fun.
'''
import sys
import os
import os.path
import glob
import argparse
import math
import time
from multiprocessing import Pool

from wand.image import Image

class SizeAction(argparse.Action):
    '''Parse an argument of format WxH.'''
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(SizeAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if values is not None:
            setattr(namespace, self.dest, [int(i.strip()) for i in values.lower().split('x', 1)])
        else:
            setattr(namespace, self.dest, None)


def gcm(a, b):
    """Find greatest common multiple of (a,b).
    """
    m = min(a, b)
    for i in range(m, 0, -1):
        if a % i == 0 and b % i == 0:
            return i


def ratio(a, b):
    """Compute the simplified ratio of a:b.
    """
    g = gcm(a, b)
    return a / g, b / g


def ratio_round(a, b, r_1, r_2):
    """Find the closest pair of numbers satisfying the ratio r_1:r2 to a:b.
    """
    amult = float(a) / r_1
    bmult = float(b) / r_2
    tmult = round((amult + bmult) / 2)
    return r_1*tmult, r_2*tmult


def pz(spos, ssize, dpos, dsize, n, force_ratio=False):
    """Yield n pan-zoomed (i, (pos, size)) tuples from starting position
    and size to destination position and size.

    If force_ratio, enforce that all sizes yielded maintain the starting ratio.
    """
    sp_x, sp_y = spos
    ss_w, ss_h = ssize
    dp_x, dp_y = dpos
    ds_w, ds_h = dsize
    ratio_w, ratio_h = ratio(ss_w, ss_h)
    if force_ratio:
        assert ratio_w, ratio_h == ratio(ds_w, ds_h)
    pdiff_x, pdiff_y = float(dp_x - sp_x), float(dp_y - sp_y)
    sdiff_w, sdiff_h = float(ds_w - ss_w), float(ds_h - ss_h)

    def linear_ease(diff, n, _):
        return diff / n

    for i in range(n):
        if force_ratio:
            rs_w, rs_h = ratio_round(ss_w, ss_h, ratio_w, ratio_h)
        else:
            rs_w, rs_h = ratio_w, ratio_h
        yield map(int, map(math.floor, (sp_x, sp_y, rs_w, rs_h)))
        sp_x += linear_ease(pdiff_x, n, i)
        sp_y += linear_ease(pdiff_y, n, i)
        ss_w += linear_ease(sdiff_w, n, i)
        ss_h += linear_ease(sdiff_h, n, i)


def progress_bar(width, percent, char='#'):
    """Progress bar with variable width, scales percentage to width
    """
    width -= 7 + len(str(percent))
    filled = int(round((float(width)*(float(percent)/100))))
    return '\r[ %s%s ] %i ' % (char*filled, '-'*(width-filled), percent) + r'%'


def process(v):
    i, (bb_x, bb_y, bb_w, bb_h) = v
    with Image(filename=files[i]) as image:
        image.format = 'jpeg'
        image.crop(bb_x, bb_y, width=bb_w, height=bb_h)
        if args.resize:
            image.resize(*args.resize)
        image.save(filename=os.path.join(od, files[i]))

parser = argparse.ArgumentParser(description='Crop sequence of jpg images for pan-zoomed timelapse.')
parser.add_argument('spos', action=SizeAction, help="Start position, XxY from top left")
parser.add_argument('ssize', action=SizeAction, help="Start size, WidthxHeight")
parser.add_argument('epos', action=SizeAction, help="End position, XxY from top left")
parser.add_argument('esize', action=SizeAction, help="End size, WidthxHeight")
parser.add_argument('--resize', metavar='size', action=SizeAction, help="Resize all to this WidthxHeight", default=None)
parser.add_argument('--parallel', metavar='P', help="Number of processes to run in parallel", default=1, type=int)
parser.add_argument('--force-aspect', action='store_true', help="Whether to force all frames to same aspect ratio", default=False)
parser.add_argument('--working-dir', action='store_true', help="Where to find images", default=".")
args = parser.parse_args()

wd = args.working_dir
od = os.path.join(wd, "pz_out")
files = glob.glob(os.path.join(wd, "*.jpg"))
files.sort(key=os.path.getmtime)
n = len(files)


def main():
    if not os.path.exists(od):
        os.makedirs(od)
    start = time.time()
    pool = Pool(args.parallel)
    x = 0
    sys.stdout.write(progress_bar(80, 0))
    sys.stdout.flush()
    for _ in pool.imap_unordered(process,
            enumerate(pz(args.spos, args.ssize, args.epos, args.esize, n)), 5):
        x += 1
        sys.stdout.write(progress_bar(80, 100.0 * x / n))
        sys.stdout.flush()

    print("\nFinished processing {} images in {:.2f}s".format(n, time.time() - start))


if __name__ == '__main__':
    main()
