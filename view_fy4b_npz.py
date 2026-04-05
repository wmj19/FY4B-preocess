#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np


def load_npz_file(npz_path: str | Path) -> dict[str, Any]:
    npz_path = Path(npz_path)
    with np.load(npz_path, allow_pickle=False) as loaded:
        data = np.asarray(loaded["data"], dtype=np.float32)
        channels = [str(item) for item in loaded["channels"].tolist()]
        lat = np.asarray(loaded["lat"], dtype=np.float64)
        lon = np.asarray(loaded["lon"], dtype=np.float64)
        metadata = {
            key: loaded[key].item() if loaded[key].shape == () else loaded[key]
            for key in loaded.files
            if key not in {"data", "channels", "lat", "lon"}
        }

    if data.ndim != 3:
        raise ValueError("NPZ field 'data' must have shape (channels, lat, lon).")
    if data.shape[0] != len(channels):
        raise ValueError("The number of channels does not match the data array.")
    if data.shape[1] != len(lat) or data.shape[2] != len(lon):
        raise ValueError("Latitude/longitude sizes do not match the data array.")

    return {
        "path": str(npz_path.resolve()),
        "data": data,
        "channels": channels,
        "lat": lat,
        "lon": lon,
        "metadata": metadata,
    }


def _import_matplotlib(backend: str | None = None):
    if "MPLCONFIGDIR" not in os.environ:
        cache_dir = Path(tempfile.gettempdir()) / "fy4b_matplotlib_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(cache_dir)

    import matplotlib

    if backend:
        matplotlib.use(backend)

    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button, Slider

    return plt, Button, Slider


class NpzChannelViewer:
    def __init__(
        self,
        dataset: dict[str, Any],
        *,
        cmap: str = "viridis",
        vmin: float | None = None,
        vmax: float | None = None,
        show: bool = True,
        backend: str | None = None,
    ) -> None:
        self.dataset = dataset
        self.data = dataset["data"]
        self.channels = dataset["channels"]
        self.lat = dataset["lat"]
        self.lon = dataset["lon"]
        self.cmap = cmap
        self.fixed_vmin = vmin
        self.fixed_vmax = vmax
        self.index = 0

        self.plt, Button, Slider = _import_matplotlib(backend)

        self.fig, self.ax = self.plt.subplots(figsize=(10, 7))
        self.plt.subplots_adjust(left=0.1, bottom=0.22, right=0.88)

        channel_data = self.data[self.index]
        clim = self._compute_clim(channel_data)
        self.image = self.ax.imshow(
            channel_data,
            cmap=self.cmap,
            extent=self._extent(),
            origin="upper",
            aspect="auto",
            vmin=clim[0],
            vmax=clim[1],
        )
        self.colorbar = self.fig.colorbar(self.image, ax=self.ax, fraction=0.046, pad=0.04)
        self.colorbar.set_label("Value")

        self.ax.set_xlabel("Longitude")
        self.ax.set_ylabel("Latitude")
        self._update_title()

        slider_ax = self.fig.add_axes([0.16, 0.09, 0.58, 0.04])
        self.slider = Slider(
            ax=slider_ax,
            label="Channel Index",
            valmin=0,
            valmax=len(self.channels) - 1,
            valinit=0,
            valstep=1,
        )
        self.slider.on_changed(self._on_slider_change)

        prev_ax = self.fig.add_axes([0.16, 0.025, 0.12, 0.05])
        next_ax = self.fig.add_axes([0.62, 0.025, 0.12, 0.05])
        self.prev_button = Button(prev_ax, "Previous")
        self.next_button = Button(next_ax, "Next")
        self.prev_button.on_clicked(self.prev_channel)
        self.next_button.on_clicked(self.next_channel)

        if show:
            self.plt.show()

    @property
    def current_channel(self) -> str:
        return self.channels[self.index]

    def _extent(self) -> tuple[float, float, float, float]:
        return (float(self.lon[0]), float(self.lon[-1]), float(self.lat[-1]), float(self.lat[0]))

    def _compute_clim(self, channel_data: np.ndarray) -> tuple[float | None, float | None]:
        if self.fixed_vmin is not None or self.fixed_vmax is not None:
            return self.fixed_vmin, self.fixed_vmax

        finite = channel_data[np.isfinite(channel_data)]
        if finite.size == 0:
            return None, None

        return float(np.nanpercentile(finite, 2.0)), float(np.nanpercentile(finite, 98.0))

    def _update_title(self) -> None:
        source_name = Path(self.dataset["path"]).name
        self.ax.set_title(f"{self.current_channel} | {source_name}")

    def _on_slider_change(self, value: float) -> None:
        self.set_channel_by_index(int(value), sync_slider=False)

    def set_channel_by_index(self, index: int, *, sync_slider: bool = True) -> None:
        if not 0 <= index < len(self.channels):
            raise IndexError("Channel index out of range.")

        self.index = index
        channel_data = self.data[self.index]
        self.image.set_data(channel_data)
        vmin, vmax = self._compute_clim(channel_data)
        self.image.set_clim(vmin=vmin, vmax=vmax)
        self.colorbar.update_normal(self.image)
        self._update_title()

        if sync_slider and int(self.slider.val) != self.index:
            self.slider.set_val(self.index)
        else:
            self.fig.canvas.draw_idle()

    def next_channel(self, _event: Any) -> None:
        self.set_channel_by_index((self.index + 1) % len(self.channels))

    def prev_channel(self, _event: Any) -> None:
        self.set_channel_by_index((self.index - 1) % len(self.channels))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Open an interactive viewer for FY-4B NPZ files with channel switching.",
    )
    parser.add_argument("npz_file", type=Path, help="Path to the generated NPZ file.")
    parser.add_argument("--cmap", default="viridis", help="Matplotlib colormap name.")
    parser.add_argument("--vmin", type=float, default=None, help="Optional fixed lower color limit.")
    parser.add_argument("--vmax", type=float, default=None, help="Optional fixed upper color limit.")
    parser.add_argument(
        "--backend",
        default=None,
        help="Optional matplotlib backend, for example MacOSX, TkAgg, or QtAgg.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dataset = load_npz_file(args.npz_file)
    NpzChannelViewer(
        dataset,
        cmap=args.cmap,
        vmin=args.vmin,
        vmax=args.vmax,
        backend=args.backend,
        show=True,
    )


if __name__ == "__main__":
    main()
