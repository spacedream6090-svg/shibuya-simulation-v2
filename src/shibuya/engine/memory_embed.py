"""engine.memory_embed — 記憶 MR2 の意味の手がかり(埋め込み)の口(第 6 期 6-5・腕 ``--memory-cue embed``)。

正: 決定 10-12 §4-6 MR2(問い 1=その場の手がかり(ID の一致)が既定・意味の手がかりは腕で並走/問い 2=Ruri-v3-30m と 130m を
両方腕で並べ、人の記憶のデータに近い方を選ぶ/問い 3=印象と出来事の要旨に埋め込みを付ける/問い 4=会話中は相手の直前の発言、
それ以外は本人の直前の理由か予定を手がかりに)。R-87 §1-6(Ruri-v3-30m 37M・256 次元・Apache-2.0 / 130m 132M・512 次元・
Apache-2.0・JMTEB の値は表とモデルカードで 1.5 ポイント前後ずれる)。

形
- 埋め込みの口 :class:`Embedder`(``encode(texts, query=…)`` → L2 で正規化した ``(件, 次元)`` の float32)。
  - :class:`RuriEmbedder`: huggingface ``cl-nagoya/ruri-v3-30m``・``ruri-v3-130m`` の重みを版(commit)で固定して
    ``data/models/ruri/<名>@<commit>/`` から読む(CPU・GPU は使わない・torch と transformers が要る=重みも依存も無ければ
    :class:`EmbedUnavailable`)。版と sha は :data:`RURI_PINS`。
  - :class:`NgramEmbedder`(``ngram-test``): 重みの要らない試験用の代わり(文字の 1〜3-gram を crc32 で 256 次元へ・意味の
    手がかりでは**ない**=経路・決定論・計算量を測るためだけ)。
- 状態 :class:`CueState`(記憶の器の子の持ち主 ``mem_layer.memory_store.cue``・状態台帳の腕の行 ``M0C``=腕 memory-cue):
  手がかりの文(相手の直前の発言 ``_heard``・本人の直前の理由 ``_own``=required)と、行の埋め込み(``_vec``=注釈=要旨から
  作り直せる=hash_skip)・手がかりの文の埋め込みの控え(``_qcache``=hash_skip)。
- 想起(``MemoryStore.recall`` の腕): ``score += W_CTX · cos(手がかり, 行)``・一致=``cos ≥ COS_MATCH``(ID の一致の代わり=
  「意味の手がかりだけの腕」=MR6 の後段の比べ)。埋め込みの無い行(要旨の無い出来事)の cos は 0。
- 既定 off(腕 id)では状態も埋め込みも作らない=計算しない(結果不変)。

**未リサーチ(expedient)**(つなぎの台帳の行 ``DOC-mr65-embed-*``): ``W_CTX``=1.0(R-87 §4-1 の感度の腕 {0, 0.5, 1, 2} の
中)・``COS_MATCH``=0.5・Ruri の接頭辞(``検索クエリ: ``/``検索文書: ``=モデルカードで確かめる前の仮)・埋め込みを float16 に
丸めて持つ(決定論の手当て)・``ngram-test`` の次元 256・手がかりの文の控え 4,096 件。

**重みの取得(第 6 期 6-5 の記録 mr65/README.md)**: huggingface.co の ``model.safetensors`` は ``us.aws.cdn.hf.co`` へ転送
される(許可の一覧の外のドメイン=CLAUDE.md §7「転送先が別ドメインなら取得せず先に聞く」)=本段では取得していない。

逐次ループ宣言(P4): ``encode`` はバッチ(1 回の呼びの文の数ぶん=``NgramEmbedder`` は文の字数ぶんの Python ループ・Ruri は
1 回の前向き計算)。``embed_rows`` は注釈を置いた行の数ぶん(会話の要旨=1 刻みに数件)。``cos_rows`` は配列演算。
"""

from __future__ import annotations

import zlib
from collections import OrderedDict
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping, NamedTuple, Protocol, Sequence

import numpy as np

__all__ = [
    "W_CTX", "COS_MATCH", "QUERY_PREFIX", "DOC_PREFIX", "QCACHE_MAX", "MODEL_ROOT", "RuriPin", "RURI_PINS",
    "EmbedUnavailable", "Embedder", "NgramEmbedder", "RuriEmbedder", "make_embedder", "model_identity", "CueState",
]

