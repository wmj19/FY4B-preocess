# FY4B Batch Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a batch FY4B conversion script that scans nested directories, converts only whole-hour and half-hour files, and writes flat timestamp-named NPZ outputs.

**Architecture:** Keep `fy4b_to_npz.py` as the single-file conversion module and add a new `batch_fy4b_to_npz.py` wrapper for scanning, filtering, and orchestration. Put filename parsing and batch conversion logic in small testable functions so the CLI stays thin.

**Tech Stack:** Python 3.11, pathlib, argparse, pytest, existing `fy4b_to_npz` conversion helpers.

---

### Task 1: Record approved design artifacts

**Files:**
- Create: `docs/superpowers/specs/2026-04-05-fy4b-batch-conversion-design.md`
- Create: `docs/superpowers/plans/2026-04-05-fy4b-batch-conversion.md`

- [ ] **Step 1: Save the approved design**

Create the spec file with the confirmed behavior: recursive scan, start-time parsing, `00`/`30` minute filter, flat output naming, overwrite semantics, and failure handling.

- [ ] **Step 2: Save the implementation plan**

Create this plan file with focused TDD tasks for tests, implementation, and verification.

### Task 2: Add failing batch behavior tests

**Files:**
- Create: `tests/test_batch_fy4b_to_npz.py`
- Modify: `tests/test_batch_fy4b_to_npz.py`
- Test: `tests/test_batch_fy4b_to_npz.py`

- [ ] **Step 1: Write a failing test for timestamp extraction**

```python
def test_extract_start_time_from_fy4b_name():
    value = extract_start_time_from_name(
        "FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230620080000_20230620081459_4000M_V0001.HDF"
    )
    assert value == "20230620080000"
```

- [ ] **Step 2: Run the single test to verify it fails**

Run: `pytest tests/test_batch_fy4b_to_npz.py::test_extract_start_time_from_fy4b_name -v`
Expected: FAIL because `batch_fy4b_to_npz` or the target function does not exist yet.

- [ ] **Step 3: Add failing tests for time acceptance and batch processing**

```python
def test_is_supported_start_time_accepts_whole_and_half_hour():
    assert is_supported_start_time("20230620100000")
    assert is_supported_start_time("20230620103000")
    assert not is_supported_start_time("20230620101500")
    assert not is_supported_start_time("20230620104500")
    assert not is_supported_start_time("20230620103059")


def test_batch_convert_recurses_filters_and_overwrites(tmp_path, monkeypatch):
    ...


def test_batch_convert_continues_after_single_failure(tmp_path, monkeypatch):
    ...
```

- [ ] **Step 4: Run the test file to verify the new tests fail for the expected reason**

Run: `pytest tests/test_batch_fy4b_to_npz.py -v`
Expected: FAIL because the new batch module and behavior are not implemented yet.

### Task 3: Implement minimal batch conversion module

**Files:**
- Create: `batch_fy4b_to_npz.py`
- Test: `tests/test_batch_fy4b_to_npz.py`

- [ ] **Step 1: Implement test-driven helpers**

Create helpers with narrow responsibilities:

```python
def extract_start_time_from_name(filename: str) -> str | None:
    ...


def is_supported_start_time(start_time: str) -> bool:
    ...


def build_output_path(output_dir: Path, start_time: str) -> Path:
    return output_dir / f"{start_time}.npz"
```

- [ ] **Step 2: Implement batch orchestration**

Add a function shaped like:

```python
def batch_convert_fy4b_files(
    input_root: str | Path,
    output_dir: str | Path,
    bbox: tuple[float, float, float, float],
    resolution_deg: float,
    channels: list[str] | None = None,
    resampler: str = DEFAULT_RESAMPLER,
) -> dict[str, int]:
    ...
```

This function should recursively scan `*.HDF`, skip invalid names, skip unsupported timestamps, call `convert_fy4b_file`, save with `save_npz`, overwrite existing outputs, collect counts, and continue after per-file errors.

- [ ] **Step 3: Add the CLI**

Expose positional `input_root` and `output_dir`, plus `--bbox`, `--resolution`, `--channels`, and `--resampler`, then print a compact summary after processing.

- [ ] **Step 4: Run the focused test file to verify it passes**

Run: `pytest tests/test_batch_fy4b_to_npz.py -v`
Expected: PASS

### Task 4: Run regression checks

**Files:**
- Modify: `batch_fy4b_to_npz.py`
- Test: `tests/test_batch_fy4b_to_npz.py`
- Test: `tests/test_fy4b_to_npz.py`

- [ ] **Step 1: Run the batch tests**

Run: `pytest tests/test_batch_fy4b_to_npz.py -v`
Expected: PASS

- [ ] **Step 2: Run the existing single-file conversion tests**

Run: `pytest tests/test_fy4b_to_npz.py -v`
Expected: PASS

- [ ] **Step 3: Fix any regression if needed and re-run the affected tests**

If a failure appears, make the smallest change necessary in `batch_fy4b_to_npz.py` and re-run the failing command until green.

## Self-Review

- Spec coverage: the plan covers scanning, parsing, filtering, naming, overwrite behavior, and continuation after errors.
- Placeholder scan: no `TODO` or undefined implementation steps remain.
- Type consistency: helper and orchestration function names are consistent across tasks.

## Notes

- The workspace is not a git repository, so commit steps from the standard workflow are not available here.
