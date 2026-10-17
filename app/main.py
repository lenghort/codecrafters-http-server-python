import argparse
import gzip
import os
import socket
import threading

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
            should_close = (connection_header == "close")

            if path == "/":
                header_list = ["HTTP/1.1 200 OK"]
                if should_close:
                    header_list.append("Connection: close")
                response = ("\r\n".join(header_list) + "\r\n\r\n").encode("utf-8")

            elif path.startswith("/echo/"):
                echo_str = path[len("/echo/") :]
                accept_encoding = headers.get("accept-encoding", "")
                encodings = [e.strip() for e in accept_encoding.split(",")]
                
                if "gzip" in encodings:
                    compressed_body = gzip.compress(echo_str.encode("utf-8"))
                    header_list = [
                        "HTTP/1.1 200 OK",
                        "Content-Encoding: gzip",
                        "Content-Type: text/plain",
                        f"Content-Length: {len(compressed_body)}"
                    ]
                    if should_close:
                        header_list.append("Connection: close")
                    response = ("\r\n".join(header_list) + "\r\n\r\n").encode("utf-8") + compressed_body
                else:
                    body_bytes = echo_str.encode("utf-8")
                    header_list = [
                        "HTTP/1.1 200 OK",
                        "Content-Type: text/plain",
                        f"Content-Length: {len(body_bytes)}"
                    ]
                    if should_close:
                        header_list.append("Connection: close")
                    response = ("\r\n".join(header_list) + "\r\n\r\n").encode("utf-8") + body_bytes

            elif path == "/user-agent":
                user_agent = headers.get("user-agent", "")
                body_bytes = user_agent.encode("utf-8")
                header_list = [
                    "HTTP/1.1 200 OK",
                    "Content-Type: text/plain",
                    f"Content-Length: {len(body_bytes)}"
                ]
                if should_close:
                    header_list.append("Connection: close")
                response = ("\r\n".join(header_list) + "\r\n\r\n").encode("utf-8") + body_bytes

            elif path.startswith("/files/"):
                filename = path[len("/files/") :]
                if not directory:
                    header_list = ["HTTP/1.1 404 Not Found"]
                    if should_close:
                        header_list.append("Connection: close")
                    response = ("\r\n".join(header_list) + "\r\n\r\n").encode("utf-8")
                else:
                    abs_dir = os.path.abspath(directory)
                    os.makedirs(abs_dir, exist_ok=True)
                    filepath = os.path.join(abs_dir, filename)

                    if method == "GET":
                        if os.path.isfile(filepath):
                            with open(filepath, "rb") as f:
                                content = f.read()
                            header_list = [
                                "HTTP/1.1 200 OK",
                                "Content-Type: application/octet-stream",
                                f"Content-Length: {len(content)}"
                            ]
                            if should_close:
                                header_list.append("Connection: close")
                            response = ("\r\n".join(header_list) + "\r\n\r\n").encode("utf-8") + content
                        else:
                            header_list = ["HTTP/1.1 404 Not Found"]
                            if should_close:
                                header_list.append("Connection: close")
                            response = ("\r\n".join(header_list) + "\r\n\r\n").encode("utf-8")
                    elif method == "POST":
                        content_length = int(headers.get("content-length", 0))
                        body = parts[1] if len(parts) > 1 else b""
                        while len(body) < content_length:
                            remaining = content_length - len(body)
                            body += client_socket.recv(remaining)
                        with open(filepath, "wb") as f:
                            f.write(body[:content_length])
                        
                        header_list = ["HTTP/1.1 201 Created"]
                        if should_close:
                            header_list.append("Connection: close")
                        response = ("\r\n".join(header_list) + "\r\n\r\n").encode("utf-8")
                    else:
                        header_list = ["HTTP/1.1 404 Not Found"]
                        if should_close:
                            header_list.append("Connection: close")
                        response = ("\r\n".join(header_list) + "\r\n\r\n").encode("utf-8")
            else:
                header_list = ["HTTP/1.1 404 Not Found"]
                if should_close:
                    header_list.append("Connection: close")
                response = ("\r\n".join(header_list) + "\r\n\r\n").encode("utf-8")

            client_socket.sendall(response)

            if should_close:
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