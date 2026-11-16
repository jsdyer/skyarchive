#!/usr/bin/env python3
"""Fetch bounded MAST Table Access Protocol snapshots and build the browser index."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
from itertools import islice
import math
from pathlib import Path
import shutil
from urllib.error import URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
TAP = "https://mast.stsci.edu/vo-tap/api/v0.1/caom/sync"
PORTAL = "https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html"
POLICY = "https://archive.stsci.edu/publishing/data-use"
TAP_DOC = "https://archive.stsci.edu/contents/newsletters/may-2025/mast-vo-tap-changes-async-vao-stsci-edu-leaving-june-26"
SEED = ROOT / "data/snapshot.json"
UA = "CoolCode Sky Archive (https://coolcode.ca/skyarchive/)"
TARGETS = {
    "M31 · Andromeda Galaxy": "target_name='M31' AND obs_collection='HLA'",
    "M42 · Orion Nebula": "target_name='M42' AND obs_collection='HST'",
    "NGC 3132 · Southern Ring Nebula": "target_name='NGC-3132' AND obs_collection='JWST' AND calib_level=3",
    "NGC 3324 · Cosmic Cliffs": "target_name='NGC-3324' AND obs_collection='JWST' AND calib_level=3",
    "30 Doradus · Tarantula Nebula": (
        "s_ra > 84.60 AND s_ra < 84.80 AND s_dec > -69.2 AND s_dec < -69.00 "
        "AND obs_collection='JWST' AND calib_level=3"
    ),
}
COLUMNS = (
    "obs_id, obs_collection, target_name, instrument_name, t_min, t_exptime, s_ra, s_dec, "
    "dataproduct_type, access_url, access_format, calib_level, em_min, em_max"
)
MJD_EPOCH = datetime(1858, 11, 17, tzinfo=timezone.utc)


def mast_rows(where):
    query = f"SELECT TOP 85 {COLUMNS} FROM ivoa.obscore WHERE {where}"
    request = Request(TAP + "?" + urlencode({"LANG": "ADQL", "QUERY": query, "FORMAT": "json"}),
                      headers={"User-Agent": UA})
    with urlopen(request, timeout=16) as response:
        data = json.loads(response.read(2_000_000))
    header = [column["name"] for column in data["info"]]
    return [dict(zip(header, row, strict=True)) for row in data["data"]]


def source_url(value):
    url = urlsplit(value or "")
    host = url.hostname or ""
    return value if url.scheme == "https" and host in {"mast.stsci.edu", "hla.stsci.edu", "archive.stsci.edu"} else ""


def filename(url):
    params = parse_qs(urlsplit(url or "").query)
    return next(iter(params.get("uri", params.get("filename", params.get("dataset", [""]))))).rsplit("/", 1)[-1]


def public_preview(url):
    try:
        request = Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urlopen(request, timeout=6) as response:
            return response.headers.get_content_type() in {"image/jpeg", "image/png", "image/gif"}
    except (OSError, URLError, ValueError):
        return False


def number(value, digits=3):
    return f"{float(value):,.{digits}f}" if isinstance(value, (int, float)) and math.isfinite(value) else ""


def group_records(target, rows):
    by_observation = {}
    for row in rows:
        if row.get("obs_collection") not in {"HLA", "HST", "JWST"}:
            continue
        product_id = row.get("obs_id")
        if product_id and source_url(row.get("access_url")):
            by_observation.setdefault(product_id, []).append(row)
    checked = []
    for obs_id, products in islice(by_observation.items(), 12):
        previews = [row for row in products if str(row.get("access_format", "")).startswith("image/")
                    and row.get("access_format") != "image/fits"]
        images = sorted(previews, key=lambda row: ("_thumb." not in filename(row["access_url"]), row["access_url"]))
        preview = next((row for row in images[:2] if public_preview(row["access_url"])), None)
        if not preview:
            continue
        fits_candidates = [row for row in products if "fits" in str(row.get("access_format", "")).lower()]
        science_suffixes = ("_i2d.fits", "_s2d.fits", "_s3d.fits", "_drz.fits", "_x1d.fits")
        downloads = sorted(fits_candidates, key=lambda row: (not filename(row["access_url"]).endswith(science_suffixes), row["access_url"]))
        checked.append(summarize(target, obs_id, preview, downloads[0] if downloads else None))
        if len(checked) == 6:
            break
    return checked


def summarize(target, obs_id, row, fits):
    source = row["obs_collection"]
    mission = "Webb (JWST)" if source == "JWST" else "Hubble (HST)"
    collection = "Hubble Legacy Archive" if source == "HLA" else source
    kind = str(row.get("dataproduct_type") or "Observation").capitalize()
    instrument = row.get("instrument_name") or "Instrument unavailable"
    start = row.get("t_min")
    observed = ((MJD_EPOCH + timedelta(days=start)).date().isoformat()
                if isinstance(start, (float, int)) and 0 < start < 150_000 else "")
    ra, dec = number(row.get("s_ra")), number(row.get("s_dec"))
    low, high = row.get("em_min"), row.get("em_max")
    wavelengths = f"{low * 1e6:.3f}–{high * 1e6:.3f} µm" if isinstance(low, (float, int)) and isinstance(high, (float, int)) else ""
    file_label = filename(row["access_url"])
    links = [{"label": "Original MAST preview", "url": row["access_url"]}]
    if fits:
        links.append({"label": "MAST FITS data (size varies)", "url": fits["access_url"]})
    links.append({"label": "Search the full MAST portal", "url": PORTAL})
    display_piece = f"{instrument} · {kind}"
    return {
        "title": target, "date": observed, "kicker": f"{mission} / {collection}",
        "summary": display_piece + (f" · {wavelengths}" if wavelengths else ""),
        "highlight": instrument, "a": mission, "b": kind, "c": target,
        "keywords": f"{obs_id} {collection} {row.get('target_name') or ''} RA {ra} Dec {dec} {file_label}",
        "preview": row["access_url"],
        "fields": {
            "Observation ID": obs_id, "Target label at MAST": row.get("target_name"), "Collection": collection,
            "Telescope": mission, "Instrument": instrument, "Product type": kind, "Observation start (UTC)": observed,
            "Right ascension": f"{ra}°" if ra else "", "Declination": f"{dec}°" if dec else "",
            "Wavelength range": wavelengths, "Exposure": (number(row.get("t_exptime"), 1) + " s") if number(row.get("t_exptime")) else "",
            "Preview identifier": file_label,
        },
        "links": links,
    }


def build_snapshot(fixture_dir=None):
    def load(item):
        target, where = item
        try:
            if fixture_dir:
                ix = list(TARGETS).index(target)
                filenames = ["usable-andromeda", "usable-orion", "usable-southern-ring", "usable-cosmic-cliffs", "usable-tarantula"]
                payload = json.loads((fixture_dir / filenames[ix]).read_text())
                header = [column["name"] for column in payload["info"]]
                raw = [dict(zip(header, row, strict=True)) for row in payload["data"]]
            else:
                raw = mast_rows(where)
            rows = group_records(target, raw)
            print(f"{target}: {len(rows)} observations with public previews", flush=True)
            return rows
        except (OSError, KeyError, TypeError, ValueError) as error:
            print(f"Could not refresh {target}: {error}", flush=True)
            return []
    with ThreadPoolExecutor(max_workers=5) as executor:
        groups = list(executor.map(load, TARGETS.items()))
    if not all(groups):
        raise ValueError("The refreshed snapshot did not contain every target")
    return {"updated": datetime.now(timezone.utc).date().isoformat(),
            "records": [record for group in groups for record in group]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Use the checked-in snapshot.")
    parser.add_argument("--save-snapshot", action="store_true", help="Save a successfully refreshed source snapshot.")
    parser.add_argument("--captured-responses", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    fallback = args.offline
    if fallback:
        snapshot = json.loads(SEED.read_text())
    else:
        try:
            snapshot = build_snapshot(args.captured_responses)
            if args.save_snapshot:
                SEED.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n")
        except (OSError, ValueError):
            if args.save_snapshot:
                raise
            fallback = True
            snapshot = json.loads(SEED.read_text())
            print("MAST refresh incomplete. Using the verified snapshot from " + snapshot["updated"])
    count = len(snapshot["records"])
    catalog = {
        "slug": "skyarchive", "coverage": f"{count} observations · {len(TARGETS)} targets", **snapshot,
        "facets": ["Telescope", "Product type", "Target"], "examples": ["Andromeda", "Orion", "Tarantula", "Webb"],
        "method": ("Serving the verified snapshot because this build used its offline fallback. " if fallback else "")
                  + "Indexed metadata and original preview links credit NASA, ESA, CSA and STScI as appropriate. "
                  "The application checks anonymous preview access when refreshing. A linked FITS product may be "
                  "larger or follow its own release rules. Follow the full MAST record and product credits when reusing data.",
        "sources": [
            {"label": "Live MAST portal search", "url": PORTAL},
            {"label": "HST and JWST metadata service", "url": TAP_DOC},
            {"label": "MAST data-use policy", "url": POLICY},
        ],
    }
    dist = ROOT / "dist"
    shutil.copytree(ROOT / "web", dist, dirs_exist_ok=True)
    (dist / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")))
    print(f"Sky Archive: {count} verified observation entries")


if __name__ == "__main__":
    main()
