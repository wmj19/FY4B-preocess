# FY4B Batch Conversion Design

**Date:** 2026-04-05

**Goal:** Add a batch conversion entrypoint that recursively scans FY4B AGRI L1 `.HDF` files, converts only whole-hour and half-hour files to `.npz`, and names each output by the source filename start timestamp.

## Context

The project already provides single-file conversion in `fy4b_to_npz.py` via `convert_fy4b_file` and `save_npz`. The new work should avoid duplicating Satpy loading and NPZ writing logic. Instead, it should add a thin batch layer around the existing converter.

## Requirements

1. Recursively scan a user-provided input root for `.HDF` files.
2. Parse the first 14-digit timestamp embedded in the FY4B filename as the file start time.
3. Convert only files whose start time is exactly `HH:00:00` or `HH:30:00`.
4. Write all outputs into one flat output directory.
5. Name each output file `<start_time>.npz`, for example `20230620080000.npz`.
6. Overwrite existing output files with the same target name.
7. Skip invalid filenames and skipped timestamps without aborting the full batch run.
8. Continue processing when a single file conversion fails and report the error.

## Proposed Approach

Add a new script, `batch_fy4b_to_npz.py`, that reuses the existing single-file conversion functions. The new script will:

- walk the input directory recursively,
- parse filenames into start timestamps,
- filter to whole-hour and half-hour starts,
- call `convert_fy4b_file(...)`,
- save with `save_npz(...)` into the flat output directory.

This keeps single-file conversion unchanged and makes the new behavior easy to test in isolation.

## CLI Shape

```bash
python batch_fy4b_to_npz.py sate_data output --bbox 100 20 110 30 --resolution 0.04
```

Supported arguments:

- positional `input_root`
- positional `output_dir`
- required `--bbox`
- required `--resolution`
- optional `--channels`
- optional `--resampler`

## Batch Behavior

### Filename parsing

Example:

`FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230620080000_20230620081459_4000M_V0001.HDF`

The batch script uses `20230620080000` as the start timestamp and outputs:

`output/20230620080000.npz`

### Time filtering

Accepted start times:

- `YYYYMMDDHH0000`
- `YYYYMMDDHH3000`

Rejected examples:

- `YYYYMMDDHH1500`
- `YYYYMMDDHH4500`
- any timestamp with non-zero seconds

### Overwrite rule

If the output file already exists, it is replaced by the new conversion result.

### Failure handling

- Invalid filename: skip and report.
- Non-matching timestamp: skip and report in summary.
- Conversion failure for one file: report and continue with remaining files.

## Testing Strategy

Add focused tests for:

1. extracting the FY4B start timestamp from filenames,
2. accepting only `00` and `30` minute timestamps with `00` seconds,
3. building the output path as `<timestamp>.npz`,
4. recursively scanning nested directories,
5. overwriting an existing output file,
6. continuing after one conversion failure.

## Notes

- The current workspace is not a git repository, so this design file cannot be committed here.
