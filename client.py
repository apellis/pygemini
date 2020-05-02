"""

A simple Gemini client.

TODO: add TLS

"""
import socket

CRLF = b"\r\n"
BUFFER_SIZE = 2048


def _recv_all(sock):
    ret = bytes()
    while True:
        data = sock.recv(BUFFER_SIZE)
        if not data:
            break
        ret += data
    return ret


hostname = "localhost"

urls = [
    "foo",
    "baz",
    "bar",
]

for url in urls:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        # Connect and send request
        sock.connect((hostname, 1965))
        sock.send(bytes(url, "utf-8") + CRLF)

        # Did we get a success code?
        reply = _recv_all(sock)
        crlf_index = reply.find(CRLF)
        if crlf_index == -1:
            # No CRLF in the response
            print(f"received a response with no CRLF (invalid!)")
            continue
        header, body = reply[:crlf_index].decode("utf-8"), reply[crlf_index+len(CRLF):]
        code = int(header[:2])
        meta = header[2:].strip()
        print(f"response: code {code}, meta {meta}")

        # If a success code, get doc
        if code >= 20 and code <= 29:
            print(f"doc: {body}")

        print()
        sock.close()
