import socket  # noqa: F401


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    client_socket, address = server_socket.accept()

    request_data = client_socket.recv(1024).decode("utf-8")
    request_line = request_data.split("\r\n")[0]
    path = request_line.split(" ")[1]
    
    if path == "/":
        client_socket.sendall(b"HTTP/1.1 200 OK\r\n\r\n")

    elif path.startswith("/echo/"):
        echo_str = path[len("/echo/"):]
        content_length = len(echo_str)
        
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {content_length}\r\n\r\n"
            f"{echo_str}"
        )
        client_socket.sendall(response.encode("utf-8"))
    
    else:
        client_socket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

    client_socket.close()

if __name__ == "__main__":
    main()
