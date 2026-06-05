import pytest
import activityprocessor as ap


categories_source = "DOCS\nBACKUPS\nADMIN\nPROFESSIONAL"
categories = ap.extract_categories(categories_source)


def test_valid_header_should_not_fail():
    csv_data = "Date, Activity, Duration\nrow1,row2,row3"
    ap.check_csv_header(csv_data)  # Should not raise


def test_invalid_header_typo_should_raise_valueError():
    csv_data = "Date, Activity, Durtion\nrow1,row2,row3"
    with pytest.raises(ValueError):
        ap.check_csv_header(csv_data)


def test_malformed_csv_row():
    # categories_source = "DOCS\nBACKUPS\nADMIN\nPROFESSIONAL"
    bad_csv = "Date, Activity, Duration\n2025-04-28, BACKUPS - Something| XXX, 30:00\n2025-04-28, BACKUPS - Something| XXX, 30:00, extra"
    with pytest.raises(ValueError, match="Malformed CSV row at line 3"):
        ap.process_activities(categories_source, bad_csv)


@pytest.mark.parametrize("input_str,expected_minutes", [
    ('30:00', 30),
    ('1:00:00', 60),
    ('1:30:00', 90),
    ('2:15:00', 135),
    ('0:90:00', 90),
    ('0:60:00', 60),
    ('90:00', 90),
    ('60:00', 60),
    ('2:75:00', 195),
])
def test_duration_parsing(input_str, expected_minutes):
    assert ap.duration_to_minutes(input_str) == expected_minutes


@pytest.mark.parametrize("minutes, expected_hours", [
        (120, 2.0),
        (60, 1.0),
        (0, 0.0),
        (90, 1.5),
        (150, 2.5),
        (45, 0.75),
        (30, 0.5),
        (15, 0.25),
        (77, 1.28),  # 77/60 = 1.2833..., rounded to 1.28
    ]
)
def test_minutes_to_hours_decimal(minutes, expected_hours):
    assert ap.minutes_to_hours_decimal(minutes) == expected_hours


@pytest.mark.parametrize("activity,expected", [
    ('DOCS - hyphen', 'DOCS'),
    ('DOCS', 'DOCS'),
    ('DOCS - Mixed case', 'DOCS'),
    ('DOCS no hyphen', 'DOCS'),
    ('BACKUPS - hyphen', 'BACKUPS'),
    ('BACKUPS Test no hyphen', 'BACKUPS'),
    ('BACKUPS Test lowercase', 'BACKUPS'),
    ('PROFESSIONAL Test', 'PROFESSIONAL'),
    ('ADMIN lower case', 'ADMIN'),
    ('PROFESSIONAL lower case test', 'PROFESSIONAL'),
    ('admin category lower case test', 'ADMIN'),
    ('Test other', 'OTHER'),
])
def test_category_extraction(activity, expected):
    assert ap.extract_category(activity, categories) == expected


@pytest.mark.parametrize("category,activity,expected", [
    ('DOCS', 'DOCS - no pipe', 'no pipe'),
    ('DOCS', 'DOCS - nothing after pipe|', 'nothing after pipe'),
    ('BACKUPS', 'BACKUPS pipe+no space|no space', 'pipe+no space'),
    ('BACKUPS', 'BACKUPS pipe+space | ignore', 'pipe+space'),
    ('BACKUPS', 'BACKUPS pipe+space |  ignore', 'pipe+space'),
    ('BACKUPS', 'BACKUPS pipe+space  | ignore', 'pipe+space'),
    ('BACKUPS', 'BACKUPS pipe+space |ignore', 'pipe+space'),
    ('BACKUPS', 'BACKUPS pipe+space| ignore', 'pipe+space'),
])
def test_clean_activity_name(category, activity, expected):
    assert ap.clean_activity_name(activity, category) == expected


@pytest.mark.parametrize("input_csv,expected", [
    (
        "Date, Activity, Duration\n"
        "28/04/2025, BACKUPS appointment | detail to be ignored, 30:00\n"
        "28/04/2025, DOCS - Pick up mail, 15:00\n"
        "28/04/2025, BACKUPS - admin |detail to be ignored, 30:00\n"
        "28/04/2025, ADMIN tax return, 1:00:00\n"
        "28/04/2025, bACKUPS - admin| duplicate combined with above, 30:00\n"
        "28/04/2025, PROFESSIONAL - Papa Reo, 1:00:00\n"
        "28/04/2025, BACKUPS - admin | , 30:00\n"
        "29/04/2025, PROFESSIONAL - admin| detail to be ignored, 30:00\n"
        "29/04/2025, PROFESSIONAL - PT conditioning, 45:00\n"
        "29/04/2025, backups - admin, 30:00\n"
        "29/04/2025, something else | detail to be ignored, 30:00\n"
        "29/04/2025, something else |, 30:00\n",
        {
            '28/04/2025': {
                'totalDateMinutes': 255,
                'totalDateHours': 4.25,
                'BACKUPS': {
                    'totalDateMinutes': 120,
                    'totalDateHours': 2.0,
                    'activities': [
                        ('appointment', 30),
                        ('admin', 90)
                    ]
                },
                'DOCS': {
                    'totalDateMinutes': 15,
                    'totalDateHours': 0.25,
                    'activities': [
                        ('Pick up mail', 15)
                    ]
                },
                'ADMIN': {
                    'totalDateMinutes': 60,
                    'totalDateHours': 1.00,
                    'activities': [
                        ('tax return', 60)
                    ]
                },
                'PROFESSIONAL': {
                    'totalDateMinutes': 60,
                    'totalDateHours': 1.00,
                    'activities': [
                        ('Papa Reo', 60)
                    ]
                }
            },
            '29/04/2025': {
                'totalDateMinutes': 165,
                'totalDateHours': 2.75,
                'PROFESSIONAL': {
                    'totalDateMinutes': 75,
                    'totalDateHours': 1.25,
                    'activities': [
                        ('admin', 30),
                        ('PT conditioning', 45)
                    ]
                },
                'BACKUPS': {
                    'totalDateMinutes': 30,
                    'totalDateHours': 0.5,
                    'activities': [
                        ('admin', 30)
                    ]
                },
                'OTHER': {
                    'totalDateMinutes': 60,
                    'totalDateHours': 1.0,
                    'activities': [
                        ('something else', 60)
                    ]
                }
            }
        }
    )
])
def test_process_activities(input_csv, expected):
    assert ap.process_activities(categories_source, input_csv) == expected
