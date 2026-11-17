"""Compute a ground footprint for every MoonKAM frame in the public catalogue.

For each frame: the point below the spacecraft, altitude, the ground point at
the image centre and corners, how much of the image falls on the Moon, the
sun's incidence angle at the centre, and the nearest named feature from the
USGS gazetteer.

Clock offset: the Carrel control-point test (validate_carrel.py) fits the
file-name time as 24.0 s late. CLOCK_OFFSET_S applies that to every frame.
It is measured on one frame only, so the output also keeps the centre point
computed without it.

Flow (GRAIL-B) rows have no camera in the catalogue, so they get the point
below the spacecraft only.

Usage: python footprints.py <catalogue.csv> <out.csv>
"""
import csv
import math
import sys

import spiceypy as sp

from camera import NX, NY, ground
from gazetteer import features
from kernels import load

CLOCK_OFFSET_S = -24.0
R = 1737.4


def utc_of(s):
    # catalogue form: 2012-088-23:04:42.337 -> 2012-088T23:04:42.337
    y, doy, rest = s.split("-", 2)
    return f"{y}-{doy}T{rest}"


def subpoint(et, craft):
    st, _ = sp.spkezr(f"GRAIL-{craft}", et, "MOON_ME", "LT+S", "MOON")
    r, lon, lat = sp.reclat(st[:3])
    return math.degrees(lon), math.degrees(lat), r - R


def incidence(et, lon, lat):
    lo, la = math.radians(lon), math.radians(lat)
    p = [R * math.cos(la) * math.cos(lo), R * math.cos(la) * math.sin(lo), R * math.sin(la)]
    sun, _ = sp.spkpos("SUN", et, "MOON_ME", "LT+S", "MOON")
    s = [sun[i] - p[i] for i in range(3)]
    cosang = sum(s[i] * p[i] for i in range(3)) / (math.sqrt(sum(x * x for x in s)) * R)
    return math.degrees(math.acos(max(-1, min(1, cosang))))


class Nearest:
    """Nearest named feature by great-circle distance, preferring craters."""

    def __init__(self, min_diam_km=3.0):
        self.f = [x for x in features() if x["diam_km"] >= min_diam_km and x["type"].startswith(("Crater", "Mare", "Mons", "Rima", "Vallis", "Lacus", "Sinus", "Palus", "Dorsum", "Rupes", "Montes", "Catena", "Planitia"))]
        for x in self.f:
            la, lo = math.radians(x["lat"]), math.radians(x["lon"])
            x["v"] = (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))

    def __call__(self, lon, lat):
        la, lo = math.radians(lat), math.radians(lon)
        v = (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))
        best = max(self.f, key=lambda x: x["v"][0] * v[0] + x["v"][1] * v[1] + x["v"][2] * v[2])
        d = R * math.acos(max(-1, min(1, sum(best["v"][i] * v[i] for i in range(3)))))
        return best["name"], best["diam_km"], d


def frame_row(r, nearest):
    craft = "A" if r["spacecraft"].startswith("GRAIL-A") else "B"
    et_raw = sp.str2et(utc_of(r["captured_utc"]))
    et = et_raw + CLOCK_OFFSET_S
    out = {"filename": r["filename"], "spacecraft": r["spacecraft"], "camera": r["camera"],
           "captured_utc": r["captured_utc"], "clock_offset_s": CLOCK_OFFSET_S}
    lon, lat, alt = subpoint(et, craft)
    out.update(sub_lon=round(lon, 4), sub_lat=round(lat, 4), alt_km=round(alt, 2))
    if not r["camera"]:
        out["status"] = "camera unknown; point below spacecraft only"
        return out
    cam = int(r["camera"][-1])
    grid = [(x, y) for x in (0, NX / 4, NX / 2, 3 * NX / 4, NX - 1) for y in (0, NY / 4, NY / 2, 3 * NY / 4, NY - 1)]
    hits = [ground(et, craft, cam, x, y) for x, y in grid]
    out["on_moon_fraction"] = round(sum(1 for h in hits if h) / len(hits), 2)
    c = ground(et, craft, cam, NX / 2, NY / 2)
    c0 = ground(et_raw, craft, cam, NX / 2, NY / 2)
    if c0:
        out.update(center_lon_no_offset=round(c0[0], 4), center_lat_no_offset=round(c0[1], 4))
    corners = [ground(et, craft, cam, x, y) for x, y in ((0, 0), (NX - 1, 0), (NX - 1, NY - 1), (0, NY - 1))]
    if all(corners):
        out["corners"] = ";".join(f"{a:.4f},{b:.4f}" for a, b in corners)
    if c:
        name, diam, dist = nearest(*c)
        out.update(center_lon=round(c[0], 4), center_lat=round(c[1], 4),
                   sun_incidence_deg=round(incidence(et, *c), 1),
                   nearest_feature=name, nearest_feature_diam_km=round(diam, 1),
                   nearest_feature_dist_km=round(dist, 1))
        out["status"] = "footprint" if all(corners) else "partial: horizon or sky in frame"
    else:
        out["status"] = "image centre misses the Moon (sky or limb)"
    return out


FIELDS = ["filename", "spacecraft", "camera", "captured_utc", "clock_offset_s", "status",
          "sub_lon", "sub_lat", "alt_km", "on_moon_fraction", "center_lon", "center_lat",
          "center_lon_no_offset", "center_lat_no_offset", "corners", "sun_incidence_deg",
          "nearest_feature", "nearest_feature_diam_km", "nearest_feature_dist_km"]

if __name__ == "__main__":
    load()
    nearest = Nearest()
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    with open(sys.argv[2], "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for i, r in enumerate(rows):
            try:
                w.writerow(frame_row(r, nearest))
            except Exception as e:  # keep going; record why
                w.writerow({"filename": r["filename"], "spacecraft": r["spacecraft"], "camera": r["camera"],
                            "captured_utc": r["captured_utc"], "status": f"error: {type(e).__name__}"})
            if i % 500 == 0:
                print(i, "of", len(rows), flush=True)
