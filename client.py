"""

A simple Gemini client.

TODO: add TLS

"""
from collections import namedtuple
import socket
from urllib.parse import urlparse

from pygemini.common import CRLF, DEFAULT_PORT, MAX_META_SIZE, recv_until_closed
from pygemini.exceptions import InvalidResponseFromServer, UnsupportedMimeType
from pygemini.status_code import is_input, is_success, StatusCode

BUFFER_SIZE = 2048


GeminiResponse = namedtuple("GeminiResponse", ["code", "meta", "body"])


class GeminiClient:
    def get(self, url: str) -> GeminiResponse:
        url_obj = urlparse(url)

        if url_obj.scheme != "gemini":
            raise ValueError(f"Unsupported URL scheme: {url_obj.scheme}")

        if (colon_index := url_obj.netloc.find(":")) == -1:
            host = url_obj.netloc
            port = DEFAULT_PORT
        else:
            host = url_obj.netloc[:colon_index]
            port = int(url_obj.netloc[colon_index + 1 :])

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
            # Connect and send request
            sock.connect((host, port))
            message = url_obj.path
            if url_obj.query is not None and len(url_obj.query) > 0:
                message += "?" + url_obj.query
            sock.send(bytes(message, "utf-8") + CRLF)

            # Did we get a success code?
            reply = recv_until_closed(sock)
            crlf_index = reply.find(CRLF)
            if crlf_index == -1:
                # No CRLF in the response
                raise InvalidResponseFromServer()
            header, body = (
                reply[:crlf_index].decode("utf-8"),
                reply[crlf_index + len(CRLF) :],
            )
            code = int(header[:2])
            meta = header[2:].strip()

            # If code isn't two-digit or if meta has length exceeding 1024, ignore
            # the response and report and error to the user
            if code < 10 or code > 99 or len(meta) > MAX_META_SIZE:
                raise InvalidResponseFromServer()

            # If a success code, get doc
            body_str = None
            if is_success(code):
                if meta in ["text/gemini", "text/plain"]:
                    body_str = body.decode("utf-8")
                else:
                    raise UnsupportedMimeType(meta)

            sock.close()

            return GeminiResponse(code=code, meta=meta, body=body_str)


if __name__ == "__main__":
    import argparse
    import colorama

    colorama.init()

    BRIGHT_GREEN = colorama.Style.BRIGHT + colorama.Fore.GREEN
    BRIGHT_RED = colorama.Style.BRIGHT + colorama.Fore.RED
    BRIGHT_WHITE = colorama.Style.BRIGHT + colorama.Fore.WHITE
    RESET_OUT = colorama.Style.RESET_ALL

    def _print_response_header(response: GeminiResponse):
        code_name = StatusCode(response.code).name.replace("_", " ")
        if is_success(response.code) or is_input(response.code):
            code_color = BRIGHT_GREEN
        else:
            code_color = BRIGHT_RED
        print(
            f"{BRIGHT_WHITE}Response header: "
            f"{code_color}{str(response.code)} ({code_name}) "
            f"{response.meta}{RESET_OUT}"
        )

    def _print_response_body(response: GeminiResponse):
        print(f"{BRIGHT_WHITE}Response body:{RESET_OUT}")
        print(response.body)

    def _prompt_for_input(prompt: str):
        return input(BRIGHT_WHITE + prompt + RESET_OUT + " ")

    parser = argparse.ArgumentParser(description="Gemini protocol client")
    parser.add_argument("url", type=str, nargs=1, help="URL to fetch")
    args = parser.parse_args()
    url = args.url[0]

    client = GeminiClient()

    response = client.get(url)
    while is_input(response.code):
        # The server requested input from the client; prompt the user for input
        # and re-request
        _print_response_header(response)
        input_str = _prompt_for_input(response.meta)
        response = client.get(url + "?" + input_str)

    _print_response_header(response)
    if response.body is not None:
        _print_response_body(response)