#: 関連の重み(MR1 の「共通にするもの」の 1 つ=強さと同じ尺度に足す・expedient)。
W_CTX: Final[float] = 1.0
#: 意味の手がかりの一致の境目(cos・expedient)。
COS_MATCH: Final[float] = 0.5
#: Ruri-v3 の接頭辞(問い=手がかりの文・文書=要旨と印象)。モデルカードで確かめる前の仮(expedient)。
QUERY_PREFIX: Final[str] = "検索クエリ: "
DOC_PREFIX: Final[str] = "検索文書: "
#: 手がかりの文の埋め込みの控えの件数(LRU)。
QCACHE_MAX: Final[int] = 4096
#: 重みの置き場(gitignore の下)。
MODEL_ROOT: Final[str] = "data/models/ruri"


class RuriPin(NamedTuple):
    """Ruri-v3 の版の固定(huggingface のリポ・commit・重みの sha256=X-Linked-ETag・大きさ・ライセンス)。"""

    repo: str
    revision: str
    safetensors_sha256: str
    safetensors_bytes: int
    dim: int
    license: str
    base_model: str


#: 版の固定(2026-10-15 に huggingface.co の API と HEAD で確かめた値=重みは取得していない)。
RURI_PINS: Final[Mapping[str, RuriPin]] = MappingProxyType({
    "ruri-v3-30m": RuriPin("cl-nagoya/ruri-v3-30m", "24899e5de370b56d179604a007c0d727bf144504",
                           "e94155e342cbfc33280c345c6e2912905fb5de6e1a3adeb938f395aafd2f8832", 146_828_152, 256,
                           "apache-2.0", "cl-nagoya/ruri-v3-pt-30m"),
    "ruri-v3-130m": RuriPin("cl-nagoya/ruri-v3-130m", "e3114c6ee10dbab8b4b235fbc6dcf9dd4d5ac1a6",
                            "1c342581efc23d0b50b92fb11ac1eeb02719691bcc59bdc0dc0b09a36b4fc6d1", 528_573_472, 512,
                            "apache-2.0", "cl-nagoya/ruri-v3-pt-130m"),
})


class EmbedUnavailable(RuntimeError):
    """埋め込みのモデルが使えない(重みが置き場に無い・torch/transformers が無い)。"""


class Embedder(Protocol):
    """埋め込みの口(``encode`` は L2 で正規化した ``(件, dim)`` の float32)。"""

    name: str
    dim: int

    def encode(self, texts: Sequence[str], *, query: bool) -> np.ndarray: ...


class NgramEmbedder:
    """試験用の代わり ``ngram-test``(文字の 1〜3-gram を crc32 で ``dim`` 次元に足して正規化・意味の手がかりではない)。"""

    name = "ngram-test"

    def __init__(self, dim: int = 256) -> None:
        self.dim = int(dim)

    def encode(self, texts: Sequence[str], *, query: bool) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):  # 逐次ループ宣言: 文の数 × 字数 × 3(試験用)
            s = str(t or "")
            for n in (1, 2, 3):
                for j in range(max(0, len(s) - n + 1)):
                    h = zlib.crc32(s[j:j + n].encode("utf-8"))
                    out[i, h % self.dim] += 1.0
        nrm = np.linalg.norm(out, axis=1, keepdims=True)
        return np.where(nrm > 0, out / np.where(nrm > 0, nrm, 1.0), 0.0).astype(np.float32)


