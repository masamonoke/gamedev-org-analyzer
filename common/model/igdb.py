from datetime import datetime
from typing import List

class Game:
    def __init__(self, igdb_id: int, name: str, release_date: int, hypes: int, rating: int, rating_count: int, reddit: str):
        self.igdb_id = igdb_id
        self.name = name
        self.release_date = release_date
        self.hypes = hypes  # Number of follows a game gets before release
        self.rating = rating
        self.rating_count = rating_count
        self.reddit = reddit

    def _key(self):
        return self.name

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, o):
        if isinstance(o, Game):
            return self._key() == o._key()
        return False


# country is of type pycountry.db.Country
class Company:
    def __init__(self, id: str, name: str, developed_games: List[Game], published_games: List[Game], founded: datetime, country):
        self.id = id
        self.name = name
        self.developed_games = developed_games
        self.published_games = published_games
        self.founded = founded
        self.country = country

    def list_games_name(self, sorted=True, reverse=True, with_hypes=True, sort_by="release_date"):
        games = self.developed_games + self.published_games
        if with_hypes:
            tmp = []
            for g in games:
                if g.hypes != 0:
                    tmp.append(g)
            games = tmp
        games = list(set(games))
        if sorted:
            games.sort(reverse=reverse, key=lambda x: getattr(x, sort_by))
        return games
