import datetime as dt
import json
from threading import Lock
import time
from concurrent.futures import ThreadPoolExecutor
from random import shuffle
from typing import Dict, List
import pickle
import socket
import os

import pycountry
import requests
from dateutil.relativedelta import relativedelta
import sqlite3

from common.config import logging, config_get_key, REDIS_CACHE_PORT, IGDB_CACHE_PORT
from common.model.igdb import Company, Game
from common.utilities import send_msg, recv_msg


class IGDBSocket:
    def __init__(self) -> None:
        is_docker = os.environ.get('DOCKER_CONTAINER', False)
        if is_docker:
            host = "host.docker.internal"
        else:
            host = socket.gethostname()
        port = IGDB_CACHE_PORT

        self.sock = socket.socket()
        self.sock.connect((host, port))
        logging.info("Connected to IGDB cache service")

    def company_data(self, company_name: str) -> Company|None:

        send_msg(self.sock, company_name.encode())
        company_bytes = recv_msg(self.sock)
        logging.info(f"Recevied {company_name} data from IGDB cache service")
        if company_bytes is None:
            return None
        company: Company = pickle.loads(company_bytes)
        if company is None:
            return None

        return company

    def request(self, req: str, data):
        send_msg(self.sock, pickle.dumps((req, data)))
        data = recv_msg(self.sock)
        return data

    def close(self):
        self.sock.close()

