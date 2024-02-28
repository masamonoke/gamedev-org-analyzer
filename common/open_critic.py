import json
from threading import Lock
from typing import Dict
import socket
import pickle
import requests

from common.config import logging, config, IGDB_CACHE_PORT
from common.utilities import send_msg, recv_msg
from common.model.igdb import Company

# TODO: need to save it to sql database because of requests limit per day
open_critic_data = {}

def save_open_critic_data(lock: Lock, game_name: str, d: dict):
    lock.acquire()
    open_critic_data[game_name] = d
    lock.release()


class OpenCritic:
    def __init__(self, lock: Lock) -> None:
        self.key = config["RAPIDAPI"]
        self.lock = lock

    def _params(self, game_name: str) -> Dict[str, str]:
        params = {
            "criteria": game_name
        }
        return params

    def _headers(self) -> Dict[str, str]:
        headers = {
            "X-RapidAPI-Key": self.key,
            "X-RapidAPI-Host": "opencritic-api.p.rapidapi.com"
        }
        return headers

    # WARNING: may throw exception if game not found
    def game(self, game_name: str) -> dict:
        if game_name in open_critic_data:
            return open_critic_data[game_name]

        id = self._game_id(game_name)
        url = f"https://opencritic-api.p.rapidapi.com/game/{id}"
        res = requests.get(url=url, headers=self._headers())
        js = json.loads(res.text)
        save_open_critic_data(self.lock, game_name, js)

        return js

    def median_score(self, game_name: str):
        try:
            game = self.game(game_name)
            score = game["medianScore"]
        except ValueError:
            score = 0

        return score

    def _game_id(self, game_name) -> str:
        url = "https://opencritic-api.p.rapidapi.com/game/search"
        res = requests.get(url=url, params=self._params(game_name), headers=self._headers())
        js_list = json.loads(res.text)
        try:
            data = js_list[0]
        except:
            raise ValueError
        return data["id"]

def critic_score(company_name: str, lock: Lock) -> float:
    logging.info(f"Evaluating critic score for {company_name}")
    host = socket.gethostname()
    port = IGDB_CACHE_PORT

    sock = socket.socket()
    sock.connect((host, port))
    logging.info("Connected to IGDB cache service")

    send_msg(sock, company_name.encode())
    company_bytes = recv_msg(sock)
    logging.info(f"Recevied {company_name} data from IGDB cache service")

    if company_bytes is None:
        return 0
    company: Company = pickle.loads(company_bytes)
    if company is None:
        return 0

    c = OpenCritic(lock)
    games = company.list_games_name()
    score = 0
    open_critic_scores_num = 0
    igdb_scores_num = 0
    for g in games:
        if g.critic_rating != 0:
            score += g.critic_rating
            igdb_scores_num += 1
        open_critic_score = c.median_score(g.name)
        if open_critic_score != 0:
            score += open_critic_score
            open_critic_scores_num += 1

    score = score / (igdb_scores_num + open_critic_scores_num)

    logging.info(f"Critic score for {company_name} is {score}. Based on {open_critic_scores_num} Open Critic scores and {igdb_scores_num} IGDB scores")

    return score

