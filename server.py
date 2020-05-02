"""

A simple Gemini server.

TODO: add TLS

"""
import socketserver
from typing import Optional

from pygemini.common import CRLF, MAX_META_SIZE

BUFFER_SIZE = 2048


class GeminiRequestHandler(socketserver.BaseRequestHandler):

    _docs = {
        "/foo": bytes("this is the foo doc", "utf-8"),
        "/bar": bytes("this is the bar doc", "utf-8"),
    }

    def handle(self):
        # Receive request
        gemini_request = self.request.recv(BUFFER_SIZE)
        url = self.request_to_url(gemini_request)

        if len(url) == 0:
            response = self.make_response(51)
            self.request.sendall(response)

        if url[-1] == "/":
            url = url[:-1]

        # Try to get doc for requested url
        doc = self.get_page(url)
        if doc is None:
            response = self.make_response(51)
            self.request.sendall(response)
        else:
            response = self.make_response(20, "text/gemini")
            self.request.sendall(response)
            self.request.sendall(doc)

    def request_to_url(self, request: bytes) -> Optional[str]:
        if request[-2:] != CRLF:
            # A valid request must end with <CR><LF>
            return None

        return request[:-2].decode("utf-8")

    def make_response(self, code: int, meta: str = "") -> bytes:
        if len(meta) > MAX_META_SIZE:
            raise ValueError(f"Response meta too long")

        ret = bytes(str(code) + " ", "utf-8")
        if meta is not None:
            ret += bytes(meta, "utf-8")
        ret += CRLF

        return ret

    def get_page(self, url: str) -> Optional[str]:
        return self._docs.get(url)


class GeminiServer:

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def server_forever(self):
        with socketserver.ThreadingTCPServer(
                (self.host, self.port), GeminiRequestHandler) as server:
            server.serve_forever()


if __name__ == "__main__":
    gs = GeminiServer("localhost", 1965)
    gs.server_forever()
