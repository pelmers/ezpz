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


def gcm(a, b):
    m = min(a, b)
    for i in range(m, 0, -1):
        if a % i == 0 and b % i == 0:
            return i


def ratio(a, b):
    g = gcm(a, b)
    return a / g, b / g


def ratio_floor(a, b, r_1, r_2):
    amult = float(a) / r_1
    bmult = float(b) / r_2
    # TODO: should I use floor instead?
    tmult = round((amult + bmult) / 2)
    return r_1*tmult, r_2*tmult


def tpz(sp_x, sp_y, ss_w, ss_h, dp_x, dp_y, ds_w, ds_h, n):
    ratio_w, ratio_h = ratio(ss_w, ss_h)
    print "Asserting equality of input-output ratios: {}x{}".format(ratio_w, ratio_h)
    assert ratio_w, ratio_h == ratio(ds_w, ds_h)
    pdiff_x, pdiff_y = float(dp_x - sp_x), float(dp_y - sp_y)
    sdiff_w, sdiff_h = float(ds_w - ss_w), float(ds_h - ss_h)

    def ease(diff, n, _):
        return diff / n

    for i in range(n):
        rs_w, rs_h = ratio_floor(ss_w, ss_h, ratio_w, ratio_h)
        yield (math.floor(sp_x), math.floor(sp_y), rs_w, rs_h)
        sp_x += ease(pdiff_x, n, i)
        sp_y += ease(pdiff_y, n, i)
        ss_w += ease(sdiff_w, n, i)
        ss_h += ease(sdiff_h, n, i)


def main():
    # TODO: use argparse....
    wd = sys.argv[1]
    od = os.path.join(wd, "pz_out")
    if not os.path.exists(od):
        os.makedirs(od)
    sp_x, sp_y, ss_w, ss_h, dp_x, dp_y, ds_w, ds_h, os_w, os_h = map(int, sys.argv[2:])
    files = glob.glob(os.path.join(wd, "*.jpg"))
    files.sort(key=os.path.getmtime)
    n = len(files)
    for (i, (bb_x, bb_y, bb_w, bb_h)) in enumerate(
            tpz(sp_x, sp_y, ss_w, ss_h, dp_x, dp_y, ds_w, ds_h, n)):
        crop_geometry = "{:.0f}x{:.0f}+{:.0f}+{:.0f}".format(bb_w, bb_h, bb_y, bb_x)
        resize_geometry= "{}x{}".format(os_w, os_h)
        cmd = " ".join(["mogrify", "-path", od, "-crop", crop_geometry, "-resize", resize_geometry, files[i]])
        print cmd
        # TODO: use subprocess, maybe parallelize
        if os.system(cmd):
            break


if __name__ == '__main__':
    main()
