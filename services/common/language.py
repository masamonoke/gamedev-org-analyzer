from threading import Lock
import pickle

from common.config import logging
from common.loader.igdb import IGDBSocket

# TODO: add cache
def language_support(company_name: str, lock: Lock) -> float:
    logging.info(f"Evaluating language support score for {company_name}")

    sock = IGDBSocket()
    company = sock.company_data(company_name)
    if company is None:
        return 0

    logging.info(f"Evaluating coverage score for {company_name}")

    languages_sum = 0

    game_ids = set()
    for d in company.developed_games:
        game_ids.add(d.igdb_id)
    for p in company.published_games:
        game_ids.add(p.igdb_id)

    data = sock.request("lang", list(game_ids))
    if data is not None:
        lang_map = pickle.loads(data)
        for _, v in lang_map.items():
            languages_sum += len(v)

    titles_count = len(game_ids)
    avg_lang_support = languages_sum / titles_count if titles_count != 0 else 0

    score = avg_lang_support

    sock.close()
    logging.info(f"Language support for {company_name} is {score}")
    return score

