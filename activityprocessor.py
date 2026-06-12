import csv
import logging
import sys
import io
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to INFO or WARNING to reduce verbosity
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


EXPECTED_HEADER = ["Date", "Activity", "Duration"]
MAX_COMMENT_LENGTH = 245


def extract_categories(categories_source):
    return [line.strip() for line in categories_source.splitlines() if line.strip()]


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


def minutes_to_hours_decimal(minutes):
    logger.debug(f"Parsing minutes to hours decimal: {minutes}")
    return round(minutes / 60, 2)


def extract_category(activity, categories):
    logger.debug(f"Extracting category from activity: {activity}")
    for cat in categories:
        if activity.upper().startswith(cat.upper()):
            logger.debug(f"Matched category: {cat}")
            return cat
    logger.debug("No matching category found, using 'OTHER'")
    return 'OTHER'


def clean_activity_name(activity, category):
    # Remove leading category prefix
    pattern = re.compile('^' + re.escape(category), re.IGNORECASE)
    cleaned = pattern.sub('', activity, count=1).strip(' -')
    # If there's a '|', remove everything from it onwards
    if '|' in cleaned:
        cleaned = cleaned.split('|', 1)[0].rstrip()
    return cleaned.strip()


def process_activities(categories_source, csv_data):
    categories = extract_categories(categories_source)
    check_csv_header(csv_data)
    reader = csv.reader(io.StringIO(csv_data), skipinitialspace=True)
    next(reader)

    result = {}

    for row_num, row in enumerate(reader, start=2):
        if len(row) != len(EXPECTED_HEADER):
            raise ValueError(
                f"Malformed CSV row at line {row_num}: expected {len(EXPECTED_HEADER)} fields, got {len(row)}. Row: {row}"
            )
        date = row[0].strip()
        activity_raw = row[1].strip()
        duration_str = row[2].strip()

        category = extract_category(activity_raw, categories)
        activity = clean_activity_name(activity_raw, category)
        minutes = duration_to_minutes(duration_str)

        # Initialize date entry if not present
        if date not in result:
            result[date] = {
                'totalDateMinutes': 0,
                'totalDateHours': 0.0,
                'categories': {}
            }
        date_entry = result[date]

        # Initialize category entry if not present
        if category not in date_entry['categories']:
            date_entry['categories'][category] = {
                'totalDateMinutes': 0,
                'totalDateHours': 0.0,
                'activities': {}
            }
        cat_entry = date_entry['categories'][category]

        # Combine duplicate activities (preserving first-seen order)
        activities = cat_entry['activities']
        activities[activity] = activities.get(activity, 0) + minutes

        # accumulate minutes
        cat_entry['totalDateMinutes'] += minutes
        date_entry['totalDateMinutes'] += minutes

    # compute hours
    for date_entry in result.values():
        date_entry['totalDateHours'] = minutes_to_hours_decimal(date_entry['totalDateMinutes'])
        for cat_entry in date_entry['categories'].values():
            cat_entry['totalDateHours'] = minutes_to_hours_decimal(cat_entry['totalDateMinutes'])
            cat_entry['activities'] = list(cat_entry['activities'].items())

    return result


def format_result(result, max_comment_length=MAX_COMMENT_LENGTH):
    lines = []
    total_overall_minutes = 0
    for date, date_entry in result.items():
        total_overall_minutes += date_entry['totalDateMinutes']
        lines.append(f"\n{date} ({date_entry['totalDateHours']})")
        for category, cat_data in date_entry['categories'].items():
            lines.append(f"{category} ({cat_data['totalDateHours']})")
            total_length = 0
            for activity, minutes in cat_data['activities']:
                hours = minutes_to_hours_decimal(minutes)
                comment = f" - {activity} ({hours})"
                lines.append(comment)
                total_length += len(comment)

            if total_length > max_comment_length:
                lines.append(
                    f"###### {category} TOTAL CHARACTER LENGTH ({total_length}) TOO BIG ######")
    lines.append(
        f"\nTOTAL OVERALL HOURS: {minutes_to_hours_decimal(total_overall_minutes)}")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.error("Usage: python activityprocessor.py path/to/your/.csv")
        sys.exit(1)

    category_file_path = Path(__file__).with_name('categories.txt')
    try:
        with open(category_file_path, 'r', encoding='utf-8') as f:
            categories_source = f.read()
    except Exception as e:
        logger.error(f"Failed to read file '{category_file_path}': {e}")
        sys.exit(1)
    csv_file_path = sys.argv[1]
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            csv_data = f.read()
    except Exception as e:
        logger.error(f"Failed to read file '{csv_file_path}': {e}")
        sys.exit(1)

    result = process_activities(categories_source, csv_data)
    print(format_result(result))
