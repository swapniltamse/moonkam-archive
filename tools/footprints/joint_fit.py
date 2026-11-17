"""Separate the clock offset from camera mounting errors, using all control-point sets.

Model A: one time offset per camera (what gcp_tools eval finds frame by frame).
Model B: one clock offset for everything (fitted on camera 1, which looks nearly
         straight down and so is least affected by mounting) plus one small fixed
         rotation per camera (a mounting correction), shared by all its frames.

If Model B fits about as well as Model A, the per-camera differences are mounting,
not timing.

Usage: python joint_fit.py <gcp_dir> <set1.csv> <set2.csv> ...
"""
import csv
import json
import math
import os
import sys

import numpy as np
import spiceypy as sp
from scipy.optimize import minimize

from camera import CX, CY, HALF, NX, NY, gc_km
from footprints import utc_of
from kernels import load

ORIENT = (-1, -1)


def read(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    r0 = rows[0]
    return {"name": os.path.basename(path), "craft": r0["craft"], "cam": int(r0["camera"]),
            "et": sp.str2et(utc_of(r0["utc"])),
            "pts": [(float(r["px"]), float(r["py"]), float(r["lon"]), float(r["lat"])) for r in rows]}


def errors(s, offset, rot=(0.0, 0.0, 0.0)):
    m = np.array(sp.eul2m(rot[0], rot[1], rot[2], 3, 2, 1))
    hx, hy = HALF[s["cam"]]
    out = []
    for px, py, lon, lat in s["pts"]:
        v = np.array([ORIENT[0] * math.tan(math.radians(hx)) * (px - CX) / (NX / 2),
                      ORIENT[1] * math.tan(math.radians(hy)) * (py - CY) / (NY / 2), 1.0])
        v = m @ v
        try:
            p, _, _ = sp.sincpt("Ellipsoid", "MOON", s["et"] + offset, "MOON_ME", "LT+S",
                                f"GRAIL-{s['craft']}", f"GRAIL-{s['craft']}_MK{s['cam']}", v.tolist())
        except Exception:
            out.append(50.0)
            continue
        _, lo, la = sp.reclat(p)
        out.append(gc_km((math.degrees(lo), math.degrees(la)), (lon, lat)))
    return out


def rms(errs):
    return math.sqrt(sum(e * e for e in errs) / len(errs))


if __name__ == "__main__":
    load()
    sets = [read(os.path.join(sys.argv[1], f)) for f in sys.argv[2:]]
    report = {"sets": [s["name"] for s in sets]}

    cam1 = [s for s in sets if s["cam"] == 1]
    clk = minimize(lambda x: rms([e for s in cam1 for e in errors(s, x[0])]), [-24.0], method="Nelder-Mead",
                   options={"xatol": 0.01, "fatol": 1e-4}).x[0]
    report["clock_offset_s_from_camera1"] = round(clk, 2)

    report["cameras"] = {}
    for cam in sorted({s["cam"] for s in sets}):
        group = [s for s in sets if s["cam"] == cam]
        # Model A: per-camera time offset
        ta = minimize(lambda x: rms([e for s in group for e in errors(s, x[0])]), [clk], method="Nelder-Mead",
                      options={"xatol": 0.01, "fatol": 1e-4})
        # Model B: fixed clock, per-camera mounting rotation
        rb = minimize(lambda x: rms([e for s in group for e in errors(s, clk, x)]), [0.0, 0.0, 0.0],
                      method="Nelder-Mead", options={"xatol": 1e-6, "fatol": 1e-4, "maxiter": 4000})
        report["cameras"][cam] = {
            "frames": len(group),
            "A_time_offset_s": round(ta.x[0], 2), "A_rms_km": round(ta.fun, 2),
            "B_rotation_deg": [round(math.degrees(v), 3) for v in rb.x], "B_rms_km": round(rb.fun, 2),
            "B_per_frame_rms_km": {s["name"]: round(rms(errors(s, clk, rb.x)), 2) for s in group},
            "no_mount_fix_at_clock_rms_km": round(rms([e for s in group for e in errors(s, clk)]), 2),
        }
    print(json.dumps(report, indent=1))
