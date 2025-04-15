import socket
import sys
from typing import Callable, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor


class HTTPStatus:
    OK = 200
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CREATED = 201

    messages = {
        OK: 'OK',
        NOT_FOUND: 'Not Found',
        METHOD_NOT_ALLOWED: 'Method Not Allowed',
        CREATED: 'Created'
    }

    @staticmethod
    def get_message(code):
        return HTTPStatus.messages.get(code, '')



class Router:
    def __init__(self):
        self.routes: dict[str, Callable[[], str]] = {}

    def add_route(self, path: str, handler: Callable[[], str]):
        self.routes[path] = handler

    def resolve(self, method: str, path: str, user_agent: str, body: str = '') -> tuple[int, str, str]:
        if method not in ('GET', 'POST'):
            return HTTPStatus.METHOD_NOT_ALLOWED, 'text/plain', 'Method Not Allowed'

        if path in self.routes:
            return HTTPStatus.OK, 'text/plain', self.routes[path]()

        if path.startswith('/echo/'):
            return HTTPStatus.OK, 'text/plain', path[len('/echo/'):]

        if path.startswith('/user-agent'):
            return HTTPStatus.OK, 'text/plain', user_agent

        if path.startswith('/files/'):
            return self._serve_file(path, method, body)

        return HTTPStatus.NOT_FOUND, 'text/plain', '404 Not Found'

    def _serve_file(self, path: str, method: str, body: str) -> tuple[int, str, str]:
        if len(sys.argv) < 3:
            return HTTPStatus.NOT_FOUND, 'text/plain', '404 Not Found'

        directory = sys.argv[2]
        filename = path[len('/files/'):]

        if method == 'GET':
            file_path = f'{directory}/{filename}'
            content = self._read_file(file_path)
            if content is None:
                return HTTPStatus.NOT_FOUND, 'text/plain', '404 Not Found'
            return HTTPStatus.OK, 'application/octet-stream', content

        elif method == 'POST':
            file_path = f'{directory}/{filename}'
            success = self._create_file(file_path, body)
            if success:
                return HTTPStatus.CREATED, 'application/octet-stream', ''
            else:
                return HTTPStatus.NOT_FOUND, 'text/plain', 'Failed to create file'

        return HTTPStatus.METHOD_NOT_ALLOWED, 'text/plain', 'Method Not Allowed'

    def _create_file(self, file_path: str, content: str) -> bool:
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False

    def _read_file(self, file_path: str) -> str | None:
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception:
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
            print(f'Server running at http://{self.host}:{self.port}')

            with ThreadPoolExecutor(max_workers=10) as executor:
                while True:
                    conn, addr = server_socket.accept()
                    executor.submit(self._handle_client, conn, addr)

    def _handle_client(self, conn: socket.socket, addr: tuple):
        try:
            with conn:
                request_data = conn.recv(1024).decode('utf-8')
                method, path, user_agent, body = self._parse_request(request_data)
                print(f'[{addr}] {method} {path}')

                status, content_type, response_body = self.router.resolve(method, path, user_agent, body)
                response = self._build_response(status, content_type, response_body)
                conn.sendall(response.encode('utf-8'))
        except Exception as e:
            print(f'[{addr}] Error: {e}')

    def _parse_request(self, request: str) -> tuple[str, str, str, str]:
        lines = request.splitlines()
        if not lines:
            return '', '', '', ''

        method, path, *_ = lines[0].split()
        user_agent = ''
        body = ''
        content_length = 0

        for line in lines:
            if line.lower().startswith('user-agent:'):
                user_agent = line.split(':', 1)[1].strip()
            elif line.lower().startswith('content-length:'):
                content_length = int(line.split(':', 1)[1].strip())

        if content_length > 0:
            body = request[-content_length:]  

        return method, path, user_agent, body

    def _build_response(self, status: int, content_type: str, body: str) -> str:
        status_text = HTTPStatus.get_message(status)
        return (
            f'HTTP/1.1 {status} {status_text}\r\n'
            f'Content-Type: {content_type}\r\n'
            f'Content-Length: {len(body.encode("utf-8"))}\r\n'
            'Connection: close\r\n'
            '\r\n'
            f'{body}'
        )


def main():
    router = Router()
    router.add_route('/', lambda: 'Welcome to the home page!')
    router.add_route('/hello', lambda: 'Hello, world!')

    server = HTTPServer('localhost', 4221, router)
    server.start()


if __name__ == '__main__':
    main()