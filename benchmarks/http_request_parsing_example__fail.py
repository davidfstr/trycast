from benchmarks.data.http_request_parsing_example import _ProxiedHttpRequestEnvelope
from trycast import trycast


def run() -> None:
    trycast(
        _ProxiedHttpRequestEnvelope,
        {
            "request": {
                "url": "https://example.com/api/posts",
                "method": "GET",
                "headers": {},
                "content": {
                    "type": {"value": "application/json"},
                    "text": '{"offset": 0, "limit": 20}',
                },
            }
        },
    )


if __name__ == "__main__":
    run()
