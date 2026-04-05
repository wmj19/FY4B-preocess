#!/usr/bin/env python3

from __future__ import annotations

import argparse
import warnings
from pathlib import Path
from typing import Any

import numpy as np
from pyresample import create_area_def
from satpy import Scene


DEFAULT_READER = "agri_fy4b_l1"
DEFAULT_RESAMPLER = "nearest"


def validate_bbox(bbox: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    xmin, ymin, xmax, ymax = bbox
    if xmin >= xmax:
        raise ValueError("bbox requires xmin < xmax.")
    if ymin >= ymax:
        raise ValueError("bbox requires ymin < ymax.")
    return bbox


def get_available_channels(input_path: str | Path, reader: str = DEFAULT_READER) -> list[str]:
    scene = Scene(reader=reader, filenames=[str(input_path)])
    return sorted(scene.available_dataset_names())


def create_latlon_area(
    bbox: tuple[float, float, float, float],
    resolution_deg: float,
    area_id: str = "fy4b_latlon_crop",
):
    validate_bbox(bbox)
    if resolution_deg <= 0:
        raise ValueError("resolution_deg must be positive.")
    return create_area_def(
        area_id=area_id,
        projection="EPSG:4326",
        area_extent=bbox,
        resolution=resolution_deg,
        units="degrees",
    )


def _to_iso8601(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def convert_fy4b_file(
    input_path: str | Path,
    bbox: tuple[float, float, float, float],
    resolution_deg: float,
    channels: list[str] | None = None,
    reader: str = DEFAULT_READER,
    resampler: str = DEFAULT_RESAMPLER,
) -> dict[str, Any]:
    input_path = Path(input_path)
    target_area = create_latlon_area(bbox, resolution_deg)
    scene = Scene(reader=reader, filenames=[str(input_path)])
    available_channels = sorted(scene.available_dataset_names())

    selected_channels = list(channels or available_channels)
    missing_channels = sorted(set(selected_channels) - set(available_channels))
    if missing_channels:
        raise ValueError(f"Requested channels are unavailable: {missing_channels}")

    scene.load(selected_channels)

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="invalid value encountered in subtract",
            category=RuntimeWarning,
        )
        resampled = scene.resample(target_area, resampler=resampler)

    first_ds = resampled[selected_channels[0]]
    lat = np.asarray(first_ds["y"].values, dtype=np.float64)
    lon = np.asarray(first_ds["x"].values, dtype=np.float64)
    data = np.stack(
        [np.asarray(resampled[name].values, dtype=np.float32) for name in selected_channels],
        axis=0,
    )

    return {
        "data": data,
        "channels": selected_channels,
        "lat": lat,
        "lon": lon,
        "bbox": np.asarray(bbox, dtype=np.float64),
        "resolution_deg": float(resolution_deg),
        "source_file": str(input_path.resolve()),
        "reader": reader,
        "resampler": resampler,
        "platform_name": str(first_ds.attrs.get("platform_name", "")),
        "sensor": str(first_ds.attrs.get("sensor", "")),
        "start_time": _to_iso8601(first_ds.attrs.get("start_time")),
        "end_time": _to_iso8601(first_ds.attrs.get("end_time")),
    }


def save_npz(output_path: str | Path, result: dict[str, Any]) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        data=result["data"],
        channels=np.asarray(result["channels"]),
        lat=result["lat"],
        lon=result["lon"],
        bbox=result["bbox"],
        resolution_deg=np.asarray(result["resolution_deg"], dtype=np.float64),
        source_file=np.asarray(result["source_file"]),
        reader=np.asarray(result["reader"]),
        resampler=np.asarray(result["resampler"]),
        platform_name=np.asarray(result["platform_name"]),
        sensor=np.asarray(result["sensor"]),
        start_time=np.asarray(result["start_time"]),
        end_time=np.asarray(result["end_time"]),
    )
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert FY-4B AGRI L1 HDF data to a cropped regular lat/lon grid saved as NPZ.",
    )
    parser.add_argument("input_file", type=Path, help="Input FY-4B HDF file.")
    parser.add_argument("output_file", type=Path, help="Output NPZ file.")
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

    result = convert_fy4b_file(
        input_path=args.input_file,
        bbox=tuple(args.bbox),
        resolution_deg=args.resolution,
        channels=args.channels,
        resampler=args.resampler,
    )
    output_path = save_npz(args.output_file, result)

    print(f"Saved {len(result['channels'])} channels to {output_path}")
    print(f"data shape: {result['data'].shape}")
    print(f"lat size: {len(result['lat'])}, lon size: {len(result['lon'])}")


if __name__ == "__main__":
    main()
