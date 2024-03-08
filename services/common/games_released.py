from threading import Lock

from common.config import logging
from common.loader.igdb import IGDBSocket

# TODO: add cache
def games_released_count(company_name: str, lock: Lock) -> float:
    logging.info(f"Evaluating game release count score for {company_name}")

    sock = IGDBSocket()
    company = sock.company_data(company_name)
    if company is None:
        return 0

    games = set()
    for g in company.developed_games:
        games.add(g.name)
    for g in company.published_games:
        games.add(g.name)

    score = len(games)

    logging.info(f"Game release count score for {company_name} is {score}")
    return float(score)
