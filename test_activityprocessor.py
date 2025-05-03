import unittest
import os
import activityprocessor as ap


class TestActivityProcessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Adjust the path as needed
        sample_path = os.path.join(os.path.dirname(__file__),
                                   './sample_activities.csv')
        with open(sample_path, encoding='utf-8') as f:
            cls.sample_csv = f.read()

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
                'BSR': {'totalTime': 60,
                        'activities': [('Doctor', 30), ('admin', 30)]},
                'BSR OPS': {'totalTime': 15,
                            'activities': [('Pick up mail', 15)]},
                'INTERNAL': {'totalTime': 60,
                             'activities': [('tax return', 60)]},
                'PRACTICE': {'totalTime': 60,
                             'activities': [('Papa Reo', 60)]}
            },
            '29/04/2025': {
                'BSR':
                    {'totalTime': 60,
                        'activities': [('admin', 30), ('admin', 30)]},
                'PRACTICE': {'totalTime': 45,
                             'activities': [('PT conditioning', 45)]},
                'OTHER': {'totalTime': 30,
                          'activities': [('something else entirely', 30)]}
            }
        }
        result = ap.process_activities(self.sample_csv)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
