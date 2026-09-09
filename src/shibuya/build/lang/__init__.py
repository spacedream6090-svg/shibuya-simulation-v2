"""build.lang — 世界データ構築 W14/W15(静的言語化レーン)。

各段階=純関数(入力ファイル群+パラメータ→出力+ヘッダ)。ヘッダ形式は build.geo と同一。
仕様: docs/design/v2-world-data-build-spec.md §0 構築原則(原則8「LLM呼は3段のみ・1回限り・
温度とseedを固定・出力をバイト凍結」)・§1 段階表 W14/W15・§2 D-W18(静的言語化のモデル=
T2 32B AWQ・温度0・1回生成→凍結・ゲート「固有名詞は入力(POI名)由来のみ」)。
接続: 知覚契約書 §2.2 B2(場所セル静的 150 tok)・§2.4 正規化規約9項・§3 チャネル仕様表
(看板(a)=店舗基本属性 → B2)・§3.2 チャネル別トークン上限(B2.signage 25 / B2.visible 60)・
§5 prefix(B2 は prefix キャッシュの一部=セル共有)。広告答申 §4(自由文をそのまま渡さない・
構造化属性へ還元・命令文除去・評価語と誘導表現の禁止)。

**この段階は LLM を呼ばない**(§0-1 決定論: 段階=純関数)。3 手順に分かれる:

1. ``run``(段階本体・前半): 入力から**プロンプト jsonl** を決定論で作って書く。
   ``w14_prompts.jsonl`` / ``w15_prompts.jsonl``(``tools/gen/fleet_gen.py`` の入力形式)。
2. **段階の外**: 親が ``tools/gen/fleet_gen.py`` でサーバー上の vLLM(Qwen3-32B-AWQ・温度0)
   へ流し、``w14_responses.jsonl`` / ``w15_responses.jsonl`` を ``--out`` へ置く。
3. ``run``(段階本体・後半=``ingest``): 応答 jsonl が**在れば**それを**入力資産**として
   ``input_hash`` に含め、ゲート(rep 間バイト一致・固有名詞検査・正規化規約・長さ上限)を
   通ったものだけを parquet へ**バイト凍結**する。落ちた行は凍結せず、レンダラは従来の
   合成文へフォールバックする(ゲート json に件数と理由を残す)。

応答が無い状態で ``run`` を回しても落ちない(プロンプトだけ書いて「応答未取得」を報告する)。

実行: ``python -m shibuya.build.lang.run --out data/world/v2 [--stage W14]``
      (通し実行は ``python -m shibuya.build.run --out data/world/v2``)

層契約: build は manifest と core だけを import してよい——**本レーンだけの例外**として
``shibuya.perception`` の ``normalize``/``channels``/``attention`` を import する(登録簿に宣言)。
理由: W14/W15 の出力は**知覚ブロックの文面そのもの**をバイト凍結する。正規化規約(§2.4)を
二重定義すると「凍結したバイト列」と「描画されるバイト列」が静かに食い違う=文面凍結宣言
(§1 条5)が壊れる。語彙定数の二重定義(w10_noise の騒音段語彙など)とは危険度が違う。
import の向きは build → perception のみで、実行時に build を import しない規約
(pyproject の import-linter 契約)には触れない。
"""

from __future__ import annotations

from typing import Callable

__all__ = ["STAGES", "stage_funcs"]

#: 実行順(W 番号順)。W14 は W6/W7 の出力を、W15 は W2/W6/W8 の出力を読む。
STAGES: tuple[str, ...] = ("W14", "W15")


def stage_funcs() -> dict[str, Callable]:
    """段階名 → 段階関数(``run.STAGE_FUNCS`` の遅延取得)。

    ``__init__`` が ``run`` を import すると循環するので関数内 import にする
    (``build.geo``/``field``/``vis``/``pop`` と同じ形: 名前は ``__init__``・関数は ``run``)。
    """
    from .run import STAGE_FUNCS

    return dict(STAGE_FUNCS)
