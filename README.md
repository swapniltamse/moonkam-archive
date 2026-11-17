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

## Footprints (added Nov 2026, revised Nov 17)
`moonkam_footprints.csv` gives a computed ground footprint for every frame in the catalogue, joined on `filename`.
Map: https://grail.swapniltamse.com/moonkam/map/

Columns: camera (for Flow, inferred; see camera_source), camera_source, clock_offset_s, status, sub_lon and
sub_lat (point below the spacecraft), alt_km, on_moon_fraction (share of a 5 x 5 pixel grid that hits the Moon),
center_lon and center_lat (picture centre), center_lon_no_offset and center_lat_no_offset (no clock offset and no
mounting correction), corners (four lon,lat pairs, clockwise from top left), sun_incidence_deg, nearest_feature,
nearest_feature_diam_km, nearest_feature_dist_km. Longitudes are east, -180 to 180, Moon mean-Earth frame, on the
1737.4 km sphere.

Method: NASA NAIF GRAIL SPICE kernels (navigation SPK, reconstructed pointing CK, MoonKAM instrument kernels),
traced with SPICE `sincpt`. Feature names from the USGS Gazetteer of Planetary Nomenclature (public domain).
Code and the control points: `tools/footprints/`.

How it was checked:
- 14 frames were matched to the LRO WAC mosaic (6 to 20 points each, 8 days, Ebb cameras 1 to 3 and Flow):
  one (Carrel) by hand, the rest with image-matching tools checked by eye. The matching was not shown any model
  prediction. Each set was then fitted blind for clock offset, image flip and (Flow) camera. Every set chose the
  same flip. Control points are in `tools/footprints/control_points/`.
- Ebb's file-name times are 23.5 s late (4 camera-1 frames: -22.9 to -24.0 s). Cameras 2 and 3 get small mounting
  corrections (about 1 and 2 degrees, `camera.py`), fitted with the clock fixed. Camera 3 holds up when one frame
  is left out; camera 2 is weaker (3 of 4 held-out frames improve).
- Flow's file-name times are about 61.5 s late (its nadir frame; oblique frames -57.6 to -64.8 s). Flow does not
  record the camera; `flow_camera.py` infers it from where the sky sits, and named the right camera on all four
  matched Flow frames. Frames with no sky could be camera 1 or 4 and are placed as camera 1.
- Error of the final model on the control points (`validate_all.py`): Ebb 0.9 to 2.4 km RMS on all 10 sets;
  Flow 1.9 and 3.3 km on two sets, 6.1 and 7.8 km on two oblique sets (Flow has no mounting correction).
- Positions are on a smooth sphere, without terrain.

## Rights
The catalogue and documentation are CC BY 4.0 (see LICENSE and NOTICE): reuse them freely, with credit. The images and videos are NASA mission material;
the contributor claims no copyright in them. Details, and the open question on UC San Diego, are in RIGHTS.md.

## More
https://grail.swapniltamse.com and https://grail.swapniltamse.com/spif/
