from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from pathlib import Path
import mimetypes
import logging
from threading import Thread
import socket
import datetime
import json


BASE_DIR = Path()
HTTP_PORT = 3000
HTTP_HOST = 'localhost'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000
BUFFER_SIZE = 1024
logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        if route.path == '/':
            self.send_html_file('index.html')
        elif route.path == '/message':
            self.send_html_file('message.html')
        else:
            file = BASE_DIR.joinpath(route.path[1:])
            if file.exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    try:
        parse_dict = {key: value for key, value in [
            el.split('=') for el in parse_data.split('&')]}
        log_time = str(datetime.datetime.now())
        parse_dict = {log_time: parse_dict}

        try:
            with open(r'.\storage\data.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
                data.update(parse_dict)
        except:
            data = {}
            data.update(parse_dict)

        with open(r'.\storage\data.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)


def run_http_server(host, port):
    server_address = (host, port)
    http = HTTPServer(server_address, HttpHandler)
    logging.info("Starting http server")
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http.server_close()


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {msg}")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()


if __name__ == '__main__':

    # run_http_server()
    logging.basicConfig(level=logging.DEBUG,
                        format='%(threadName)s %(message)s')
    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server,
                           args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()
    server.join()
    server_socket.join()
    logging.info("End http server")
