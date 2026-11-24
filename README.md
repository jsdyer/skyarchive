# Sky Archive

<!-- coolcode:guide -->
Search the selected observation index, inspect a record’s dates and instruments, and request its source preview or export metadata. Use Search all of MAST for arbitrary targets; the local selection is not the full archive and individual products can require additional attribution.
<!-- /coolcode:guide -->

Explore a small, verified index of observations from the James Webb Space Telescope and the Hubble Space Telescope, including Hubble Legacy Archive entries. Find Andromeda, Orion, the Southern Ring Nebula, the Cosmic Cliffs, and the Tarantula Nebula. Search by observed target, instrument, product type or observation ID. Inspect dates, coordinates, exposure and wavelength fields, preview source imagery, and export filtered metadata to CSV.

For an arbitrary target name or coordinate, select **Search all of MAST** and enter it in the official portal. This selected index fits a static site and uses no cross-origin API call while searching. Image previews are fetched from the source only when requested in a record. The linked FITS file may be large and follow its own access rules. Check the archive's required product attributions before reuse.

For exoplanet papers and measurements, [compare the published masses of TRAPPIST-1 e](https://coolcode.ca/planetpapers/?planet=TRAPPIST-1%20e).

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

## Regression checks

Pull requests that change code run logic tests and Chromium checks at this tool’s
Pages subpath, including a real control interaction and 320/390-pixel layouts.
Documentation-only pull requests skip this workflow. Publication waits for the
same checks. Test data stays in a separate job and is never packaged for Pages.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py --offline
python3 -m pip install -r tests/browser-requirements.txt
python3 -m playwright install chromium
python3 tests/browser_smoke.py
```

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

This is an interim mitigation, not a scheduling guarantee: GitHub does not document active-workflow renewal as a permanent exemption, and scheduled runs can be delayed or dropped. A scheduler on our own Linux server is the planned independent trigger. The guard does not collect data, create dummy commits, or change source/check timestamps; successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->
