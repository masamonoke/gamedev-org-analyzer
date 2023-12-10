import unittest

import sys
sys.path.append("../")
from loader.reddit import RedditLoader

class TestRedditLoader(unittest.TestCase):

    def setUp(self):
        self.reddit = RedditLoader()

    def test_load_correct_game(self):
        comms = self.reddit.comments("Starfield")
        self.assertTrue(len(comms) != 0)

    def test_load_incorrect_game(self):
        comms = self.reddit.comments("Starfied")
        self.assertTrue(len(comms) == 0)


if __name__ == '__main__':
    unittest.main()

