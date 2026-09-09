"""プロセス内の偽 vLLM(OpenAI 互換の最小面・**非ストリーミングのみ**)。

C6-b は「艦隊ランの診断行が L6(64 in-flight/GPU)を破らないこと」を見たいだけなので、
SSE・注入つまみ・再試行の検査は ``tests/llm/test_fleet.py``(サブ O)に任せ、ここは
**同時実行数を実測できる最小のサーバー**に絞る。実サーバーへは接続しない。
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

GOOD = "理由: 予定の時間になったから\n行動: 移動 対象: なし ひと言: なし"


class FakeVLLM:
    """``/v1/models`` と ``/v1/chat/completions``(JSON)だけを返す偽サーバー。

    Attributes:
        peak_concurrency: 同時に処理していた要求数の最大(艦隊の in-flight の実測値)。
    """

    def __init__(self, model: str = "fake-qwen3-8b-int8", delay_s: float = 0.01) -> None:
        self.model = model
        self.delay_s = float(delay_s)
        self.text = GOOD
        self.lock = threading.Lock()
        self.n_requests = 0
        self.in_flight = 0
        self.peak_concurrency = 0
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(self))
        self.server.daemon_threads = True
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

    @property
    def endpoint(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self._thread.join(timeout=5.0)


def _handler(fake: "FakeVLLM"):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args, **kwargs) -> None:  # 静かに
            pass

        def _send(self, status: int, obj) -> None:
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path.rstrip("/") == "/v1/models":
                self._send(200, {"object": "list", "data": [{"id": fake.model, "object": "model"}]})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self) -> None:
            n = int(self.headers.get("Content-Length", "0") or 0)
            if n:
                self.rfile.read(n)
            with fake.lock:
                fake.n_requests += 1
                fake.in_flight += 1
                fake.peak_concurrency = max(fake.peak_concurrency, fake.in_flight)
            try:
                if fake.delay_s:
                    time.sleep(fake.delay_s)
                self._send(
                    200,
                    {
                        "id": "x",
                        "choices": [
                            {
                                "index": 0,
                                "message": {"role": "assistant", "content": fake.text},
                                "finish_reason": "stop",
                            }
                        ],
                        "usage": {"prompt_tokens": 123, "completion_tokens": 20},
                    },
                )
            finally:
                with fake.lock:
                    fake.in_flight -= 1

    return Handler
