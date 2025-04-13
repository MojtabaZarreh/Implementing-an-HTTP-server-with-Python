import socket
import sys
import logging
from pathlib import Path
from typing import Callable, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
import mimetypes

# Setup logging
logging.basicConfig(level=logging.INFO)

HOST = 'localhost'
PORT = 4221

class HTTPStatus:
    OK = 200
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405

    status_messages = {
        OK: "OK",
        NOT_FOUND: "Not Found",
        METHOD_NOT_ALLOWED: "Method Not Allowed",
    }

    @classmethod
    def get_message(cls, code: int) -> str:
        return cls.status_messages.get(code, "Unknown")


class Router:
    def __init__(self):
        self.routes: Dict[str, Callable[[], str]] = {}

    def add_route(self, path: str, handler: Callable[[], str]):
        self.routes[path] = handler

    def resolve(self, method: str, path: str, user_agent: str) -> Tuple[int, str, str]:
        if method != 'GET':
            return HTTPStatus.METHOD_NOT_ALLOWED, 'text/plain', "Method Not Allowed"

        if path in self.routes:
            return HTTPStatus.OK, 'text/plain', self.routes[path]()
        if path.startswith('/echo'):
            return self.handle_echo(path)
        if path.startswith('/user-agent'):
            return self.handle_user_agent(user_agent)
        if path.startswith('/files'):
            return self.handle_static_file(path)
        
        return HTTPStatus.NOT_FOUND, 'text/plain', "404 Not Found"

    def handle_echo(self, path: str) -> Tuple[int, str, str]:
        return HTTPStatus.OK, 'text/plain', path[len('/echo/'):]

    def handle_user_agent(self, user_agent: str) -> Tuple[int, str, str]:
        return HTTPStatus.OK, 'text/plain', user_agent

    def handle_static_file(self, path: str) -> Tuple[int, str, str]:
        if len(sys.argv) < 3:
            return HTTPStatus.NOT_FOUND, 'text/plain', "404 Not Found"

        directory = Path(sys.argv[2])
        filename = path[len('/files'):]
        file_path = directory / filename

        content = self.read_file(file_path)
        if content is None:
            return HTTPStatus.NOT_FOUND, 'text/plain', "404 Not Found"

        content_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
        return HTTPStatus.OK, content_type, content

    def read_file(self, file_path: Path) -> Optional[str]:
        try:
            if file_path.is_file():
                return file_path.read_text()
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
        return None


class HTTPServer:
    def __init__(self, host: str, port: int, router: Router):
        self.host = host
        self.port = port
        self.router = router

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(100)
            logging.info(f"Server running at http://{self.host}:{self.port}")

            with ThreadPoolExecutor(max_workers=20) as executor:
                while True:
                    client_conn, client_addr = server_socket.accept()
                    executor.submit(self.handle_client, client_conn, client_addr)

    def handle_client(self, conn: socket.socket, addr: Tuple[str, int]):
        try:
            with conn:
                data = conn.recv(1024).decode('utf-8')
                method, path, user_agent = self.parse_request(data)

                logging.info(f"[{addr}] {method} {path}")

                status_code, content_type, body = self.router.resolve(method, path, user_agent)
                response = self.build_response(body, content_type, status_code)
                conn.sendall(response.encode('utf-8'))
        except Exception as e:
            logging.error(f"[{addr}] Error: {e}")

    def parse_request(self, request_data: str) -> Tuple[str, str, str]:
        lines = request_data.splitlines()
        if not lines:
            return "", "", ""
        try:
            method, path, *_ = lines[0].split()
            user_agent = ""
            for line in lines:
                if line.lower().startswith("user-agent:"):
                    user_agent = line.split(":", 1)[1].strip()
                    break
            return method, path, user_agent
        except Exception as e:
            logging.warning(f"Malformed request: {e}")
            return "", "", ""

    def build_response(self, body: str, content_type: str, status_code: int) -> str:
        status_text = HTTPStatus.get_message(status_code)
        return (
            f"HTTP/1.1 {status_code} {status_text}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body.encode('utf-8'))}\r\n"
            "Connection: close\r\n"
            "\r\n"
            f"{body}"
        )


def main():
    router = Router()
    router.add_route("/", lambda: "Welcome to the Home Page!")
    router.add_route("/hello", lambda: "Hello there!")
    
    server = HTTPServer(HOST, PORT, router)
    server.start()


if __name__ == "__main__":
    main()