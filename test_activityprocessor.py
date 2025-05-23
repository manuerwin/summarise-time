import pytest
import activityprocessor as ap


def test_valid_header_should_not_fail():
    csv_data = "Date, Activity, Duration\nrow1,row2,row3"
    ap.check_csv_header(csv_data)  # Should not raise


def test_invalid_header_typo_should_raise_valueError():
    csv_data = "Date, Activity, Durtion\nrow1,row2,row3"
    with pytest.raises(ValueError):
        ap.check_csv_header(csv_data)


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
    ('BSR OPS - Test', 'BSR OPS'),
    ('BSR OPS no dash', 'BSR OPS'),
    ('BSR - Test', 'BSR'),
    ('BSR Test no dash', 'BSR'),
    ('PRACTICE Test', 'PRACTICE'),
    ('Test other', 'OTHER'),
])
def test_category_extraction(activity, expected):
    assert ap.extract_category(activity) == expected


@pytest.mark.parametrize("category,activity,expected", [
    ('BSR OPS', 'BSR OPS - no pipe', 'no pipe'),
    ('BSR OPS', 'BSR OPS - nothing after pipe|', 'nothing after pipe'),
    ('BSR', 'BSR pipe+no space|no space', 'pipe+no space'),
    ('BSR', 'BSR pipe+space | ignore', 'pipe+space'),
    ('BSR', 'BSR pipe+space |  ignore', 'pipe+space'),
    ('BSR', 'BSR pipe+space  | ignore', 'pipe+space'),
    ('BSR', 'BSR pipe+space |ignore', 'pipe+space'),
    ('BSR', 'BSR pipe+space| ignore', 'pipe+space'),
])
def test_clean_activity_name(category, activity, expected):
    assert ap.clean_activity_name(activity, category) == expected


@pytest.mark.parametrize("input_csv,expected", [
    (
        "Date, Activity, Duration\n"
        "28/04/2025, BSR appointment | detail to be ignored, 30:00\n"
        "28/04/2025, BSR OPS - Pick up mail, 15:00\n"
        "28/04/2025, BSR - admin |detail to be ignored, 30:00\n"
        "28/04/2025, INTERNAL tax return, 1:00:00\n"
        "28/04/2025, BSR - admin| duplicate combined with above, 30:00\n"
        "28/04/2025, PRACTICE - Papa Reo, 1:00:00\n"
        "28/04/2025, BSR - admin | , 30:00\n"
        "29/04/2025, PRACTICE - admin| detail to be ignored, 30:00\n"
        "29/04/2025, PRACTICE - PT conditioning, 45:00\n"
        "29/04/2025, BSR - admin, 30:00\n"
        "29/04/2025, something else | detail to be ignored, 30:00\n"
        "29/04/2025, something else |, 30:00\n",
        {
            '28/04/2025': {
                'totalTimeMinutes': 255,
                'totalTimeHours': 4.25,
                'BSR': {
                    'totalTimeMinutes': 120,
                    'totalTimeHours': 2.0,
                    'activities': [
                        ('appointment', 30),
                        ('admin', 90)
                    ]
                },
                'BSR OPS': {
                    'totalTimeMinutes': 15,
                    'totalTimeHours': 0.25,
                    'activities': [
                        ('Pick up mail', 15)
                    ]
                },
                'INTERNAL': {
                    'totalTimeMinutes': 60,
                    'totalTimeHours': 1.00,
                    'activities': [
                        ('tax return', 60)
                    ]
                },
                'PRACTICE': {
                    'totalTimeMinutes': 60,
                    'totalTimeHours': 1.00,
                    'activities': [
                        ('Papa Reo', 60)
                    ]
                }
            },
            '29/04/2025': {
                'totalTimeMinutes': 165,
                'totalTimeHours': 2.75,
                'PRACTICE': {
                    'totalTimeMinutes': 75,
                    'totalTimeHours': 1.25,
                    'activities': [
                        ('admin', 30),
                        ('PT conditioning', 45)
                    ]
                },
                'BSR': {
                    'totalTimeMinutes': 30,
                    'totalTimeHours': 0.5,
                    'activities': [
                        ('admin', 30)
                    ]
                },
                'OTHER': {
                    'totalTimeMinutes': 60,
                    'totalTimeHours': 1.0,
                    'activities': [
                        ('something else', 60)
                    ]
                }
            }
        }
    )
])
def test_process_activities(input_csv, expected):
    assert ap.process_activities(input_csv) == expected
