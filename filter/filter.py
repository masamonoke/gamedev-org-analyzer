from threading import Lock, Thread

def evaluate(companies_scores, eval_func):
    tasks = []
    lock = Lock()

    for score in companies_scores:
        tasks.append(Thread(target=_evaluate, args=(score, lock, eval_func,)))
    for t in tasks:
        t.start()
    for t in tasks:
        t.join()

def _evaluate(score, lock, eval_func):
    s = eval_func(score.company.symbol, lock)
    lock.acquire()
    score.total_score += s
    lock.release()