class RuriEmbedder:
    """Ruri-v3(``cl-nagoya/ruri-v3-30m``・``130m``)を CPU で(重みは :data:`MODEL_ROOT` の版の置き場から読む)。

    **本段では重みを取得していない**(転送先が許可の一覧の外)=作ると :class:`EmbedUnavailable`。重みが置かれた後の
    読み方(未試験): ``transformers`` の ``AutoTokenizer``/``AutoModel``・平均の pooling(``1_Pooling/config.json`` で
    確かめる)・接頭辞 :data:`QUERY_PREFIX`/:data:`DOC_PREFIX`・``torch.use_deterministic_algorithms(True)``・スレッド 1。
    """

    def __init__(self, name: str, *, root: str | Path = MODEL_ROOT) -> None:
        if name not in RURI_PINS:
            raise ValueError(f"Ruri の名は {tuple(RURI_PINS)} のどれか(いま {name!r})")
        pin = RURI_PINS[name]
        self.name = name
        self.dim = int(pin.dim)
        d = Path(root) / f"{name}@{pin.revision}"
        if not (d / "model.safetensors").exists():
            raise EmbedUnavailable(f"{name} の重みが {d.as_posix()} に無い(本段では取得していない=転送先 us.aws.cdn.hf.co が"
                                   f"許可の一覧の外。取得の許可の後に版 {pin.revision[:12]} を置く)")
        try:
            import torch  # noqa: F401
            from transformers import AutoModel, AutoTokenizer
        except ImportError as e:  # pragma: no cover - 依存が無い環境
            raise EmbedUnavailable(f"{name} は torch と transformers が要る({e})") from None
        import torch as _torch

        _torch.use_deterministic_algorithms(True)
        _torch.set_num_threads(1)
        self._tok = AutoTokenizer.from_pretrained(str(d))
        self._model = AutoModel.from_pretrained(str(d)).eval()
        self._torch = _torch

    def encode(self, texts: Sequence[str], *, query: bool) -> np.ndarray:  # pragma: no cover - 重みが無い本段では通らない
        pre = QUERY_PREFIX if query else DOC_PREFIX
        batch = self._tok([pre + str(t or "") for t in texts], padding=True, truncation=True, return_tensors="pt")
        with self._torch.no_grad():
            h = self._model(**batch).last_hidden_state
        m = batch["attention_mask"].unsqueeze(-1).to(h.dtype)
        v = (h * m).sum(dim=1) / m.sum(dim=1).clamp(min=1.0)
        v = v / v.norm(dim=1, keepdim=True).clamp(min=1e-12)
        return v.cpu().numpy().astype(np.float32)


def model_identity(name: str) -> str:
    """〔検収 L1〕埋め込みのモデルの名 → 版の同定(設定の指紋と manifest の設定の節に入れる=再開で取り違えを止める)。

    Ruri は ``<repo>@<commit>:sha256=<重みの sha256>``(:data:`RURI_PINS`)・``ngram-test`` は作りの名と次元。
    """
    if name in RURI_PINS:
        p = RURI_PINS[name]
        return f"{p.repo}@{p.revision}:sha256={p.safetensors_sha256}"
    if name == NgramEmbedder.name:
        return f"{NgramEmbedder.name}:crc32-char-1..3gram/{NgramEmbedder().dim}"
    raise ValueError(f"埋め込みのモデルの名は {tuple(RURI_PINS) + (NgramEmbedder.name,)} のどれか(いま {name!r})")


def make_embedder(name: str, *, root: str | Path = MODEL_ROOT) -> Embedder:
    """腕のモデルの名 → 埋め込みの口(``ngram-test`` は試験用の代わり・Ruri は重みが無ければ :class:`EmbedUnavailable`)。"""
    if name == NgramEmbedder.name:
        return NgramEmbedder()
    return RuriEmbedder(name, root=root)


