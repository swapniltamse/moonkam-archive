"""Helpers for matching MoonKAM frames to the LRO WAC basemap (control points).

  python gcp_tools.py basemap <frame_id> <lon_c> <lat_c> <half_deg> <out_dir>
      Map crop around (lon_c, lat_c), +/- half_deg in latitude (wider in longitude
      near the poles), with a labelled grid and named features. Writes
      <frame_id>_map.png and <frame_id>_map.json (pixel to lon/lat).
  python gcp_tools.py frame <frame_id> <bmp_path> <out_dir>
      The frame enlarged 2x with a grid every 50 original pixels. Writes <frame_id>_frame.png.
  python gcp_tools.py maplonlat <map_json> <map_px> <map_py>
      Converts a pixel on the map crop to lon/lat.
  python gcp_tools.py eval <gcp_csv>
      Fits clock offset, image flip and (for Flow) camera to control points.

Basemap: LRO WAC global mosaic, NASA/GSFC/Arizona State University, served by NASA Moon Trek.
Feature names: USGS Gazetteer of Planetary Nomenclature.
"""
import csv
import io
import json
import math
import os
import ssl
import sys
import urllib.request

TILE = "https://trek.nasa.gov/tiles/Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/default/default028mm/{z}/{r}/{c}.jpg"
CA = "C:/Program Files/Git/mingw64/etc/ssl/certs/ca-bundle.crt"
CACHE = os.path.join(os.environ.get("GRAIL_SPICE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "kernels")), "wac_tiles")


def tile(z, r, c):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, f"{z}_{r}_{c}.jpg")
    if not os.path.exists(p):
        ctx = ssl.create_default_context(cafile=CA)
        b = urllib.request.urlopen(urllib.request.Request(TILE.format(z=z, r=r, c=c), headers={"User-Agent": "grail-tribute-research"}), context=ctx, timeout=60).read()
        open(p, "wb").write(b)
    from PIL import Image
    return Image.open(p).convert("L")


def basemap(fid, lon_c, lat_c, half, out, z=7):
    from PIL import Image, ImageDraw
    from gazetteer import features
    ppd = 256 * 2 ** z / 180.0
    lat0, lat1 = max(-90, lat_c - half), min(90, lat_c + half)
    halflon = min(180, half / max(0.15, math.cos(math.radians(lat_c))))
    lon0, lon1 = lon_c - halflon, lon_c + halflon
    x0, x1 = int((lon0 + 180) * ppd), int((lon1 + 180) * ppd)
    y0, y1 = int((90 - lat1) * ppd), int((90 - lat0) * ppd)
    W, H = x1 - x0, y1 - y0
    img = Image.new("L", (W, H))
    ncol = 2 * 2 ** z
    for r in range(y0 // 256, (y1 - 1) // 256 + 1):
        for c in range(x0 // 256, (x1 - 1) // 256 + 1):
            t = tile(z, r, c % ncol)
            img.paste(t, (c * 256 - x0, r * 256 - y0))
    # keep the crop a readable size
    scale = min(1.0, 1400 / max(W, H))
    if scale < 1:
        img = img.resize((int(W * scale), int(H * scale)))
    rgb = img.convert("RGB")
    d = ImageDraw.Draw(rgb)
    sx = rgb.width / (lon1 - lon0)
    sy = rgb.height / (lat1 - lat0)
    step = 0.5 if half <= 4 else 1.0
    lon = math.ceil(lon0 / step) * step
    while lon <= lon1:
        x = (lon - lon0) * sx
        d.line([(x, 0), (x, rgb.height)], fill=(0, 140, 255), width=1)
        d.text((x + 2, 2), f"{lon:.1f}E", fill=(0, 170, 255))
        lon += step
    lat = math.ceil(lat0 / step) * step
    while lat <= lat1:
        y = (lat1 - lat) * sy
        d.line([(0, y), (rgb.width, y)], fill=(0, 140, 255), width=1)
        d.text((2, y + 2), f"{lat:.1f}N", fill=(0, 170, 255))
        lat += step
    for f in features():
        if f["diam_km"] < 4:
            continue
        flon = f["lon"]
        if flon < lon0 - 1:
            flon += 360
        if lon0 <= flon <= lon1 and lat0 <= f["lat"] <= lat1:
            x, y = (flon - lon0) * sx, (lat1 - f["lat"]) * sy
            d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(255, 200, 0))
            d.text((x + 5, y - 6), f["name"], fill=(255, 210, 60))
    os.makedirs(out, exist_ok=True)
    rgb.save(os.path.join(out, f"{fid}_map.png"))
    meta = {"lon0": lon0, "lon1": lon1, "lat0": lat0, "lat1": lat1, "width": rgb.width, "height": rgb.height,
            "note": "pixel (0,0) is top-left; lon = lon0 + px/width*(lon1-lon0); lat = lat1 - py/height*(lat1-lat0)"}
    json.dump(meta, open(os.path.join(out, f"{fid}_map.json"), "w"), indent=1)
    print(json.dumps(meta))


def frame(fid, bmp, out):
    from PIL import Image, ImageDraw
    im = Image.open(bmp).convert("RGB")
    big = im.resize((im.width * 2, im.height * 2))
    d = ImageDraw.Draw(big)
    for x in range(0, im.width + 1, 50):
        d.line([(2 * x, 0), (2 * x, big.height)], fill=(0, 255, 120), width=1)
        d.text((2 * x + 3, 3), str(x), fill=(0, 255, 120))
    for y in range(0, im.height + 1, 50):
        d.line([(0, 2 * y), (big.width, 2 * y)], fill=(0, 255, 120), width=1)
        d.text((3, 2 * y + 3), str(y), fill=(0, 255, 120))
    os.makedirs(out, exist_ok=True)
    big.save(os.path.join(out, f"{fid}_frame.png"))
    print(f"frame {im.width}x{im.height}; grid labels are ORIGINAL pixel coordinates (x right, y down)")


def maplonlat(mj, px, py):
    m = json.load(open(mj))
    lon = m["lon0"] + float(px) / m["width"] * (m["lon1"] - m["lon0"])
    lat = m["lat1"] - float(py) / m["height"] * (m["lat1"] - m["lat0"])
    if lon > 180:
        lon -= 360
    print(f"{lon:.4f} {lat:.4f}")


def evaluate(path):
    """GCP csv columns: frame_file, utc (catalogue form), craft (A/B), camera (1-4 or blank), px, py, lon, lat, feature."""
    import spiceypy as sp
    from camera import HALF, CX, CY, NX, NY, gc_km
    from kernels import load
    from footprints import utc_of
    load()
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    craft, utc, cam_given = rows[0]["craft"], rows[0]["utc"], rows[0]["camera"]
    et0 = sp.str2et(utc_of(utc))
    cams = [int(cam_given)] if cam_given else [1, 2, 3, 4]

    def ground(et, cam, px, py, o):
        hx, hy = HALF[cam]
        v = [o[0] * math.tan(math.radians(hx)) * (px - CX) / (NX / 2), o[1] * math.tan(math.radians(hy)) * (py - CY) / (NY / 2), 1.0]
        try:
            p, _, _ = sp.sincpt("Ellipsoid", "MOON", et, "MOON_ME", "LT+S", f"GRAIL-{craft}", f"GRAIL-{craft}_MK{cam}", v)
        except Exception:
            return None
        _, lo, la = sp.reclat(p)
        return math.degrees(lo), math.degrees(la)

    def rms(et, cam, o):
        e = []
        for r in rows:
            g = ground(et, cam, float(r["px"]), float(r["py"]), o)
            if g is None:
                return float("inf")
            e.append(gc_km(g, (float(r["lon"]), float(r["lat"]))))
        return math.sqrt(sum(x * x for x in e) / len(e))

    results = []
    for cam in cams:
        for o in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            coarse = min((rms(et0 + dt, cam, o), dt) for dt in range(-90, 91, 3))
            fine = min((rms(et0 + coarse[1] + d / 10, cam, o), coarse[1] + d / 10) for d in range(-30, 31))
            results.append({"camera": cam, "orient": o, "best_offset_s": round(fine[1], 1), "best_rms_km": round(fine[0], 2),
                            "rms_at_0s_km": round(rms(et0, cam, o), 2), "rms_at_-24s_km": round(rms(et0 - 24.0, cam, o), 2)})
    results.sort(key=lambda r: r["best_rms_km"])
    out = {"file": os.path.basename(path), "points": len(rows), "craft": craft, "utc": utc, "best": results[0], "runner_up": results[1]}
    print(json.dumps(out))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "basemap":
        basemap(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6])
    elif cmd == "frame":
        frame(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "maplonlat":
        maplonlat(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "eval":
        evaluate(sys.argv[2])
