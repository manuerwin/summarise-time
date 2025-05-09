# Overview
Python app - process and summarise activity lines from CSV

## Installation
1. Requirements: python3 - suggest installing via Homebrew [https://brew.sh/] for convenience

## Usage
1. Download to local
2. Generate your csv file of activities with:
- headers: Date, Activity, Duration
- each row:
  - date in format dd/mm/yyyy
  - activity text
  - duration in format [optional hours]:minutes:seconds
For example:
28/04/2025, Doctor appointment, 30:00
3. Run this script:
>python3 activityprocessor.py path/to/your/.csv

## License
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this software, either in source code form or as a compiled binary, for any purpose, commercial or non-commercial, and by any means.

## Development testing
Via shell
> pytest -v

Or use VS Code Testing :)