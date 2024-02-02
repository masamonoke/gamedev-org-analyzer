import datetime as dt
import json
import sys
from threading import Lock
import time
from concurrent.futures import ThreadPoolExecutor
from random import shuffle

import pycountry
import requests
from dateutil.relativedelta import relativedelta

sys.path.append("../")
from config import logging
from config import config_get_key
from model.igdb import Company, Game
from cache import TimedCache

# INFO: igdb has request per second limit from one ip and because sleep is used


class IGDBCache(TimedCache):
    def get_games_by_company(self, name: str) -> list:
        self.lock.acquire()
        games = []
        company: Company = self.cache[name]
        for game in company.developed_games:
            games.append(game)
        for game in company.published_games:
            games.append(game)
        shuffle(games)
        self.lock.release()
        return games

igdb_cache = IGDBCache()

class LoaderIGDB:

    instances = 0

    def __init__(self, lock: Lock):
        self.client_id = config_get_key("CLIENT_ID")
        self.client_secret = config_get_key("CLIENT_SECRET")
        self.token = self._auth()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.lock = lock

    def _auth(self):
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        r = requests.post("https://id.twitch.tv/oauth2/token", params=params)
        logging.debug(f"IGDB authorization response: {r.text}")
        return json.loads(r.text)["access_token"]

    def get_company_by_name(self, name: str) -> Company|None:

        if igdb_cache.exists(name):
            company = igdb_cache.get(name)
            return company

        self.lock.acquire()
        self.instances += 1
        self.lock.release()

        logging.debug(f"Getting '{name}' company data")
        headers = self.header()
        raw_data = f"fields *; where name = \"{name}\";"
        r = requests.post("https://api.igdb.com/v4/companies/", headers=headers, data=raw_data)
        try:
            j = json.loads(r.text)[0]
        except IndexError:
            logging.error(f"Company with name {name} is not found in IGDB")
            return None
        developed = self.get_games_by_id(j["developed"])[0]
        time.sleep(1 + self.instances)
        published = self.get_games_by_id(j["published"])[0]
        d, p = self.get_subsidiary_games(j["id"])
        developed += d
        published += p
        c = Company(j["id"], name, developed, published, j["created_at"],
                    pycountry.countries.get(numeric=str(j["country"])))

        self.lock.acquire()
        self.instances -= 1
        self.lock.release()

        igdb_cache.add(name, c)

        return c

    def get_subsidiary_games(self, id: int) -> tuple:
        logging.debug(f"Getting '{id}' company subsidiary companies")
        headers = self.header()
        raw_data = f"fields *; where parent = {id};"
        r = requests.post("https://api.igdb.com/v4/companies/", headers=headers, data=raw_data)
        # TODO: make recursive call for subsidiary of these companies until there is none subsidiary
        developed = []
        published = []
        json_data = json.loads(r.text)
        logging.debug(f"Getting {len(json_data)} companies games data")
        results = []
        for j in json_data:
            if type(j) != str:
                f1 = self.executor.submit(self.get_games_by_id, j["developed"],
                                          "developed") if "developed" in j.keys() else None
                f2 = self.executor.submit(self.get_games_by_id, j["published"],
                                          "published") if "published" in j.keys() else None
                if f1 != None:
                    results.append(f1)
                if f2 != None:
                    results.append(f2)
            else:
                logging.error(f"Got error from IGDB while fetching subsidiary: {r.text}")
        for r in results:
            games, t = r.result()
            if t == "published":
                published += games
            elif t == "developed":
                developed += games
        return (developed, published)

    def get_games_by_id(self, ids: list, t=None):
        if t != None:
            logging.debug(f"Getting {t} games")

        games = []

        ids_text = ",".join([str(id) for id in ids])
        headers = self.header()
        date = dt.datetime.now() - relativedelta(years=5)
        date = int(time.mktime(date.timetuple()))
        raw_data = f"fields *; where id = ({ids_text}) & first_release_date > {date} & category = 0;"
        r = requests.post("https://api.igdb.com/v4/games/", headers=headers, data=raw_data)
        jsons = json.loads(r.text)

        for j in jsons:
            if type(j) != str:
                genres = self._get_genres_by_id([str(g) for g in j["genres"]]) if "genres" in j else None
                hypes = j["hypes"] if "hypes" in j.keys() else 0
                rating = j["rating"] if "rating" in j.keys() else 0
                rating_count = 0 if rating == 0 else j["rating_count"]
                first_release_date = j["first_release_date"] if "first_release_date" in j.keys() else None

                raw_data = f"fields url; where category = 14 & game = {j['id']};"
                time.sleep(5 + self.instances)
                r = requests.post("https://api.igdb.com/v4/websites/", headers=headers, data=raw_data)
                sites_json = json.loads(r.text)
                if len(sites_json) > 0:
                    try:
                        reddit_url = sites_json[0]["url"]
                    except:
                        logging.error(f"Got exception fetching reddit url: {sites_json}")
                        reddit_url = ""
                    g = Game(j["name"], first_release_date, genres, hypes, rating, rating_count, reddit_url)
                    games.append(g)
            else:
                logging.error(f"Got error from IGDB while fetching games: {r.text}")

        return (games, t)

    def _get_genres_by_id(self, ids: list):
        ids_text = ",".join(ids)
        headers = self.header()
        raw_data = f"fields *; where id = ({ids_text});"
        time.sleep(1 + self.instances)
        r = requests.post("https://api.igdb.com/v4/genres/", headers=headers, data=raw_data)
        genres = []
        for j in json.loads(r.text):
            try:
                genres.append(j["name"])
            except Exception:
                logging.error(f"Got exception while fetching genres from IGDB: {r.text}")
        return genres

    def header(self) -> dict:
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.token}"
        }
        return headers
