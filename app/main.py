import argparse
import os
import socket  # noqa: F401
import threading

def handle_client(client_socket, directory):
    try:
        request_data = client_socket.recv(1024).decode("utf-8")
        if not request_data:
            return

        lines = request_data.split("\r\n")
        request_line = lines[0]
        path = request_line.split(" ")[1]

        headers = {}
        for line in lines[1:]:
            if not line:
                break
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

        # Handle routes
        if path == "/":
            client_socket.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        elif path.startswith("/echo/"):
            echo_str = path[len("/echo/"):]
            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/plain\r\n"
                f"Content-Length: {len(echo_str)}\r\n\r\n"
                f"{echo_str}"
            )
            client_socket.sendall(response.encode("utf-8"))
        elif path == "/user-agent":
            user_agent = headers.get("user-agent", "")
            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/plain\r\n"
                f"Content-Length: {len(user_agent)}\r\n\r\n"
                f"{user_agent}"
            )
            client_socket.sendall(response.encode("utf-8"))
        elif path.startswith("/files/"):
            filename = path[len("/files/"):]
            if directory:
                abs_dir = os.path.abspath(directory)
                filepath = os.path.join(abs_dir, filename)
        
                if os.path.isfile(filepath):
                    with open(filepath, "rb") as f:
                        content = f.read()
            
                    header = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: application/octet-stream\r\n"
                         f"Content-Length: {len(content)}\r\n\r\n"
                    )
                    client_socket.sendall(header.encode("utf-8") + content)
                    return

            client_socket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
        else:
            client_socket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
    finally:
        client_socket.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=str, default=None)
    args = parser.parse_args()
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    # Loop continuously to accept multiple incoming connections
    while True:
        client_socket, address = server_socket.accept()
        # Spawn a new thread for each connected client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, args.directory))
        client_thread.start()


if __name__ == "__main__":
    main()