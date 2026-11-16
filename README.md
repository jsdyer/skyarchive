# Sky Archive

Explore a small, verified index of observations from the James Webb Space Telescope and the Hubble Space Telescope, including Hubble Legacy Archive entries. Find Andromeda, Orion, the Southern Ring Nebula, the Cosmic Cliffs, and the Tarantula Nebula. Search by observed target, instrument, product type or observation ID. Inspect dates, coordinates, exposure and wavelength fields, preview source imagery, and export filtered metadata to CSV.

For an arbitrary target name or coordinate, select **Search all of MAST** and enter it in the official portal. This selected index fits a static site and uses no cross-origin API call while searching. Image previews are fetched from the source only when requested in a record. The linked FITS file may be large and follow its own access rules. Check the archive's required product attributions before reuse.

## Build

- `python3 scripts/build.py` queries the MAST Table Access Protocol service for bounded results, checks anonymous preview URLs, and writes `dist/`. A failed or incomplete refresh builds from the verified local snapshot and displays the dated fallback.
- `python3 scripts/build.py --offline` builds from the checked-in snapshot.
- `python3 scripts/build.py --save-snapshot` refreshes the checked-in fallback if all target groups return public previews.

A scheduled GitHub Pages build may use the default command. No API key or account is required. Search and CSV export run in the browser. Serve `dist/` to preview locally.

## Sources

- [MAST Discovery Portal](https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html)
- [MAST Table Access Protocol documentation](https://archive.stsci.edu/contents/newsletters/may-2025/mast-vo-tap-changes-async-vao-stsci-edu-leaving-june-26)
- [MAST Data Use](https://archive.stsci.edu/publishing/data-use)

Credit NASA, ESA, CSA and STScI as appropriate. Product records, previews and data may require additional investigators or archive-specific credit.
