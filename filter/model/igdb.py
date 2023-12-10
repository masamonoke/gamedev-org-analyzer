from datetime import datetime

class Game:
    def __init__(self, name: str, release_date: datetime, genres: list, hypes: None,
            rating: None, rating_count: None):
        self.name = name
        self.release_date = release_date
        self.genres = genres
        self.hypes = hypes # Number of follows a game gets before release
        self.rating = rating
        self.rating_count = rating_count

    # TODO: define if game is update of released product or some new release
    def isUpdate():
        pass

    def _key(self):
        return (self.name)

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, o):
        if isinstance(o, Game):
            return self._key() == o._key()
        return False

    def __str__(self):
        return f"Game(name={self.name}, release_date={self.release_date}, genres={self.genres}, hypes={self.hypes}, rating={self.rating}, rating_count={self.rating_count})"

class Company:
    def __init__(self, id: str, name: str, developed_games: list, published_games: list, founded: datetime, country: str):
        self.id = id
        self.name = name
        self.developed_games = developed_games
        self.published_games = published_games
        self.founded = founded
        self.country = country

    def listGamesName(self, sorted=True, reverse=True, with_hypes=True, sort_by="release_date"):
        games = self.developed_games + self.published_games
        if with_hypes:
            tmp = []
            for g in games:
                if g.hypes != 0:
                    tmp.append(g)
            games = tmp
        games = list(set(games))
        if sorted:
            games.sort(reverse=reverse, key= lambda x: getattr(x, sort_by))
        return games

    def __str__(self):
        d = [str(d) for d in self.developed_games]
        d = "[" + "".join(d) + "]"
        p = [str(p) for p in self.published_games]
        p =  "[" + "".join(p) + "]"
        return f"Company(name={self.name}, developed_games=\n\t{d},\n published_games=\n\t{p},\n founded={self.founded}, country={self.country})"

