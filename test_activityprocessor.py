import pytest
import tempfile
import os
import activityprocessor as ap

SAMPLE_CSV = """Date, Activity, Duration
28/04/2025, BSR Doctor appointment, 30:00
28/04/2025, BSR OPS - Pick up mail, 15:00
28/04/2025, BSR - admin, 30:00
28/04/2025, INTERNAL tax return, 1:00:00
28/04/2025, PRACTICE - Papa Reo, 1:00:00
29/04/2025, BSR - admin, 30:00
29/04/2025, PRACTICE - PT conditioning, 45:00
29/04/2025, BSR - admin, 30:00
29/04/2025, something else, 30:00
"""

def test_valid_header():
    csv_data = "Date, Activity, Duration\nrow1,row2,row3"
    ap.check_csv_header(csv_data)  # Should not raise

def test_invalid_header_typo():
    csv_data = "Date, Activity, Durtion\nrow1,row2,row3"
    with pytest.raises(ValueError):
        ap.check_csv_header(csv_data)

@pytest.mark.parametrize("input_str,expected", [
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
def test_duration_parsing(input_str, expected):
    assert ap.duration_to_minutes(input_str) == expected

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

def test_full_processing(tmp_path):
    expected = {
        '28/04/2025': {
            'BSR':
                {'total_time': 60,
                 'activities': [('Doctor appointment', 30),
                                ('admin', 30)]},
            'BSR OPS':
                {'total_time': 15,
                 'activities': [('Pick up mail', 15)]},
            'INTERNAL':
                {'total_time': 60,
                 'activities': [('tax return', 60)]},
            'PRACTICE':
                {'total_time': 60,
                 'activities': [('Papa Reo', 60)]}
        },
        '29/04/2025': {
            'BSR':
                {'total_time': 60,
                 'activities': [('admin', 30), ('admin', 30)]},
            'PRACTICE':
                {'total_time': 45,
                 'activities': [('PT conditioning', 45)]},
            'OTHER':
                {'total_time': 30,
                 'activities': [('something else', 30)]}
        }
    }

    tmp_csv_path = tmp_path / "test.csv"
    tmp_csv_path.write_text(SAMPLE_CSV, encoding='utf-8')

    csv_content = tmp_csv_path.read_text(encoding='utf-8')
    result = ap.process_activities(csv_content)
    assert result == expected
