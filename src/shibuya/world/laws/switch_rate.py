"""engine.rate_rules — 率の形の規則を外す切替口(指示書 11-01 段 2 の 3・4・回答 11-01 §2・§3・小さな版上げ 1 回分)。

回答 11-01 §2(A1-2 案 a): 人や組織の判断で決まるべき量は規則で決めない。まだ判断の口が無い過程は「無い」と宣言する。
集計の量(率)が世界を駆動することは認めない。本モジュールは、率の形で入っていた規則 9 件をまとめて既定で外す切替口を持つ
(棚卸し ``docs/reference/decision-inventory-2026-10-31.md`` §1 の #2・#3・#10・#22・#42・#83・#99・#101・#105)。

| 名 | 外したもの(棚卸しの行) | 外した後の宣言 |
|---|---|---|
| ``attendance`` | 出勤率のくじ E6(#2・``--attendance-rate``) | 全員出勤(判断モデルの口ができるまで) |
| ``event_injection`` | 催しの 18 時の 200 人注入と 21 時の退出(#10) | 催しの人の注入は無い(会場 3 セルの開催は残す) |
| ``arrival_spread`` | E8 到着を E1 便の ±8 便に散らす(#3) | 全員が間に合う最も遅い便(E1)に乗る |
| ``board_accept`` | 乗車の受け入れ確率(混雑率 150〜200% で 1.0→0.7・#22) | 200% の上限だけ物理として残す(上限までは全員乗る) |
| ``litter`` | ポイ捨て 0.05 g/人/刻み(#42) | ポイ捨ては無い |
| ``leftover_waste`` | 05:00 の売れ残りの廃棄率(#99) | 売れ残りの廃棄は無い(店の仕事の腕 duties を既定にするまで) |
| ``parcels`` | 宅配の区按分 27,000 個/日(#105) | 宅配は無い(W2 は錨に残す) |
| ``collapse`` | 倒れる率 1 万体あたり 1 日 3.0 件のポアソン(#83) | 体の式ができるまで倒れる人は無い(W3 は錨に残す) |
| ``calvo`` | 価格の改定確率(Calvo・#101) | 結線しない=価格は固定(``economy.pricing`` はエンジンから呼ばれていない) |

腕: ランはいつも既定 ``off``=上の 8 件を外した状態(``calvo`` は前から結線していない)。〔第347 止めた切替口の削除〕切替口
``--rate-rules {off,legacy}``(環境変数 ``SHIBUYA_RATE_RULES``)は消した(回答 10-13b §0-6・返事その 8 §1-1)。環境変数を与えると
読み込みで止まり、ランの入口(組み立ての最初)でも止まる(一覧は ``foundation.arms.removed``)。旧値の再現は安定版のタグ
``stable-v2-before-switch-removal-347``。``legacy``(版上げの前の値)は部品の口(過程の引数 ``rate_rules``)としてだけ残る=部品の
単体試験の基準の口(ランの口からは選べない=返事その 8 §1-10)。出勤率のくじは ``legacy`` でも戻らない(くじの道ごと消した=旧の
既定 1.0 は全員出勤なので旧値は同じ)。腕の名と外した印と件数は manifest の ``rate_rules`` と、状態のファイルの見出しの
``rate_rules``(off のランだけ書く=見出しに無い状態のファイルは legacy=版上げの前のラン=再開できない)に出る。

計器(指示書の 10): manifest の ``rate_rules.removed`` に規則ごとの ``rate_rule_<名>_removed``(1=外した・0=旧道で動いている)、
``rate_rules.counts`` に旧道の件数(off のランでは 0 のはず=外したことの確かめ)。件数の出どころは各過程の ``counters()``
(``rail.left_behind_by_rate``・``large_event.arrived``・``street_cleaning.litter_generated_g``・``waste.to_bin_rows``・
``last_mile.delivered``・``salient.collapse``・計画実行層の ``spread_moved``)。

逐次ループ宣言(P4): なし(組み立てで 1 回読む・ランの終わりに 1 回数える)。
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from shibuya.foundation.arms import removed as _RSW

__all__ = [
    "MODE_OFF", "MODE_LEGACY", "MODES", "DEFAULT_MODE", "SCHEMA", "RULES", "REMOVED_RULES", "ALWAYS_REMOVED",
    "ENV_REMOVED", "resolve", "is_legacy", "removed_flags", "manifest_fields", "header_fields", "check_resume",
    "WASTE_BAND_NA",
]

MODE_OFF: Final[str] = "off"
MODE_LEGACY: Final[str] = "legacy"
MODES: Final[tuple[str, ...]] = (MODE_OFF, MODE_LEGACY)
#: 既定(11-01 段 2 の 4)=ランの腕。``legacy`` は部品の口だけ(〔第347〕ランの切替口は消した)。
DEFAULT_MODE: Final[str] = MODE_OFF
#: manifest の ``rate_rules`` の値の形の版(欄の意味を変えたら上げる)。
SCHEMA: Final[str] = "shibuya.rate_rules/1"

#: 外した規則の名(manifest の並びの順)。
RULES: Final[tuple[str, ...]] = (
    "attendance", "event_injection", "arrival_spread", "board_accept", "litter", "leftover_waste", "parcels",
    "collapse", "calvo",
)
#: 〔検収 M1〕腕 off の店の廃棄の帯の判定=非該当の理由(帯は外した #99 の静的な期待=比べる相手が無い・値は残す)。
WASTE_BAND_NA: Final[str] = "非該当(売れ残りの廃棄率を外した=11-01 §2)"

#: 旧道でも戻らない規則(出勤率のくじは道ごと消した・Calvo は前から結線していない)。
ALWAYS_REMOVED: Final[frozenset[str]] = frozenset({"attendance", "calvo"})

#: 規則ごとの宣言(棚卸しの行・外した後の文・錨に残す系)。manifest の ``rate_rules.rules`` に写す。
REMOVED_RULES: Final[Mapping[str, Mapping[str, str]]] = {
    "attendance": {"inventory": "#2", "declared": "全員出勤(判断モデルの口ができるまで)", "anchor_kept": ""},
    "event_injection": {"inventory": "#10", "declared": "催しの人の注入は無い(会場の開催は残す・催しの情報を外の人へ届けるのは段 3)",
                        "anchor_kept": "D1′・D4′"},
    "arrival_spread": {"inventory": "#3", "declared": "全員が間に合う最も遅い便(E1)に乗る", "anchor_kept": ""},
    "board_accept": {"inventory": "#22", "declared": "200% の上限だけ物理として残す(上限までは全員乗る)", "anchor_kept": "D10′"},
    "litter": {"inventory": "#42", "declared": "ポイ捨ては無い", "anchor_kept": "W1"},
    "leftover_waste": {"inventory": "#99", "declared": "売れ残りの廃棄は無い(店の仕事の腕 duties を既定にするまで)",
                       "anchor_kept": "W1"},
    "parcels": {"inventory": "#105", "declared": "宅配は無い", "anchor_kept": "W2"},
    "collapse": {"inventory": "#83", "declared": "体の式ができるまで倒れる人は無い(出動の過程は残す=発火しない)",
                 "anchor_kept": "W3"},
    "calvo": {"inventory": "#101", "declared": "価格は固定(価格の改定確率は結線しない)", "anchor_kept": "E7"},
}

#: 〔第347 止めた切替口の削除〕消した切替口の環境変数(与えると読み込みで止まる=ランの入口の組み立ての最初でも止まる)。
ENV_REMOVED: Final[str] = "SHIBUYA_RATE_RULES"
_RSW.stop_if_set(ENV_REMOVED)  # 一覧と止める文は foundation.arms.removed


def resolve(mode: str | None) -> str:
    """過程の引数の腕(``None``=既定 off。〔第347〕ランの切替口は消した)を名に直す(名の誤りは止める)。"""
    m = DEFAULT_MODE if mode is None else str(mode)
    if m not in MODES:
        raise ValueError(f"rate_rules は {MODES} のどれか(いま {m!r})")
    return m


def is_legacy(mode: str | None = None) -> bool:
    """``mode``(省略=既定 off)が旧道(率の形の規則を動かす)か。"""
    return resolve(mode) == MODE_LEGACY


def removed_flags(mode: str | None = None) -> dict[str, int]:
    """規則ごとの ``rate_rule_<名>_removed``(1=外した・0=旧道)。腕だけで決まる印(設定)。

    実際に動いた件数は :func:`manifest_fields` の ``counts``(観測)。倒れる率の部品の口(実行器の ``salient_rate_per_10k``・
    ``SalientProcess`` の ``rate_per_10k_per_day``)は旧道でだけ効く(〔検収 L3〕腕 off では無視=印が 1 のとき
    ``counts.collapse_events`` は常に 0)。〔第347〕``run_day`` の同じ名の試験の口は None 以外で止める(消した)。
    """
    legacy = is_legacy(mode)
    return {f"rate_rule_{r}_removed": int(r in ALWAYS_REMOVED or not legacy) for r in RULES}


def _counts(runner: Any, presence: Any) -> dict[str, Any]:
    """旧道の件数(off のランでは 0 のはず)。過程の無いランは ``None``。"""
    pc = runner.counters() if runner is not None else {}
    prc = presence.counters() if presence is not None else {}

    def _g(d: Mapping[str, float], k: str) -> Any:
        return None if k not in d else (int(d[k]) if float(d[k]).is_integer() else float(d[k]))

    return {
        "attendance_absent": _g(prc, "absent"),
        "event_injection_arrived": _g(pc, "large_event.arrived"),
        "arrival_spread_moved": _g(prc, "spread_moved"),
        "board_accept_refused": _g(pc, "rail.left_behind_by_rate"),
        "litter_generated_g": _g(pc, "street_cleaning.litter_generated_g"),
        "leftover_waste_bin_rows": _g(pc, "waste.to_bin_rows"),
        "parcels_delivered": _g(pc, "last_mile.delivered"),
        "collapse_events": _g(pc, "salient.collapse"),
        "collapse_rate_per_10k": _g(pc, "salient.collapse_rate_per_10k"),
        "calvo_draws": 0,
    }


def manifest_fields(mode: str, runner: Any = None, presence: Any = None) -> dict[str, Any]:
    """manifest の ``rate_rules``(設定=形の版・腕・規則の宣言・外した印/観測=旧道の件数)。"""
    return {
        "schema": SCHEMA,
        "mode": resolve(mode),
        "rules": {k: dict(v) for k, v in REMOVED_RULES.items()},
        "removed": removed_flags(mode),
        "counts": _counts(runner, presence),
    }


def header_fields(mode: str) -> dict[str, Any] | None:
    """状態のファイルの見出しの ``rate_rules``(legacy のランは書かない=None=版上げの前の見出しのまま)。"""
    return {"mode": MODE_OFF} if str(mode) == MODE_OFF else None


def check_resume(saved: Any) -> None:
    """再開のときに、保存したランの見出しの ``rate_rules``(無ければ legacy=版上げの前のラン)が既定の off かを確かめる
    (違えば止める)。〔第347〕切替口を消したので、今の腕はいつも既定。"""
    s = saved if isinstance(saved, Mapping) else {}
    s_mode = str(s.get("mode", MODE_LEGACY))
    if s_mode != DEFAULT_MODE:
        raise ValueError(f"再開の率の規則の腕が親と違う(親 {s_mode}・今 {DEFAULT_MODE})=旧値の切替口 --rate-rules legacy"
                         f"(環境変数 {ENV_REMOVED})は消した(安定版のタグ {_RSW.tag_of(ENV_REMOVED)} で回す)")
