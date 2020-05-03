# pygemini

This is a hobby project. Please have no expectations! The goal is to write a "good enough" implementation (client and server) of the [Gemini protocol](https://gemini.circumlunar.space/).

## TODO

Here are some TODO items, very roughly in descending order of importance.

* Python niceties: consistent docstrings, pass mypy tests, automatic linting, etc.
* Make the client render `text/gemini` responses nicely instead of dumping the raw text.
* Add TLS to client and server, including client certificates.
	* There's a lot to do here (e.g. handling of transient client certificates).
* Add rate limiting to the server. Add automatic retry with backoff to the client when it receives a 44 (slow down) response. Maybe also a few retries for other 4x codes.
* Add unit tests.
* Add support for proxies.
* Add support for redirects.
* Figure out a way to catch all exceptions and return either 40 (temporary failure) or 42 (CGI error) in these cases. It's not clear how to do this while using `socketserver.TCPServer`.
	* Using the server class's `handle_error` doesn't work, since by the time that's called, the socket is already closed (see the source: <https://github.com/python/cpython/blob/master/Lib/socketserver.py>).
	* Adding a try-catch block around the handler seems to mess with assumptions in the server or handler in a way I don't yet understand. Even using `TCPServer` instead of `ThreadingTCPServer`, this always leads to either "Connection reset by peer" or an empty-bytestring response.
* Handle MIME types other than `text/plain` and `text/gemini`. The server should detect these from filenames, and the client should take appropriate actions.
* Don't always assume `text/plain` and `text/gemini` use UTF-8.
* Add integration tests.
* Server should refuse to serve very large files and send a useful error message to the client.
* Client should limit the number of consecutive redirects to avoid an infinite loop (say max of 5).
* Add support for `gopher://` URLs (user must explicitly agree because gopher has no TLS).