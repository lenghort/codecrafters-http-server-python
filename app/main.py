import argparse
import os
import socket  # noqa: F401
import threading
import gzip

def handle_client(client_socket, directory):
    try:
        while True:
            request_data = client_socket.recv(4096)
            if not request_data:
                break

            parts = request_data.split(b"\r\n\r\n", 1)
            header_part = parts[0].decode("utf-8", errors="ignore")
            
            lines = header_part.split("\r\n")
            if not lines or not lines[0]:
                break

            request_line = lines[0]
            req_parts = request_line.split(" ")
            if len(req_parts) < 2:
                break
                
            method = req_parts[0]
            path = req_parts[1]

            headers = {}
            for line in lines[1:]:
                if not line:
                    break
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()

            connection_header = headers.get("connection", "").lower()

            # Handle routes
            if path == "/":
                response = b"HTTP/1.1 200 OK\r\n\r\n"
            elif path.startswith("/echo/"):
                echo_str = path[len("/echo/") :]
                accept_encoding = headers.get("accept-encoding", "")
                encodings = [e.strip() for e in accept_encoding.split(",")]
                
                if "gzip" in encodings:
                    compressed_body = gzip.compress(echo_str.encode("utf-8"))
                    header_str = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Encoding: gzip\r\n"
                        "Content-Type: text/plain\r\n"
                        f"Content-Length: {len(compressed_body)}\r\n\r\n"
                    )
                    response = header_str.encode("utf-8") + compressed_body
                else:
                    response = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: text/plain\r\n"
                        f"Content-Length: {len(echo_str)}\r\n\r\n"
                        f"{echo_str}"
                    ).encode("utf-8")
            elif path == "/user-agent":
                user_agent = headers.get("user-agent", "")
                response = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: text/plain\r\n"
                    f"Content-Length: {len(user_agent)}\r\n\r\n"
                    f"{user_agent}"
                ).encode("utf-8")
            elif path.startswith("/files/"):
                filename = path[len("/files/") :]
                if not directory:
                    response = b"HTTP/1.1 404 Not Found\r\n\r\n"
                else:
                    abs_dir = os.path.abspath(directory)
                    os.makedirs(abs_dir, exist_ok=True)
                    filepath = os.path.join(abs_dir, filename)

                    if method == "GET":
                        if os.path.isfile(filepath):
                            with open(filepath, "rb") as f:
                                content = f.read()
                            header = (
                                f"HTTP/1.1 200 OK\r\n"
                                f"Content-Type: application/octet-stream\r\n"
                                f"Content-Length: {len(content)}\r\n\r\n"
                            )
                            response = header.encode("utf-8") + content
                        else:
                            response = b"HTTP/1.1 404 Not Found\r\n\r\n"
                    elif method == "POST":
                        content_length = int(headers.get("content-length", 0))
                        body = parts[1] if len(parts) > 1 else b""
                        while len(body) < content_length:
                            remaining = content_length - len(body)
                            body += client_socket.recv(remaining)
                        with open(filepath, "wb") as f:
                            f.write(body[:content_length])
                        response = b"HTTP/1.1 201 Created\r\n\r\n"
                    else:
                        response = b"HTTP/1.1 404 Not Found\r\n\r\n"
            else:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"

            client_socket.sendall(response)

            if connection_header == "close":
                break
    finally:
        client_socket.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=str, default=None)
    args = parser.parse_args()
    
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        client_socket, address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, args.directory))
        client_thread.start()


if __name__ == "__main__":
    main()