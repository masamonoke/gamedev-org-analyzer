from threading import Lock, Thread

def evaluate(companies_scores, eval_func, by_symbol):
    tasks = []
    lock = Lock()

    for score in companies_scores:
        name = None
        if by_symbol:
            name = score.company.symbol
        else:
            name = score.company.name

        tasks.append(Thread(target=_evaluate, args=(score, lock, eval_func, name)))


    for t in tasks:
        t.start()
    for t in tasks:
        t.join()

def _evaluate(score, lock, eval_func, name):
    s = eval_func(name, lock)
    lock.acquire()
    score.total_score += s
    lock.release()

