#!/usr/bin/env python3
"""
Evirgen build script.

Produces two store-ready packages from src/:
  dist/evirgen-<version>-chrome.zip    (Chrome / Edge, MV3 service worker)
  dist/evirgen-<version>-firefox.zip   (Firefox, MV3 event page + gecko id)

Usage:  python3 build.py [--clean]
"""

import argparse
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

GECKO_ID = "evirgen@kaktusdev.net"
GECKO_MIN_VERSION = "115.0"  # storage.session requires FF 102+, MV3 stable 115+


def load_manifest() -> dict:
    with open(SRC / "manifest.json", encoding="utf-8") as f:
        return json.load(f)


def transform_firefox(manifest: dict) -> dict:
    """Chrome MV3 manifest -> Firefox MV3 manifest."""
    m = json.loads(json.dumps(manifest))  # deep copy
    sw = m.get("background", {}).get("service_worker")
    if sw:
        m["background"] = {"scripts": [sw]}
    m["browser_specific_settings"] = {
        "gecko": {"id": GECKO_ID, "strict_min_version": GECKO_MIN_VERSION}
    }
    return m


def copy_tree(target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SRC, target)


def write_manifest(target: Path, manifest: dict) -> None:
    with open(target / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")


def zip_dir(folder: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(folder))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Evirgen packages")
    parser.add_argument("--clean", action="store_true", help="remove dist/ and exit")
    args = parser.parse_args()

    if args.clean:
        shutil.rmtree(DIST, ignore_errors=True)
        print("dist/ removed")
        return

    manifest = load_manifest()
    version = manifest["version"]
    DIST.mkdir(exist_ok=True)

    # Chrome / Edge — source used verbatim
    chrome_dir = DIST / "chrome"
    copy_tree(chrome_dir)
    chrome_zip = DIST / f"evirgen-{version}-chrome.zip"
    zip_dir(chrome_dir, chrome_zip)
    print(f"chrome  -> {chrome_zip.relative_to(ROOT)}")

    # Firefox — manifest transformed
    firefox_dir = DIST / "firefox"
    copy_tree(firefox_dir)
    write_manifest(firefox_dir, transform_firefox(manifest))
    firefox_zip = DIST / f"evirgen-{version}-firefox.zip"
    zip_dir(firefox_dir, firefox_zip)
    print(f"firefox -> {firefox_zip.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
