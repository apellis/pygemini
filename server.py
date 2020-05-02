"""

A simple Gemini server.

TODO: add TLS

"""
import os
from pathlib import Path
import socketserver
from typing import Callable, Dict, Optional

from pygemini.common import CRLF, MAX_META_SIZE
from pygemini.status_code import StatusCode

BUFFER_SIZE = 2048


class GeminiRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        # Receive request
        gemini_request = self.request.recv(BUFFER_SIZE)

        resource_name = self.request_to_url(gemini_request)

        # Remove leading "/"'s
        while len(resource_name) > 0 and resource_name[0] == "/":
            resource_name = resource_name[1:]

        # If the resource has a query, separate that
        query = None
        if (qmark_index := resource_name.find("?")) != -1:
            query = resource_name[qmark_index + 1:]
            resource_name = resource_name[:qmark_index]

        # First look for static routes
        if (doc := self.get_page(resource_name)) is not None:
            response = self.make_response(StatusCode.SUCCESS, "text/gemini")
            self.request.sendall(response)
            self.request.sendall(doc)
            return

        # Next look for interactive routes
        if (route_handler := self.server.interactive_routes.get(resource_name)) is not None:
            if query is None:
                prompt = route_handler(None)
                response = self.make_response(StatusCode.INPUT, prompt)
                self.request.sendall(response)
            else:
                response = self.make_response(StatusCode.SUCCESS, "text/gemini")
                self.request.sendall(response)
                self.request.sendall(bytes(route_handler(query), "utf-8"))
            return

        # Route was not found
        response = self.make_response(StatusCode.NOT_FOUND)
        self.request.sendall(response)

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

    def __init__(self, host: str, port: int, root_path: str,
                 interactive_routes: Dict[str, Callable[[Optional[str]], str]] = {}):
        self.host = host
        self.port = port

        # Absolute path with symlinks, ..'s, and ~'s resolved
        self.root_path = Path(os.path.realpath(os.path.expanduser(root_path)))

        # A mapping from route_name -> handler. If no query parameter is provided,
        # the handler is called with argument None. Otherwise, the full query
        # string is send as an argument to the handler.
        self.interactive_routes = interactive_routes

    def serve_forever(self):
        with socketserver.ThreadingTCPServer(
                (self.host, self.port), GeminiRequestHandler) as server:
            server.root_path = self.root_path
            server.interactive_routes = self.interactive_routes
            server.serve_forever()


if __name__ == "__main__":
    def greeter(whom: Optional[str]) -> str:
        if whom is None:
            return "Whom shall I greet?"
        else:
            return f"Howdy, {whom}!"

    def reverser(s: Optional[str]) -> str:
        if s is None:
            return "What shall I reverse?"
        else:
            return "".join(reversed(s))

    interactive_routes = {
        "greet": greeter,
        "reverse": reverser,
    }
    gs = GeminiServer("localhost", 1965, "~/gemini_root", interactive_routes)
    gs.serve_forever()
