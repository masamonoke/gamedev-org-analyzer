import sys
from threading import Lock

from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import prawcore
from prawcore.exceptions import NotFound


sys.path.append("../")
from config import logging
from loader.reddit import RedditLoader
from loader.igdb import LoaderIGDB
from cache import TimedCache

modality_cache = TimedCache()

class CommentsSentiment:
    def __init__(self, source: str = "reddit"):
        if source == "reddit":
            self.loader = RedditLoader()
        try:
            self.sentiment_method = SentimentIntensityAnalyzer()
        except LookupError:
            logging.error(f"vader_lexicon not found. Downloading...")
            nltk.download('vader_lexicon')
            self.sentiment_method = SentimentIntensityAnalyzer()

    def _prepare_data(self, game: str):
        self.comments = self.loader.comments(game)

    def sentiment(self, game: str):
        self._prepare_data(game)
        total_pos = 0
        total_neg = 0

        for comment in self.comments:
            sn = self.sentiment_method.polarity_scores(comment)
            if sn["neg"] > sn["pos"]:
                total_neg += 1
            else:
                total_pos += 1

        s = total_neg + total_pos
        logging.debug(f"total negative: {total_neg}, total positive: {total_pos}")
        try:
            score = -(total_neg / s) + (total_pos / s)
        except ZeroDivisionError:
            logging.error(f"Zero division happend with game {game}")
            score = 0
        return score

def modality(company_name: str, lock: Lock) -> float:

    if modality_cache.exists(company_name):
        return modality_cache.get(company_name)

    igdb = LoaderIGDB(lock)
    company = igdb.get_company_by_name(company_name)
    if company == None:
        return 0

    games = company.listGamesName()[:5]
    sent = CommentsSentiment()
    score = 0
    score_count = 0
    for g in games:
        if len(g.name) == 0:
            continue
        logging.debug(f"Getting sentiment score for game: {g.name} from company {company_name}")
        try:
            if len(g.reddit) > 0 and g.reddit[-1] == '/':
                g.reddit = g.reddit[:-1]
            splitted = g.reddit.split("/")
            name = splitted[-1]
            # TODO: make in parallel
            try:
                score += sent.sentiment(name)
            except prawcore.exceptions.Forbidden as e:
                logging.error(f"Exception evaluating comments for {name}: 403 Forbidden")
                score_count -= 1
            score_count += 1
        except NotFound:
            logging.error(f"Not a game reddit thread: {g.name}")
    try:
        score /= score_count
    except Exception as e:
        logging.error(f"Got exception while evaluating modality for {company_name}: {e}")

    logging.info(f"Modality for company {company_name} is {score}")

    modality_cache.add(company_name, score)

    return score

