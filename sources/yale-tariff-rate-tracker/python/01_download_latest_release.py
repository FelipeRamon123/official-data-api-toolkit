from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

API = "https://api.github.com/repos/Budget-Lab-Yale/tariff-rate-tracker"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the latest Yale tracker release asset.")
    parser.add_argument("--output", default="data/yale-tariff-rate-tracker/latest-release.zip")
    parser.add_argument("--metadata", default="data/yale-tariff-rate-tracker/release.json")
    args = parser.parse_args()

    headers = {"Accept": "application/vnd.github+json", "User-Agent": "official-data-api-toolkit"}
    response = requests.get(f"{API}/releases/latest", headers=headers, timeout=60)
    response.raise_for_status()
    release = response.json()
    zip_assets = [asset for asset in release.get("assets", []) if asset.get("name", "").endswith(".zip")]
    if not zip_assets:
        raise SystemExit("The latest Yale release has no ZIP asset.")
    asset = max(zip_assets, key=lambda item: item.get("created_at", ""))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(asset["browser_download_url"], stream=True, timeout=600) as download:
        download.raise_for_status()
        with output.open("wb") as handle:
            for chunk in download.iter_content(1024 * 1024):
                handle.write(chunk)

    metadata = {
        "repository": "https://github.com/Budget-Lab-Yale/tariff-rate-tracker",
        "release_url": release["html_url"],
        "tag": release["tag_name"],
        "published_at": release["published_at"],
        "asset": asset["name"],
        "asset_url": asset["browser_download_url"],
        "asset_size": asset["size"],
    }
    metadata_path = Path(args.metadata)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Downloaded {metadata['tag']} to {output}")


if __name__ == "__main__":
    main()
