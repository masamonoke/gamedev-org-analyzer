import requests
import json
import os
import logging
from datetime import datetime
import pycountry
from tqdm import tqdm
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor

import time
from dateutil.relativedelta import relativedelta
import datetime as dt

import sys
sys.path.append("../")
from config import config_get_key
from model.igdb import Company, Game

logging.basicConfig(format='%(asctime)s, %(msecs)03d %(levelname)-3s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO)

class LoaderIGDB:
    def __init__(self):
        self.client_id = config_get_key("CLIENT_ID")
        self.client_secret = config_get_key("CLIENT_SECRET")
        self.token = self._auth()
        self.executor = ThreadPoolExecutor()

    def _auth(self):
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        r = requests.post("https://id.twitch.tv/oauth2/token", params=params)
        logging.info(f"IGDB authorization response: {r.text}")
        return json.loads(r.text)["access_token"]

    def getCompanyByName(self, name: str) -> Company:
        logging.info(f"Getting '{name}' company data")
        headers = self.header()
        raw_data = f"fields *; where name = \"{name}\";"
        r = requests.post("https://api.igdb.com/v4/companies/", headers=headers, data=raw_data)
        try:
            j = json.loads(r.text)[0]
        except IndexError:
            logging.error(f"Company with name {name} is not found if IGDB")
            return None
        developed = self.getGamesById(j["developed"])[0]
        published = self.getGamesById(j["published"])[0]
        d, p = self.getSubsidiaryGames(j["id"])
        developed += d
        published += p
        c = Company(j["id"], name, developed, published, j["created_at"], pycountry.countries.get(numeric=str(j["country"])))
        return c

    def getSubsidiaryGames(self, id: int) -> list:
        logging.info(f"Getting '{id}' company subsidiary companies")
        headers = self.header()
        raw_data = f"fields *; where parent = {id};"
        r = requests.post("https://api.igdb.com/v4/companies/", headers=headers, data=raw_data)
        developed = []
        published = []
        json_data = json.loads(r.text)
        logging.info(f"Getting {len(json_data)} companies games data")
        results = []
        for j in json_data:
            if "developed" in j.keys():
                d_ids = j["developed"]
            f1 = self.executor.submit(self.getGamesById, j["developed"], "developed") if "developed" in j.keys() else None
            f2 = self.executor.submit(self.getGamesById, j["published"], "published") if "published" in j.keys() else None
            if f1 != None:
                results.append(f1)
            if f2 != None:
                results.append(f2)
        for r in results:
            games, t = r.result()
            if t == "published":
                published += games
            elif t == "developed":
                developed += games
        return (developed, published)

    def getGameById(self, id: list) -> Game:
        headers = self.header()
        raw_data = f"fields *; where id = {id};"
        r = requests.post("https://api.igdb.com/v4/games/", headers=headers, data=raw_data)
        j = json.loads(r.text)
        try:
            j = j[0]
        except:
            print(j)
        genres = self._getGenresById([str(g) for g in j["genres"]]) if "genres" in j else None
        hypes = j["hypes"] if "hypes" in j.keys() else 0
        rating = j["rating"] if "rating" in j.keys() else 0
        rating_count = 0 if rating == 0 else j["rating_count"]
        first_release_date = j["first_release_date"] if "first_release_date" in j.keys() else None
        g = Game(j["name"], first_release_date, genres, hypes, rating, rating_count)
        return g

    def getGamesById(self, ids: list, t=None):
        if t != None:
            logging.info(f"Getting {t} games")
        ids_text = ",".join([str(id) for id in ids])
        headers = self.header()
        date = dt.datetime.now() - relativedelta(years=5)
        date = int(time.mktime(date.timetuple()))
        raw_data = f"fields *; where id = ({ids_text}) & first_release_date > {date};"
        r = requests.post("https://api.igdb.com/v4/games/", headers=headers, data=raw_data)
        jsons = json.loads(r.text)
        games = []
        for j in jsons:
            genres = self._getGenresById([str(g) for g in j["genres"]]) if "genres" in j else None
            hypes = j["hypes"] if "hypes" in j.keys() else 0
            rating = j["rating"] if "rating" in j.keys() else 0
            rating_count = 0 if rating == 0 else j["rating_count"]
            first_release_date = j["first_release_date"] if "first_release_date" in j.keys() else None
            g = Game(j["name"], first_release_date, genres, hypes, rating, rating_count)
            games.append(g)
        return (games, t)


    def _getGenresById(self, ids: list):
        ids_text = ",".join(ids)
        headers = self.header()
        raw_data = f"fields *; where id = ({ids_text});"
        r = requests.post("https://api.igdb.com/v4/genres/", headers=headers, data=raw_data)
        genres = []
        for j in json.loads(r.text):
            try:
                genres.append(j["name"])
            except:
                print(j)
        return genres

    def header(self) -> dict:
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.token}"
        }
        return headers
