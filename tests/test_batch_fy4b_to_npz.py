from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from batch_fy4b_to_npz import (  # type: ignore[import-not-found]
    batch_convert_fy4b_files,
    build_output_path,
    extract_start_time_from_name,
    is_supported_start_time,
)


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("placeholder", encoding="utf-8")
    return path


def test_extract_start_time_from_fy4b_name():
    value = extract_start_time_from_name(
        "FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230620080000_20230620081459_4000M_V0001.HDF"
    )
    assert value == "20230620080000"


def test_extract_start_time_returns_none_for_invalid_name():
    assert extract_start_time_from_name("not_a_fy4b_file.HDF") is None


def test_is_supported_start_time_accepts_whole_and_half_hour():
    assert is_supported_start_time("20230620100000")
    assert is_supported_start_time("20230620103000")
    assert not is_supported_start_time("20230620101500")
    assert not is_supported_start_time("20230620104500")
    assert not is_supported_start_time("20230620103059")


def test_build_output_path_uses_timestamp_name(tmp_path):
    output_path = build_output_path(tmp_path, "20230620080000")
    assert output_path == tmp_path / "20230620080000.npz"


def test_batch_convert_recurses_filters_and_overwrites(tmp_path, monkeypatch):
    input_root = tmp_path / "sate_data"
    output_dir = tmp_path / "output"

    keep_one = _touch(
        input_root
        / "20230620"
        / "FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230620080000_20230620081459_4000M_V0001.HDF"
    )
    keep_two = _touch(
        input_root
        / "20230621"
        / "nested"
        / "FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230621103000_20230621104459_4000M_V0001.HDF"
    )
    _touch(
        input_root
        / "20230620"
        / "FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230620101500_20230620102959_4000M_V0001.HDF"
    )
    _touch(input_root / "20230620" / "invalid_name.HDF")

    overwritten = output_dir / "20230620080000.npz"
    overwritten.parent.mkdir(parents=True, exist_ok=True)
    overwritten.write_text("old-content", encoding="utf-8")

    converted_files: list[Path] = []

    def fake_convert(input_path, bbox, resolution_deg, channels=None, reader=None, resampler=None):
        converted_files.append(Path(input_path))
        return {"source_file": str(input_path)}

    def fake_save(output_path, result):
        Path(output_path).write_text(
            f"new:{Path(result['source_file']).name}",
            encoding="utf-8",
        )
        return Path(output_path)

    monkeypatch.setattr("batch_fy4b_to_npz.convert_fy4b_file", fake_convert)
    monkeypatch.setattr("batch_fy4b_to_npz.save_npz", fake_save)

    stats = batch_convert_fy4b_files(
        input_root=input_root,
        output_dir=output_dir,
        bbox=(100.0, 20.0, 110.0, 30.0),
        resolution_deg=0.04,
    )

    assert stats == {
        "scanned": 4,
        "skipped_invalid_name": 1,
        "skipped_time": 1,
        "converted": 2,
        "failed": 0,
    }
    assert converted_files == [keep_one, keep_two]
    assert overwritten.read_text(encoding="utf-8").startswith("new:")
    assert (output_dir / "20230621103000.npz").exists()


def test_batch_convert_continues_after_single_failure(tmp_path, monkeypatch):
    input_root = tmp_path / "sate_data"
    output_dir = tmp_path / "output"

    failing_file = _touch(
        input_root
        / "20230620"
        / "FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230620080000_20230620081459_4000M_V0001.HDF"
    )
    good_file = _touch(
        input_root
        / "20230620"
        / "FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230620083000_20230620084459_4000M_V0001.HDF"
    )

    def fake_convert(input_path, bbox, resolution_deg, channels=None, reader=None, resampler=None):
        if Path(input_path) == failing_file:
            raise RuntimeError("broken input")
        return {"source_file": str(input_path)}

    def fake_save(output_path, result):
        Path(output_path).write_text("ok", encoding="utf-8")
        return Path(output_path)

    monkeypatch.setattr("batch_fy4b_to_npz.convert_fy4b_file", fake_convert)
    monkeypatch.setattr("batch_fy4b_to_npz.save_npz", fake_save)

    stats = batch_convert_fy4b_files(
        input_root=input_root,
        output_dir=output_dir,
        bbox=(100.0, 20.0, 110.0, 30.0),
        resolution_deg=0.04,
    )

    assert stats == {
        "scanned": 2,
        "skipped_invalid_name": 0,
        "skipped_time": 0,
        "converted": 1,
        "failed": 1,
    }
    assert not (output_dir / "20230620080000.npz").exists()
    assert (output_dir / "20230620083000.npz").exists()
    assert good_file.exists()
