"""Load the GRAIL SPICE kernels used by the tools in this folder.

Kernels are not stored in the repo. Set GRAIL_SPICE_DIR (default: a "kernels" folder next to this file)
to a folder holding the files below, all from
https://naif.jpl.nasa.gov/pub/naif/pds/data/grail-l-spice-6-v1.0/grlsp_1000/data/
"""
import glob
import os

import spiceypy as sp

DIR = os.environ.get("GRAIL_SPICE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "kernels"))

FIXED = [
    "naif0010.tls", "pck00009.tpc", "moon_pa_de421_1900_2050.bpc", "moon_080317.tf",
    "de421.bsp", "grail_v07.tf", "gra_mk_v02.ti", "grb_mk_v02.ti",
    "gra_sclkscet_00014.tsc", "grb_sclkscet_00021.tsc",
    "grail_crashsite_v01.tf", "grail_121217_991231_crashsite_v01.bsp",
    "grail_120301_120529_nav_v01.bsp", "grail_120830_121217_nav_v01.bsp",
]


def load():
    sp.kclear()
    for f in FIXED:
        sp.furnsh(os.path.join(DIR, f))
    for f in sorted(glob.glob(os.path.join(DIR, "gr?_rec_*.bc"))):
        sp.furnsh(f)
