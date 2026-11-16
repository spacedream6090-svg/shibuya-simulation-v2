"""engine.absent_processes — 「無い」と宣言した世界過程 5 件を止める切替口(指示書 11-02 返事その 2 §1 #7・小さな版上げ 1 回分)。

決定(11-02r/§1 #7): まだ動いている「無い」の過程 5 件(ごみ収集・街路の清掃・道路工事・救急と警察・電気と水)は次の小さな
版上げで外す。計器で 5 件が「止めた」側へ移ることを確かめる。街路にごみが残る・倒れた人が運ばれないのは正しい不合格。
宣言の正は ``world/processes/absent.py``(主体が居ない過程=回答 11-01 §2・§10-3)。本モジュールはエンジンの側の切替だけを持つ。

| 名 | 過程(実行器の名・台帳の id) | 止めたもの | 宣言(absent の id) |
|---|---|---|---|
| ``waste_collection`` | ``waste``・``waste_collection`` | 06〜10 時のセル順の収集(店のビン → 範囲の外) | ``absent.waste_collection`` |
| ``street_cleaning`` | ``street_cleaning``・``street_cleaning`` | 05〜07・13〜15 時の掃除の巡回(8 セルずつ) | ``absent.street_cleaning`` |
| ``road_works`` | ``road_works``・``road_works_occupancy`` | 毎晩 6 辺の占用(22〜05 時) | ``absent.road_works`` |
| ``dispatch`` | ``dispatch``・``public_service_dispatch`` | 通報を受けた出動と到着(倒れた人は運ばれない) | ``absent.public_service_dispatch`` |
| ``infra`` | ``infra``・``infra_daily_load`` | 人数 × 原単位の電気と水の負荷の集計 | ``absent.power_water`` |

止めないもの: 同じ過程の中の別の判断=世帯の消費(#41・11-02r §1 #8 で残す)・腕 ``--duties arm`` の担当の体の廃棄・
売れ残りの廃棄率とポイ捨て(``engine.rate_rules`` の腕が決める)・倒れる事象そのもの(``rate_rules`` の ``collapse``)。
納品(``delivery_inbound``)は止めない(E5 と気象の文と一緒に次の版上げ)。

腕: ランはいつも既定 ``stopped``=上の 5 件を止めた状態。〔第347 止めた切替口の削除〕切替口 ``--absent-processes
{stopped,legacy}``(環境変数 ``SHIBUYA_ABSENT_PROCESSES``)は消した(回答 10-13b §0-6・返事その 8 §1-1)。環境変数を与えると
読み込みで止まり、ランの入口(組み立ての最初)でも止まる(一覧は ``foundation.arms.removed``)。旧値の再現は安定版のタグ
``stable-v2-before-switch-removal-347``。``legacy``(版上げの前の値)は部品の口(過程の引数 ``absent_processes``)としてだけ残る=
部品の単体試験の基準の口(ランの口からは選べない=返事その 8 §1-10)。腕の名と止めた印と件数は manifest の ``absent_processes``
と、状態のファイルの見出しの ``absent_processes``(stopped のランだけ書く=見出しに無い状態のファイルは legacy=版上げの前の
ラン=再開できない)に出る。

計器: manifest の ``absent_processes.stopped`` に過程ごとの ``absent_<名>_stopped``(1=止めた・0=旧道で動く)、
``absent_processes.counts`` に旧道の件数(stopped のランでは 0 のはず=止めたことの確かめ)。件数の出どころは各過程の
``counters()``(``waste.stops``・``waste.collected_g``・``street_cleaning.swept_cells``・``road_works.started``・
``dispatch.dispatched``・``infra.power_kwh_day``)。正しい不合格の計器(11-02r #7「街路にごみが残る・倒れた人が運ばれない」)
として、街路に残るごみ ``street_cleaning.litter_now_g`` と倒れた数 ``salient.collapse`` も並べる(どちらも率の規則の旧道=
部品の口 ``rate_rules="legacy"`` でだけ生じる=既定のランでは 0。〔第347〕ランの切替口 ``--rate-rules legacy`` は消した)。

時間の方針(11-02r §2-2): 本モジュールは時刻を持たない(腕の名だけ)。

逐次ループ宣言(P4): なし(組み立てで 1 回読む・ランの終わりに 1 回数える)。
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from shibuya.foundation.arms import removed as _RSW

__all__ = [
    "MODE_STOPPED", "MODE_LEGACY", "MODES", "DEFAULT_MODE", "SCHEMA", "PROCESSES", "STOPPED_PROCESSES",
    "ENV_REMOVED", "resolve", "is_legacy", "stopped_flags", "manifest_fields", "header_fields", "check_resume",
]

MODE_STOPPED: Final[str] = "stopped"
MODE_LEGACY: Final[str] = "legacy"
MODES: Final[tuple[str, ...]] = (MODE_STOPPED, MODE_LEGACY)
#: 既定(11-02r §1 #7)=ランの腕。``legacy`` は部品の口だけ(〔第347〕ランの切替口は消した)。
DEFAULT_MODE: Final[str] = MODE_STOPPED
#: manifest の ``absent_processes`` の値の形の版(欄の意味を変えたら上げる)。
SCHEMA: Final[str] = "shibuya.absent_processes/1"

#: 止めた過程の名(manifest の並びの順)。
PROCESSES: Final[tuple[str, ...]] = ("waste_collection", "street_cleaning", "road_works", "dispatch", "infra")

#: 過程ごとの宣言(実行器の名・台帳の id・absent の id・止めたもの・止めないもの・検証に残す錨=absent の ``keeps_anchor``)。
#: manifest の ``absent_processes.processes``。
STOPPED_PROCESSES: Final[Mapping[str, Mapping[str, str]]] = {
    "waste_collection": {"runner_key": "waste", "world_process": "waste_collection", "absent": "absent.waste_collection",
                         "stopped": "06〜10 時のセル順の収集(店のビン → 範囲の外)",
                         "kept": "世帯の消費(#41)・担当の体の廃棄(腕 duties)・売れ残りの廃棄率(rate_rules)",
                         "anchor_kept": ""},
    "street_cleaning": {"runner_key": "street_cleaning", "world_process": "street_cleaning",
                        "absent": "absent.street_cleaning", "stopped": "掃除の巡回(05〜07・13〜15 時に 8 セルずつ)",
                        "kept": "ポイ捨て(rate_rules の litter=既定は無い)", "anchor_kept": ""},
    "road_works": {"runner_key": "road_works", "world_process": "road_works_occupancy", "absent": "absent.road_works",
                   "stopped": "毎晩 6 辺の占用(22〜05 時)", "kept": "その日の工事の辺の抽選(日の鍵の counter=記録しない)",
                   "anchor_kept": ""},
    "dispatch": {"runner_key": "dispatch", "world_process": "public_service_dispatch",
                 "absent": "absent.public_service_dispatch", "stopped": "通報を受けた出動と到着(倒れた人は運ばれない)",
                 "kept": "倒れる事象そのもの(rate_rules の collapse=既定は無い)", "anchor_kept": "W3"},
    "infra": {"runner_key": "infra", "world_process": "infra_daily_load", "absent": "absent.power_water",
              "stopped": "人数 × 原単位の電気と水の負荷の集計", "kept": "", "anchor_kept": "W5"},
}

#: 〔第347 止めた切替口の削除〕消した切替口の環境変数(与えると読み込みで止まる=ランの入口の組み立ての最初でも止まる)。
ENV_REMOVED: Final[str] = "SHIBUYA_ABSENT_PROCESSES"
_RSW.stop_if_set(ENV_REMOVED)  # 一覧と止める文は foundation.arms.removed


def resolve(mode: str | None) -> str:
    """過程の引数の腕(``None``=既定 stopped。〔第347〕ランの切替口は消した)を名に直す(名の誤りは止める)。"""
    m = DEFAULT_MODE if mode is None else str(mode)
    if m not in MODES:
        raise ValueError(f"absent_processes は {MODES} のどれか(いま {m!r})")
    return m


def is_legacy(mode: str | None = None) -> bool:
    """``mode``(省略=既定 stopped)が旧道(5 件の過程を動かす)か。"""
    return resolve(mode) == MODE_LEGACY


def stopped_flags(mode: str | None = None) -> dict[str, int]:
    """過程ごとの ``absent_<名>_stopped``(1=止めた・0=旧道)。腕だけで決まる印(設定)。"""
    stopped = not is_legacy(mode)
    return {f"absent_{p}_stopped": int(stopped) for p in PROCESSES}


def _counts(runner: Any) -> dict[str, Any]:
    """旧道の件数。stopped のランでは、正しい不合格の 2 欄(``street_litter_now_g``・``collapse_events``)を除き 0。
    この 2 欄は率の規則の旧道(部品の口 ``rate_rules="legacy"``)と組むと 0 にならない(街路に残るごみ・倒れた数=止めた側で
    増える)。
    過程の無いランは ``None``。"""
    pc = runner.counters() if runner is not None else {}

    def _g(k: str) -> Any:
        return None if k not in pc else (int(pc[k]) if float(pc[k]).is_integer() else float(pc[k]))

    return {
        "waste_stops": _g("waste.stops"),
        "waste_collected_g": _g("waste.collected_g"),
        "street_swept_cells": _g("street_cleaning.swept_cells"),
        "street_litter_now_g": _g("street_cleaning.litter_now_g"),
        "road_works_started": _g("road_works.started"),
        "dispatch_dispatched": _g("dispatch.dispatched"),
        "collapse_events": _g("salient.collapse"),
        "infra_power_kwh_day": _g("infra.power_kwh_day"),
        "infra_water_m3_day": _g("infra.water_m3_day"),
    }


def manifest_fields(mode: str, runner: Any = None) -> dict[str, Any]:
    """manifest の ``absent_processes``(設定=形の版・腕・過程の宣言・止めた印/観測=旧道の件数)。"""
    return {
        "schema": SCHEMA,
        "mode": resolve(mode),
        "processes": {k: dict(v) for k, v in STOPPED_PROCESSES.items()},
        "stopped": stopped_flags(mode),
        "counts": _counts(runner),
    }


def header_fields(mode: str) -> dict[str, Any] | None:
    """状態のファイルの見出しの ``absent_processes``(legacy のランは書かない=None=版上げの前の見出しのまま)。"""
    return {"mode": MODE_STOPPED} if str(mode) == MODE_STOPPED else None


def check_resume(saved: Any) -> None:
    """再開のときに、保存したランの見出しの ``absent_processes``(無ければ legacy=版上げの前のラン)が既定の stopped かを
    確かめる(違えば止める)。〔第347〕切替口を消したので、今の腕はいつも既定。"""
    s = saved if isinstance(saved, Mapping) else {}
    s_mode = str(s.get("mode", MODE_LEGACY))
    if s_mode != DEFAULT_MODE:
        raise ValueError(f"再開の「無い」の過程の腕が親と違う(親 {s_mode}・今 {DEFAULT_MODE})=旧値の切替口 "
                         f"--absent-processes legacy(環境変数 {ENV_REMOVED})は消した(安定版のタグ "
                         f"{_RSW.tag_of(ENV_REMOVED)} で回す)")
