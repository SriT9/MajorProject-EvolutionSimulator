"Module to perform unittest"
import unittest
from . import load_generations


class FileTestCase(unittest.TestCase):
    "Class that contains test cases for project"

    def test_load_generations(self):
        ''' Tests the creation of some creatures '''
        print(load_generations('test_data/default.pickle'))


if __name__ == "__main__":
    unittest.main()
