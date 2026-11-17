# GRAIL MoonKAM recovered image archive

About 5,800 original images from NASA's GRAIL MoonKAM program (2011 to 2012), the cameras that
middle-school classrooms aimed at the Moon during the GRAIL mission. The public gallery went offline for
over a decade. This set was recovered in 2026 from a mission backup, catalogued, and released for
preservation.

## Credit
NASA / Caltech-JPL / MIT / Sally Ride Science. Recovered and contributed by Swapnil Tamse
(grail.swapniltamse.com), 2026, with the images preserved by Chris Leong and the connection made by
Margaret King at Sally Ride Science. Independent, non-commercial, not affiliated with or endorsed by NASA.

## Packages
- moonkam_grail-a_partN.zip : GRAIL-A (Ebb) frames, organized by day and camera (2012-088 onward).
- moonkam_emily-dickinson-and-flow.zip : the Emily Dickinson Elementary set (the first images taken) and the GRAIL-B (Flow) frames.
- GRA.mp4 : the full near five-hour recording from Ebb.
- moonkam_videos_clips.zip : four shorter mission videos.
- moonkam_catalogue_public.csv : the per-image catalogue.

## Catalogue columns
group, folder, filename, spacecraft, camera, request_code, captured_utc (UTC, formatted YYYY-DOY-HH:MM:SS.mmm),
orbit, album, image_no, size_bytes. Orbit, album, and image_no are populated where a frame could be
cross-referenced to the surviving published gallery index.

## How it was recovered
The index was reconstructed from Internet Archive captures of the retired gallery (181 original filenames
carrying orbit, image number, and capture timestamp), then matched to the raw backup on the request code and
the exact millisecond capture time. The set was deduplicated and screened for corrupted frames.

## A note on names
A small number of award-tagged frames carried individual student names and are intentionally not included in
this public release. That subset is available to the hosting institution for curation.

## Footprints (added Nov 2026, terrain version Nov 17)
`moonkam_footprints.csv` gives a computed ground footprint for every frame in the catalogue, joined on `filename`.
Map: https://grail.swapniltamse.com/moonkam/map/

Columns: camera (for Flow, inferred; see camera_source), camera_source, clock_offset_s, status, sub_lon and
sub_lat (point below the spacecraft), alt_km, on_moon_fraction (share of a 5 x 5 pixel grid that hits the Moon),
center_lon and center_lat (picture centre), center_lon_no_offset and center_lat_no_offset (no clock offset and no
mounting correction), corners (four lon,lat pairs, clockwise from top left), sun_incidence_deg, nearest_feature,
nearest_feature_diam_km, nearest_feature_dist_km. Longitudes are east, -180 to 180, Moon mean-Earth frame.

Method: NASA NAIF GRAIL SPICE kernels (navigation SPK, reconstructed pointing CK, MoonKAM instrument kernels).
Each pixel's line of sight is ray-traced to the LRO LOLA elevation model LDEM_64 (64 pixels per degree,
PDS product LRO-L-LOLA-4-GDR-V1.0; see `terrain.py` for the URL), not a smooth sphere. Feature names from the
USGS Gazetteer of Planetary Nomenclature (public domain). Code: `tools/footprints/`.

Model: Ebb's file-name times are 23.44 s late, Flow's 61.5 s late. Ebb camera 3 has one small mounting
correction (about 1 degree, `camera.py`). With terrain, no other camera needs one; an earlier camera 2
correction was compensating for the missing terrain and was removed. Flow does not record the camera;
`flow_camera.py` infers it from where the sky sits. Frames with no sky could be camera 1 or 4 and are placed as camera 1.

How it was built and tested (control points are pixel to lon/lat matches against the LRO WAC mosaic):
- Fitting: 14 frames, 6 to 20 points each, 8 days, Ebb cameras 1 to 3 and Flow, in
  `tools/footprints/control_points/`. One (Carrel) matched by hand, the rest with image-matching tools checked
  by eye, without sight of any model prediction.
- Testing: separate frames matched the same way and never used for fitting, in `control_points/holdout/`
  (H-* and H2-*). RMS error of the published model:

  | Camera | Hold-out frames | RMS |
  |---|---|---|
  | Ebb camera 1 | 3 | 0.77, 0.91, 0.93 km |
  | Ebb camera 2 | 2 | 1.74, 2.73 km |
  | Ebb camera 3 | 2 | 1.09, 4.59 km (the Copernicus frame, not yet explained) |
  | Flow | 2 | 0.34, 0.64 km |

- Truth noise: three frames were matched twice, independently (`control_points/holdout/R-*`). The two
  matchings differ by 0.19 to 0.88 km RMS, so errors below about 1 km are within matching noise.
- Reproduce: `python validate_all.py control_points/holdout H2-CAM2-1.csv ...` with `GRAIL_SPICE_DIR`
  pointing at the NAIF kernels and `terrain/ldem_64.img`.

## Rights
The catalogue and documentation are CC BY 4.0 (see LICENSE and NOTICE): reuse them freely, with credit. The images and videos are NASA mission material;
the contributor claims no copyright in them. Details, and the open question on UC San Diego, are in RIGHTS.md.

## More
https://grail.swapniltamse.com and https://grail.swapniltamse.com/spif/
