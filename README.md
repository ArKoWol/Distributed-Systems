# Homework 1 Setup Guide

This folder contains the implementation for Distributed Systems Homework 1 (Variant 2).

Main script:
- `hw1_variant2.py`

## Requirements

- macOS/Linux/Windows
- Python 3.10+ (Python 3.8+ should also work)
- No external packages needed (standard library only)

## Setup

From terminal:

```bash
cd "/Users/arkow/VGTU /BDS/hw-1"
python3 --version
```

No installation step is required.

## Run (recommended)

Generate a valid sample input file (12,000 lines) and run processing:

```bash
python3 hw1_variant2.py --auto-generate-sample
```

## Run with your own file

```bash
python3 hw1_variant2.py --input your_text_file.txt --workers 6 --log-file processing.log
```

Notes:
- Homework requirement: input should have at least 10,000 lines.
- `--workers` controls number of processing threads.

## Output

After execution, you will get:
- Console output:
  - total word count
  - unique word count
  - top 20 most frequent words
  - log statistics per level
  - single-thread vs multi-thread timing
  - throughput
- Log file (default): `processing.log`
- Sample input (if generated): `sample_text_12000.txt`

## Report files

- `report.md` (report in markdown format)
- `report.docx` (report in Word format)
