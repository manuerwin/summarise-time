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
    ('ADMIN', 'ADMIN only ADMIN leading prefix removed', 'only ADMIN leading prefix removed'),
    ('DOCS', 'DOCS about DOCS', 'about DOCS'),
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
                'categories': {
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
                }
            },
            '29/04/2025': {
                'totalDateMinutes': 165,
                'totalDateHours': 2.75,
                'categories': {
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
        }
    )
])
def test_process_activities(input_csv, expected):
    assert ap.process_activities(categories_source, input_csv) == expected


def test_total_overall_hours_derives_from_grand_total_minutes():
    # Three days of 10 minutes. Each day rounds to 0.17h, so naively adding the
    # displayed per-day totals gives 0.51. The overall total must instead derive
    # from the grand total of minutes: round(30/60, 2) == 0.5. Hardcoded so the
    # test asserts the intended behaviour, not the implementation against itself.
    csv_data = (
        "Date, Activity, Duration\n"
        "01/01/2025, DOCS a, 10:00\n"
        "02/01/2025, DOCS b, 10:00\n"
        "03/01/2025, DOCS c, 10:00\n"
    )
    result = ap.process_activities(categories_source, csv_data)
    summary = ap.format_result(result)
    naive_sum_of_displayed = round(
        sum(result[d]['totalDateHours'] for d in result), 2)
    assert naive_sum_of_displayed == 0.51  # each day displays 0.17
    assert "TOTAL: 0.5" in summary
    assert "TOTAL: 0.51" not in summary


def test_format_result_emits_single_length_warning_per_category():
    long_name = "x" * 300
    csv_data = (
        "Date, Activity, Duration\n"
        f"01/01/2025, DOCS {long_name}, 30:00\n"
        f"01/01/2025, DOCS another entry, 30:00\n"
    )
    result = ap.process_activities(categories_source, csv_data)
    summary = ap.format_result(result)
    assert summary.count("TOTAL CHARACTER LENGTH") == 1


def test_format_result_overall_by_category():
    # DOCS is seen first (15 min total) but BACKUPS accrues more hours (75 min),
    # so first-seen order (DOCS before BACKUPS) differs from hours-descending.
    csv_data = (
        "Date, Activity, Duration\n"
        "01/01/2025, DOCS mail, 15:00\n"
        "01/01/2025, BACKUPS admin, 30:00\n"
        "02/01/2025, BACKUPS admin, 45:00\n"
    )
    result = ap.process_activities(categories_source, csv_data)
    summary = ap.format_result(result)

    # Header present, above the grand total line.
    assert "OVERALL HOURS:" in summary
    assert summary.index("OVERALL HOURS:") < summary.index("\nTOTAL:")

    # Per-category totals summed across dates, in first-seen order (DOCS before
    # BACKUPS). The per-day lines use parentheses, so assert the colon form
    # inside the OVERALL section to target the summary block specifically.
    section = summary[summary.index("OVERALL HOURS:"):summary.index("\nTOTAL:")]
    assert "DOCS: 0.25" in section     # 15 min
    assert "BACKUPS: 1.25" in section  # 30 + 45 = 75 min
    assert section.index("DOCS: 0.25") < section.index("BACKUPS: 1.25")

    # Category totals sum to the grand total.
    assert "TOTAL: 1.5" in summary
