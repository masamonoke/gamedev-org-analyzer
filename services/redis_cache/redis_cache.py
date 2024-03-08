import pickle
import socket
from typing import List
from concurrent.futures import ThreadPoolExecutor
import os

import redis

is_docker = os.environ.get('DOCKER_CONTAINER', False)

if not is_docker:
    import sys
    sys.path.append("../")
    from services.common.config import logging
    from services.common.utilities import send_msg, recv_msg
else:
    from common.config import logging
    from common.utilities import send_msg, recv_msg

class RedisCache():
    def __init__(self, port: int = 12100, workers: int = 20) -> None:
        if is_docker:
            host = "host.docker.internal"
        else:
            host = "127.0.0.1"
        self.redis_conn = redis.StrictRedis(host=host, port=6379)
        self.redis_conn.ping() # if there is no connection then this line will throw
        # WARNING: for debug purposes
        # self.redis_conn.flushall()
        self.port = port
        self.workers = workers
        self.executors = ThreadPoolExecutor(max_workers=workers)
        self.sockets: List[socket.socket] = []

    def run(self):

        logging.info("Redis cache service is running")

        host = socket.gethostname()

        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_socket.bind((host, self.port))

            server_socket.listen(self.workers)
            while True:
                conn, address = server_socket.accept()
                self.sockets.append(conn)
                logging.info(f"Connection from: {str(address)}")
                self.executors.submit(self._socket_routine, conn, address)
        except KeyboardInterrupt:
            logging.info("Gracefully stopping redis cache service")
            for sock in self.sockets:
                sock.close()
            server_socket.close()
            logging.info("Killed all redis cache service sockets")
            self.redis_conn.close()

    def _socket_routine(self, conn: socket.socket, address: tuple):
        while True:

            packet = recv_msg(conn)

            if packet is None:
                logging.error(f"Connection reset: {str(address)}")
                break
            else:
                try:
                    data = packet.decode()
                except UnicodeDecodeError:
                    # if not a string then it is bytes
                    data = pickle.loads(packet)
                if type(data) == str:
                    logging.info(f"Loading {data} cache from redis database")
                    bytes_data = cache.redis_conn.get(data)
                    if type(bytes_data) == bytes:
                        send_msg(conn, bytes_data)
                        logging.info(f"Loaded {data} cache from redis database")
                    else:
                        logging.info(f"{data} data is not presented in redis cache")
                        pickled_data = pickle.dumps(bytes_data)
                        send_msg(conn, pickled_data)
                else:
                    # tuple
                    val = pickle.dumps(data[1])
                    key = data[0]
                    logging.info(f"Saving {key} data to redis cache")
                    self.redis_conn.set(key, val)


if __name__ == '__main__':
    cache = RedisCache()
    cache.run()
