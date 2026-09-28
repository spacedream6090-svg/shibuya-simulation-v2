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

**段 2b(行き先を対象欄から・D-112 ②)** :meth:`TargetResolver.resolve_move`: 移動の対象欄の解決順=
**セル ID**(「セル」接頭辞つきも・``llm.contract.parse_target`` の CELL)→ **名指し**(POI 名・目印名 →
その POI のセル。同名が複数なら選び手=最寄り)→ **カテゴリ語**(現在セル → W8 で見えている POI →
``cell_dist`` の昇順の近いセル :data:`MOVE_SEARCH_RADIUS_CELLS` 個まで、の順に最初に営業中の候補がある所
→ 選び手で 1 件 → そのセル)→ **なし/説明語**(``-1``=従来の既定=職場/自宅のうち今いない方を**保つ**・
宣言)。解決できない対象(存在しないセル ID・近傍に候補の無いカテゴリ)は ``MOVE_BAD_TARGET``
(``resolve._apply_move`` が ``BAD_TARGET``)=「経路なし」(``UNREACHABLE``)と分ける。
計数は manifest ``move_resolution``。**段 2c の Q18**: 対象欄が**人 ID**(``P-17``)なら、その人の
**いまのセル**へ(自分なら今いるセル=動かない・域外/存在しない人は ``MOVE_BAD_TARGET``)。
2 m の「近づく」(C9b・対象ヒント approach)は従来どおり別の経路。

**段 2c(意図の保持・D-112 ①・D-114 案 A)** :meth:`TargetResolver.resolve` に ``intent_out`` を渡すと、
購入/食事/並ぶの対象が**現在セルに無く解決できる**行を「意図」として返す(対象 ``-1`` のまま・
``intent_out[行] = (POI, IntentKind)``): (i) **名指し**が現在セルに無い → 名指しの店のうち**意図に合い**
(食事=飲食店・購入/並ぶ=店舗系)**いまのセルから見える**(W8=B2 の可視物)もの → **営業中 ∧(購入は)
在庫あり**(2a の候補の絞り込みと同じ・親決定 Q21)を選び手で 1 件。見える店が全部閉店なら歩かずに
その代表 1 件を返す(``CLOSED`` を即時に)・開いているが全部在庫切れなら同じく ``OUT_OF_STOCK``
(着いたときに閉まっていた=途中で閉店、だけが到着時の ``CLOSED``)/ (ii) **カテゴリ語**で現在セルに営業中の
候補(購入は在庫も)が無い → 2b と同じ近傍探索(W8 で見えている POI → ``cell_dist`` の近いセル R 個)で
営業中・意図に合う・(購入は)在庫ありの店 → 選び手で 1 件。「なし」の対象は意図にしない(どこへ
行くかを言っていない)。``intent_out`` を渡さない呼び方(既定)は段 2a/2b と 1 バイトも変わらない。

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

from shibuya.agents.state import IntentKind
from shibuya.engine.chooser import ChoiceContext, Chooser, draw_index, entropy_bits
from shibuya.engine.commit import WANDER_BAD_TARGET
from shibuya.world.assets import BAND_CODES, SYNTHETIC_POI_CATS
from shibuya.world.state import LANDMARK_CATS

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
    "MOVE_SEARCH_RADIUS_CELLS",
    "MOVE_BAD_TARGET",
    "MOVE_DIST_BINS_M",
    "move_resolution_summary",
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


