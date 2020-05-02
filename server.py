"""

A simple Gemini server.

TODO: add TLS

"""
import os
from pathlib import Path
import socketserver
from typing import Optional

from pygemini.common import CRLF, MAX_META_SIZE
from pygemini.status_code import StatusCode

BUFFER_SIZE = 2048


class GeminiRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        # Receive request
        gemini_request = self.request.recv(BUFFER_SIZE)
        url = self.request_to_url(gemini_request)

        # Try to get doc for requested url
        doc = self.get_page(url)
        if doc is None:
            response = self.make_response(StatusCode.NOT_FOUND)
            self.request.sendall(response)
        else:
            response = self.make_response(StatusCode.SUCCESS, "text/gemini")
            self.request.sendall(response)
            self.request.sendall(doc)

    def request_to_url(self, request: bytes) -> Optional[str]:
        if request[-2:] != CRLF:
            # A valid request must end with <CR><LF>
            return None

        return request[:-2].decode("utf-8")

    def make_response(self, code: StatusCode, meta: str = "") -> bytes:
        if len(meta) > MAX_META_SIZE:
            raise ValueError(f"Response meta too long")

        ret = bytes(str(code.value) + " ", "utf-8")
        if meta is not None:
            ret += bytes(meta, "utf-8")
        ret += CRLF

        return ret

    def get_page(self, url: str) -> Optional[str]:
        # Remove leading and trailing "/"'s
        while len(url) > 0 and url[0] == "/":
            url = url[1:]
        while len(url) > 0 and url[-1] == "/":
            url = url[:-1]

        if len(url) == 0:
            return None

        # Absolute path with symlinks, ..'s, and ~'s resolved
        path = Path(
            os.path.realpath(
                os.path.expanduser(
                    os.path.join(self.server.root_path, url))))

        # Only serve result if the requested path is nested below the root
        # (otherwise, this is probably an attempt to gain unauthorized access)
        if self.server.root_path in path.parents and path.exists():
            with open(path, "rb") as f:
                return f.read()
        else:
            return None


class GeminiServer:

    def __init__(self, host: str, port: int, root_path: str):
        self.host = host
        self.port = port

        # Absolute path with symlinks, ..'s, and ~'s resolved
        self.root_path = Path(os.path.realpath(os.path.expanduser(root_path)))

    def serve_forever(self):
        with socketserver.ThreadingTCPServer(
                (self.host, self.port), GeminiRequestHandler) as server:
            server.root_path = self.root_path
            server.serve_forever()


if __name__ == "__main__":
    gs = GeminiServer("localhost", 1965, "~/gemini_root")
    gs.serve_forever()
