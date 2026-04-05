from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fy4b_to_npz import convert_fy4b_file, save_npz


SAMPLE_FILE = (
    PROJECT_ROOT
    / "sample"
    / "FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230621080000_20230621081459_4000M_V0001.HDF"
)


def test_convert_fy4b_file_outputs_all_channels_on_a_regular_latlon_grid(tmp_path):
    result = convert_fy4b_file(
        SAMPLE_FILE,
        bbox=(100.0, 20.0, 110.0, 30.0),
        resolution_deg=1.0,
    )

    expected_channels = [f"C{i:02d}" for i in range(1, 16)]

    assert result["channels"] == expected_channels
    assert result["data"].shape == (15, len(result["lat"]), len(result["lon"]))
    assert result["data"].dtype == np.float32
    assert result["lon"].ndim == 1
    assert result["lat"].ndim == 1
    np.testing.assert_allclose(np.diff(result["lon"]), 1.0)
    np.testing.assert_allclose(np.diff(result["lat"]), -1.0)
    assert np.isfinite(result["data"]).any()

    output_path = tmp_path / "fy4b_crop.npz"
    save_npz(output_path, result)

    loaded = np.load(output_path, allow_pickle=False)
    assert loaded["data"].shape == result["data"].shape
    assert loaded["channels"].tolist() == expected_channels
    np.testing.assert_allclose(loaded["lon"], result["lon"])
    np.testing.assert_allclose(loaded["lat"], result["lat"])
