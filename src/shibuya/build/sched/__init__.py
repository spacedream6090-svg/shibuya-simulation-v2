"""build.sched — 世界データ構築 W17(週次スケジュール生成・T0 活動表)。

仕様: docs/design/v2-world-data-build-spec.md §1 段階表 W17(入力=W16+PT 目的×時間帯カーブ
(較正)+PlanSpec / 出力=週7日活動表/体(T0) / ゲート=PT 時間帯カーブとの JSD・修正率<20%・
呼数=体数 / 呼 400,000)・§0-8(LLM 呼は 3 段のみ・1 回限り・温度と seed を固定・出力を凍結)・
D-W17(モデル=T1 8B INT8 全件・温度 0.7・seed=hash(agent)・プロンプト=種別別テンプレ凍結 SHA・
較正=PT 目的別時間帯カーブで raking → 修正率<20%・予算 I1・感度=T2 対照 5,000 体)・
D-W14(集計表は生成入力・較正・検証にのみ使う=来街を抽選する装置ではない)。
接続: 決定台帳「母集団合成」7段の⑦「スケジュール3段生成」+追補「同じ日は決してないから
フル生成」(週7日フル生成・I1=1回限り)・境界経済設計書 §1.1(U10 案A: 週次表 T0 → T1 差分 →
T2 LLM)・認知設計書 §1(T0=反射/習慣レーン・思考 0)・行動契約書 §2.1(活動語は行動語彙 12 語へ
写像できること)・知覚契約書 §6(計画境界起床)。

**この段階は LLM を呼ばない**(§0-1 決定論: 段階=純関数)。build.lang(W14/W15)と同じ 3 手順:

1. ``run``(前半): W16 の全個体からプロンプト jsonl を決定論で作って書く
   (``w17_prompts.jsonl`` / シャード時は ``w17_prompts.<i>of<n>.jsonl``)。
2. **段階の外**: 親が ``tools/gen/fleet_gen.py`` で 8B INT8 艦隊(DP7)へ流し、
   ``w17_responses*.jsonl`` を ``--out`` へ置く。
3. ``run``(後半=``ingest``): 応答 jsonl が**在れば**入力資産として ``input_hash`` に含め、
   行パーサ → 整合修復 → raking を通して ``w17_schedule.parquet`` へ凍結する。

応答が無い状態で ``run`` を回しても落ちない(プロンプトだけ書いて「応答未取得」を報告する)。

実行: ``python -m shibuya.build.sched.run --out data/world/v2 [--shard 0/8]``

層契約: build は manifest と core だけを import してよい。**build.lang と違い perception は
import しない**(W17 の出力は知覚ブロックの文面ではなく構造化された表なので、正規化規約を
共有する理由がない)。実行時側(``agents.weekly``)とは語彙定数を**二重定義**し、
``tests/build_sched/test_weekly_loader.py`` が一致を機械検査する
(``agents.population`` が ``AGE_EDGES``/最大剰余法を二重定義しているのと同じ理由)。
"""

from __future__ import annotations

from typing import Callable

__all__ = ["STAGES", "stage_funcs"]

#: 実行順(W 番号順)。W17 のみ。W16(母集団)と W7(PlanSpec)の出力を読む。
STAGES: tuple[str, ...] = ("W17",)


def stage_funcs() -> dict[str, Callable]:
    """段階名 → 段階関数(``run.STAGE_FUNCS`` の遅延取得)。

    ``__init__`` が ``run`` を import すると循環するので関数内 import にする
    (``build.geo``/``field``/``vis``/``pop``/``lang`` と同じ形)。
    """
    from .run import STAGE_FUNCS

    return dict(STAGE_FUNCS)
