# -*- coding: utf-8 -*-
"""dm_eval.backends — モデルの当て口(〔11-01 段 1 の 3〕判断モデルの候補と Qwen3-8B の logprob=(G) 案の比べ)。

- ``base``: 抽象 ``ChoiceBackend``(候補の logprob → 分布=Choice/Score)・``FreeTextBackend``(自由記述 → 候補=Noul)・
  推論の形 ``ChoiceForm``(差し替えられる=R-125 が決める)・当て口 ``LogprobChoiceScorer``・``FreeTextScorer``。
- ``hf``: (a) ``HFCausalChoiceScorer``(transformers の causal LM・import は遅延・手元の重みだけ)。
- ``vllm``: (b) ``VLLMLogprobScorer``(OpenAI 互換 ``/v1/completions`` の logprobs/prompt_logprobs・127.0.0.1 固定)。

重みは取らない・GPU とネットワークは使わない(試験は偽の口)。``hf`` と ``vllm`` は名を引いたときに読む。
"""

from __future__ import annotations

from dm_eval.backends.base import (FORM_CHOICE, FORM_LABELS, FORM_NOUL, FORM_SCORE, FORMS, BackendError,
                                   BackendUnavailable, ChoiceBackend, ChoiceForm, FreeTextBackend, FreeTextScorer,
                                   LogprobChoiceScorer, TokenBoundaryError, match_free_text, softmax_dist)

__all__ = [
    "FORM_CHOICE", "FORM_SCORE", "FORM_NOUL", "FORM_LABELS", "FORMS", "BackendError", "BackendUnavailable",
    "TokenBoundaryError", "ChoiceBackend", "FreeTextBackend", "ChoiceForm", "LogprobChoiceScorer", "FreeTextScorer",
    "match_free_text", "softmax_dist", "HFCausalChoiceScorer", "VLLMLogprobScorer",
]


def __getattr__(name: str):  # 遅延の読み(hf と vllm は使うときだけ)
    if name == "HFCausalChoiceScorer":
        from dm_eval.backends.hf import HFCausalChoiceScorer
        return HFCausalChoiceScorer
    if name == "VLLMLogprobScorer":
        from dm_eval.backends.vllm import VLLMLogprobScorer
        return VLLMLogprobScorer
    raise AttributeError(name)
