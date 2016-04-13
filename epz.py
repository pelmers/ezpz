#!/usr/bin/env python

'''
epz.py: Pan-Zoom across all the pictures in a directory.
Good for timelapse fun.
'''
import math
import os
import sys
import os.path
import glob
import argparse

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
    m = min(a, b)
    for i in range(m, 0, -1):
        if a % i == 0 and b % i == 0:
            return i


def ratio(a, b):
    g = gcm(a, b)
    return a / g, b / g


def ratio_round(a, b, r_1, r_2):
    amult = float(a) / r_1
    bmult = float(b) / r_2
    tmult = round((amult + bmult) / 2)
    return r_1*tmult, r_2*tmult


def tpz(spos, ssize, dpos, dsize, n, force_ratio=False):
    sp_x, sp_y = spos
    ss_w, ss_h = ssize
    dp_x, dp_y = dpos
    ds_w, ds_h = dsize
    ratio_w, ratio_h = ratio(ss_w, ss_h)
    if force_ratio:
        print "Asserting equality of input-output ratios: {}x{}".format(ratio_w, ratio_h)
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


parser = argparse.ArgumentParser(description='Crop sequence of jpg images for pan-zoomed timelapse.')
# TODO: add start_pos start_size end_pos end_size [resize_size] [force aspect?] [working-dir?]
parser.add_argument('spos', action=SizeAction, help="Start position, XxY from top left")
parser.add_argument('ssize', action=SizeAction, help="Start size, WidthxHeight")
parser.add_argument('epos', action=SizeAction, help="End position, XxY from top left")
parser.add_argument('esize', action=SizeAction, help="End size, WidthxHeight")
parser.add_argument('--resize', action=SizeAction, help="Resize all to this WidthxHeight", default=None)
parser.add_argument('--force-aspect', action='store_true', help="Whether to force all frames to same aspect ratio", default=False)
parser.add_argument('--working-dir', action='store_true', help="Where to find images", default=".")

def main():
    # TODO: use argparse....
    args = parser.parse_args()
    wd = args.working_dir
    od = os.path.join(wd, "pz_out")
    if not os.path.exists(od):
        os.makedirs(od)
    files = glob.glob(os.path.join(wd, "*.jpg"))
    files.sort(key=os.path.getmtime)
    n = len(files)
    for (i, (bb_x, bb_y, bb_w, bb_h)) in enumerate(
            tpz(args.spos, args.ssize, args.epos, args.esize, n)):
        with Image(filename=files[i]) as image:
            image.format = 'jpeg'
            image.crop(bb_x, bb_y, width=bb_w, height=bb_h)
            if args.resize:
                image.resize(*args.resize)
            image.save(filename=os.path.join(od, files[i]))

if __name__ == '__main__':
    main()
