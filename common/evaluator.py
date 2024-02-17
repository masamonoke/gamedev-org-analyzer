from threading import Lock, Thread
from typing import Callable

from common.model.company import CompanyScore


def evaluate(companies_scores: list, eval_func: Callable[[str, Lock], float], by_symbol: bool):
    tasks = []
    lock = Lock()

    for score in companies_scores:
        if by_symbol:
            name = score.company.symbol
        else:
            name = score.company.name

        tasks.append(Thread(target=_evaluate, args=(score, lock, eval_func, name)))

    for t in tasks:
        t.start()
    for t in tasks:
        t.join()


def _evaluate(score: CompanyScore, lock: Lock, eval_func: Callable[[str, Lock], float], name: str):
    s = eval_func(name, lock)
    lock.acquire()
    score.score = s
    score.evaluator_name = eval_func.__name__
    lock.release()
