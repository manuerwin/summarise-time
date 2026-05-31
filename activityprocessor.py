import csv
import logging
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


def minutes_to_hours_decimal(minutes):
    logger.debug(f"Parsing minutes to hours decimal: {minutes}")
    return round(minutes / 60, 2)


def extract_category(activity):
    activity = activity.upper()
    logger.debug(f"Extracting category from activity: {activity}")
    for cat in ['BSR OPS', 'BSR', 'INTERNAL', 'PRACTICE']:
        if activity.startswith(cat):
            logger.debug(f"Matched category: {cat}")
            return cat
    logger.debug("No matching category found, using 'OTHER'")
    return 'OTHER'


def clean_activity_name(activity, category):
    # Remove the category prefix and any leading/trailing spaces/dashes
    cleaned = activity.replace(category, '', 1).strip(' -')
    # If there's a '|', remove everything from it onwards
    if '|' in cleaned:
        cleaned = cleaned.split('|', 1)[0].rstrip()
    return cleaned.strip()


def process_activities(csv_data):
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

        category = extract_category(activity_raw)
        activity = clean_activity_name(activity_raw, category)
        minutes = duration_to_minutes(duration_str)

        # Initialize date entry if not present
        if date not in result:
            result[date] = {
                'totalDateMinutes': 0,
                'totalDateHours': 0.0
            }

        # Initialize category entry if not present
        if category not in result[date]:
            result[date][category] = {
                'totalDateMinutes': 0,
                'totalDateHours': 0.0,
                'activities': []
            }

        # Combine duplicate activities (preserving order)
        activities = result[date][category]['activities']
        for i, (act, mins) in enumerate(activities):
            if act == activity:
                activities[i] = (act, mins + minutes)
                break
        else:
            activities.append((activity, minutes))

        # Update category and day totals
        result[date][category]['totalDateMinutes'] += minutes
        result[date][category]['totalDateHours'] = minutes_to_hours_decimal(result[date][category]['totalDateMinutes'])
        result[date]['totalDateMinutes'] += minutes
        result[date]['totalDateHours'] = minutes_to_hours_decimal(result[date]['totalDateMinutes'])

    return result


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
    maxCommentLength = 245
    total_overall_hours = 0.0
    for date in result:
        print(f"\n{date} ({result[date]['totalDateHours']})")
        # Print per-category totalDateHours and activities
        for category, cat_data in result[date].items():
            if category.startswith("totalDate"):
                continue
            print(f"{category} ({cat_data['totalDateHours']})")
            totalLength = 0
            for activity, minutes in cat_data['activities']:
                hours = minutes_to_hours_decimal(minutes)
                total_overall_hours += hours
                comments = f" - {activity} ({hours})"
                print(comments)
                totalLength += (len(comments))
                if totalLength > maxCommentLength:
                    print(f"###### {category} TOTAL CHARACTER LENGTH ({totalLength}) TOO BIG ######")
    print(f"\nTOTAL OVERALL HOURS: {total_overall_hours}")