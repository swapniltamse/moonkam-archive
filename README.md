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

## Footprints (added Nov 2026)
`moonkam_footprints.csv` gives a computed ground footprint for every frame in the catalogue, joined on `filename`.
Map: https://grail.swapniltamse.com/moonkam/map/

Columns: status, sub_lon and sub_lat (point below the spacecraft), alt_km, on_moon_fraction (share of a 5 x 5
pixel grid that hits the Moon), center_lon and center_lat (picture centre), center_lon_no_offset and
center_lat_no_offset (the same without the clock offset), corners (four lon,lat pairs, clockwise from top left),
sun_incidence_deg, nearest_feature, nearest_feature_diam_km, nearest_feature_dist_km. Longitudes are east,
-180 to 180, in the Moon mean-Earth frame (IAU sphere, 1737.4 km).

Method: NASA NAIF GRAIL SPICE kernels (navigation SPK, reconstructed pointing CK, MoonKAM instrument kernels),
traced with SPICE `sincpt` onto the Moon ellipsoid. Feature names from the USGS Gazetteer of Planetary
Nomenclature (public domain). Code: `tools/footprints/` in this repository.

How it was checked, and its limits:
- One Carrel frame (Ebb, camera 1, 2012-089 14:38:20) placed by hand on the LRO WAC mosaic with 9 control
  points matches to 1.7 km RMS when the image is flipped on both axes and the file-name time is moved 24.0 s
  earlier. Other flips stay at 19.6 km or more. The best pointing correction without a clock shift reaches 10.8 km.
- The same flip matches the limb in a camera 3 frame of Poinsot (2012-075 00:09:38) to about 5 pixels.
- The 24.0 s clock offset is measured on one frame and applied to all. It is not yet confirmed on a second frame,
  so the uncorrected centre is kept. Camera 2 has no test frame. Flow frames record no camera, so they carry the
  point below the spacecraft only.
- Positions are on a smooth sphere, without terrain. Expect errors of a few kilometres at best.

## Rights
The catalogue and documentation are CC BY 4.0 (see LICENSE and NOTICE): reuse them freely, with credit. The images and videos are NASA mission material;
the contributor claims no copyright in them. Details, and the open question on UC San Diego, are in RIGHTS.md.

## More
https://grail.swapniltamse.com and https://grail.swapniltamse.com/spif/
