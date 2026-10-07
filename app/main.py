import socket  # noqa: F401


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    
    client_socket, address = server_socket.accept()
    
    client_socket.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    
    client_socket.close()

if __name__ == "__main__":
    main()
