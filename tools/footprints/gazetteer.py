"""Read the USGS Gazetteer of Planetary Nomenclature lunar points (public domain).

Source: https://asc-planetarynames-data.s3.us-west-2.amazonaws.com/MOON_nomenclature_center_pts.zip
Reads the .dbf directly (no GIS library). Longitudes returned east, -180 to 180.
"""
import os
import struct

from kernels import DIR

DBF = os.path.join(DIR, "gazetteer", "MOON_nomenclature_center_pts.dbf")


def read_dbf(path=DBF):
    with open(path, "rb") as f:
        hdr = f.read(32)
        n, hlen, rlen = struct.unpack("<IHH", hdr[4:12])
        fields = []
        while True:
            d = f.read(32)
            if d[0] == 0x0D:
                break
            fields.append((d[:11].split(b"\0")[0].decode(), d[11:12].decode(), d[16]))
        f.seek(hlen)
        for _ in range(n):
            rec = f.read(rlen)
            if rec[:1] == b"*":
                continue
            pos, row = 1, {}
            for name, typ, size in fields:
                row[name] = rec[pos:pos + size].decode("utf-8", "replace").strip()
                pos += size
            yield row


def features():
    out = []
    for r in read_dbf():
        try:
            lat = float(r.get("center_lat") or r.get("CENTER_LAT"))
            lon = float(r.get("center_lon") or r.get("CENTER_LON"))
            diam = float(r.get("diameter") or r.get("DIAMETER") or 0)
        except (TypeError, ValueError):
            continue
        if lon > 180:
            lon -= 360
        name = r.get("clean_name") or r.get("name") or r.get("NAME")
        ftype = r.get("type") or r.get("TYPE") or ""
        out.append({"name": name, "lat": lat, "lon": lon, "diam_km": diam, "type": ftype})
    return out


if __name__ == "__main__":
    first = next(read_dbf())
    print(list(first.keys()))
    fs = features()
    print(len(fs), [f for f in fs if f["name"] in ("Poinsot", "Carrel")])
