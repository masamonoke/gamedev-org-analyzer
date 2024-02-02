import praw
from praw.models.reddit.comment import Comment
import prawcore

import sys

sys.path.append("../")
from config import config_get_key, logging


class RedditLoader:
    def __init__(self):
        self.reddit = self._auth();

    def _auth(self) -> praw.Reddit:
        logging.debug("Auth to Reddit API")
        reddit = praw.Reddit(
            client_id=config_get_key("REDDIT_CLIENT_ID"),
            client_secret=config_get_key("REDDIT_SECRET"),
            password=config_get_key("REDDIT_PASS"),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            username=config_get_key("REDDIT_USERNAME")
        )
        if reddit.user.me() == None:
            logging.error("Auth to Reddit API failed")
            raise ValueError

        return reddit

    def comments(self, game: str, post_limit: int = 5):
        if len(game) == 0:
            return []
        comments = []
        try:
            posts = self.reddit.subreddit(game).hot(limit=post_limit)
            for post in posts:
                submission = self.reddit.submission(id=post)
                for comm in submission.comments.list():
                    if isinstance(comm, Comment):
                        comments.append(comm.body)
        except prawcore.exceptions.Redirect:
            logging.error(f"Cannot load subreddit of {game}. Probably it is wrong game name.")
        except ValueError:
            logging.error(f"Failed to load subreddit for name {game}")

        return comments
