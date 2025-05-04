import csv
import logging
from collections import defaultdict
import sys
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to INFO or WARNING to reduce verbosity
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


EXPECTED_HEADER = ["Date", "Activity", "Duration"]


def check_csv_header(csv_data):
    first_line = csv_data.lstrip().splitlines()[0]
    if first_line.startswith('\ufeff'):
        first_line = first_line.replace('\ufeff', '')
    header = [col.strip() for col in first_line.split(',')]
    if header != EXPECTED_HEADER:
        raise ValueError(
            f"CSV header mismatch: got {header}, expected {EXPECTED_HEADER}")


def duration_to_minutes(duration_str):
    logger.debug(f"Parsing duration: {duration_str}")
    parts = duration_str.strip().split(':')
    try:
        if len(parts) == 2:  # mm:ss
            minutes = int(parts[0]) + int(parts[1]) / 60
        elif len(parts) == 3:  # hh:mm:ss
            minutes = int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60
        else:
            logger.error(f"Invalid duration format: {duration_str}")
            raise ValueError(f"Invalid duration format: {duration_str}")
    except Exception as e:
        logger.error(f"Error parsing duration '{duration_str}': {e}")
        raise
    logger.debug(f"Duration in minutes: {minutes}")
    return round(minutes)


def extract_category(activity):
    logger.debug(f"Extracting category from activity: {activity}")
    for cat in ['BSR OPS', 'BSR', 'INTERNAL', 'PRACTICE']:
        if activity.startswith(cat):
            logger.debug(f"Matched category: {cat}")
            return cat
    logger.debug("No matching category found, using 'OTHER'")
    return 'OTHER'


def clean_activity_name(activity, category):
    cleaned = activity.replace(category, '', 1).strip(' -')
    logger.debug(f"Cleaned activity name: '{activity}' -> '{cleaned}'")
    return cleaned


def process_activities(csv_data):
    logger.info("Checking csv header")
    check_csv_header(csv_data)
    logger.info("Processing CSV data")
    # Prepare the result structure
    result = defaultdict(lambda:
                         defaultdict(lambda:
                                     {'total_time': 0, 'activities': []}))
    reader = csv.DictReader(io.StringIO(csv_data), skipinitialspace=True)
    for row in reader:
        date = row['Date'].strip()
        activity_raw = row['Activity'].strip()
        duration_str = row['Duration'].strip()

        logger.debug(f"Processing row: {row}")

        category = extract_category(activity_raw)
        activity = clean_activity_name(activity_raw, category)
        minutes = duration_to_minutes(duration_str)

        result[date][category]['total_time'] += minutes
        result[date][category]['activities'].append((activity, minutes))

    logger.info("Processing complete")
    # Convert defaultdicts to dicts for output
    return {date: dict(cats) for date, cats in result.items()}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.error("Usage: python activityprocessor.py path/to/your/.csv")
        sys.exit(1)
    csv_file_path = sys.argv[1]
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            csv_data = f.read()
    except Exception as e:
        logger.error(f"Failed to read file '{csv_file_path}': {e}")
        sys.exit(1)

    result = process_activities(csv_data)
    for date in result:
        print(date)
        for category in result[date]:
            print(
                f"{category} - total: {result[date][category]['total_time']}")
            for activity, duration in result[date][category]['activities']:
                print(
                    f"- {activity} ({duration})")
