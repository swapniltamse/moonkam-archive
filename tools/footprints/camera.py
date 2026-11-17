"""MoonKAM pixel to ground projection with SPICE.

Camera model from gra_mk_v02.ti / grb_mk_v02.ti: 720 x 486 pixels, CCD
centre (359.5, 242.5), rectangular field of view whose half-angles are 28 x 22
degrees for cameras 1 to 3 and 3.65 x 2.75 for camera 4, boresight +Z,
field width along camera +X. Pixel x counts from the left edge, y down from
the top edge. ORIENT gives the sign of camera X and Y per image axis; it is
fixed by the Carrel control-point test (validate_carrel.py), not assumed.
"""
import math

import spiceypy as sp

HALF = {1: (28.0, 22.0), 2: (28.0, 22.0), 3: (28.0, 22.0), 4: (3.65, 2.75)}
CX, CY, NX, NY = 359.5, 242.5, 720, 486
ORIENT = (-1, -1)  # fixed by validate_carrel.py: RMS 1.74 km with the 24.0 s clock offset; other orientations 19.6 km or worse


def frame_name(craft, cam):
    return f"GRAIL-{craft}_MK{cam}"


def pixel_dir(px, py, cam, orient=None):
    sx, sy = orient or ORIENT
    hx, hy = HALF[cam]
    x = sx * math.tan(math.radians(hx)) * (px - CX) / (NX / 2)
    y = sy * math.tan(math.radians(hy)) * (py - CY) / (NY / 2)
    return [x, y, 1.0]


# Mounting correction (Euler angles in degrees, axes 3-2-1, applied in the camera
# frame) for Ebb camera 3 only, fitted with LOLA terrain on its 2 control frames.
# Hold-out decided the model (Nov 17, 2026): with terrain and no camera-2 correction,
# unseen camera-2 frames scored 1.74 and 2.73 km, against 2.84 and 4.23 km for the
# earlier sphere model with a camera-2 clock. The earlier camera-2 tilt and camera-2
# clock were both compensating for terrain. See evals/ for the full record.
MOUNT = {("A", 3): (-0.593, -0.845, -0.312)}   # refitted with terrain (sphere fit was -0.771, -1.971, -0.341)


def pixel_dir_mounted(px, py, craft, cam, orient=None):
    d = pixel_dir(px, py, cam, orient)
    rot = MOUNT.get((craft, cam))
    if rot:
        m = sp.eul2m(*[math.radians(a) for a in rot], 3, 2, 1)
        d = list(sp.mxv(m, d))
    return d


def ground(et, craft, cam, px, py, orient=None, mount=True):
    """Return (lon_deg_east, lat_deg) where the pixel's ray first meets the LOLA
    terrain (terrain.py, LDEM_64), or None if it misses (sky or limb)."""
    import terrain  # imported here: terrain imports this module
    rot = MOUNT.get((craft, cam)) if mount else None
    return terrain.ground_terrain(et, craft, cam, px, py, rot=rot, orient=orient)


def ground_sphere(et, craft, cam, px, py, orient=None, mount=True):
    """Same ray to the smooth 1737.4 km sphere (SPICE sincpt). Kept for comparison."""
    d = pixel_dir_mounted(px, py, craft, cam, orient) if mount else pixel_dir(px, py, cam, orient)
    try:
        spoint, _, _ = sp.sincpt("Ellipsoid", "MOON", et, "MOON_ME", "LT+S",
                                 f"GRAIL-{craft}", frame_name(craft, cam), d)
    except sp.stypes.NotFoundError:
        return None
    except sp.stypes.SpiceyError:
        return None
    _, lon, lat = sp.reclat(spoint)
    return math.degrees(lon), math.degrees(lat)


def gc_km(a, b, R=1737.4):
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def to_pixel(et, craft, cam, lon, lat, orient=None, R=1737.4):
    """Project a surface point into the image. Returns (px, py) or None if it is
    behind the camera or over the horizon."""
    sx, sy = orient or ORIENT
    lo, la = math.radians(lon), math.radians(lat)
    p = [R * math.cos(la) * math.cos(lo), R * math.cos(la) * math.sin(lo), R * math.sin(la)]
    sc, _ = sp.spkpos(f"GRAIL-{craft}", et, "MOON_ME", "LT+S", "MOON")
    los = [p[i] - sc[i] for i in range(3)]
    # over the horizon if the line of sight meets the sphere before the point
    if sum(los[i] * p[i] for i in range(3)) > 0:
        return None
    m = sp.pxform("MOON_ME", frame_name(craft, cam), et)
    v = sp.mxv(m, los)
    rot = MOUNT.get((craft, cam))
    if rot:  # undo the mounting correction applied in pixel_dir_mounted
        v = sp.mtxv(sp.eul2m(*[math.radians(a) for a in rot], 3, 2, 1), v)
    if v[2] <= 0:
        return None
    hx, hy = HALF[cam]
    px = CX + (v[0] / v[2]) / (sx * math.tan(math.radians(hx))) * (NX / 2)
    py = CY + (v[1] / v[2]) / (sy * math.tan(math.radians(hy))) * (NY / 2)
    return px, py
