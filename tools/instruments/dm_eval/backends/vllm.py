# -*- coding: utf-8 -*-
"""dm_eval.backends.vllm — vLLM の OpenAI 互換 ``/v1/completions`` の logprob の口(〔11-01 段 1 の 3〕・(b)=(G) 案)。

``VLLMLogprobScorer`` は ``ChoiceBackend`` と ``FreeTextBackend`` の両方の口。艦隊は **127.0.0.1 だけ**(5070 の安全の
規則 1=ほかの宛先は作るときに落とす)。API key は環境変数(既定 ``DM_EVAL_VLLM_API_KEY``)から呼ぶたびに読み、
``Authorization: Bearer`` のヘッダにだけ載せる(記録・``describe``・例外の文に値を書かない)。HTTP は標準ライブラリの
``http.client``(宛先が固定の 1 本の接続=proxy の環境変数を通らない)。``LogprobChoiceScorer(backend, form)`` で当て口に。

候補の文字列の logprob の取り方(``mode``)
    - ``prompt_logprobs``(既定・〔検収 中 3〕): vLLM の ``prompt_logprobs=0`` で送り、``choices[i].prompt_logprobs`` の
      各トークンの ``decoded_token`` の長さを**後ろから**引いて頭の位置を出す(先頭のトークンは logprob が空=文の側)。
      末尾の候補の位置は、前の日本語の文のトークンの切れ目に左右されない。
    - ``echo``(腕): 文+候補を ``prompt`` に、``echo=true``・``logprobs=1``・``max_tokens=1`` で送り、答えの
      ``logprobs.text_offset`` が文の長さ以上・文+候補の長さ未満のトークンを切り出す。位置は文の頭から数えるので、
      日本語の文の途中でバイト単位のトークンの decoded がずれると位置もずれ得る。
    どちらも切り出す前に、切り出したトークンの文字列の連結が候補の文字列と同じかを確かめ、違えば
    ``TokenBoundaryError``(破綻に数え、その件は失敗=黙って別のトークンを使わない)。
    1 トークン目の形(``choice_number_first``)は ``logprobs=top_logprobs``・``max_tokens=1`` の ``top_logprobs[0]``
    から、前後の空白を除いて候補と同じトークンの値の logsumexp(無ければ -inf)。
    ``batch=True`` は候補の全部を 1 回の要求の ``prompt`` の列で送る(答えは ``index`` で並べ直す)。

expedient(未計測・R-125 と B14 で確かめる)
    - ``text_offset`` と ``decoded_token`` は文字の位置として読む(日本語の候補でトークンが 1 文字の途中で切れると
      位置か字面がずれ得る=その場合は ``TokenBoundaryError``)。
    - (G) の要求は ``temperature=0``・``seed=0``(親の判断 11-01: (G) は logprob の採点で生成ではないので、住民の LLM の
      ランの「生成の設定は既定のまま」とは別=expedient の印)。
"""

from __future__ import annotations

import http.client
import json
import math
import os
from typing import Any, Final, Mapping, Sequence

import dm_eval  # noqa: F401
from dm_eval.backends.base import (BackendError, BackendHTTPError, BackendTimeout, ChoiceBackend, ChoiceForm,
                                   FreeTextBackend, LogprobChoiceScorer, slice_continuation)

__all__ = ["HOST", "COMPLETIONS_PATH", "MODES", "DEFAULT_API_KEY_ENV", "post_json", "VLLMLogprobScorer"]

#: 艦隊の宛先(固定・5070 の安全の規則 1)。
HOST: Final[str] = "127.0.0.1"
COMPLETIONS_PATH: Final[str] = "/v1/completions"
MODES: Final[tuple[str, ...]] = ("prompt_logprobs", "echo")
DEFAULT_API_KEY_ENV: Final[str] = "DM_EVAL_VLLM_API_KEY"
_NEG_INF: Final[float] = float("-inf")


