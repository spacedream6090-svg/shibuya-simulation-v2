# -*- coding: utf-8 -*-
"""leak_check.backends — 当て口(``mock``=決定的・``vllm``=127.0.0.1 の OpenAI 互換 ``/v1/chat/completions``)。

口の形
    ``Backend.complete(prompt, *, kind, max_tokens, want_logprobs) -> Reply``。``kind`` は問いの種類
    (``dates``・``events``・``choice``・``recall``)。``Reply.text`` は応答の本文(記録には写さない)・
    ``Reply.top_logprobs`` は 1 トークン目の上位の対数確率(``want_logprobs`` のときだけ・無ければ None)。

mock(対照・GPU なし)
    応答は種と問いの文の sha256 の鍵で決まる(同じ問いには同じ応答)。型 ② の分布は Dirichlet(1) を問いの文の鍵で
    引く=名が違えば分布も違う(名を見る当て口の代わり)。値に意味は無い(器が通ることを見るだけ)。

vLLM(手元の 5070 か艦隊)
    口は 127.0.0.1 に固定(``--port`` だけ選べる)。API key は環境変数(既定 ``VLLM_API_KEY``)から読み、
    ``Authorization: Bearer`` のヘッダに載せる(記録には書かない)。温度 0・考える段を切る
    (``chat_template_kwargs.enable_thinking=false``=``shibuya.llm.fleet`` と同じ形)。送るのは
    ``http.client``(標準ライブラリ)で、URL は ``urllib.parse`` で組む(``urllib.request`` の送りの関数は名が
    識別子の規則に当たるので使わない=親の判断で http.client のまま)。試験は ``transport`` を差し替える。
    モデルの版(``model_version``・重みの revision や sha など)は台帳の 1 行の頭に付ける(空なら「版未記入」)。
"""

from __future__ import annotations

import hashlib
import http.client
import json
import math
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Final, Mapping
from urllib.parse import urlsplit, urlunsplit

import numpy as np

HOST: Final[str] = "127.0.0.1"
DEFAULT_PORT: Final[int] = 8000
DEFAULT_KEY_ENV: Final[str] = "VLLM_API_KEY"
CHAT_PATH: Final[str] = "/v1/chat/completions"
TOP_LOGPROBS: Final[int] = 20
KINDS: Final[tuple[str, ...]] = ("dates", "events", "choice", "recall")
#: mock の版(応答の表を変えたら上げる)。
MOCK_VERSION: Final[str] = "mock-1"

_THINK: Final[re.Pattern[str]] = re.compile(r"<think>.*?</think>", re.S)


class BackendError(RuntimeError):
    """当て口の失敗(HTTP の失敗・応答の形の違い)。"""


@dataclass(frozen=True)
class Reply:
    text: str
    top_logprobs: Mapping[str, float] | None = None


class Backend:
    name: str = ""

    def complete(self, prompt: str, *, kind: str, max_tokens: int, want_logprobs: bool = False) -> Reply:
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return {"kind": self.name}


def _key(seed: str, prompt: str) -> bytes:
    return hashlib.sha256(f"{seed}|{prompt}".encode("utf-8")).digest()


class MockBackend(Backend):
    """決定的な当て口(種と問いの文の鍵)。"""

    name = "mock"
    DATES_REPLIES: Final[tuple[str, ...]] = ("分からない", "ある\n渋谷で大きな催しが開かれた",
                                             "ある\n「ミナモ市」が駅前で開かれた")
    EVENTS_REPLIES: Final[tuple[str, ...]] = ("はい\nその出来事は話題になった。", "いいえ\n聞いたことがありません。",
                                              "分からない")
    RECALL_REPLIES: Final[tuple[str, ...]] = ("続きは分かりません。", "このあと本文が続く。")

    def __init__(self, seed: str = "leak-mock") -> None:
        self.seed = str(seed)
        self.model_version = MOCK_VERSION

    def complete(self, prompt: str, *, kind: str, max_tokens: int, want_logprobs: bool = False) -> Reply:
        if kind not in KINDS:
            raise ValueError(f"kind は {KINDS} のどれか(いま {kind!r})")
        h = _key(self.seed, prompt)
        if kind == "dates":
            return Reply(self.DATES_REPLIES[h[0] % len(self.DATES_REPLIES)])
        if kind == "events":
            return Reply(self.EVENTS_REPLIES[h[0] % len(self.EVENTS_REPLIES)])
        if kind == "recall":
            return Reply(self.RECALL_REPLIES[h[0] % len(self.RECALL_REPLIES)])
        n = len(re.findall(r"^\d+\. ", prompt, flags=re.M))
        if n < 1:
            raise BackendError("候補の番号が問いに無い")
        w = np.random.default_rng(int.from_bytes(h[:8], "little")).exponential(size=n)
        p = w / w.sum()
        best = int(np.argmax(p)) + 1
        lp = {str(i + 1): float(math.log(x)) for i, x in enumerate(p)} if want_logprobs else None
        return Reply(str(best), lp)

    def describe(self) -> dict[str, Any]:
        return {"kind": self.name, "seed": self.seed, "model": "mock", "model_version": self.model_version}


