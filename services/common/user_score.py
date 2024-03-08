from threading import Lock
import pickle

from common.config import logging
from common.utilities import send_msg, recv_msg
from common.model.igdb import Company
from common.loader.igdb import IGDBSocket

def user_score(company_name: str, lock: Lock) -> float:
    logging.info(f"Evaluating critic score for {company_name}")

    igdb_socket = IGDBSocket()
    sock = igdb_socket.sock

    send_msg(sock, company_name.encode())
    company_bytes = recv_msg(sock)
    logging.info(f"Recevied {company_name} data from IGDB cache service")

    if company_bytes is None:
        return 0
    company: Company = pickle.loads(company_bytes)
    if company is None:
        return 0

    games = company.list_games_name()
    score = 0
    score_num = 0
    for g in games:
        if g.user_rating != 0:
            score += g.user_rating
            score_num += 1

    score = score / score_num

    sock.close()
    logging.info(f"Critic score for {company_name} is {score}. Based on {score_num} ratings")

    return score
