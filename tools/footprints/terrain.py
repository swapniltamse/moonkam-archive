"""Terrain-aware pixel to ground projection for MoonKAM.

camera.ground() traces each pixel to a smooth 1737.4 km sphere. Here the same ray
(camera.pixel_dir plus the camera.MOUNT correction, or a rotation passed in for
fitting) is traced to the LRO LOLA gridded elevation model LDEM_64 instead:

  Product: LRO-L-LOLA-4-GDR-V1.0, PRODUCT_ID LDEM_64, PRODUCT_VERSION_ID V3.1
  URL:     https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_64.img
  Label:   ldem_64.lbl (same folder). 23040 x 11520 LSB int16, 64 pixels per degree (473.8 m),
           simple cylindrical, pixel registered, line 0 at 90 N, sample 0 at 0 E.
           height_m = DN * 0.5, relative to the 1737.4 km sphere (OFFSET 1737400 m).

Method: find where the ray enters the shell between the lowest and highest DEM
heights, march along it in steps of STEP_KM comparing the ray's height with the
DEM height (bilinear), and refine the first crossing by bisection. This handles
grazing views, where the first terrain hit can be far from the sphere hit.

The DEM file is read from $GRAIL_DEM, else $GRAIL_SPICE_DIR/terrain/ldem_64.img.
"""
import math
import os

import numpy as np
import spiceypy as sp

from camera import MOUNT, frame_name, pixel_dir

R = 1737.4
STEP_KM = 0.1
_DEM = None


class Dem:
    def __init__(self, path=None):
        path = path or os.environ.get("GRAIL_DEM") or os.path.join(
            os.environ.get("GRAIL_SPICE_DIR", ""), "terrain", "ldem_64.img")
        self.ppd = 64
        self.nl, self.ns = 180 * self.ppd, 360 * self.ppd
        a = np.fromfile(path, dtype="<i2")
        if a.size != self.nl * self.ns:
            raise ValueError(f"{path}: expected {self.nl * self.ns} samples, found {a.size}")
        self.z = a.reshape(self.nl, self.ns)
        self.hmin = float(self.z.min()) * 0.5e-3
        self.hmax = float(self.z.max()) * 0.5e-3

    def height_km(self, lon, lat):
        """Bilinear height in km above the 1737.4 km sphere; lon east and lat in degrees (arrays ok)."""
        x = (np.mod(lon, 360.0) * self.ppd) - 0.5
        y = ((90.0 - np.asarray(lat, dtype=float)) * self.ppd) - 0.5
        y = np.clip(y, 0, self.nl - 1.000001)
        x0 = np.floor(x).astype(np.int64)
        y0 = np.floor(y).astype(np.int64)
        fx, fy = x - x0, y - y0
        xa, xb = np.mod(x0, self.ns), np.mod(x0 + 1, self.ns)
        y1 = np.minimum(y0 + 1, self.nl - 1)
        z = self.z
        h = ((z[y0, xa] * (1 - fx) + z[y0, xb] * fx) * (1 - fy)
             + (z[y1, xa] * (1 - fx) + z[y1, xb] * fx) * fy)
        return h * 0.5e-3


def dem():
    global _DEM
    if _DEM is None:
        _DEM = Dem()
    return _DEM


def _sphere_hits(o, d, r):
    """Both ray parameters where |o + t d| = r (d unit), or None."""
    b = float(np.dot(o, d))
    c = float(np.dot(o, o)) - r * r
    disc = b * b - c
    if disc < 0:
        return None
    s = math.sqrt(disc)
    return -b - s, -b + s


def _lonlat(p):
    p = np.atleast_2d(p)
    r = np.linalg.norm(p, axis=1)
    return np.degrees(np.arctan2(p[:, 1], p[:, 0])), np.degrees(np.arcsin(p[:, 2] / r)), r


def intersect(o, d, model=None, step=None):
    """First terrain hit of the ray o + t d (MOON_ME, km). Returns (lon, lat, h_km) or None."""
    m = model or dem()
    step = step or STEP_KM
    d = d / np.linalg.norm(d)
    top = _sphere_hits(o, d, R + m.hmax + 0.01)
    if top is None or top[1] <= 0:
        return None
    t0 = max(top[0], 0.0)
    bot = _sphere_hits(o, d, R + m.hmin - 0.01)
    t1 = bot[0] if bot and bot[0] > t0 else top[1]

    def f(t):
        p = o[None, :] + np.asarray(t, dtype=float)[:, None] * d[None, :]
        lon, lat, r = _lonlat(p)
        return r - R - m.height_km(lon, lat)

    # march in chunks so a nadir ray does not evaluate the whole grazing length
    chunk = 2000
    prev_t, prev_f = t0, f(np.array([t0]))[0]
    if prev_f <= 0:
        lon, lat, _ = _lonlat(o + t0 * d)
        return float(lon[0]), float(lat[0]), float(m.height_km(lon, lat)[0])
    start = t0
    while start < t1:
        ts = start + step * np.arange(1, chunk + 1)
        ts = ts[ts <= t1 + step]
        if ts.size == 0:
            break
        fs = f(ts)
        neg = np.nonzero(fs <= 0)[0]
        if neg.size:
            i = neg[0]
            lo = ts[i - 1] if i > 0 else prev_t
            hi = ts[i]
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                if f(np.array([mid]))[0] > 0:
                    lo = mid
                else:
                    hi = mid
            lon, lat, _ = _lonlat(o + hi * d)
            return float(lon[0]), float(lat[0]), float(m.height_km(lon, lat)[0])
        prev_t = ts[-1]
        start = ts[-1]
    return None


def ray(et, craft, cam, px, py, rot="default", orient=None):
    """Spacecraft position and pixel ray direction in MOON_ME (km) at et.

    rot: "default" uses camera.MOUNT (as camera.pixel_dir_mounted does), None uses no
    mounting correction, or a 3-tuple of Euler angles in degrees (3-2-1, camera frame).
    Aberration and light time (sub-metre at GRAIL's 20 to 100 km range) are ignored.
    """
    v = pixel_dir(px, py, cam, orient)
    if rot == "default":
        rot = MOUNT.get((craft, cam))
    if rot is not None:
        v = list(sp.mxv(sp.eul2m(*[math.radians(a) for a in rot], 3, 2, 1), v))
    o, _ = sp.spkpos(f"GRAIL-{craft}", et, "MOON_ME", "NONE", "MOON")
    m = sp.pxform(frame_name(craft, cam), "MOON_ME", et)
    return np.array(o), np.array(sp.mxv(m, v))


def ground_terrain(et, craft, cam, px, py, rot="default", orient=None, with_height=False):
    """(lon_deg_east, lat_deg) where the pixel's ray first meets the LOLA terrain, or None."""
    o, d = ray(et, craft, cam, px, py, rot, orient)
    hit = intersect(o, d)
    if hit is None:
        return None
    return hit if with_height else hit[:2]


def ground_sphere(et, craft, cam, px, py, rot="default", orient=None):
    """Same ray as ground_terrain, to the 1737.4 km sphere (cross-check against camera.ground)."""
    o, d = ray(et, craft, cam, px, py, rot, orient)
    d = d / np.linalg.norm(d)
    h = _sphere_hits(o, d, R)
    if h is None or h[0] <= 0:
        return None
    lon, lat, _ = _lonlat(o + h[0] * d)
    return float(lon[0]), float(lat[0])