def post_json(port: int, path: str, payload: Mapping[str, Any], *, api_key: str | None, timeout: float
              ) -> dict[str, Any]:
    """127.0.0.1 の ``port`` へ JSON を POST して JSON を返す(key は文に書かない)。

    時間切れは ``BackendTimeout``(分類 timeout)・接続の失敗と 200 でない答えは ``BackendHTTPError``(http)・JSON で
    ない答えは ``BackendError``(parse)。どれも ``judge.ScoreFailed`` で、場面ごとに捕まえて型の名と分類だけを記録する。
    例外の文には艦隊の答えの本文を入れない(入力を引き写す艦隊があり得る=〔再検収 新 低 1〕)。
    """
    body = json.dumps(dict(payload), ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    conn = http.client.HTTPConnection(HOST, int(port), timeout=float(timeout))
    try:
        conn.request("POST", path, body=body, headers=headers)
        resp = conn.getresponse()
        status = int(resp.status)
        data = resp.read()
    except TimeoutError as e:
        raise BackendTimeout("艦隊の答えが時間内に来ない") from e
    except (OSError, http.client.HTTPException) as e:
        raise BackendHTTPError(f"艦隊への接続の失敗({type(e).__name__})") from e
    finally:
        conn.close()
    if status != 200:
        raise BackendHTTPError(f"艦隊の答えが HTTP {status}")
    try:
        return json.loads(data.decode("utf-8"))
    except ValueError as e:
        raise BackendError("艦隊の答えが JSON でない") from e


def _logsumexp(xs: Sequence[float]) -> float:
    vals = [float(x) for x in xs if x is not None and float(x) != _NEG_INF]
    if not vals:
        return _NEG_INF
    m = max(vals)
    return m + math.log(sum(math.exp(v - m) for v in vals))


class VLLMLogprobScorer(ChoiceBackend, FreeTextBackend):
    """vLLM の艦隊(127.0.0.1)の logprob と自由記述の口。作るときは接続しない(呼ぶときだけ)。"""

    def __init__(self, model: str, *, port: int = 8000, host: str = HOST, mode: str = "prompt_logprobs",
                 api_key_env: str = DEFAULT_API_KEY_ENV, top_logprobs: int = 20, timeout: float = 120.0,
                 max_new_tokens: int = 48, batch: bool = True, name: str | None = None) -> None:
        if host != HOST:
            raise ValueError(f"艦隊の宛先は {HOST} だけ(いま {host!r}・5070 の安全の規則 1)")
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ValueError(f"port は 1〜65535 の整数(いま {port!r})")
        if mode not in MODES:
            raise ValueError(f"mode は {MODES} のどれか(いま {mode!r})")
        if not str(model).strip():
            raise ValueError("model の名が空")
        self.model = str(model)
        self.port = int(port)
        self.mode = mode
        self.api_key_env = str(api_key_env)
        self.top_logprobs = int(top_logprobs)
        self.timeout = float(timeout)
        self.max_new_tokens = int(max_new_tokens)
        self.batch = bool(batch)
        self.name = name or f"vllm:{self.model.split('/')[-1]}"
        self.uses_gpu = True

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "kind": "vLLM OpenAI 互換 /v1/completions", "model": self.model, "host": HOST,
                "port": self.port, "mode": self.mode, "top_logprobs": self.top_logprobs, "batch": self.batch,
                "api_key": f"環境変数 {self.api_key_env} から(値は記録しない)", "temperature": 0.0, "seed": 0,
                "uses_gpu": True, "vram_gb": None}

    def scorer(self, form: ChoiceForm | str = "choice_number", **kw: Any) -> LogprobChoiceScorer:
        return LogprobChoiceScorer(self, form, **kw)

    def _post(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return post_json(self.port, COMPLETIONS_PATH, payload, api_key=os.environ.get(self.api_key_env) or None,
                         timeout=self.timeout)

    def _base(self, prompt: Any, max_tokens: int) -> dict[str, Any]:
        return {"model": self.model, "prompt": prompt, "max_tokens": int(max_tokens), "temperature": 0.0, "seed": 0}

    def _choices(self, resp: Mapping[str, Any], n: int) -> list[Mapping[str, Any]]:
        ch = list(resp.get("choices") or ())
        if len(ch) != n:
            raise BackendError(f"答えの choices の数 {len(ch)} が要求の {n} と違う")
        return sorted(ch, key=lambda c: int(c.get("index", 0)))

    def _request_continuations(self, prompts: list[str]) -> list[Mapping[str, Any]]:
        extra: dict[str, Any] = ({"echo": True, "logprobs": 1} if self.mode == "echo" else {"prompt_logprobs": 0})
        if self.batch:
            return self._choices(self._post({**self._base(prompts, 1), **extra}), len(prompts))
        return [self._choices(self._post({**self._base(p, 1), **extra}), 1)[0] for p in prompts]

    @staticmethod
    def _echo_slice(choice: Mapping[str, Any], begin: int, end: int, expected: str) -> tuple[float, ...]:
        lp = choice.get("logprobs") or {}
        starts = lp.get("text_offset")
        vals = lp.get("token_logprobs")
        toks = lp.get("tokens")
        if starts is None or vals is None or toks is None:
            raise BackendError("echo の答えに logprobs.text_offset・token_logprobs・tokens が無い")
        return slice_continuation(starts, vals, begin, end, texts=toks, expected=expected)

    @staticmethod
    def _prompt_logprobs_slice(choice: Mapping[str, Any], total: int, begin: int, end: int, expected: str
                               ) -> tuple[float, ...]:
        pl = choice.get("prompt_logprobs")
        if not pl:
            raise BackendError("答えに prompt_logprobs が無い")
        starts = [0] * len(pl)
        vals: list[float | None] = [None] * len(pl)
        texts: list[str | None] = [None] * len(pl)
        pos = int(total)
        for i in range(len(pl) - 1, -1, -1):  # 逐次ループ宣言: 文のトークンの数(後ろから)
            e = pl[i]
            if e is None:
                starts[i] = 0
                continue
            if len(e) != 1:
                raise BackendError("prompt_logprobs の 1 トークンに複数の行(prompt_logprobs=0 で送る)")
            (only,) = e.values()
            texts[i] = str(only.get("decoded_token", ""))
            pos -= len(texts[i])
            starts[i] = pos
            vals[i] = float(only["logprob"])
        return slice_continuation(starts, vals, begin, end, texts=texts, expected=expected)

    def continuation_logprobs(self, prompt: str, continuations: Sequence[str]) -> list[tuple[float, ...]]:
        prompts = [prompt + c for c in continuations]
        choices = self._request_continuations(prompts)
        begin = len(prompt)
        out = []
        for c, ch in zip(continuations, choices):
            end = begin + len(c)
            if self.mode == "echo":
                out.append(self._echo_slice(ch, begin, end, c))
            else:
                out.append(self._prompt_logprobs_slice(ch, end, begin, end, c))
        return out

    def first_token_logprobs(self, prompt: str, continuations: Sequence[str]) -> list[float]:
        resp = self._post({**self._base(prompt, 1), "logprobs": self.top_logprobs})
        ch = self._choices(resp, 1)[0]
        tops = (ch.get("logprobs") or {}).get("top_logprobs")
        if not tops or not isinstance(tops[0], Mapping):
            raise BackendError("答えに logprobs.top_logprobs[0] が無い")
        top = tops[0]
        return [_logsumexp([v for k, v in top.items() if str(k).strip() == str(c).strip()]) for c in continuations]

    def generate(self, prompt: str) -> str:
        ch = self._choices(self._post(self._base(prompt, self.max_new_tokens)), 1)[0]
        return str(ch.get("text", ""))
