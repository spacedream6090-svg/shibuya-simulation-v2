# -*- coding: utf-8 -*-
"""dm_eval.backends.hf — transformers の causal LM の口(〔11-01 段 1 の 3〕・(a)・重みは取らない・import は遅延)。

``HFCausalChoiceScorer`` は ``ChoiceBackend``(候補の文字列の logprob)と ``FreeTextBackend``(貪欲の自由記述)の両方の
口。重みは**手元の道筋だけ**から読む(``local_files_only=True`` が既定・``trust_remote_code`` は常に切る・safetensors
だけ=5070 の安全の規則 2)。transformers と torch は最初に使うときに import する(本体の venv に無い=GPU の後)。
``LogprobChoiceScorer(backend, form)`` で dm_eval の当て口にする(``.scorer(form)`` は同じ物の近道)。

計算の形(expedient・R-125 で見直す)
    - 文と候補を別々にトークンにして id を連結する(``add_special_tokens`` は文だけ既定・候補は付けない)。結合の境目で
      トークンが混ざらない代わりに、続けて書いた文のトークン化と違うことがある。
    - 候補ごとに 1 回の前向き(まとめない=決定論の検査の「まとめ方」を固定)。KV の共有はしない。
    - 候補の位置の行の logits だけを CPU に移し、numpy で log-softmax して当たりの id の値を取る
      (``continuation_logprobs_from_logits``=試験は numpy だけで回る)。
VRAM の欄は空(GPU の後で ``torch.cuda.max_memory_allocated`` を読む形にする=今は欄だけ)。
"""

from __future__ import annotations

from typing import Any, Final, Sequence

import numpy as np

import dm_eval  # noqa: F401
from dm_eval.backends.base import BackendUnavailable, ChoiceBackend, ChoiceForm, FreeTextBackend, LogprobChoiceScorer

__all__ = ["HFCausalChoiceScorer", "continuation_logprobs_from_logits", "log_softmax_rows"]

_DTYPES: Final[tuple[str, ...]] = ("bfloat16", "float16", "float32")


def log_softmax_rows(logits: np.ndarray) -> np.ndarray:
    """行ごとの log-softmax(float64・最大を引いてから)。"""
    x = np.asarray(logits, dtype=np.float64)
    m = x.max(axis=-1, keepdims=True)
    z = x - m
    return z - np.log(np.exp(z).sum(axis=-1, keepdims=True))


def continuation_logprobs_from_logits(rows: np.ndarray, targets: Sequence[int]) -> tuple[float, ...]:
    """候補のトークンを当てる位置の logits の行(``rows[k]`` が ``targets[k]`` を当てる)→ トークンごとの logprob。"""
    r = np.asarray(rows)
    if r.ndim != 2 or r.shape[0] != len(targets):
        raise ValueError(f"logits の行の数 {r.shape} と候補のトークンの数 {len(targets)} が違う")
    lp = log_softmax_rows(r)
    return tuple(float(lp[k, int(t)]) for k, t in enumerate(targets))


def _lazy_imports() -> tuple[Any, Any]:
    try:
        import torch
        import transformers
    except ImportError as e:  # 本体の venv には無い(GPU の後・pip は許可の後)
        raise BackendUnavailable("transformers と torch が要る(GPU の後・pip は許可の後)") from e
    return torch, transformers


class HFCausalChoiceScorer(ChoiceBackend, FreeTextBackend):
    """transformers の causal LM(手元の道筋の重み)の logprob と自由記述の口。"""

    def __init__(self, model_path: str, *, name: str | None = None, device: str = "cuda", dtype: str = "bfloat16",
                 revision: str | None = None, local_files_only: bool = True, max_new_tokens: int = 48) -> None:
        if dtype not in _DTYPES:
            raise ValueError(f"dtype は {_DTYPES} のどれか")
        self.model_path = str(model_path)
        self.name = name or f"hf:{self.model_path.replace(chr(92), '/').rstrip('/').split('/')[-1]}"
        self.device = str(device)
        self.dtype = dtype
        self.revision = revision
        self.local_files_only = bool(local_files_only)
        self.max_new_tokens = int(max_new_tokens)
        self.uses_gpu = not self.device.startswith("cpu")
        self._loaded: tuple[Any, Any, Any] | None = None

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "kind": "transformers causal LM", "model": self.name.split(":", 1)[-1],
                "revision": self.revision, "device": self.device, "dtype": self.dtype,
                "local_files_only": self.local_files_only, "trust_remote_code": False, "use_safetensors": True,
                "uses_gpu": self.uses_gpu, "vram_gb": None, "batching": "候補ごとに 1 回の前向き(まとめない)"}

    def scorer(self, form: ChoiceForm | str = "choice_number", **kw: Any) -> LogprobChoiceScorer:
        return LogprobChoiceScorer(self, form, **kw)

    def _load(self) -> tuple[Any, Any, Any]:
        if self._loaded is None:
            torch, transformers = _lazy_imports()
            tok = transformers.AutoTokenizer.from_pretrained(
                self.model_path, revision=self.revision, local_files_only=self.local_files_only,
                trust_remote_code=False)
            model = transformers.AutoModelForCausalLM.from_pretrained(
                self.model_path, revision=self.revision, local_files_only=self.local_files_only,
                trust_remote_code=False, use_safetensors=True, torch_dtype=getattr(torch, self.dtype))
            model.to(self.device)
            model.eval()
            self._loaded = (torch, tok, model)
        return self._loaded

    def _ids(self, tok: Any, text: str, *, special: bool) -> list[int]:
        return [int(x) for x in tok(text, add_special_tokens=special)["input_ids"]]

    def _rows(self, ids: list[int], begin: int, end: int) -> np.ndarray:
        """``ids`` を 1 回前向きに通し、位置 begin−1 〜 end−2 の logits の行(位置 k の行が k+1 番目を当てる)。"""
        torch, _tok, model = self._load()
        with torch.no_grad():
            x = torch.tensor([ids], dtype=torch.long, device=self.device)
            logits = model(input_ids=x).logits[0, begin - 1:end - 1, :]
            return logits.float().cpu().numpy()

    def continuation_logprobs(self, prompt: str, continuations: Sequence[str]) -> list[tuple[float, ...]]:
        _torch, tok, _model = self._load()
        p = self._ids(tok, prompt, special=True)
        if not p:
            raise ValueError("文のトークンが 0 個")
        out = []
        for c in continuations:  # 逐次ループ宣言: 候補の数
            cids = self._ids(tok, c, special=False)
            if not cids:
                raise ValueError(f"候補の文字列のトークンが 0 個: {c!r}")
            ids = p + cids
            out.append(continuation_logprobs_from_logits(self._rows(ids, len(p), len(ids)), cids))
        return out

    def first_token_logprobs(self, prompt: str, continuations: Sequence[str]) -> list[float]:
        _torch, tok, _model = self._load()
        p = self._ids(tok, prompt, special=True)
        lp = log_softmax_rows(self._rows(p, len(p), len(p) + 1))[0]  # 文の末尾の行=次のトークンの分布
        return [float(lp[self._ids(tok, c, special=False)[0]]) for c in continuations]

    def generate(self, prompt: str) -> str:
        torch, tok, model = self._load()
        p = self._ids(tok, prompt, special=True)
        with torch.no_grad():
            x = torch.tensor([p], dtype=torch.long, device=self.device)
            y = model.generate(input_ids=x, max_new_tokens=self.max_new_tokens, do_sample=False)
        return str(tok.decode([int(v) for v in y[0, len(p):].tolist()], skip_special_tokens=True))
