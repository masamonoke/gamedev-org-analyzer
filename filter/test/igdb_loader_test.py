import unittest

import sys
sys.path.append("../")
from loader.igdb import LoaderIGDB

class TestIgdbLoader(unittest.TestCase):

    def setUp(self):
        self.idgb = LoaderIGDB()
        self.cachedCompany = self.idgb.getCompanyByName("Microsoft")

    def test_load_company(self):
        self.assertEqual("Microsoft", self.cachedCompany.name)

    #TODO: check duplicates in games list
    def test_sort_games(self):
        games = self.cachedCompany.listGamesName()
        is_sorted = True
        prev = None
        for g in games:
            if prev == None:
                prev = g
                continue
            if prev.release_date < g.release_date:
                is_sorted = False
                break
        for g in games:
            print(g.name, g.hypes)
        self.assertTrue(is_sorted)


if __name__ == '__main__':
    unittest.main()
