from concurrent.futures import ThreadPoolExecutor
import pickle
from threading import Lock
import socket
from typing import List, Set
import sys

sys.path.append("../")
from common.utilities import send_msg, recv_msg
from common.loader.igdb import LoaderIGDB
from common.config import logging


class IGDBCacheService:
    def __init__(self, port: int = 12101, workers: int = 20) -> None:
        self.lock = Lock()
        self.port = port
        self.executors = ThreadPoolExecutor(max_workers=workers)
        self.workers = workers
        self.sockets: List[socket.socket] = []
        self.loader = LoaderIGDB()
        self.companies_loading_list: Set[str] = set()

    def run(self):

        logging.info("IGDB cache service is running")

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
            logging.info("Gracefully stopping IGDB cache service")
            for sock in self.sockets:
                sock.close()
            server_socket.close()
            logging.info("Killed all IGDB cache service sockets")

    def _socket_routine(self, conn: socket.socket, address: tuple):
        while True:

            packet = recv_msg(conn)

            if packet is None:
                logging.info(f"Connection reset: {str(address)}")
                break
            else:
                try:
                    company_name: str = packet.decode()
                    while company_name in self.companies_loading_list:
                        pass

                    self.lock.acquire()
                    self.companies_loading_list.add(company_name)
                    self.lock.release()
                    company = self.loader.get_company_by_name(company_name)
                    self.lock.acquire()
                    self.companies_loading_list.remove(company_name)
                    self.lock.release()
                    pickled_company = pickle.dumps(company)
                    send_msg(conn, pickled_company)
                    logging.info(f"Sent {company_name} data")
                except UnicodeDecodeError:
                    data = pickle.loads(packet)

                    if type(data) == tuple:
                        what = data[0]
                        ids = data[1]
                        if what == "genres":
                            logging.info("Getting genres data")
                            loaded_data = self.loader.get_genres_by_id(ids)
                        else:
                            logging.info("Getting languages data")
                            loaded_data = self.loader.get_languages_sup_by_id(ids)

                        pickled = pickle.dumps(loaded_data)
                        send_msg(conn, pickled)
                    else:
                        logging.error(f"Wrong data type passed: {type(data)}")