# WARNING: this class depends on redis cache service and redis server opened on 6379 port
class IGDBCache:
    def __init__(self) -> None:
        super().__init__()
        self.conn = sqlite3.connect("companies_data.db", check_same_thread=False)
        self.lock = Lock()

        is_docker = os.environ.get('DOCKER_CONTAINER', False)
        if is_docker:
            host = "host.docker.internal"
        else:
            host = socket.gethostname()
        port = REDIS_CACHE_PORT

        self.socket = socket.socket()
        self.socket.settimeout(30)
        self.socket.connect((host, port))
        logging.info("Connected to redis cache service")

        query = """
            CREATE TABLE IF NOT EXISTS game (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                igdb_id INTEGER,
                name TEXT,
                release_date INTEGER,
                hypes INTEGER,
                user_rating REAL,
                user_rating_count REAL,
                critic_rating REAL,
                critic_rating_count REAL,
                reddit TEXT,
                company_name TEXT,
                game_type TEXT
            );
        """
        self.conn.execute(query)
        self.conn.commit()

        query = """
            CREATE TABLE IF NOT EXISTS company (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                igdb_id INTEGER UNIQUE,
                name TEXT UNIQUE,
                founded INTEGER,
                country TEXT
            );
        """
        self.conn.execute(query)
        self.conn.commit()

    def _company_from_redis(self, name: str) -> Company | None:
        self.lock.acquire()
        send_msg(self.socket, name.encode())
        try:
            data = recv_msg(self.socket)
            if data is not None:
                data = bytes(data)
            else:
                return None
        except TimeoutError:
            self.lock.release()
            logging.error(f"Timeout error receiving {name}")
            return None
        self.lock.release()

        company = pickle.loads(data)
        return company

    def _set_company_to_redis(self, key: str, company: Company):
        pickled_tuple = pickle.dumps((key, company))
        self.lock.acquire()
        send_msg(self.socket, pickled_tuple)
        self.lock.release()

    def get_games_by_company(self, name: str) -> list:
        games = []
        company = self._company_from_redis(name)
        self.lock.acquire()
        if company is not None:
            for game in company.developed_games:
                games.append(game)
            for game in company.published_games:
                games.append(game)
            shuffle(games)
        self.lock.release()
        return games

    def add(self, key: str, entry: Company) -> None:
        self.lock.acquire()

        query = """
            INSERT INTO game (igdb_id, name, release_date, hypes, user_rating, user_rating_count, critic_rating, critic_rating_count, reddit, company_name, game_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # TODO: make sure that games in developed and in published is unique and not duplicating
        for g in entry.developed_games:
            try:
                self.conn.execute(query, (
                    g.igdb_id, g.name, g.release_date, g.hypes, g.user_rating, g.user_rating_count,  g.critic_rating, g.critic_rating_count,g.reddit, key, "developed"))
            except sqlite3.IntegrityError:
                logging.error(f"Tried to save game that is already in database: {g.name}")

        for g in entry.published_games:
            try:
                self.conn.execute(query, (
                    g.igdb_id, g.name, g.release_date, g.hypes, g.user_rating, g.user_rating_count, g.critic_rating, g.critic_rating_count, g.reddit, key, "published"))
            except sqlite3.IntegrityError:
                logging.error(f"Tried to save game that is already in database: {g.name}")

        query = """
            INSERT INTO company (igdb_id, name, founded, country)
            VALUES (?, ?, ?, ?)
        """
        try:
            self.conn.execute(query, (entry.id, entry.name, entry.founded, entry.country))
        except sqlite3.IntegrityError:
            logging.error(f"Company {entry} is already saved")
            self.lock.release()
            return

        self.conn.commit()
        self.lock.release()

    def _game_from_db_fetch(self, t: tuple):
        game = Game(t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9])

        return game

    def exists(self, key: str) -> Company | None:
        company = self._company_from_redis(key)
        if company is not None:
            logging.info(f"{key} data present in redis cache")
            return company

        self.lock.acquire()
        cur = self.conn.cursor()

        query = f"""
            SELECT * FROM game WHERE company_name = '{key}' and game_type = 'developed';
        """
        cur.execute(query)
        res = cur.fetchall()

        developed = []
        for t in res:
            developed.append(self._game_from_db_fetch(t))

        query = f"""
            SELECT * FROM game WHERE company_name = '{key}' and game_type = 'published';
        """
        cur.execute(query)
        res = cur.fetchall()

        published = []
        for t in res:
            published.append(self._game_from_db_fetch(t))

        query = f"""
            SELECT * FROM company WHERE name = '{key}'
        """
        cur.execute(query)
        res = cur.fetchone()

        if res is None:
            self.lock.release()
            return None

        self.lock.release()

        company = Company(res[1], res[2], developed, published, res[3], res[4])
        self._set_company_to_redis(company.name, company)

        logging.info(f"{key} company is now loaded to redis cache from sqlite3 database")

        return company

    def get(self, key: str, only_announced: bool = False) -> Company | None:
        if only_announced:
            company = self._company_from_redis(key)
            if company is not None:
                dev = []
                for game in company.developed_games:
                    if game.release_date > time.time():
                        dev.append(game)
                pub = []
                for game in company.published_games:
                    if game.release_date > time.time():
                        pub.append(game)

                return company

        return self._company_from_redis(key)


igdb_cache = IGDBCache()


class LoaderIGDB:

    def __init__(self):
        self.client_id = config_get_key("CLIENT_ID")
        self.client_secret = config_get_key("CLIENT_SECRET")
        self.token = self._auth()
        self.executor = ThreadPoolExecutor(max_workers=2)

    def _auth(self):
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        r = requests.post("https://id.twitch.tv/oauth2/token", params=params)
        logging.debug(f"IGDB authorization response: {r.text}")
        logging.info("Authenticated to IGDB database")
        return json.loads(r.text)["access_token"]

    def get_company_by_name(self, name: str, only_announced: bool = False) -> Company | None:

        try:

            company = igdb_cache.exists(name)
            if company is not None:
                logging.info(f"Got company {name} info from cache")
                return company

            logging.info(f"Loading {name} company data")

            logging.debug(f"Getting '{name}' company data")
            headers = self.header()
            raw_data = f"fields *; where name = \"{name}\";"
            time.sleep(1)
            r = requests.post("https://api.igdb.com/v4/companies/", headers=headers, data=raw_data)
            try:
                j = json.loads(r.text)[0]
            except IndexError:
                logging.error(f"Company with name {name} is not found in IGDB")
                return None
            developed = self._get_games_by_id(j["developed"], only_announced=only_announced)[0]
            published = self._get_games_by_id(j["published"], only_announced=only_announced)[0]
            d, p = self.get_subsidiary_games(j["id"], only_announced=only_announced)
            developed += d
            published += p

            developed.sort(reverse=True, key=lambda x: x.release_date)
            published.sort(reverse=True, key=lambda x: x.release_date)

            c = Company(j["id"], name, developed, published, j["created_at"],
                        pycountry.countries.get(numeric=str(j["country"])).name)

            igdb_cache.add(name, c)
        except Exception as e:
            logging.error(f"Got exception while loading company: {e}")
            return None

        logging.info(f"Loaded {name} company data")

        return c

    def get_subsidiary_games(self, id: int, only_announced: bool = False) -> tuple:
        logging.debug(f"Getting '{id}' company subsidiary companies")
        headers = self.header()
        raw_data = f"fields *; where parent = {id};"
        r = requests.post("https://api.igdb.com/v4/companies/", headers=headers, data=raw_data)
        # TODO: make recursive call for subsidiary of these companies until there is none subsidiary
        developed = []
        published = []
        json_sub_company_data = json.loads(r.text)
        if len(json_sub_company_data) == 0:
            return [], []
        logging.debug(f"Getting {len(json_sub_company_data)} companies games data")
        results = []
        for j in json_sub_company_data:
            if type(j) is not str:
                f1 = self.executor.submit(self._get_games_by_id, j["developed"],
                                          "developed", only_announced) if "developed" in j.keys() else None
                f2 = self.executor.submit(self._get_games_by_id, j["published"],
                                          "published", only_announced) if "published" in j.keys() else None
                if f1 is not None:
                    results.append(f1)
                if f2 is not None:
                    results.append(f2)

                if only_announced:
                    d, p = self.get_subsidiary_games(j["id"], only_announced=only_announced)
                    developed += d
                    published += p
            else:
                logging.error(f"Got error from IGDB while fetching subsidiary: {r.text}")

        for r in results:
            games, t = r.result()
            if t == "published":
                published += games
            elif t == "developed":
                developed += games

        return developed, published

    def _get_games_by_id(self, ids: list, release_type: str = "", only_announced: bool = False):

        games = []

        headers = self.header()

        if not only_announced:
            date = dt.datetime.now() - relativedelta(years=5)
            date = int(time.mktime(date.timetuple()))
        else:
            date = dt.datetime.now()
            date = int(time.mktime(date.timetuple()))

        ids_parts = []
        start_idx, end_idx = 0, 10
        for _ in ids:
            if end_idx < len(ids) - 1:
                ids_parts.append(ids[start_idx:end_idx])
                start_idx += 10
                end_idx += 10
        jsons = []
        for part in ids_parts:
            text = ",".join([str(id) for id in part])
            raw_data = f"fields *; where id = ({text}) & first_release_date > {date} & category = 0 & version_parent = null;"
            time.sleep(1)
            r = requests.post("https://api.igdb.com/v4/games/", headers=headers, data=raw_data)
            j = json.loads(r.text)
            jsons += j

        for j in jsons:
            if type(j) != str:
                hypes = j["hypes"] if "hypes" in j.keys() else 0
                user_rating = j["rating"] if "rating" in j.keys() else 0
                user_rating_count = 0 if user_rating == 0 else j["rating_count"]
                critic_rating = j["total_rating"] if "total_rating" in j.keys() else 0
                critic_rating_count = 0 if critic_rating == 0 else j["total_rating_count"]
                first_release_date = j["first_release_date"] if "first_release_date" in j.keys() else 0
                reddit_url = ""

                if only_announced:
                    g = Game(j["id"], j["name"], first_release_date, hypes, user_rating, user_rating_count, critic_rating, critic_rating_count,reddit_url)
                    games.append(g)
                else:
                    raw_data = f"fields url; where category = 14 & game = {j['id']};"
                    time.sleep(1)
                    r = requests.post("https://api.igdb.com/v4/websites/", headers=headers, data=raw_data)
                    sites_json = json.loads(r.text)
                    if len(sites_json) > 0:
                        try:
                            reddit_url = sites_json[0]["url"]
                        except:
                            logging.error(f"Got exception fetching reddit url: {sites_json}")
                    g = Game(j["id"], j["name"], first_release_date, hypes, user_rating, user_rating_count, critic_rating, critic_rating_count, reddit_url)
                    games.append(g)
            else:
                logging.error(f"Got error from IGDB while fetching games")

        return games, release_type

    def _get_games_data(self, game_ids: List[int]) -> List[dict]:
        if len(game_ids) < 10:
            ids = ",".join([str(id) for id in game_ids])
            raw_data = f"fields *; where id = ({ids});"
            r = requests.post("https://api.igdb.com/v4/games/", headers=self.header(), data=raw_data)
            jsons = json.loads(r.text)
        else:
            ids_parts = []
            start_idx, end_idx = 0, 10
            for _ in game_ids:
                if end_idx < len(game_ids):
                    ids_parts.append(game_ids[start_idx:end_idx])
                    start_idx += 10
                    end_idx += 10
            jsons = []

            for part in ids_parts:
                text = ",".join([str(id) for id in part])
                raw_data = f"fields *; where id = ({text});"
                r = requests.post("https://api.igdb.com/v4/games/", headers=self.header(), data=raw_data)
                j = json.loads(r.text)
                jsons += j

        return jsons

    def get_genres_by_id(self, game_ids: List[int]) -> Dict[str, List[int]]:

        jsons = self._get_games_data(game_ids)

        map = {}
        for j in jsons:
            if type(jsons) != str:
                if "genres" in j:
                    map[j["id"]] = j["genres"]
            else:
                logging.error(f"Got exception while fetching genres from IGDB: {j}")

        return map

    def get_languages_sup_by_id(self, game_ids: List[int]):

        jsons = self._get_games_data(game_ids)

        res = {}
        for j in jsons:
            if type(j) != str:
                if "id" in j:
                    language_supports = j["language_supports"] if "language_supports" in j.keys() else []
                    res[j["id"]] = language_supports

        return res

    def header(self) -> dict:
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.token}"
        }
        return headers

