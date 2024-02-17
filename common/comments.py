import time
from threading import Lock
import re
import socket
import pickle

from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import prawcore
from prawcore.exceptions import NotFound

from common.config import logging, IGDB_CACHE_PORT
from common.loader.reddit import RedditLoader
from common.cache import TimedCache
from common.utilities import send_msg, recv_msg

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
    logging.info(f"Evaluating modality for {company_name}")

    if modality_cache.exists(company_name):
        return modality_cache.get(company_name)

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

    games = company.list_games_name()

    sent = CommentsSentiment()
    score: float = 0
    score_count: int = 0
    for g in games:
        if len(g.name) == 0:
            continue
        logging.debug(f"Getting sentiment score for game: {g.name} from company {company_name}")
        try:
            if len(g.reddit) > 0 and g.reddit[-1] == '/':
                g.reddit = g.reddit[:-1]
            splitted = g.reddit.split("/")
            name = splitted[-1]
            if name == "":
                if g.release_date < time.time():  # if it is just announced game then skip it

                    for f in franchises:
                        if g.name.startswith(f):
                            name = f.lower()
                            name = re.sub("[\\s+]|'|-|\\!", "", name)
                            name = name.replace("&", "and")
                            if name == "likeadragon":
                                name = "yakuzagames"
                            break

                    if name == "":
                        logging.debug(f"Game: {g.name} has no reddit thread")
                        continue
                else:
                    logging.debug(f"Game {g.name} is not released. Not counting")
                    continue
            # TODO: make in parallel
            try:
                if g.rating_count != 0:
                    score += (g.rating / 100) / g.rating_count
                score += sent.sentiment(name)
            except prawcore.exceptions.Forbidden:
                logging.error(f"Exception evaluating comments for {name}: 403 Forbidden")
                score_count -= 1
            except prawcore.exceptions.TooManyRequests:
                logging.error("TooManyRequests error: waiting...")
                time.sleep(1)
                # score counts because there is user rating and critic ratings counted also
            score_count += 1
        except NotFound:
            logging.error(f"Not a game reddit thread: {g.name}")

    try:
        score /= score_count
    except Exception as e:
        logging.error(f"Got exception while evaluating modality for {company_name}: {e}")

    if score_count < 2:
        score = 0.05

    logging.info(f"Modality for company {company_name} is {score}. Calculation based on {score_count} games")

    modality_cache.add(company_name, score)

    return score


franchises = [
    "Mario",
    "Tetris",
    "Pokémon",
    "Call of Duty",
    "Grand Theft Auto",
    "FIFA",
    "Minecraft",
    "Lego",
    "The Sims",
    "Assassin's Creed",
    "Final Fantasy",
    "Sonic the Hedgehog",
    "The Legend of Zelda",
    "Need for Speed",
    "Resident Evil",
    "Madden NFL",
    "NBA 2K",
    "Star Wars",
    "Pro Evolution Soccer",
    "WWE 2K",
    "Tomb Raider",
    "Monster Hunter",
    "Gran Turismo",
    "Battlefield",
    "Dragon Quest",
    "Tom Clancy's",
    "Halo",
    "Red Dead",
    "Just Dance",
    "Mortal Kombat",
    "Borderlands",
    "Animal Crossing",
    "The Witcher",
    "Worms",
    "Super Smash Bros.",
    "Dragon Ball",
    "God of War",
    "Metal Gear",
    "The Elder Scrolls",
    "Civilization",
    "Tekken",
    "Street Fighter",
    "Far Cry",
    "Diablo",
    "Crash Bandicoot",
    "Destiny",
    "Pac-Man",
    "Uncharted",
    "Kirby",
    "Mega Man",
    "Spider-Man",
    "BioShock",
    "Guitar Hero",
    "Gears of War",
    "Medal of Honor",
    "Fallout",
    "Total War",
    "Kingdom Hearts",
    "Dark Souls",
    "NBA Live",
    "Batman",
    "Megami Tensei",
    "Football Manager",
    "Horizon",
    "Naruto",
    "Saints Row",
    "Gundam",
    "The Last of Us",
    "James Bond",
    "Tony Hawk's",
    "Command & Conquer",
    "Tales",
    "Devil May Cry",
    "Splatoon",
    "The Walking Dead",
    "Half-Life",
    "Ratchet & Clank",
    "Rayman",
    "Dying Light",
    "Age of Empires",
    "Yu-Gi-Oh!",
    "Like a Dragon",
    "Metroid",
    "Microsoft Flight Simulator",
    "Dynasty Warriors",
    "Prince of Persia",
    "Castlevania",
    "SpongeBob SquarePants",
    "Spyro",
    "Mass Effect",
    "SimCity",
    "Watch Dogs"
]
