# Footprint scripts

The code that produced `moonkam_footprints.csv`. Same files as the GRAIL tribute site's tools.

1. Download the kernels listed in `kernels.py` from
   https://naif.jpl.nasa.gov/pub/naif/pds/data/grail-l-spice-6-v1.0/grlsp_1000/data/
   into a folder, plus the USGS gazetteer
   https://asc-planetarynames-data.s3.us-west-2.amazonaws.com/MOON_nomenclature_center_pts.zip
   unzipped into `<that folder>/gazetteer/`.
2. Set `GRAIL_SPICE_DIR` to that folder (default: a `kernels` folder next to these scripts).
3. `pip install spiceypy numpy`
4. `python validate_carrel.py` prints the control-point test for all four image flips.
5. `python footprints.py ../../moonkam_catalogue_public.csv out.csv` rebuilds the table.

The camera flip and clock offset are set in `camera.py` and `footprints.py`; see the README at the top of this
repository for how they were measured and what is still open.
