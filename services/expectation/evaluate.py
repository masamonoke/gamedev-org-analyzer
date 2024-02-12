from threading import Lock
import sys
import socket
import pickle

sys.path.append("../")
from config import logging, IGDB_CACHE_PORT
from cache import TimedCache
from utilities import send_msg, recv_msg

expectation_cache = TimedCache()

def expectation(company_name: str, lock: Lock) -> float:

    if expectation_cache.exists(company_name):
        return expectation_cache.get(company_name)

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
    company = pickle.loads(company_bytes)
    if company is None:
        return 0

    logging.info(f"Evaluating expectation score for {company_name}")

    score = 0

    languages_sum = 0
    titles_count = len(company.developed_games) + len(company.published_games)

    unique_genres = set()

    game_ids = []
    for d in company.developed_games:
        game_ids.append(d.igdb_id)
    for p in company.published_games:
        game_ids.append(p.igdb_id)

    send_msg(sock, pickle.dumps(("genres", game_ids)))
    data = recv_msg(sock)
    if data is not None:
        genres_map = pickle.loads(data)
        for _, genres in genres_map.items():
            for genre in genres:
                unique_genres.add(genre)

    send_msg(sock, pickle.dumps(("lang", game_ids)))
    data = recv_msg(sock)
    if data is not None:
        lang_map = pickle.loads(data)
        for _, v in lang_map.items():
            languages_sum = + len(v)

    avg_lang_support = languages_sum / titles_count if titles_count != 0 else 0
    unique_genres_count = len(unique_genres)

    score += avg_lang_support + unique_genres_count

    logging.info(f"Expectation score for {company_name} is {score} based on {len(game_ids)} games")

    expectation_cache.add(company_name, score)

    sock.close()
    logging.info(f"Closed socket after loading {company_name}")

    return score
