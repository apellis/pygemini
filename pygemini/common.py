"""Common functions and constants for Gemini."""
import socket

CRLF = b"\r\n"
DEFAULT_PORT = 1965  # from specification
MAX_META_SIZE = 1024  # required by specification
BUFFER_SIZE = 2048


def recv_until_closed(sock: socket.socket) -> bytes:
    """Returns bytes received from socket until sock is closed."""
    ret = bytes()

    while True:
        data = sock.recv(BUFFER_SIZE)
        if not data:
            break
        ret += data

    return ret
