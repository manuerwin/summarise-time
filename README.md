# Overview
Python app - process and summarise activity lines from CSV

## Installation
1. Requirements: python3 - suggest installing via Homebrew [https://brew.sh/] for convenience

## Usage
1. Download to local
2. Update categories.txt with your categories (can be upper, mixed, or lower case), one per line
3. Generate your csv file of activities
- header format: Date, Activity, Duration
- each row:
  - date in format dd/mm/yyyy
  - category and activity text
    - note: dash (-) is optional and will be removed
    - note: any detail after the pipe (|) character (for example TMI below) will be removed
    - commas (') must be escaped by surrounding with double-quotes ("")
    - category can be upper, mixed or lower case
  - duration in format [optional hours]:minutes:seconds

For example:
> 28/04/2025, "adMIN - Doctor appointment | TMI, surround commas with quotes", 30:00

3. Run this script:
> python3 activityprocessor.py path/to/your/.csv

You will be warned if the header doesn't match and/or any csv rows are malformed.

## License
Released under the MIT License. See [LICENSE](LICENSE) for the full text.

Anyone is free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, subject to the conditions in the license (retaining the copyright and permission notice).

## Development testing
Via shell
> pytest -v

Or use VS Code Testing :)