class CueState:
    """意味の手がかりの状態(記憶の器の子の持ち主 ``mem_layer.memory_store.cue``・状態台帳の腕の行 ``M0C``)。

    書く口は器の中からだけ: 手がかりの文(:meth:`note_heard`・:meth:`note_own`=``MemoryLayer.note_utterance`` から器の口
    ``MemoryStore.note_cue`` を通る)・行の埋め込み(:meth:`embed_rows`・:meth:`drop_rows`・:meth:`remap`・:meth:`rebuild`=
    器の ``remember`` の注釈・追い出し・広げる口・再開)。欄の付け替えは ``__setattr__`` が落とす。
    """

    LEDGER_ARM: str = "memory-cue"
    __slots__ = ("embedder", "model", "dim", "_heard", "_own", "_vec", "_qcache", "_cue_stats")

    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder
        self.model = str(embedder.name)
        self.dim = int(embedder.dim)
        #: 体 → 会話の相手の直前の発言(会話中の手がかり=MR2 問い 4)。
        self._heard: dict[int, str] = {}
        #: 体 → 本人の直前の理由か予定(会話の外の手がかり)。
        self._own: dict[int, str] = {}
        #: 行の番地 → 埋め込み(float16・要旨と印象の文から=作り直せる)。
        self._vec: dict[int, np.ndarray] = {}
        #: 手がかりの文 → 埋め込み(LRU・作り直せる)。
        self._qcache: "OrderedDict[str, np.ndarray]" = OrderedDict()
        self._cue_stats: dict[str, int] = {"heard": 0, "own": 0, "rows_embedded": 0, "rows_dropped": 0,
                                           "queries": 0, "query_cache_hits": 0, "recalls_with_cue": 0,
                                           "recalls_without_cue": 0}

    def __setattr__(self, name: str, value: Any) -> None:
        if not hasattr(self, name):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"意味の手がかりの状態の欄 {name} は付け替えられない")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"意味の手がかりの状態の欄 {name} は消せない")

    # ------------------------------------------------------------------ 器の口の中から呼ぶ
    def note_heard(self, listeners: Sequence[int], text: str) -> None:
        t = str(text or "").strip()
        if not t or t == "なし":
            return
        for x in listeners:  # 逐次ループ宣言: 聞き手の数(≤ 2)
            self._heard[int(x)] = t
            self._cue_stats["heard"] += 1

    def note_own(self, agent: int, text: str) -> None:
        t = str(text or "").strip()
        if not t or t == "なし":
            return
        self._own[int(agent)] = t
        self._cue_stats["own"] += 1

    def embed_rows(self, rows: Sequence[int], texts: Sequence[str]) -> None:
        """行の注釈(要旨・印象)の埋め込みを置く(1 回のバッチ)。"""
        if not rows:
            return
        v = self.embedder.encode(list(texts), query=False).astype(np.float16)
        for g, vec in zip(rows, v):  # 逐次ループ宣言: 注釈を置いた行の数ぶん
            self._vec[int(g)] = vec
        self._cue_stats["rows_embedded"] += len(rows)

    def drop_rows(self, rows: Sequence[int]) -> None:
        for g in rows:  # 逐次ループ宣言: 追い出した・消した行の数ぶん
            if self._vec.pop(int(g), None) is not None:
                self._cue_stats["rows_dropped"] += 1

    def remap(self, n_agents: int, old_rows: int, new_rows: int) -> None:
        """上限なしの腕で行の幅を広げたとき、番地 ``a × old + j`` を ``a × new + j`` に付け替える。"""
        old = dict(self._vec)
        self._vec.clear()
        for g, vec in old.items():  # 逐次ループ宣言: 埋め込みのある行の数ぶん(広げるときだけ)
            a, j = divmod(int(g), int(old_rows))
            self._vec[a * int(new_rows) + j] = vec

    def rebuild(self, notes: Mapping[int, str]) -> int:
        """再開: 注釈(要旨)から行の埋め込みを作り直す → 行の数。"""
        self._vec.clear()
        rows = sorted(int(g) for g in notes)
        self.embed_rows(rows, [notes[g] for g in rows])
        return len(rows)

    # ------------------------------------------------------------------ 読み口
    def text_for(self, agent: int, conversation: bool) -> str | None:
        """手がかりの文(会話中=相手の直前の発言・無ければ本人の直前の理由/会話の外=本人の直前の理由か予定)。"""
        i = int(agent)
        if conversation and i in self._heard:
            return self._heard[i]
        return self._own.get(i)

    def query(self, text: str) -> np.ndarray:
        """手がかりの文の埋め込み(控えつき)。"""
        q = self._qcache.get(text)
        if q is not None:
            self._qcache.move_to_end(text)
            self._cue_stats["query_cache_hits"] += 1
            return q
        q = self.embedder.encode([text], query=True)[0].astype(np.float16)
        self._qcache[text] = q
        while len(self._qcache) > QCACHE_MAX:
            self._qcache.popitem(last=False)
        self._cue_stats["queries"] += 1
        return q

    def cue_cos(self, rows: np.ndarray, text: str | None) -> np.ndarray | None:
        """想起の 1 回: 手がかりの文 → 行の cos(文が無ければ ``None``=一致 0)。計数を足す(器の想起の口の中から)。"""
        if not text:
            self._cue_stats["recalls_without_cue"] += 1
            return None
        self._cue_stats["recalls_with_cue"] += 1
        return self.cos_rows(rows, self.query(str(text)))

    def cos_rows(self, rows: np.ndarray, q: np.ndarray) -> np.ndarray:
        """行の番地の配列 → cos(埋め込みの無い行は 0)。"""
        g = np.asarray(rows, dtype=np.int64)
        out = np.zeros(g.size, dtype=np.float64)
        have = [j for j, x in enumerate(g.tolist()) if x in self._vec]  # 逐次ループ宣言: 体の行の数(≤ 行の幅)
        if have:
            V = np.stack([self._vec[int(g[j])] for j in have]).astype(np.float64)
            out[np.asarray(have)] = V @ np.asarray(q, dtype=np.float64)
        return out

    def summary(self) -> dict[str, Any]:
        """manifest ``memory_summary.memory_store.cue``(観測)。"""
        return {"model": self.model, "dim": self.dim, "w_ctx": W_CTX, "cos_match": COS_MATCH,
                "rows_with_vec": len(self._vec), "agents_heard": len(self._heard), "agents_own": len(self._own),
                "counts": dict(self._cue_stats)}
