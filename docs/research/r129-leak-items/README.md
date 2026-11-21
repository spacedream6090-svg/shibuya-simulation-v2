# R-129 の漏洩検査の問い(起草・未実施)

- 答申: [v2-r129-forecast-target-candidates.md](../v2-r129-forecast-target-candidates.md) §3。器: `tools/instruments/leak_check/`(IMPLEMENTED #129)。
- 作成 2026-11-02・リサーチ役(Opus 5.5)。**実 LLM には一度も当てていない。** 形の確認だけ、mock の当て口で型 ①②④ を 1 回ずつ通した(全部の行が読めて採点まで通った)。
- 行の作り方は `leak_check.sets` の関数(`_scene`・`choice_prompt`・`block_sequence`・`fictional_name`・`event_prompt`・`side_of`)をそのまま使った。鍵は既存の `question_sets/` と同じ。
- 既にある対(渋谷スクランブルスクエア 5・MIYASHITA PARK 5)と同じ名と日付は使っていない(東棟は展望の施設 SHIBUYA SKY、MIYASHITA PARK はホテルと商業の名で対を作り、日付は 2019-11-01 と 2020-07-28 を外した)。

## 件数(候補 × 型)

| ファイル | 候補 | 型 ① (a) 日付 | 型 ① (b) 架空の出来事 | 型 ② 対(行) | 型 ④ 参照の指定 | 行の計 |
|---|---|---|---|---|---|---|
| `shibuya_stream.jsonl` | 渋谷ストリーム | 6 | 2 | 3(6) | 2 | 16 |
| `scramble_square_east.jsonl` | 渋谷スクランブルスクエア第Ⅰ期(東棟) | 6 | 2 | 3(6) | 2 | 16 |
| `miyashita_park.jsonl` | MIYASHITA PARK | 6 | 2 | 3(6) | 2 | 16 |
| `sakura_stage.jsonl` | 渋谷サクラステージ | 6 | 2 | 4(8) | 2 | 18 |
| `tenjin_bigbang.jsonl` | 天神ビッグバンの棟(TBC・大名 GC・ワンビル ほか) | 8 | 2 | 5(10) | 3 | 23 |
| 計 | | 32 | 10 | 18(36) | 11 | 89 |

## 行の形(行の鍵で型が分かる)

| 型 | 見分け方 | 鍵(既存と同じ) | 写す先の名(器の既定) |
|---|---|---|---|
| ① (a) | `qid` があり `part` = `a` | `qid, type, part, date, side, days_from_world, lang, prompt` | `type1_dates.jsonl` |
| ① (b) | `qid` があり `part` = `b` | `qid, type, part, kind(=fictional), when, side, lang, prompt` | `type1_events.jsonl` |
| ② | `sid` がある | `sid, pair_id, variant, target, target_group, target_kind, name, lang, judgment_kind, input_text, input_missing, facts, strata, candidates, prompt` | `type2_names.jsonl` |
| ④ | `qid` も `sid` も無い | `id, name` + `source_url, locator`(本文は無い) | 親が `data/leak_check/recall_refs.jsonl` に置く |

- 型 ① (a) の文は既存の `DATE_PROMPT` と同じ。天神だけ「東京の渋谷」を「福岡の天神」に替えた(expedient)。
- 型 ① (b) の実在の出来事は入れていない(器の方針どおり、親が `data/leak_check/real_events.jsonl` に置く)。答申 §1 の開業日の行(出典つき)から作れる。
- 型 ② の `target_group` は `r129_` を頭に付けた(既存の群と混ざらない)。架空名は既存の規則(実名の構造の語を残し、ブランドの語だけを片仮名 3 音に)に合わせた: 渋谷ネソカ(渋谷ストリーム)・ホミレ SKY(SHIBUYA SKY)・ラヌホ ルモテ PARK(sequence MIYASHITA PARK)・キセモ ルモテ PARK(RAYARD MIYASHITA PARK)・渋谷ムテヨステージ(渋谷サクラステージ)・ソヘラ FUKUOKA BLDG.(ONE FUKUOKA BLDG.)・福岡大名ヤクネシティ(福岡大名ガーデンシティ)・天神ヒサロセンター(天神ビジネスセンター)。「ルモテ」は既存の MIYASHITA の架空名と揃えた。**実在しないことは確かめていない**(親の確認)。SHIBUYA SKY は地名の語(SHIBUYA)を置き換え、構造の語(SKY)を残した(expedient)。
- 型 ④ は参照の**指定だけ**(データ名・出典の URL・どこを冒頭に使うか)。本文は写していない。器の方針(参照の文は gitignore の下)に合わせた。親が本文を取り、`text` か `prefix`+`continuation` を足して置く。`r129-scramble-r2` と `r129-sakura-r2` は来館者数などの結果の値を含む見込みなので、置くかは親が決める。

## 実行の手順(親・vLLM の導入の後)

CLI の `run` は `question_sets/` の既定の名だけを読む(`--sets-dir` が無い)。既存の集合を書き換えないため、作業用の置き場に型ごとに分けて写し、`run` の関数に `sets_dir` を渡す。

```
# 1. 分ける(作業用の置き場は gitignore の下か一時の場所。型 ④ の指示の型は既存の build_type4 のもの)
PYTHONPATH=src:tools/instruments python - <<'PY'
from pathlib import Path
from leak_check import sets as S
src, d = Path("docs/research/r129-leak-items"), Path("data/leak_check/r129_sets")
d.mkdir(parents=True, exist_ok=True)
a, b, t2, t4 = [], [], [], []
for f in sorted(src.glob("*.jsonl")):
    for r in S.read_jsonl(f):
        if "qid" in r: (a if r["part"] == "a" else b).append(r)
        elif "sid" in r: t2.append(r)
        else: t4.append(r)
(d / S.TYPE1_DATES_NAME).write_bytes(S.to_jsonl(a))
(d / S.TYPE1_EVENTS_NAME).write_bytes(S.to_jsonl(b))
(d / S.TYPE2_NAME).write_bytes(S.to_jsonl(t2))
(d / S.TYPE4_NAME).write_bytes(S.to_jsonl(S.build_type4()))
print(len(a), len(b), len(t2), len(t4))   # 32 10 36 11
PY

# 2. 当てる(型ごと・モデルごと。vLLM は 127.0.0.1・API key は環境変数 VLLM_API_KEY)
PYTHONPATH=src:tools/instruments python - <<'PY'
from pathlib import Path
from leak_check import run as R, cli as C
from leak_check.backends import make_backend
d = Path("data/leak_check/r129_sets")
be = make_backend("vllm", model="<served-model-name>", port=8000, model_version="<重みの revision>")
res = R.run_type1(be, sets_dir=d, model_cutoff="<YYYY-MM か空>")   # 実在の出来事は data/leak_check/real_events.jsonl
C.write_outputs(res, Path("<出力の置き場>/type1"))
res = R.run_type2(be, sets_dir=d)
C.write_outputs(res, Path("<出力の置き場>/type2"))
res = R.run_type4(be, sets_dir=d, recall_refs=Path("data/leak_check/recall_refs.jsonl"))
C.write_outputs(res, Path("<出力の置き場>/type4"))
PY

# 3. まとめ(運用規則 9 の 1 行・同じモデルの result.json だけ)
PYTHONPATH=src:tools/instruments python -m leak_check.cli summary <出力の置き場>/type1/result.json <出力の置き場>/type2/result.json <出力の置き場>/type4/result.json
```

- 当てるモデル: 指示書 11-02 研究 5 のとおり Qwen3-8B と候補の判断モデル(回答 11-01 §11 の 4B 以下の候補)。型 ② の logprob は判断モデルでも 1 トークン目の上位を読む(器の既定)。
- `--model-cutoff` に当たる値: Qwen3-8B の公式の記載は見つからなかった(答申 §5)。空のまま流し、前後の分けは日付の `side`(世界の時点 2026-07-13)だけにするのが器の既定。
- 試走は `limit=1` を各関数に渡す(器の `--limit` と同じ)。
- 既存の集合(`question_sets/`)と合わせて流すと、対象の群が混ざらない(`target_group` が別)。合わせるかは親が決める。