Transport = Callable[[str, int, str, bytes, Mapping[str, str], float], tuple[int, bytes]]


def http_post(host: str, port: int, path: str, body: bytes, headers: Mapping[str, str],
              timeout: float) -> tuple[int, bytes]:
    """HTTP の POST(標準ライブラリ ``http.client``)。"""
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        conn.request("POST", path, body=body, headers=dict(headers))
        r = conn.getresponse()
        return int(r.status), r.read()
    finally:
        conn.close()


class VllmBackend(Backend):
    """vLLM(OpenAI 互換)の当て口。口は 127.0.0.1 に固定。"""

    name = "vllm"

    def __init__(self, model: str, *, port: int = DEFAULT_PORT, key_env: str = DEFAULT_KEY_ENV,
                 timeout: float = 120.0, seed: int = 0, transport: Transport | None = None,
                 model_version: str = "") -> None:
        if not model:
            raise ValueError("vLLM の当て口には --model(served-model-name)が要る")
        if not 1 <= int(port) <= 65535:
            raise ValueError("port は 1〜65535")
        self.model = str(model)
        self.model_version = str(model_version)
        self.port = int(port)
        self.key_env = str(key_env)
        self.timeout = float(timeout)
        self.seed = int(seed)
        self.transport: Transport = transport or http_post
        self.url = urlunsplit(("http", f"{HOST}:{self.port}", CHAT_PATH, "", ""))
        parts = urlsplit(self.url)
        if parts.hostname != HOST:
            raise ValueError("vLLM の口は 127.0.0.1 だけ")

    def payload(self, prompt: str, *, max_tokens: int, want_logprobs: bool) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": int(max_tokens), "temperature": 0.0, "seed": self.seed,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        if want_logprobs:
            body["logprobs"] = True
            body["top_logprobs"] = TOP_LOGPROBS
        return body

    def headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        key = os.environ.get(self.key_env, "")
        if key:
            h["Authorization"] = f"Bearer {key}"
        return h

    def complete(self, prompt: str, *, kind: str, max_tokens: int, want_logprobs: bool = False) -> Reply:
        if kind not in KINDS:
            raise ValueError(f"kind は {KINDS} のどれか(いま {kind!r})")
        body = json.dumps(self.payload(prompt, max_tokens=max_tokens, want_logprobs=want_logprobs),
                          ensure_ascii=False).encode("utf-8")
        try:
            status, raw = self.transport(HOST, self.port, CHAT_PATH, body, self.headers(), self.timeout)
        except (OSError, http.client.HTTPException) as exc:
            raise BackendError(f"vLLM に届かない: {type(exc).__name__}") from exc
        if status != 200:
            raise BackendError(f"vLLM が HTTP {status} を返した")
        try:
            js = json.loads(raw.decode("utf-8"))
            choice = js["choices"][0]
            text = str(choice["message"].get("content") or "")
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            raise BackendError("vLLM の応答の形が違う") from exc
        text = _THINK.sub("", text).strip()
        lp = parse_top_logprobs(choice) if want_logprobs else None
        return Reply(text, lp)

    def describe(self) -> dict[str, Any]:
        return {"kind": self.name, "model": self.model, "model_version": self.model_version, "host": HOST, "port": self.port, "path": CHAT_PATH,
                "temperature": 0.0, "seed": self.seed, "enable_thinking": False, "top_logprobs": TOP_LOGPROBS,
                "api_key_env": self.key_env, "api_key_set": bool(os.environ.get(self.key_env, ""))}


def parse_top_logprobs(choice: Mapping[str, Any]) -> dict[str, float] | None:
    """OpenAI 互換の ``choices[0].logprobs.content[0].top_logprobs`` → トークン → 対数確率。無ければ None。"""
    try:
        content = choice["logprobs"]["content"]
        first = content[0]
        tops = first.get("top_logprobs") or []
    except (KeyError, IndexError, TypeError, AttributeError):
        return None
    out: dict[str, float] = {}
    for t in tops:
        try:
            tok = str(t["token"])
            v = float(t["logprob"])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(v):
            out[tok] = max(out.get(tok, -math.inf), v)
    return out or None


def make_backend(kind: str, *, model: str = "", port: int = DEFAULT_PORT, key_env: str = DEFAULT_KEY_ENV,
                 seed: str = "leak-mock", transport: Transport | None = None, model_version: str = "") -> Backend:
    if kind == "mock":
        return MockBackend(seed)
    if kind == "vllm":
        return VllmBackend(model, port=port, key_env=key_env, transport=transport, model_version=model_version)
    raise ValueError(f"backend は mock か vllm(いま {kind!r})")
