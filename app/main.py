import socket  # noqa: F401


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    client_socket, address = server_socket.accept()

    request_data = client_socket.recv(1024).decode("utf-8")
    request_line = request_data.split("\r\n")[0]
    path = request_line.split(" ")[1]
    
    if path == "/":
        client_socket.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    
    else:
        client_socket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
        
    client_socket.close()

if __name__ == "__main__":
    main()
