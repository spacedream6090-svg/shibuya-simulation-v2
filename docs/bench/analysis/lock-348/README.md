# ロックの版で byte-check が今の基準と同じかの確かめ(第348・返事その 9 §1 の 13)

指示の文: 「ロックの版で byte-check の 19 構成が今の基準と同じかを手元で確かめ、違えば止めて報告してください。」
この頁は、親が手で 1 つずつ回す手順です。実装の役は手順を書いただけで、venv も byte-check も回していません。

## 何と何を比べるか

- **基準**: 本体の `.venv`(ロックを作った元の venv)で回した side。
- **比べる側**: `requirements-lock.txt` だけから作った新しい venv で回した side。
- 両側とも、同じ木(本体の木・data あり)の同じ `src` と同じ道具で、同じ構成を回す。違うのは python と入っている配布だけ。
- 比べる口は今の道具の `compare` で足りる(新しい台本は足していない)。`compare` は side の JSON を 2 本比べ、どの python で
  回したかは問わない。比べる欄には manifest の `environment.platform`(Python と numpy・numba・llvmlite・blake3 の版・
  入っている全部の配布の `名==版` の一覧 `deps`・OS・CPU)が入る(`tools/bytecheck/README.md` の「比べない欄」の外)。
  だから、2 つの venv の配布の版が 1 本でも違えば、25 欄が同じでも manifest が動いて終了コード 1 になる。
  pip の版も `deps` に入るので、比べる側の venv の pip も手元と同じ版(26.2.1)にする。

## 手順(本体の木の根で・PowerShell)

`<venv>` は新しい venv の置き場(リポの外の短い道筋。例 `C:\venv348`)。`<rec>` は記録の置き場。呼び手の環境に `SHIBUYA_` の
変数が無いことを先に確かめる(side は止めないので、両側に同じ変数が載ると構成が黙って変わる)。重い物は 1 つずつ回す。

1. ロックだけから venv を作る(元の python は本体の `.venv\pyvenv.cfg` の `home` にある 3.12.10)。

   ```
   <3.12.10 の python> -m venv <venv>
   <venv>\Scripts\python.exe -m pip install pip==26.2.1
   <venv>\Scripts\python.exe -m pip install -r requirements-lock.txt
   <venv>\Scripts\python.exe -m pip install --no-deps -e .
   <venv>\Scripts\python.exe -m pip check
   <venv>\Scripts\python.exe tools/ci/check_lock.py
   ```

   `check_lock.py` が「同じ」(終了コード 0)でなければ、ここで止めて報告する。`-e .` は本体の木の `src/shibuya_sim.egg-info`
   (git の外)を作り直す。名札の中身(依存の宣言)が今の `pyproject.toml` に揃うだけで、`deps` の `名==版` は変わらない。

2. 基準の side を本体の `.venv` で回す(19 構成・約 3.5 分)。

   ```
   .venv\Scripts\python.exe tools/bytecheck/cli.py side --set all19 --label venv_main --scratch C:\bc348m --out <rec>/all19_venv_main.json --jobs 6
   ```

3. 比べる側の side を新しい venv で回す(同じ組・同じ引数)。

   ```
   <venv>\Scripts\python.exe tools/bytecheck/cli.py side --set all19 --label venv_lock --scratch C:\bc348l --out <rec>/all19_venv_lock.json --jobs 6
   ```

4. 比べる(strict=新しい欄や条件の欄が無ければ誤り)。

   ```
   .venv\Scripts\python.exe tools/bytecheck/cli.py compare --a <rec>/all19_venv_main.json --b <rec>/all19_venv_lock.json --out <rec>/all19_compare_venv_main_vs_lock.json --strict
   ```

## 読み方

- 終了コード 0(19 構成すべて同じ): ロックの版で今の基準が再現する。記録の 3 本を `<rec>` に残す。
- 終了コード 1: 動いた欄が出る。manifest の動いた欄が `environment` だけなら、配布の版の違い(`deps` を見る)。25 欄や
  テープが動いたなら、版の違いが結果に効いた。どちらも**止めて報告する**(指示のとおり)。
- 終了コード 2: 条件の違い・ランの誤りなど。誤りの文を読む。
- 仕事 C(byte-check を 20 構成に)が入った後なら、`--set all20`(既定)で 20 構成を比べてもよい。

## 結果(親が回した・2026-11-21・作者の機械・HEAD `0a28da4`)

| 確かめ | 結果 |
|---|---|
| ロックだけから作った venv(Python 3.12.10・pip 26.2.1・48 本・本体は依存なしで入れた) | `pip check` は通過。`pip freeze --exclude-editable` は本体の `.venv` と同じ 48 本 |
| `tools/ci/check_lock.py` | 本体の `.venv` でも新しい venv でも「同じ」(終了コード 0) |
| manifest の環境の欄(依存の一覧のハッシュ `deps_sha256`・`platform_id`) | 2 つの venv で同じ(依存 50 本=48 本+pip+本体) |
| 基準の side(本体の `.venv`・19 構成・6 本並列) | 終了コード 0・約 3 分 40 秒。既定の構成 `w6_v3_default` は final `c8d68704b7b0760d`・呼数 60,939 |
| 比べる側の side(新しい venv・同じ組) | 終了コード 0・約 3 分 30 秒。`w6_v3_default` は final `c8d68704b7b0760d`・呼数 60,939 |
| `compare --strict` | **19 構成・37 欄すべて同じ**(一部の欄を比べていない 0・動いた 0・誤り 0)。終了コード 0 |

- ロックの版で、今の基準が再現した。指示の「違えば止めて報告」には当たらない。
- 記録は [bytecheck/](bytecheck/) の 3 本(`all19_venv_main.json`・`all19_venv_lock.json`・`all19_compare_venv_main_vs_lock.json`)。side の中の札は `main_venv`・`lock_venv`(上の手順の例の名と語順が違うだけ)。
- 比べたのは 19 構成(この確かめは、byte-check を 20 構成にする前の道具で回した)。
- 作者の機械の OS の版は、第 347 の記録の時(10.0.26200)から上がっている(10.0.26300)。manifest の環境の欄に OS の版が入るので、古い記録とは比べず、2 つの venv を同じ日に回し直して比べた。
- 確かめていないこと: Linux(CI)でロックの 47 本が全部入るか・Python 3.12.10 が CI の実行機に入るか(どちらも CI の結果で分かる)。借りる GPU の機械での再現。

## 後始末

`C:\bc348m`・`C:\bc348l`(テープ)と `<venv>` は、それぞれ単独のコマンドで、その道筋だけを消す。side はつなぎを作らない
(つなぎを作るのは `run` だけ)。