#: 段 2b: カテゴリ語の近傍探索で見る**近いセルの数**(現在セルを除く・``cell_dist`` の昇順・宣言・
#: expedient・``--move-search-radius``)。
MOVE_SEARCH_RADIUS_CELLS: Final[int] = 5
#: 段 2b: 移動の対象が解決できない(存在しないセル ID・近傍に候補の無いカテゴリ)印。
#: ``resolve._apply_move`` が ``BAD_TARGET`` を付ける(「あたり」の域外と同じ値を使う)。
MOVE_BAD_TARGET: Final[int] = WANDER_BAD_TARGET
#: 段 2b: カテゴリで選んだ行き先までの距離の分布の刻み[m](``cell_dist``)。
MOVE_DIST_BINS_M: Final[tuple[int, ...]] = (0, 100, 200, 400, 800)


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
    #: 段 2b: カテゴリ語の近傍探索で見る近いセルの数(:data:`MOVE_SEARCH_RADIUS_CELLS`)。
    move_search_radius: int = MOVE_SEARCH_RADIUS_CELLS
    #: 計数(``resolution_summary`` が manifest の形にする)。
    stats: Counter = field(default_factory=Counter)
    entropy_sum: float = 0.0
    #: 段 2b の計数(``move_resolution_summary`` が manifest の形にする)。
    move_stats: Counter = field(default_factory=Counter)

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
        # 段 2b: セル ID(W2 の place_id=``g{ix}_{iy}_{band}``)→ セル索引
        band_name = {v: k for k, v in BAND_CODES.items()}
        self._cell_of_place = {
            f"g{int(ix)}_{int(iy)}_{band_name.get(int(b), 'GL')}": i
            for i, (ix, iy, b) in enumerate(zip(a.cell_ix, a.cell_iy, a.cell_band))
        }
        self._landmark = np.fromiter((c in LANDMARK_CATS for c in self._cat), dtype=bool, count=n)
        if int(self.move_search_radius) < 0:
            raise ValueError("move_search_radius は 0 以上")

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
        intent_out: dict[int, tuple[int, int]] | None = None,
    ) -> np.ndarray:
        """購入/食事/並ぶの体 → 対象 POI(候補 0 は理由どおりの代表か ``-1``)。

        Args:
            agent_ids / action_code: その tick の intent の体と行為コード(同じ長さ)。
            targets: 体ごとの対象(``Target`` か ``None``)。``None`` なら全員「なし」。
            is_eat: 食事の行(候補=``eatery_mask``)。
            is_buy_like: 購入と並ぶの行(候補=``BUYABLE_CATS`` の POI)。
            intent_out: **段 2c**。渡すと、対象が現在セルに無く解決できる行(名指しの店が
                見えている・カテゴリの店が近傍にある)を ``intent_out[行] = (POI, IntentKind)`` に
                入れ、その行の戻り値は ``-1`` のまま(呼び側が目的地つき移動に変える)。
                ``None``(既定)は段 2a と同じ。

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
            code = int(action_code[k])
            if kind == KIND_NAMED:
                cand_all = base[np.isin(base, np.asarray(named, dtype=np.int64))]
                if cand_all.size == 0:
                    if intent_out is not None:
                        pick, rep_poi, why = self._named_elsewhere(
                            named, cell, eat, aid, tick, text, reg, code, open_now, stock_ok
                        )
                        if pick >= 0:
                            intent_out[k] = (pick, int(IntentKind.POI_NAMED))
                            self.stats["intent:named"] += 1
                            continue
                        if rep_poi >= 0:
                            # Q21: 見える名指しの店が閉店/在庫切れ=歩かずに即時の失敗(代表 1 件)
                            self._no_candidate(kind, why)
                            out[k] = rep_poi
                            continue
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
            elsewhere = intent_out is not None and kind == KIND_CATEGORY
            if cand_all.size == 0:
                if elsewhere and self._category_elsewhere(
                    intent_out, k, cat_word, cell, eat, open_now, stock_ok, eatery, aid, tick,
                    text, reg, code,
                ):
                    continue
                self._no_candidate(kind, "not_in_eatery" if eat else "bad_target")
                continue
            is_open = cand_all[open_now[cand_all]]
            if is_open.size == 0:
                if elsewhere and self._category_elsewhere(
                    intent_out, k, cat_word, cell, eat, open_now, stock_ok, eatery, aid, tick,
                    text, reg, code,
                ):
                    continue
                self._no_candidate(kind, "closed")
                out[k] = int(self._order(cand_all)[0])
                continue
            if eat:
                cands = is_open
            else:  # 購入/並ぶ: 飲食店以外は棚在庫が要る(並ぶ→食事は在庫を見ない)
                cands = is_open[stock_ok[is_open] | eatery[is_open]]
                if cands.size == 0:
                    if elsewhere and self._category_elsewhere(
                        intent_out, k, cat_word, cell, eat, open_now, stock_ok, eatery, aid, tick,
                        text, reg, code,
                    ):
                        continue
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


    # ------------------------------------------------------------------ 段 2c: セル外の対象
    def _named_elsewhere(self, named: Sequence[int], cell: int, eat: bool, aid: int, tick: int,
                         text: str, reg: Any, code: int, open_now: np.ndarray,
                         stock_ok: np.ndarray) -> tuple[int, int, str]:
        """名指しの店が現在セルに無いとき、**意図に合い・見えて・営業中(購入は在庫あり)**の 1 件。

        見える=W8 の可視物(``World.visible_pois(cell)``=B2 の「見えるもの」の材料)。営業中・在庫は
        2a の候補の絞り込みと同じ(親決定 Q21)。落ちた理由を ``named_out_of_cell:*`` に数える。

        Returns:
            ``(選んだ POI, 代表, 理由)``。選べたら ``(POI, -1, "")``。見える店が全部閉店なら
            ``(-1, 代表, "closed")``・全部在庫切れなら ``(-1, 代表, "out_of_stock")``(歩かずに即時の
            失敗)。見えない・意図に合わない・域外は ``(-1, -1, 理由)``(段 2a の ``named_out_of_cell``)。
        """
        w = self.world
        poi_cell = np.asarray(w.pois.cell, dtype=np.int64)
        n_cells = int(w.n_cells)
        cands = np.asarray(named, dtype=np.int64)
        cands = cands[(poi_cell[cands] >= 0) & (poi_cell[cands] < n_cells)]
        if cands.size == 0:
            self.stats["named_out_of_cell:offmap"] += 1
            return -1, -1, "offmap"
        eatery = np.asarray(w.eatery_mask, dtype=bool)
        fit = eatery if eat else self._buyable
        cands = cands[fit[cands]]
        if cands.size == 0:
            self.stats["named_out_of_cell:not_fit"] += 1
            return -1, -1, "not_fit"
        vp, _vn = w.visible_pois(cell)
        cands = cands[np.isin(cands, vp)] if vp.size else cands[:0]
        if cands.size == 0:
            self.stats["named_out_of_cell:not_visible"] += 1
            return -1, -1, "not_visible"
        is_open = cands[open_now[cands]]
        if is_open.size == 0:
            self.stats["named_out_of_cell:closed"] += 1
            return -1, int(self._order(cands)[0]), "closed"
        ok = is_open if eat else is_open[stock_ok[is_open] | eatery[is_open]]
        if ok.size == 0:
            self.stats["named_out_of_cell:out_of_stock"] += 1
            return -1, int(self._order(is_open)[0]), "out_of_stock"
        vis_own = np.asarray(w.poi_visibility, dtype=np.int64)
        return self._pick(ok, vis_own[ok], cell, aid, tick, KIND_NAMED, text, reg, code), -1, ""

    def _category_elsewhere(self, intent_out: dict[int, tuple[int, int]], k: int, cat_word: str,
                            cell: int, eat: bool, open_now: np.ndarray, stock_ok: np.ndarray,
                            eatery: np.ndarray, aid: int, tick: int, text: str, reg: Any,
                            code: int) -> bool:
        """カテゴリの店が現在セルに無い(営業中・意図に合う・在庫)とき、近傍から 1 件選べたら意図にする。"""
        fit = eatery if eat else (self._buyable & (stock_ok | eatery))
        mask = self._category_mask(cat_word) & open_now & fit
        pick, _where = self._nearby_pick(cell, mask, aid, tick, KIND_CATEGORY, text, reg, code)
        if pick < 0:
            self.stats["intent_miss:category_none_nearby"] += 1
            return False
        intent_out[k] = (pick, int(IntentKind.POI_CATEGORY))
        self.stats["intent:category"] += 1
        return True

    def _nearby_pick(self, cell: int, mask: np.ndarray, aid: int, tick: int, kind: str,
                     text: str, reg: Any, code: int) -> tuple[int, str]:
        """段 2b の近傍探索(W8 で見えている POI → ``cell_dist`` の近いセル R 個)の本体。

        Returns:
            ``(POI, "visible"|"nearby")``。見つからなければ ``(-1, "")``。現在セルは見ない
            (呼び側が先に見る)。段 2b の ``resolve_move`` と段 2c の意図が同じ 1 本を使う。
        """
        w = self.world
        vp, vn = w.visible_pois(cell)
        sel = mask[vp] if vp.size else np.zeros(0, dtype=bool)
        if np.any(sel):
            return self._pick(vp[sel], vn[sel], cell, aid, tick, kind, text, reg, code), "visible"
        if self.move_search_radius > 0:
            n_cells = int(w.n_cells)
            vis_own = np.asarray(w.poi_visibility, dtype=np.int64)
            row = np.asarray(w.assets.cell_dist[cell], dtype=np.int64)
            order = np.lexsort((np.arange(n_cells), row))
            order = order[order != cell][: int(self.move_search_radius)]
            for nc in order.tolist():  # 逐次: 近いセル R 個まで
                cands = self.pois_in_cell(int(nc))
                cands = cands[mask[cands]]
                if cands.size:
                    return self._pick(cands, vis_own[cands], cell, aid, tick, kind, text, reg,
                                      code), "nearby"
        return -1, ""

    # ------------------------------------------------------------------ 段 2b: 移動の行き先
    def cell_of_target(self, target: Any) -> int | None:
        """CELL の対象 → セル索引(``None``=CELL でない・``-1``=存在しないセル)。"""
        if target is None or getattr(getattr(target, "kind", None), "name", "") != "CELL":
            return None
        cid = getattr(target, "cell_id", None)
        if cid and str(cid) in self._cell_of_place:            # W2 の place_id(g12_34_GL)
            return int(self._cell_of_place[str(cid)])
        ci = getattr(target, "cell_index", None)               # C-0117 の形=セル索引
        if ci is not None and 0 <= int(ci) < int(self.world.n_cells):
            return int(ci)
        return -1

    def _pick(self, cands: np.ndarray, vis: np.ndarray, cell: int, aid: int, tick: int,
              kind: str, text: str, reg: Any, code: int) -> int:
        dist = np.asarray(
            self.world.assets.cell_dist[cell, np.asarray(self.world.pois.cell)[cands]],
            dtype=np.float64,
        )
        ctx = ChoiceContext(
            agent_id=aid, tick=int(tick), cell=cell, node=int(reg.node[aid]), action_code=code,
            target_kind=kind, target_text=text, hunger=int(reg.hunger[aid]),
            visibility=np.asarray(vis, dtype=np.int64), distance_m=dist,
        )
        p = np.asarray(self.chooser.probs(cands, ctx), dtype=np.float64)
        if p.shape != cands.shape:
            raise ValueError("chooser.probs の長さが候補と違う")
        return int(cands[draw_index(p, self.seed, int(tick), aid)])

    def resolve_move(
        self,
        agents: Any,
        tick: int,
        agent_ids: np.ndarray,
        action_code: np.ndarray,
        targets: Sequence[Any] | None,
        rows: np.ndarray,
    ) -> np.ndarray:
        """移動の行(``rows`` が真)→ 行き先セル(``-1``=従来の既定・``MOVE_BAD_TARGET``=解決不能)。

        逐次ループ宣言(P4): **移動の呼の数**ぶん(近傍探索は 1 呼あたり高々 R+2 セル)。
        """
        a = np.asarray(agent_ids, dtype=np.int64)
        out = np.full(a.size, -1, dtype=np.int64)
        idx = np.flatnonzero(np.asarray(rows, dtype=bool))
        if idx.size == 0:
            return out
        w = self.world
        reg = agents.registry
        open_now = np.asarray(w.open_mask(int(tick)), dtype=bool)
        vis_own = np.asarray(w.poi_visibility, dtype=np.int64)
        poi_cell = np.asarray(w.pois.cell, dtype=np.int64)
        cell_dist = w.assets.cell_dist
        n_cells = int(w.n_cells)
        ms = self.move_stats
        for k in idx.tolist():  # 逐次: 移動の行
            aid = int(a[k])
            cell = int(reg.cell[aid])
            tg = None if targets is None else targets[k]
            code = int(action_code[k])
            if cell < 0:  # 域外の体は従来の既定のまま(行き先の既定は計画・自宅/職場)
                ms["offmap_default"] += 1
                continue
            if tg is not None and getattr(getattr(tg, "kind", None), "name", "") == "PERSON":
                # 段 2c Q18: 人 ID → その人の**いまのセル**(2 m の「近づく」は対象ヒントの経路)
                pid = getattr(tg, "person_id", None)
                pcell = np.asarray(reg.cell)
                if pid is None or not (0 <= int(pid) < pcell.size):
                    ms["bad_target:person_unknown"] += 1
                    out[k] = MOVE_BAD_TARGET
                elif int(pid) == aid:
                    ms["person_self"] += 1
                    out[k] = cell
                elif int(pcell[int(pid)]) < 0:
                    ms["bad_target:person_offmap"] += 1
                    out[k] = MOVE_BAD_TARGET
                else:
                    ms["person"] += 1
                    out[k] = int(pcell[int(pid)])
                continue
            c = self.cell_of_target(tg)
            if c is not None:                                   # セル ID
                if c < 0:
                    ms["bad_target:cell_unknown"] += 1
                    out[k] = MOVE_BAD_TARGET
                else:
                    ms["cell"] += 1
                    out[k] = c
                continue
            kind, text, named, cat_word = self.classify(tg)
            if kind == KIND_NAMED:                              # 名指し(POI 名・目印名)
                cands = np.asarray(named, dtype=np.int64)
                cands = cands[(poi_cell[cands] >= 0) & (poi_cell[cands] < n_cells)]
                if cands.size == 0:
                    ms["bad_target:named_offmap"] += 1
                    out[k] = MOVE_BAD_TARGET
                    continue
                here = cands[poi_cell[cands] == cell]
                pick = int(here[0]) if here.size else self._pick(
                    cands, vis_own[cands], cell, aid, tick, kind, text, reg, code
                )
                ms["named_landmark" if self._landmark[pick] else "named"] += 1
                out[k] = int(poi_cell[pick])
                continue
            if kind == KIND_CATEGORY:                           # カテゴリ語 → 近傍の候補
                mask = self._category_mask(cat_word) & open_now
                base = self.pois_in_cell(cell)
                cands = base[mask[base]]
                if cands.size:
                    ms["category_in_cell"] += 1
                    out[k] = cell
                    continue
                pick, where = self._nearby_pick(cell, mask, aid, tick, kind, text, reg, code)
                if pick >= 0:
                    ms["category_visible" if where == "visible" else "category_nearby"] += 1
                    self._record_dist(int(cell_dist[cell, poi_cell[pick]]))
                    out[k] = int(poi_cell[pick])
                    continue
                ms["bad_target:category_none_nearby"] += 1
                out[k] = MOVE_BAD_TARGET
                continue
            ms["none_default"] += 1                             # なし/説明語 → 従来の既定
        return out

    def _record_dist(self, d: int) -> None:
        bins = MOVE_DIST_BINS_M
        lab = next(
            (f"{lo}-{hi}" for lo, hi in zip(bins, bins[1:]) if lo <= d < hi), f"{bins[-1]}+"
        )
        self.move_stats[f"dist:{lab}"] += 1
        self.move_stats["dist_sum_m"] += int(d)
        self.move_stats["dist_n"] += 1


def move_resolution_summary(ms: Counter, n_bad_target: int = 0, n_unreachable: int = 0) -> dict[str, Any]:
    """段 2b の計数 → manifest ``move_resolution`` の形。"""
    bins = MOVE_DIST_BINS_M
    labels = [f"{lo}-{hi}" for lo, hi in zip(bins, bins[1:])] + [f"{bins[-1]}+"]
    n = int(ms.get("dist_n", 0))
    return {
        "cell": int(ms.get("cell", 0)),
        "named": int(ms.get("named", 0)),
        "named_landmark": int(ms.get("named_landmark", 0)),
        "category_in_cell": int(ms.get("category_in_cell", 0)),
        "category_visible": int(ms.get("category_visible", 0)),
        "category_nearby": int(ms.get("category_nearby", 0)),
        "none_default": int(ms.get("none_default", 0)),
        "offmap_default": int(ms.get("offmap_default", 0)),
        # 段 2c Q18: 人 ID → その人のいまのセル(自分=今いるセル)
        "person": int(ms.get("person", 0)),
        "person_self": int(ms.get("person_self", 0)),
        "bad_target": {
            r: int(ms.get(f"bad_target:{r}", 0))
            for r in ("cell_unknown", "named_offmap", "category_none_nearby",
                      "person_unknown", "person_offmap")
        },
        "category_distance_m": {lab: int(ms.get(f"dist:{lab}", 0)) for lab in labels},
        "category_distance_mean_m": round(int(ms.get("dist_sum_m", 0)) / n, 1) if n else 0.0,
        # resolve._apply_move の結果(移動の行のうち): 対象不正(BAD_TARGET)/ 経路なし(UNREACHABLE)
        "result_bad_target": int(n_bad_target),
        "result_unreachable": int(n_unreachable),
    }


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
        # 段 2c: 対象が現在セルに無く解決できた行(=意図にした)と、名指しがセル外で意図にも
        # ならなかった内訳(域外・意図に合わない・見えない)。意図の層が無いランでは全部 0。
        "v_intent": {
            "named": int(stats.get("intent:named", 0)),
            "category": int(stats.get("intent:category", 0)),
            "category_none_nearby": int(stats.get("intent_miss:category_none_nearby", 0)),
        },
        "named_out_of_cell_detail": {
            r: int(stats.get(f"named_out_of_cell:{r}", 0))
            for r in ("offmap", "not_fit", "not_visible", "closed", "out_of_stock")
        },
    }
