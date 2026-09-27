"""engine.poi_target — 購入/食事/並ぶの対象を**候補 → 選び手**で決める(段 2a・D-114 (a))。

正典: 実装アジェンダ ``docs/design/v2-intent-chooser-implementation-agenda.md`` §1-3〜§1-5。
それまでの規則は「現在セルの**最小 id** の POI」(``commit._poi_in_cell``・A20)で、開いているかも
意図に合うかも見なかった(D-114: 閉店の失敗の 79% は同じセルに開いている店があった)。

手順(1 呼ごと)
1. **対象欄の読み**(:meth:`TargetResolver.classify`):
   (a0) **総称語**(:data:`GENERIC_WORDS`=店・店舗・ショップ・お店)→ なし
   (a) 全体が**カテゴリ語**(:data:`CATEGORY_WORDS`)に一致 → カテゴリ
   (b) ``food1954`` の形(描画の合成名=cat+POI 索引 4 桁)→ 名指し
   (c) **POI 名**(全 POI・NFKC)に一致 → 名指し。照合順は C9b の目印照合(``llm.contract.
       resolve_landmark``)と同じ **完全一致 → 名⊂入力(最長)→ 入力⊂名(最短)**。同名の店
       (チェーン)は全部を候補にする
   (d) カテゴリ語を**含む**(最長の語)→ カテゴリ
   (e) それ以外(なし・説明語・セル ID・人 ID・自由文)→ **なし**
2. **候補**=現在セルの POI のうち **意図に合う**(食事=``eatery_mask`` / 購入・並ぶ=**店舗系 cat**
   :data:`BUYABLE_CATS`)∧ カテゴリなら**カテゴリ一致** ∧ **営業中**(``open_mask``)∧ 購入(と並ぶの
   飲食店以外)は**棚在庫 > 0**。到達可は同じセルなので自明。名指しは候補を**その店**に絞る
   (現在セルに無い名指しは段 2c=いまは失敗)。
3. **選び手**(``engine.chooser``)の分布から抽選。候補が 0 なら**理由を分けて**対象を置く:
   合う店が無い → ``-1``(購入/並ぶ=``BAD_TARGET``・食事=``NOT_IN_EATERY``)/ 合う店はあるが
   全部閉店 → その 1 件(``CLOSED``)/ 開いているが全部在庫切れ → その 1 件(``OUT_OF_STOCK``)/
   名指しが現在セルに無い → ``-1``(理由 ``named_out_of_cell``)。結果コードは ``engine.resolve`` の
   既存の判定がそのまま付ける(新しいコードは作らない)。

計数(manifest ``target_resolution``): (i) 名指し・(ii) カテゴリ語 → 候補 → 選び手・(iii) なし →
候補 → 選び手・(iv) 候補なし(理由別)と、選び手の分布のエントロピーの平均。

expedient(宣言)
- :data:`CATEGORY_WORDS`(対象欄の語 → W6 の cat/subcat)=**対応表 v0(第286・宣言)**。親決定
  (Q11)で起草をそのまま v0 として採用。語の出所は B2 に出る業種語(``build/lang/w14_signage.
  CAT_WORDS``/``SUBCAT_WORDS``=LLM が実際に読む語)と第270 の対象欄の頻出語(食品カテゴリ・食品・
  飲食店・食堂・食品店・食べ物・食事・物販店・コンビニエンスストア・薬局・サービス店・カフェ・
  レストラン …)。総称語(:data:`GENERIC_WORDS`)は「なし」。
- :data:`BUYABLE_CATS`(購入/並ぶの候補=店舗系 cat・親決定 Q12=D-114 (a) の「意図に合う」)。
  除く cat(office・hotel・school・landmark・hall・education)で起きていた「学校・事務所・教会での
  購入」(D-114 の実測=売上の 55.7% が 1,500 円帯)を消す。
- 読みの順((a) を名指しより先に置く=「カフェ」が「カフェ・ベローチェ」の名指しにならない)。
- 閉店/在庫切れの代表の 1 件は既定の選び手と同じ並び(可視の降順 → 索引)の先頭。
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Final, Sequence

import numpy as np

from shibuya.engine.chooser import ChoiceContext, Chooser, draw_index, entropy_bits
from shibuya.world.assets import SYNTHETIC_POI_CATS

__all__ = [
    "KIND_NAMED",
    "KIND_CATEGORY",
    "KIND_NONE",
    "NO_CANDIDATE_REASONS",
    "CATEGORY_WORDS",
    "GENERIC_WORDS",
    "BUYABLE_CATS",
    "POI_TARGET_MODES",
    "DEFAULT_POI_TARGET",
    "check_poi_target",
    "TargetResolver",
    "resolution_summary",
]

KIND_NAMED: Final[str] = "named"
KIND_CATEGORY: Final[str] = "category"
KIND_NONE: Final[str] = "none"
#: 候補 0 の理由((iv) の内訳)。
NO_CANDIDATE_REASONS: Final[tuple[str, ...]] = (
    "bad_target", "not_in_eatery", "closed", "out_of_stock", "named_out_of_cell",
)

#: **対応表 v0(第286・宣言)**(expedient・親決定 Q11=起草を v0 として採用): 対象欄の語 →
#: W6 の (cat の集合, subcat の集合)。POI が「cat が集合に入る **または** subcat が集合に入る」
#: とき一致。長い語から照合する。59 語。
CATEGORY_WORDS: Final[tuple[tuple[str, frozenset[str], frozenset[str]], ...]] = tuple(
    (w, frozenset(c), frozenset(s))
    for w, c, s in (
        # ---- 飲食(W14 CAT_WORDS food=「飲食店」・nightlife=「夜間営業の飲食店」)----
        ("夜間営業の飲食店", ("nightlife",), ()),
        ("飲食店", ("food",), ()),
        ("レストラン", ("food",), ()),
        ("食堂", ("food",), ()),
        ("飲食", ("food",), ()),
        ("ラーメン", ("food",), ()),
        ("カフェ", ("food",), ()),
        ("喫茶店", ("food",), ()),
        ("喫茶", ("food",), ()),
        ("居酒屋", ("nightlife",), ()),
        ("バー", ("nightlife",), ()),
        # ---- 食品・飲み物(買う物)= 飲食店+コンビニ ----
        ("食品カテゴリ", ("food",), ("convenience",)),
        ("食料品", ("food",), ("convenience",)),
        ("食品店", ("food",), ("convenience",)),
        ("食品", ("food",), ("convenience",)),
        ("食料", ("food",), ("convenience",)),
        ("食べ物", ("food",), ("convenience",)),
        ("食事", ("food",), ()),
        ("飲み物", ("food",), ("convenience",)),
        ("ドリンク", ("food",), ("convenience",)),
        ("飲料", ("food",), ("convenience",)),
        ("コーヒー", ("food",), ("convenience",)),
        # ---- 物販(W14 shop=「物販店」・convenience=「コンビニエンスストア」)----
        ("コンビニエンスストア", (), ("convenience",)),
        ("コンビニ", (), ("convenience",)),
        ("物販店", ("shop",), ()),
        ("物販", ("shop",), ()),
        ("スーパー", ("shop",), ()),
        ("書店", (), ("books",)),
        ("本屋", (), ("books",)),
        ("楽器店", (), ("musical_instrument",)),
        ("文房具", (), ("stationery",)),
        ("花屋", (), ("florist",)),
        ("自転車", (), ("bicycle",)),
        ("スポーツ用品", (), ("sports_shop",)),
        # ---- サービス(W14 service=「サービス店」・hospital=「病院」)----
        ("サービス店", ("service",), ()),
        ("薬局", ("service", "shop"), ()),
        ("ドラッグストア", ("service", "shop"), ()),
        ("病院", (), ("hospital",)),
        ("図書館", (), ("library",)),
        # ---- 娯楽・その他(W14 の業種語)----
        ("カラオケ店", (), ("karaoke",)),
        ("カラオケ", (), ("karaoke",)),
        ("ナイトクラブ", (), ("club",)),
        ("ゲームセンター", (), ("arcade",)),
        ("ぱちんこ店", (), ("pachinko",)),
        ("パチンコ", (), ("pachinko",)),
        ("サウナ", (), ("sauna",)),
        ("インターネットカフェ", (), ("net_cafe",)),
        ("ネットカフェ", (), ("net_cafe",)),
        ("映画館", ("cinema",), ()),
        ("宿泊施設", ("hotel",), ()),
        ("ホテル", ("hotel",), ()),
        ("娯楽施設", ("leisure",), ()),
        ("観光施設", ("attraction",), ()),
        ("集会施設", ("hall",), ()),
        ("事務所", ("office",), ()),
        ("公園", (), ("park",)),
        ("劇場", (), ("theatre",)),
        ("美術館", (), ("museum",)),
        ("博物館", (), ("museum",)),
    )
)

#: 購入/食事/並ぶの対象の決め方の切替口(親決定 Q13・``--poi-target``)。``candidates``(既定)=
#: 本モジュール(候補 → 選び手)/ ``legacy``=段 2a 前の「現在セルの最小 id」(``commit._poi_in_cell``)=
#: **旧 checkpoint(02bd0312 等)の再現用**。
POI_TARGET_MODES: Final[tuple[str, ...]] = ("candidates", "legacy")
DEFAULT_POI_TARGET: Final[str] = POI_TARGET_MODES[0]


def check_poi_target(mode: str) -> str:
    """``poi_target`` の値を検査して返す。"""
    m = str(mode)
    if m not in POI_TARGET_MODES:
        raise ValueError(f"poi_target は {POI_TARGET_MODES} のどれか(いま {mode!r})")
    return m


#: 総称語(対応表 v0・親決定 Q11): 「店」「店舗」「ショップ」「お店」は業態を指さない=**なし**として読む
#: (POI 名の「入力 ⊂ 名」に当てない=「〇〇ショップ」の名指しにしない)。
GENERIC_WORDS: Final[frozenset[str]] = frozenset({"店", "店舗", "ショップ", "お店"})

#: **購入/並ぶの候補になる cat**(店舗系・親決定 Q12=D-114 (a) の「意図に合う」・宣言)。W6 の cat 実測:
#: food 823・shop 721・nightlife 259・service 114・leisure 42・cinema 7・attraction 12。
#: 除く: office・hotel・school・landmark・hall・education。
BUYABLE_CATS: Final[frozenset[str]] = frozenset(
    {"food", "shop", "nightlife", "service", "leisure", "cinema", "attraction"}
)
#: 合成世界(``world.assets.SYNTHETIC_POI_CATS``=コンビニ/飲食/物販)の POI は**作りからして全部店**
#: なので購入/並ぶの候補に入れる(実資産の cat 名とは重ならない=実世界の挙動には効かない)。
SYNTHETIC_BUYABLE_CATS: Final[frozenset[str]] = frozenset(SYNTHETIC_POI_CATS)

_ID_FORM: Final[re.Pattern[str]] = re.compile(
    r"^(food|shop|service|office|hotel|school|landmark|leisure|hall|attraction|cinema|nightlife|education)(\d{4})$"
)
#: 名指しの照合で見る名の最短字数(C9b ``LANDMARK_MIN_CHARS`` と同じ)。
NAME_MIN_CHARS: Final[int] = 2
#: 対象欄の前後から剥がす語(「〇〇の店頭」「〇〇へ」)。
_SUFFIXES: Final[tuple[str, ...]] = ("の店頭", "の店", "店頭", "へ", "に", "まで")


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKC", str(text)).strip().strip("「」『』\"'。、.,").strip()


@dataclass
class TargetResolver:
    """対象欄の読み・候補の絞り込み・選び手の抽選(1 ランに 1 つ・世界は読むだけ)。"""

    world: Any
    chooser: Chooser
    seed: int | str
    #: 計数(``resolution_summary`` が manifest の形にする)。
    stats: Counter = field(default_factory=Counter)
    entropy_sum: float = 0.0

    def __post_init__(self) -> None:
        a = self.world.assets
        n = int(self.world.n_poi)
        self._cat = tuple(str(c) for c in a.poi_cat)
        sub = tuple(getattr(a, "poi_subcat", ()) or ())
        self._sub = sub if len(sub) == n else ("",) * n
        names: dict[str, list[int]] = {}
        for j, nm in enumerate(tuple(getattr(a, "poi_name", ()) or ())):
            key = _norm(nm)
            if len(key) >= NAME_MIN_CHARS:
                names.setdefault(key, []).append(j)
        self._names = {k: tuple(v) for k, v in names.items()}
        self._names_by_len = sorted(self._names, key=lambda s: (-len(s), s))
        self._cat_words = sorted(CATEGORY_WORDS, key=lambda e: (-len(e[0]), e[0]))
        self._cat_exact = {w: (c, s) for w, c, s in CATEGORY_WORDS}
        self._cat_mask_cache: dict[str, np.ndarray] = {}
        self._buyable = np.fromiter(
            (c in BUYABLE_CATS or c in SYNTHETIC_BUYABLE_CATS for c in self._cat),
            dtype=bool, count=n,
        )
        # セル → POI(CSR)
        cell = np.asarray(self.world.pois.cell, dtype=np.int64)
        order = np.argsort(cell, kind="stable")
        self._by_cell = order
        n_cells = int(self.world.n_cells)
        counts = np.bincount(cell[(cell >= 0) & (cell < n_cells)], minlength=n_cells)
        self._off = np.zeros(n_cells + 1, dtype=np.int64)
        np.cumsum(counts, out=self._off[1:])
        self._skip = int(np.count_nonzero(cell < 0))  # 場外(-1)の POI は先頭に並ぶ

    # ------------------------------------------------------------------ 対象欄の読み
    def _category_mask(self, word: str) -> np.ndarray:
        m = self._cat_mask_cache.get(word)
        if m is None:
            cats, subs = self._cat_exact[word]
            m = np.fromiter(
                ((c in cats) or (s in subs) for c, s in zip(self._cat, self._sub)),
                dtype=bool, count=len(self._cat),
            )
            self._cat_mask_cache[word] = m
        return m

    def _match_name(self, token: str) -> tuple[int, ...] | None:
        hit = self._names.get(token)
        if hit is not None:
            return hit
        for suf in _SUFFIXES:
            if token.endswith(suf) and token[: -len(suf)] in self._names:
                return self._names[token[: -len(suf)]]
        if len(token) < NAME_MIN_CHARS:
            return None
        for name in self._names_by_len:  # 名 ⊂ 入力(最長の名)
            if name in token:
                return self._names[name]
        best: str | None = None  # 入力 ⊂ 名(最短の名・同長は名の辞書順)
        for name in self._names_by_len:
            if token in name and (best is None or (len(name), name) < (len(best), best)):
                best = name
        return None if best is None else self._names[best]

    def classify(self, target: Any) -> tuple[str, str, tuple[int, ...], str]:
        """対象(``llm.contract.Target`` か ``None``)→ ``(種類, 文字列, 名指しの POI, カテゴリ語)``。"""
        if target is None:
            return KIND_NONE, "", (), ""
        kind = getattr(getattr(target, "kind", None), "name", "NONE")
        raw = str(getattr(target, "raw", "") or "")
        if kind not in ("ITEM_CATEGORY", "STATION_OR_VEHICLE"):
            return KIND_NONE, _norm(raw) if kind != "NONE" else "", (), ""
        token = _norm(raw)
        if not token:
            return KIND_NONE, "", (), ""
        if token in GENERIC_WORDS:                             # (a0) 総称語 → なし
            return KIND_NONE, token, (), ""
        if token in self._cat_exact:                          # (a) カテゴリ語そのもの
            return KIND_CATEGORY, token, (), token
        m = _ID_FORM.match(token)                              # (b) 合成名(cat+索引)
        if m:
            j = int(m.group(2))
            if 0 <= j < len(self._cat) and self._cat[j] == m.group(1):
                return KIND_NAMED, token, (j,), ""
        named = self._match_name(token)                        # (c) POI 名
        if named:
            return KIND_NAMED, token, named, ""
        for w, _c, _s in self._cat_words:                      # (d) カテゴリ語を含む
            if w in token:
                return KIND_CATEGORY, token, (), w
        return KIND_NONE, token, (), ""                         # (e)

    # ------------------------------------------------------------------ 候補 → 選び手
    def _no_candidate(self, kind: str, reason: str) -> None:
        self.stats[f"no_candidate:{reason}"] += 1
        self.stats[f"no_candidate_by_kind:{kind}:{reason}"] += 1

    def pois_in_cell(self, cell: int) -> np.ndarray:
        if cell < 0 or cell >= self._off.size - 1:
            return np.zeros(0, dtype=np.int64)
        lo, hi = int(self._off[cell]), int(self._off[cell + 1])
        return np.sort(self._by_cell[self._skip + lo : self._skip + hi])

    def _order(self, cand: np.ndarray) -> np.ndarray:
        """既定の選び手と同じ並び(可視の降順 → 索引)。代表の 1 件を決めるのに使う。"""
        vis = np.asarray(self.world.poi_visibility, dtype=np.int64)[cand]
        return cand[np.lexsort((cand, -vis))]

    def resolve(
        self,
        agents: Any,
        tick: int,
        agent_ids: np.ndarray,
        action_code: np.ndarray,
        targets: Sequence[Any] | None,
        *,
        is_eat: np.ndarray,
        is_buy_like: np.ndarray,
    ) -> np.ndarray:
        """購入/食事/並ぶの体 → 対象 POI(候補 0 は理由どおりの代表か ``-1``)。

        Args:
            agent_ids / action_code: その tick の intent の体と行為コード(同じ長さ)。
            targets: 体ごとの対象(``Target`` か ``None``)。``None`` なら全員「なし」。
            is_eat: 食事の行(候補=``eatery_mask``)。
            is_buy_like: 購入と並ぶの行(候補=``BUYABLE_CATS`` の POI)。

        逐次ループ宣言(P4): **購入/食事/並ぶの呼の数**ぶん(tick あたり数件〜数十件)。
        """
        a = np.asarray(agent_ids, dtype=np.int64)
        out = np.full(a.size, -1, dtype=np.int64)
        rows = np.flatnonzero(np.asarray(is_eat, dtype=bool) | np.asarray(is_buy_like, dtype=bool))
        if rows.size == 0:
            return out
        w = self.world
        open_now = np.asarray(w.open_mask(int(tick)), dtype=bool)
        stock_ok = np.asarray(w.pois.stock) > 0
        eatery = np.asarray(w.eatery_mask, dtype=bool)
        vis_all = np.asarray(w.poi_visibility, dtype=np.int64)
        cell_dist = w.assets.cell_dist
        poi_cell = np.asarray(w.pois.cell, dtype=np.int64)
        reg = agents.registry
        for k in rows.tolist():  # 逐次: 購入/食事/並ぶの行
            aid = int(a[k])
            cell = int(reg.cell[aid])
            eat = bool(is_eat[k])
            tg = None if targets is None else targets[k]
            kind, text, named, cat_word = self.classify(tg)
            self.stats[f"attempts:{kind}"] += 1
            base = self.pois_in_cell(cell)
            if kind == KIND_NAMED:
                cand_all = base[np.isin(base, np.asarray(named, dtype=np.int64))]
                if cand_all.size == 0:
                    self._no_candidate(kind, "named_out_of_cell")
                    continue
            else:
                cand_all = base
                if kind == KIND_CATEGORY:
                    cand_all = cand_all[self._category_mask(cat_word)[cand_all]]
            if eat:
                cand_all = cand_all[eatery[cand_all]]
            else:  # 購入/並ぶ: 店舗系 cat だけ(Q12)
                cand_all = cand_all[self._buyable[cand_all]]
            if cand_all.size == 0:
                self._no_candidate(kind, "not_in_eatery" if eat else "bad_target")
                continue
            is_open = cand_all[open_now[cand_all]]
            if is_open.size == 0:
                self._no_candidate(kind, "closed")
                out[k] = int(self._order(cand_all)[0])
                continue
            if eat:
                cands = is_open
            else:  # 購入/並ぶ: 飲食店以外は棚在庫が要る(並ぶ→食事は在庫を見ない)
                cands = is_open[stock_ok[is_open] | eatery[is_open]]
                if cands.size == 0:
                    self._no_candidate(kind, "out_of_stock")
                    out[k] = int(self._order(is_open)[0])
                    continue
            ctx = ChoiceContext(
                agent_id=aid,
                tick=int(tick),
                cell=cell,
                node=int(reg.node[aid]),
                action_code=int(action_code[k]),
                target_kind=kind,
                target_text=text,
                hunger=int(reg.hunger[aid]),
                visibility=vis_all[cands],
                distance_m=np.asarray(cell_dist[cell, poi_cell[cands]], dtype=np.float64),
            )
            p = np.asarray(self.chooser.probs(cands, ctx), dtype=np.float64)
            if p.shape != cands.shape:
                raise ValueError("chooser.probs の長さが候補と違う")
            out[k] = int(cands[draw_index(p, self.seed, int(tick), aid)])
            self.stats[f"resolved:{kind}"] += 1
            self.stats["decisions"] += 1
            self.entropy_sum += entropy_bits(p)
        return out


def resolution_summary(stats: Counter, entropy_sum: float) -> dict[str, Any]:
    """計数 → manifest ``target_resolution`` の形((i)〜(iv)+エントロピーの平均)。"""
    decisions = int(stats.get("decisions", 0))
    return {
        "i_named": int(stats.get("resolved:named", 0)),
        "ii_category": int(stats.get("resolved:category", 0)),
        "iii_none": int(stats.get("resolved:none", 0)),
        "iv_no_candidate": {r: int(stats.get(f"no_candidate:{r}", 0)) for r in NO_CANDIDATE_REASONS},
        "attempts": {k: int(stats.get(f"attempts:{k}", 0)) for k in (KIND_NAMED, KIND_CATEGORY, KIND_NONE)},
        # (iv) を対象の種類で割った内訳(名指し/カテゴリ/なし × 理由)
        "iv_by_kind": {
            k: {r: int(stats.get(f"no_candidate_by_kind:{k}:{r}", 0)) for r in NO_CANDIDATE_REASONS}
            for k in (KIND_NAMED, KIND_CATEGORY, KIND_NONE)
        },
        "chooser_entropy_mean_bits": round(entropy_sum / decisions, 6) if decisions else 0.0,
    }
