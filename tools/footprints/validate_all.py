"""Score the production model (camera.py + footprints.CLOCK_OFFSET_S) on every
control-point set, so the error the site quotes is the error of the code it runs.

Usage: python validate_all.py <gcp_dir> <set.csv>[:camera] ...
       Append :N to force a camera for Flow sets (otherwise flow_cameras.csv is used).
"""
import csv
import json
import math
import os
import sys

import spiceypy as sp

from camera import gc_km, ground
from footprints import clock_offset, flow_cameras, utc_of
from kernels import load

if __name__ == "__main__":
    load()
    flowcam = flow_cameras()
    out = []
    for arg in sys.argv[2:]:
        name, _, forced = arg.partition(":")
        rows = list(csv.DictReader(open(os.path.join(sys.argv[1], name), encoding="utf-8")))
        craft = rows[0]["craft"]
        if rows[0]["camera"]:
            cam, src = int(rows[0]["camera"]), "catalogue"
        elif forced:
            cam, src = int(forced), "forced"
        else:
            g = flowcam.get(rows[0]["frame_file"], "")
            cam, src = (1 if g in ("1 or 4", "") else int(g)), f"classifier ({g or 'missing'})"
        et = sp.str2et(utc_of(rows[0]["utc"])) + clock_offset(craft, cam)
        errs = []
        for r in rows:
            gp = ground(et, craft, cam, float(r["px"]), float(r["py"]))
            errs.append(gc_km(gp, (float(r["lon"]), float(r["lat"]))) if gp else 50.0)
        out.append({"set": name, "craft": craft, "camera": cam, "camera_from": src, "points": len(rows),
                    "rms_km": round(math.sqrt(sum(e * e for e in errs) / len(errs)), 2), "max_km": round(max(errs), 2)})
    for o in out:
        print(json.dumps(o))
