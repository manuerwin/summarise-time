import unittest
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


class TestActivityProcessing(unittest.TestCase):
    def test_valid_header(self):
        csv_data = "Date, Activity, Duration\nrow1,row2,row3"
        ap.check_csv_header(csv_data)  # Should not raise

    def test_invalid_header_typo(self):
        csv_data = "Date, Activity, Durtion\nrow1,row2,row3"
        with self.assertRaises(ValueError):
            ap.check_csv_header(csv_data)

    def test_duration_parsing(self):
        self.assertEqual(ap.duration_to_minutes('30:00'), 30)
        self.assertEqual(ap.duration_to_minutes('1:00:00'), 60)
        self.assertEqual(ap.duration_to_minutes('1:30:00'), 90)
        self.assertEqual(ap.duration_to_minutes('2:15:00'), 135)

    def test_category_extraction(self):
        self.assertEqual(ap.extract_category('BSR OPS - Test'), 'BSR OPS')
        self.assertEqual(ap.extract_category('BSR OPS no dash'), 'BSR OPS')
        self.assertEqual(ap.extract_category('BSR - Test'), 'BSR')
        self.assertEqual(ap.extract_category('BSR Test no dash'), 'BSR')
        self.assertEqual(ap.extract_category('PRACTICE Test'), 'PRACTICE')
        self.assertEqual(ap.extract_category('Test other'), 'OTHER')

    def test_full_processing(self):
        expected = {
            '28/04/2025': {
                'BSR': {'total_time': 60, 'activities': [('Doctor appointment', 30), ('admin', 30)]},
                'BSR OPS': {'total_time': 15, 'activities': [('Pick up mail', 15)]},
                'INTERNAL': {'total_time': 60, 'activities': [('tax return', 60)]},
                'PRACTICE': {'total_time': 60, 'activities': [('Papa Reo', 60)]}
            },
            '29/04/2025': {
                'BSR': {'total_time': 60, 'activities': [('admin', 30), ('admin', 30)]},
                'PRACTICE': {'total_time': 45, 'activities': [('PT conditioning', 45)]},
                'OTHER': {'total_time': 30, 'activities': [('something else', 30)]}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv', encoding='utf-8') as tmpfile:
            tmpfile.write(SAMPLE_CSV)
            tmpfile.flush()
            tmp_csv_path = tmpfile.name

        try:
            with open(tmp_csv_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            result = ap.process_activities(csv_content)
            self.assertEqual(result, expected)
        finally:
            os.remove(tmp_csv_path)


if __name__ == '__main__':
    unittest.main()
