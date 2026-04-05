#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any


DEFAULT_RESAMPLER = "nearest"
START_TIME_PATTERN = re.compile(r"_(\d{14})_(\d{14})_")


def convert_fy4b_file(*args, **kwargs):
    from fy4b_to_npz import convert_fy4b_file as _convert_fy4b_file

    return _convert_fy4b_file(*args, **kwargs)


def save_npz(*args, **kwargs):
    from fy4b_to_npz import save_npz as _save_npz

    return _save_npz(*args, **kwargs)


def extract_start_time_from_name(filename: str) -> str | None:
    match = START_TIME_PATTERN.search(filename)
    if match is None:
        return None
    return match.group(1)


def is_supported_start_time(start_time: str) -> bool:
    if len(start_time) != 14 or not start_time.isdigit():
        return False
    minute = start_time[10:12]
    second = start_time[12:14]
    return minute in {"00", "30"} and second == "00"


def build_output_path(output_dir: str | Path, start_time: str) -> Path:
    return Path(output_dir) / f"{start_time}.npz"


def iter_hdf_files(input_root: str | Path) -> list[Path]:
    input_root = Path(input_root)
    return sorted(path for path in input_root.rglob("*") if path.is_file() and path.suffix.upper() == ".HDF")


def batch_convert_fy4b_files(
    input_root: str | Path,
    output_dir: str | Path,
    bbox: tuple[float, float, float, float],
    resolution_deg: float,
    channels: list[str] | None = None,
    resampler: str = DEFAULT_RESAMPLER,
) -> dict[str, int]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "scanned": 0,
        "skipped_invalid_name": 0,
        "skipped_time": 0,
        "converted": 0,
        "failed": 0,
    }

    for input_path in iter_hdf_files(input_root):
        stats["scanned"] += 1

        start_time = extract_start_time_from_name(input_path.name)
        if start_time is None:
            stats["skipped_invalid_name"] += 1
            print(f"Skipping invalid filename: {input_path}")
            continue

        if not is_supported_start_time(start_time):
            stats["skipped_time"] += 1
            print(f"Skipping unsupported timestamp: {input_path.name}")
            continue

        try:
            result = convert_fy4b_file(
                input_path=input_path,
                bbox=bbox,
                resolution_deg=resolution_deg,
                channels=channels,
                resampler=resampler,
            )
            output_path = build_output_path(output_dir, start_time)
            save_npz(output_path, result)
            stats["converted"] += 1
            print(f"Converted {input_path} -> {output_path}")
        except Exception as exc:
            stats["failed"] += 1
            print(f"Failed to convert {input_path}: {exc}")

    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Batch convert FY-4B AGRI L1 HDF data to NPZ, keeping only files whose "
            "start time is exactly on the hour or half hour."
        )
    )
    parser.add_argument("input_root", type=Path, help="Root directory containing nested FY-4B HDF files.")
    parser.add_argument("output_dir", type=Path, help="Flat directory where timestamp-named NPZ files are written.")
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("LON_MIN", "LAT_MIN", "LON_MAX", "LAT_MAX"),
        required=True,
        help="Longitude/latitude crop bounds in degrees.",
    )
    parser.add_argument(
        "--resolution",
        type=float,
        required=True,
        help="Target regular lat/lon grid resolution in degrees.",
    )
    parser.add_argument(
        "--channels",
        nargs="+",
        default=None,
        help="Optional channel list such as C01 C02 C03. Defaults to all available channels.",
    )
    parser.add_argument(
        "--resampler",
        default=DEFAULT_RESAMPLER,
        help="Satpy resampler name. Defaults to 'nearest'.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    stats = batch_convert_fy4b_files(
        input_root=args.input_root,
        output_dir=args.output_dir,
        bbox=tuple(args.bbox),
        resolution_deg=args.resolution,
        channels=args.channels,
        resampler=args.resampler,
    )

    print("Summary:")
    for key in ("scanned", "skipped_invalid_name", "skipped_time", "converted", "failed"):
        print(f"{key}: {stats[key]}")


if __name__ == "__main__":
    main()
