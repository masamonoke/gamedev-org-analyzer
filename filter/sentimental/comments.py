import logging
import sys
from threading import Lock

from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from prawcore.exceptions import NotFound

sys.path.append("../")
from loader.reddit import RedditLoader
from loader.igdb import LoaderIGDB

logging.basicConfig(format='%(asctime)s, %(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO
                    )


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

    def _prepareData(self, game: str):
        self.comments = self.loader.comments(game)

    def sentiment(self, game: str):
        self._prepareData(game)
        total_pos = 0
        total_neg = 0

        for comment in self.comments:
            sn = self.sentiment_method.polarity_scores(comment)
            if sn["neg"] > sn["pos"]:
                total_neg += 1
            else:
                total_pos += 1

        s = total_neg + total_pos
        logging.info(f"total negative: {total_neg}, total positive: {total_pos}")
        # TODO: division by zero
        score = -(total_neg / s) + (total_pos / s)
        return score

    def to_reddit_name(self, game: str):
        game = game.strip().replace(" ", "")
        return game


def evaluate_comments(company_name: str, lock: Lock) -> float:
    igdb = LoaderIGDB()
    company = igdb.getCompanyByName(company_name)
    if company == None:
        return 0
    games = company.listGamesName()[:5]
    sent = CommentsSentiment()
    score = 0
    score_count = 0
    for g in games:
        logging.info(f"Getting sentiment score for game: {g}")
        try:
            # TODO: g.name transform to reddit thread name
            name = sent.to_reddit_name(g.name)
            score += sent.sentiment(name)
            score_count += 1
        except NotFound:
            logging.error(f"Not a game thread: {g.name}")
    score /= score_count
    return score


if __name__ == "__main__":
    sent = CommentsSentiment()
    # score = sent.sentiment("Starfield")
    # print(score)
    print(sent.to_reddit_name("Psychonauts 2"))
