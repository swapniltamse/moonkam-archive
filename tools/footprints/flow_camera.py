"""Guess which MoonKAM camera took each Flow (GRAIL-B) frame.

Flow file names do not record the camera. Each camera looks a different way, so
each predicts black sky in a different part of the frame. For every frame this
compares where the image is black sky with where cameras 1 to 4 would see sky,
at the Flow clock offset, and keeps the best match.

Cameras 1 and 4 both look down, so a frame with no sky is labelled "1 or 4".
Camera 1 (56 x 44 degrees) is taken for those, since camera 4 (7.3 x 5.5) is a
narrow camera that the four control-point frames never matched.

Usage: python flow_camera.py <catalogue.csv> <image_root> <out.csv>
"""
import csv
import glob
import os
import sys

import numpy as np
import spiceypy as sp
from PIL import Image

from camera import ground
from footprints import utc_of
from kernels import load

FLOW_CLOCK_OFFSET_S = -61.5   # nadir control-point frame FLOW-2; oblique frames gave -57.6 to -64.8
GX, GY = 12, 8                 # grid of cells compared


def observed_sky(path):
    im = np.asarray(Image.open(path).convert("L"), dtype=float)
    h, w = im.shape
    sky = np.zeros((GY, GX), bool)
    for j in range(GY):
        for i in range(GX):
            cell = im[j * h // GY:(j + 1) * h // GY, i * w // GX:(i + 1) * w // GX]
            sky[j, i] = cell.mean() < 40 and cell.std() < 12  # Flow sky reads about 25 to 28, not black
    return sky


def predicted_sky(et, cam):
    sky = np.zeros((GY, GX), bool)
    for j in range(GY):
        for i in range(GX):
            px, py = (i + 0.5) * 720 / GX, (j + 0.5) * 486 / GY
            sky[j, i] = ground(et, "B", cam, px, py) is None
    return sky


def classify(path, et):
    obs = observed_sky(path)
    scores = {cam: float((predicted_sky(et, cam) == obs).mean()) for cam in (1, 2, 3, 4)}
    best = max(scores, key=scores.get)
    if obs.sum() == 0 and not predicted_sky(et, 1).any():
        return "1 or 4", scores, int(obs.sum())
    return str(best), scores, int(obs.sum())


if __name__ == "__main__":
    load()
    cat, root, out = sys.argv[1:4]
    index = {os.path.basename(p): p for p in glob.glob(root + "/**/*.bmp", recursive=True)}
    rows = [r for r in csv.DictReader(open(cat, encoding="utf-8")) if r["spacecraft"].startswith("GRAIL-B")]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["filename", "camera_guess", "agree_cam1", "agree_cam2", "agree_cam3", "agree_cam4", "sky_cells"])
        for n, r in enumerate(rows):
            p = index.get(r["filename"])
            if not p:
                w.writerow([r["filename"], "image not found", "", "", "", "", ""])
                continue
            et = sp.str2et(utc_of(r["captured_utc"])) + FLOW_CLOCK_OFFSET_S
            try:
                guess, s, k = classify(p, et)
            except Exception as e:
                w.writerow([r["filename"], f"error {type(e).__name__}", "", "", "", "", ""])
                continue
            w.writerow([r["filename"], guess] + [round(s[c], 3) for c in (1, 2, 3, 4)] + [k])
            if n % 200 == 0:
                print(n, "of", len(rows), flush=True)
