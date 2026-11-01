"""engine.experiment.warmup — 慣らし(CP5-6)の自動判定の規則と parameter の事前登録(第 3 期 3-3b・仮-24・答申 R-117 §4-6)。

決定 10-12 §4-5 CP5-6・PENDING 仮-24。**登録するのは日付ではなく規則**(R-117 §4-6 問い 2 の段 5)。判定そのものは計器
``tools/instruments/warmup_gauge.py``(読むだけ・記録に JSON)がこの規則で行う。エンジンはこの規則を manifest の
``experiment.warmup`` と事前登録の記録(``ensemble.preregister``)に写すだけ(ランの結果は 1 バイトも変えない)。

規則(印: **mechanism**=先例の原典の作法か v2 の既決の規律から導けるもの / **expedient**=先例の無い構成で感度の腕が要るもの):

| 項 | 中身 | 印 |
|---|---|---|
| 方法 | MSER(n, d) = Σ_{i>d}(y_i − Ȳ(n,d))² / (n − d)² の最小の d*(White 1997・Hoad & Robinson 2011) | mechanism |
| 系列 | 本則=**差の系列**(問い 1=開始日から始めたラン A − k 日前から始めて慣れたラン B・問い 2=改変の枝 − A/A の枝)。感度の腕=原系列に当てる(暦と天気で動き続ける=定常に達しないと宣言) | expedient |
| まとめ | 1 バッチ=1 シム日(5 日ずつにはまとめない=日のまとめが 5 個まとめの役) | 周期=mechanism・5 にしない=expedient |
| 複数本 | 本ごとの差を日ごとに平均してから当てる(問い 1 は 5 本以上・問い 2 は 6 対以上) | 平均=mechanism・5 本=expedient・6 対=R-71 |
| 候補 | d ≤ n − 5(最後の 5 バッチは候補にしない=残りの尾が 5 バッチ以上) | mechanism(出所は親未確認=△) |
| 候補の数え方 | 〔検収 §8 (e)・親の判断〕R-117 §4-4 の記述では pymser は候補を n − 3 番目まで(=最後の 2 つを除く)とする。同じ数え方なら「最後の 5 つを除く」は d ≤ n − 6 になり、v2 の d ≤ n − 5(R-117 §4-6)とは **1 つずれる**。v2 は d ≤ n − 5 のまま(宣言・pymser のコードは読んでいない=R-117 の記述による) | 未リサーチ |
| 無効 | d* > n/2 は無効=10% 延ばす(切り上げ・最低 1 日)。3 回無効なら「未収束」と記録して報告 | 後半=mechanism・3 回=expedient |
| 束ね | 慣らしの日数 W = 有効だった指標の慣らしの日数の最大 | 出力ごと=mechanism・最大=expedient |
| 慣らしの日数 | 〔検収 L3〕系列の頭の日(直す前の系列の最初の日)から数えた日数=最初の日 + d* − 頭の日(在庫と累計は流量に直すと最初の日が落ちるので d* + 1) | mechanism |
| 測る期間 | W 以上(全体で 2W 以上) | mechanism |
| 累積 | 累積の系列(累積の平均・最大・最小)は使わない | mechanism |
| 累計 | 〔検収 M1〕ランの頭からの累計(会話の始まりの数 ``conv.opened`` など)は**累計の印**(``kind: counter``)を付けて日ごとの差(その日の数)に直す。印の無い累計の道筋は拒む。最初の記録の日は落とす(累計は再開で引き継ぐ=状態台帳 O91=記録の頭が 0 とは限らない) | 直す=mechanism・最初の日を落とす=expedient |
| 在庫 | 在庫の指標(知り合いの数など)は流量(新しく知った数・忘れた数=計器の側の欄)に直す。総流量の計器が無い間は日ごとの差(純流量)で代える | 直す=mechanism・純流量=expedient |
| 月の周期 | 月の周期の指標(給料日)は慣らしの対象から外し「推移の指標」として報告 | expedient |
| 最低の日数 | 最低 1 週間 | 未リサーチ |
| 問い 1 の先行 | k=28 日(Tocher の週 3〜4 回) | expedient |
| 問い 2 の区間 | 構え=告知(notice.at)〜実行(start)・切り替わり=実行〜新しい日常の始まり(実行の後の差の系列の d*)・新しい日常=d* 〜終わり | 決定 10-12 CP5-6=mechanism |
| 式の文・問いごとの系列の名 | ``statistic``=方法の式の文(mechanism)・``q1.series``/``q2.series``=差の系列の取り方(本則の ``series`` と同じ expedient) | 各行 |

〔検収 L5〕全部の項に印がある(``MARKS`` の鍵=``RULE`` の葉の項・試験が突き合わせる)。3-3b の初めの版にあった問い 2 の細かい刻みの数(刻みの数で 15 分を書いた直書き)は使っていなかったので消した(時間の直書き禁止)。

逐次ループ宣言: なし(定数と指紋)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from shibuya.engine.experiment.form import sha256_hex

__all__ = ["WARMUP_SCHEMA", "RULE", "MARKS", "MARK_VALUES", "rule_items", "rule_record", "rule_sha256"]

WARMUP_SCHEMA: Final[str] = "shibuya.engine.experiment/warmup-rule/1"

#: 慣らしの自動判定の規則と parameter(事前登録の中身=日付ではなく規則)。
RULE: Final[Mapping[str, Any]] = MappingProxyType({
    "method": "MSER",
    "statistic": "sum((y_i - mean_d)^2 for i > d) / (n - d)^2",
    "series": "difference",
    "sensitivity_arm": "raw",
    "batch_days": 1,
    "exclude_last_batches": 5,
    # 〔検収 §8 (e)・親の判断〕候補の数え方の宣言(d ≤ n − 5 のまま・R-117 §4-4 の pymser の数え方とは 1 つずれる)
    "exclude_last_counting": ("d <= n - 5 (tail of at least 5 batches); R-117 §4-4 says pymser takes candidates up to "
                              "n - 3 (drops the last 2), so 'drop the last 5' in that counting would be d <= n - 6 "
                              "(off by one); pymser code not read"),
    "invalid_if_d_over_n": 0.5,
    "extend_fraction": 0.1,
    "extend_min_batches": 1,
    "max_invalid": 3,
    "bundle": "max",
    # 〔検収 L3〕慣らしの日数=系列の頭の日から数えた日数(在庫・累計は流量に直すと最初の日が落ちる=d* + 1)
    "warmup_days": "first_day + d_star - head_day",
    "measure_min": "W",
    "total_min": "2W",
    "cumulative": "reject",
    # 〔検収 M1〕ランの頭からの累計は累計の印(kind: counter)で日ごとの差に直す・印の無い累計の道筋は拒む
    "counter": "daily_difference",
    "counter_unmarked": "reject",
    "counter_first_day": "drop",
    "stock": "flow",
    "stock_fallback": "daily_difference",
    "monthly": "transition",
    "min_days": 7,
    "q1": MappingProxyType({"series": "start_run_minus_warm_run", "pairs_min": 5, "lead_days": 28}),
    "q2": MappingProxyType({"series": "branch_minus_aa", "pairs_min": 6,
                            "intervals": ("prepare", "switch", "new_normal"),
                            "bounds": MappingProxyType({"prepare": "notice.at -> start",
                                                        "switch": "start -> start + d*",
                                                        "new_normal": "start + d* -> end"})}),
})

#: 規則の各項の印(mechanism / expedient / unresearched)。鍵は ``RULE`` の葉の項(入れ子は ``q1.…``・``q2.…``)と同じ
#: (〔検収 L5〕印の無い項を残さない=試験が突き合わせる)。
MARKS: Final[Mapping[str, str]] = MappingProxyType({
    "method": "mechanism", "statistic": "mechanism", "series": "expedient", "sensitivity_arm": "expedient",
    "batch_days": "expedient", "exclude_last_batches": "mechanism", "exclude_last_counting": "unresearched",
    "invalid_if_d_over_n": "mechanism", "extend_fraction": "mechanism",
    "extend_min_batches": "expedient", "max_invalid": "expedient", "bundle": "expedient", "warmup_days": "mechanism",
    "measure_min": "mechanism", "total_min": "mechanism", "cumulative": "mechanism", "counter": "mechanism",
    "counter_unmarked": "mechanism", "counter_first_day": "expedient", "stock": "mechanism",
    "stock_fallback": "expedient", "monthly": "expedient", "min_days": "unresearched",
    "q1.series": "expedient", "q1.pairs_min": "expedient", "q1.lead_days": "expedient",
    "q2.series": "expedient", "q2.pairs_min": "mechanism", "q2.intervals": "mechanism", "q2.bounds": "mechanism",
})
#: 印の語彙。
MARK_VALUES: Final[tuple[str, ...]] = ("mechanism", "expedient", "unresearched")


def rule_items() -> tuple[str, ...]:
    """``RULE`` の葉の項の名(入れ子の ``q1``・``q2`` は ``q1.…`` の形=``MARKS`` の鍵と同じ形)。"""
    out: list[str] = []
    for k, v in RULE.items():
        if k in ("q1", "q2") and isinstance(v, Mapping):
            out.extend(f"{k}.{kk}" for kk in v)
        else:
            out.append(str(k))
    return tuple(out)


def _plain(v: Any) -> Any:
    if isinstance(v, Mapping):
        return {str(k): _plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    return v


def rule_sha256() -> str:
    """規則と印の正準の JSON の sha256(事前登録の指紋)。"""
    return sha256_hex({"schema": WARMUP_SCHEMA, "rule": _plain(RULE), "marks": _plain(MARKS)})


def rule_record() -> dict[str, Any]:
    """manifest の ``experiment.warmup``・事前登録の記録の ``warmup``(規則・印・指紋・判定の道具の名)。"""
    rule, marks = _plain(RULE), _plain(MARKS)
    return {"schema": WARMUP_SCHEMA, "rule": rule, "marks": marks, "rule_sha256": rule_sha256(),
            "gauge": "tools/instruments/warmup_gauge.py", "registered": "rule_not_dates"}
