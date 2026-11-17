"""Known-answer test: project the 9 hand-placed control points of the Carrel
frame (titan-data-atlas docs/moonkam-walkthrough.md) and compare with the
lon/lat a person read off the LRO WAC basemap. Run all four image
orientations; exactly one should fit, the mirrored ones are the controls."""
import math

import spiceypy as sp

from camera import ground, gc_km
from kernels import load

GCP = [  # pixel x, pixel y, lon E, lat N
    (567.5, 170.5, 26.7071, 10.6648), (661.5, 81.5, 26.4655, 10.8951),
    (484.5, 280.5, 26.9900, 10.4770), (613.5, 388.5, 27.3321, 10.7228),
    (658.5, 402.5, 27.3735, 10.8625), (153.5, 345.5, 27.1591, 9.7459),
    (190.5, 383.5, 27.2687, 9.8461), (113.5, 177.5, 26.7461, 9.6337),
    (93.5, 387.5, 27.3303, 9.5833),
]
UTC = "2012-03-29T14:38:20.494"

if __name__ == "__main__":
    load()
    et0 = sp.str2et(UTC)
    for offset in (0.0, -24.0):  # -24.0 s is the clock offset used in footprints.py
        print(f"clock offset {offset:+.1f} s")
        for orient in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            errs = []
            for px, py, lon, lat in GCP:
                g = ground(et0 + offset, "A", 1, px, py, orient)
                errs.append(gc_km(g, (lon, lat)) if g else float("nan"))
            rms = math.sqrt(sum(e * e for e in errs) / len(errs))
            print(f"  orient X{orient[0]:+d} Y{orient[1]:+d}: RMS {rms:6.2f} km, max {max(errs):6.2f} km")
