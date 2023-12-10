import praw
from praw.models.reddit.comment import Comment
import prawcore

import logging
import sys
sys.path.append("../")
from config import config_get_key

logging.basicConfig(format='%(asctime)s, %(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO)

class RedditLoader:
    def __init__(self):
        self.reddit = self._auth();

    def _auth(self):
        logging.info("Auth to Reddit API")
        reddit = praw.Reddit(
            client_id=config_get_key("REDDIT_CLIENT_ID"),
            client_secret=config_get_key("REDDIT_SECRET"),
            password=config_get_key("REDDIT_PASS"),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            username=config_get_key("REDDIT_USERNAME")
        )
        if reddit.user.me() == None:
            logging.error("Auth to Reddit API failed")
            return None
        else:
            logging.info("Logged in to Reddit API")
        return reddit

    def comments(self, game: str,  post_limit: int = 5, comm_limit: int = 5):
        comments = []
        posts = self.reddit.subreddit(game).hot(limit=post_limit)
        try:
            for post in posts:
                submission = self.reddit.submission(id=post)
                for comm in submission.comments.list():
                    if isinstance(comm, Comment):
                        comments.append(comm.body)
        except prawcore.exceptions.Redirect as e:
            logging.error(f"Cannot load subreddit of {game}. Probably it is wrong game name.")

        return comments
