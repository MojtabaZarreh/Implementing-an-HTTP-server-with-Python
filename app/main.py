import socket
import threading
from typing import Tuple

HOST = 'localhost'
PORT = 4221

ROUTES = {
    '/': "Welcome to the Home Page!",
    '/hello': "Hello there!",
}

def build_response(body: str, status_code: int = 200) -> str:
    status_text = {
        200: "OK",
        404: "Not Found"
    }.get(status_code, "OK")
    
    return (
        f"HTTP/1.1 {status_code} {status_text}\r\n"
        "Content-Type: text/plain\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
        f"{body}"
    )

def parse_request(request_data: str) -> Tuple[str, str]:
    lines = request_data.splitlines()
    if not lines:
        return "", ""
    method, path, *_ = lines[0].split()
    return method, path

def handle_client(client_connection: socket.socket, client_address: Tuple[str, int]):
    with client_connection:
        try:
            request_data = client_connection.recv(1024).decode('utf-8')
            method, path = parse_request(request_data)

            print(f"[{client_address}] {method} {path}")

            if method != 'GET':
                body = "Method Not Allowed"
                response = build_response(body, status_code=405)
            elif path in ROUTES:
                body = ROUTES[path]
                response = build_response(body)
            else:
                response = build_response("404 Not Found", status_code=404)

            client_connection.sendall(response.encode('utf-8'))
        except Exception as e:
            print(f"[{client_address}] Error:", e)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(10)
        print(f"Server running at http://{HOST}:{PORT}")

        while True:
            client_conn, client_addr = server_socket.accept()
            threading.Thread(
                target=handle_client,
                args=(client_conn, client_addr),
                daemon=True
            ).start()

if __name__ == "__main__":
    main()