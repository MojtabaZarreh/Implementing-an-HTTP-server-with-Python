import socket
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, Dict, Callable
import sys

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
    
    def handle_files(self, file_path: str): 
        try:
            with open(file_path, "r") as f:
                body = f.read()
                return body
        except Exception as e:
            return False

    def resolve(self, method: str, path: str, user_agent: str) -> Tuple[int, str]:
        content_type = 'text/plain'
        if method != 'GET':
            return HTTPStatus.METHOD_NOT_ALLOWED, "Method Not Allowed"
        if path in self.routes:
            return HTTPStatus.OK, content_type, self.routes[path]()
        elif path.startswith('/echo'):
            return HTTPStatus.OK, content_type, path[6:]
        elif path.startswith('/user-agent'):
            return HTTPStatus.OK, content_type, user_agent
        elif path.startswith('/files'):
            directory = sys.argv[2]
            filename = path[7:]
            body = self.handle_files(f'/{directory}/{filename}')
            print(body)
            if body:
                return HTTPStatus.OK, 'application/octet-stream', body
            else :
                return HTTPStatus.METHOD_NOT_ALLOWED, content_type, "Method Not Allowed"  
        else:
            return HTTPStatus.NOT_FOUND, content_type, "404 Not Found"

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
            print(f"Server running at http://{self.host}:{self.port}")

            with ThreadPoolExecutor(max_workers=20) as executor:
                while True:
                    client_conn, client_addr = server_socket.accept()
                    executor.submit(self.handle_client, client_conn, client_addr)

    def handle_client(self, conn: socket.socket, addr: Tuple[str, int]):
        try:
            with conn:
                data = conn.recv(1024).decode('utf-8')
                method, path, user_agent = self.parse_request(data)

                print(f"[{addr}] {method} {path}")

                status_code, content_type, body = self.router.resolve(method, path, user_agent)
                response = self.build_response(body, content_type, status_code)
                conn.sendall(response.encode('utf-8'))

        except Exception as e:
            print(f"[{addr}] Error: {e}")

    def parse_request(self, request_data: str) -> Tuple[str, str]:
        lines = request_data.splitlines()
        print(lines)
        if not lines:
            return "", ""
        method, path, *_ = lines[0].split()
        user_agent = next(
            (line.split(":", 1)[1].strip() for line in lines if line.lower().startswith("user-agent:")),
            "")
        return method, path, user_agent

    def build_response(self, body: str, content_type: str, status_code: int = 200) -> str:
        status_text = HTTPStatus.get_message(status_code)
        return (
            f"HTTP/1.1 {status_code} {status_text}\r\n"
            "Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body)}\r\n"
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