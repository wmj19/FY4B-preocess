from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fy4b_to_npz import convert_fy4b_file, save_npz
from view_fy4b_npz import NpzChannelViewer, load_npz_file


SAMPLE_FILE = (
    PROJECT_ROOT
    / "sample"
    / "FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230621080000_20230621081459_4000M_V0001.HDF"
)


def _create_sample_npz(tmp_path: Path) -> Path:
    result = convert_fy4b_file(
        SAMPLE_FILE,
        bbox=(100.0, 20.0, 110.0, 30.0),
        resolution_deg=1.0,
    )
    output_path = tmp_path / "fy4b_crop.npz"
    save_npz(output_path, result)
    return output_path


def test_load_npz_file_reads_required_arrays(tmp_path):
    npz_path = _create_sample_npz(tmp_path)

    loaded = load_npz_file(npz_path)

    assert loaded["data"].shape[0] == len(loaded["channels"])
    assert loaded["lat"].ndim == 1
    assert loaded["lon"].ndim == 1
    assert loaded["channels"][0] == "C01"


def test_viewer_switches_channels_and_updates_title(tmp_path):
    npz_path = _create_sample_npz(tmp_path)
    loaded = load_npz_file(npz_path)

    viewer = NpzChannelViewer(loaded, show=False, backend="Agg")

    assert viewer.current_channel == "C01"
    assert "C01" in viewer.ax.get_title()

    viewer.set_channel_by_index(2)
    assert viewer.current_channel == "C03"
    assert "C03" in viewer.ax.get_title()

    viewer.next_channel(None)
    assert viewer.current_channel == "C04"

    viewer.prev_channel(None)
    assert viewer.current_channel == "C03"

    np.testing.assert_allclose(
        viewer.image.get_array(),
        loaded["data"][2],
        equal_nan=True,
    )
