[![progress-banner](https://backend.codecrafters.io/progress/http-server/104c767b-01be-4645-8167-29d41f20a425)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

This is a starting point for Python solutions to the
["Build Your Own HTTP server" Challenge](https://app.codecrafters.io/courses/http-server/overview).

[HTTP](https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol) is the
protocol that powers the web. In this challenge, you'll build a HTTP/1.1 server
that is capable of serving multiple clients.

Along the way you'll learn about TCP servers,
[HTTP request syntax](https://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html),
and more.

**Note**: If you're viewing this repo on GitHub, head over to
[codecrafters.io](https://codecrafters.io) to try the challenge.

## About the Project

This project is a simple HTTP server implemented in pure Python using low-level socket programming. It was developed as part of a learning exercise to better understand how HTTP servers work under the hood, without relying on external frameworks like Flask or FastAPI.

The server supports basic `GET` and `POST` requests and provides a lightweight routing system. It includes support for dynamic endpoints such as `/echo/<message>` which returns the message back, `/user-agent` which returns the client's user agent, and `/files/<filename>` for serving and saving files.

A `Router` class is used to map paths to handler functions, and a `ThreadPoolExecutor` is used to allow handling multiple clients concurrently in a simple multi-threaded fashion.

Please note that this implementation is intended for **testing and educational purposes only**. For production-level or large-scale systems, **asynchronous (async) approaches** using libraries like `asyncio`, `aiohttp`, or ASGI-based servers such as `uvicorn` are recommended to ensure scalability and performance.
