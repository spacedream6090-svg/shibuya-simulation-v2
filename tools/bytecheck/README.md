# tools/bytecheck — byte-check(決定論の確かめ)

基準の commit と比べる側の src で同じ構成を回し、結果の 25 欄が 1 バイトも動かないかを確かめる道具。発注は
[返事その 7 §2 の 4](../../docs/design/prompt-2026-11-09-reply7.md)。前の道具
[byte_check_10e.py](../../docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py) の働きを引き継いだ
(前の道具は記録の再現のために残してある)。

> **CI が緑でも決定論は確かめていない。** byte-check は data(gitignore の下)と 1 回 7 分ほどのラン(38 本)が要るので、
> CI では回せない。**作者の機械で回す。** CI の ci-1 が回すのは、この道具の単体の試験
> (`tests/tools/test_bytecheck.py`=構成の表・比べ方・写すファイルの一覧・つなぎの扱い)だけ。

## 版上げのときに回す 1 行

リポの根(作業木の根)で、venv の python で:

```
python tools/bytecheck/cli.py run --work C:\bc<N> --out-dir <記録の置き場>/bytecheck --jobs 6
```

- `--work` は短い道筋で、無いか空のディレクトリ(Windows の道筋の長さの上限を避ける)。`<N>` は devlog の番号など。
- 基準は既定で `HEAD`(`--base <commit>` で替える)。比べる側は既定で作業木の `src`(`--src <道筋>` で替える)。
  commit の前に回せば「この変更で 1 バイトも動かないか」を確かめられる。
- 終了コード: **0=19 構成すべて 25 欄が同じ**・**1=動いた欄がある**・**2=誤り**(引数・ランの誤り・写しの木の不足・
  読んだ src の違い・写しの一覧に無いファイルを開いた・つなぎを外せなかった)。
- 呼び手の環境に `SHIBUYA_` の変数があると止まる(構成が黙って変わらないように。続けるなら `--inherit-env`)。

ほかの組:

```
python tools/bytecheck/cli.py run --work C:\bc<N>p --out-dir <置き場> --set parent4 --jobs 4   # 親の 4 構成
python tools/bytecheck/cli.py run --work C:\bc<N>a --out-dir <置き場> --set arms --jobs 2      # 腕 on の 2 構成と 7 変数
```

## 何を確かめるか

- 構成: 19 構成(`--set all19`)=W6 の 15 腕(現行 8・旧 6・golden の帰無腕 1)+店の記憶・関係・古典・古典+記憶+関係。
  表は `configs.py`(前の道具の `wave2_bytecheck.configs()` と同じ並びと引数=試験で確かめる)。
  `parent4`=w6_v3_default・v3_mem_store・v3_classical・v3_classical_mem_rel。`arms`=w6_v3_default・v3_classical を、
  両側とも `SHIBUYA_DECISION_PORT=port`・`SHIBUYA_CONTACT=c1`・`SHIBUYA_CONTACT_HABIT=on`・`SHIBUYA_CALENDAR=1b`・
  `SHIBUYA_CALENDAR_2=arm`・`SHIBUYA_CALENDAR_3=arm`・`SHIBUYA_DUTIES=arm` で回す(v3-0a の README §4 の追加の確かめ)。
- 条件: mock(古典の構成は古典の方策)・5,000 体・seed 1・1 シミュ日・テープつき(`--agents`・`--seed`・`--world` で替えられる)。
- 比べる 25 欄: `final`・呼数・blocks の行数と全列の sha・calls の行数と列の名と列ごとの sha・行動の件数と sha・
  条件ごとの呼数・目立つ出来事・崩れ・気づき・出動・到着・平均の遅れ・食事・最後の checkpoint の behavior-hash と
  full-hash・日の終わりのハッシュ・開始の日時・再生の日・曜日・乱数の方式・資産の指紋(`frozen_sources`)。

## 確かめないこと

- 壁時計・刻みの時間・checkpoint の時間・テープのバイト数(記録はするが比べない)。性能は別に測る。
- 艦隊の道と判断モデルの中身(19 構成は mock と古典。腕の判断の口も mock が答える)。
- 組に入っていない腕と切替口(`arms` の 7 変数の外)。2 日以上・別の seed・別の体数。
- data の中身の変化(両側が同じ data を読む=data が変わっても両側は同じに動く)。
- GPU。

## run がすること

1. 基準の commit の `src` と、エンジンが読む `src` の外の追跡ファイル(`tree.TRACKED_READS`=8 本)を
   `<work>/tree` へ `git archive` で写す。
2. `<work>/tree/data` を道具のリポの `data` へのつなぎ(junction)にする。
3. 基準の側(写しの `src`)と比べる側の side を回す。どちらも `PYTHONPATH` に読む `src` を置く(venv の editable の道が
   本体の src を指していても、渡した src を読む。各ランが `src_as_expected` で確かめる)。
4. compare を書く。
5. **つなぎだけを外す**(つなぎであることを確かめてから `cmd /c rmdir`=中に入らない。中は消さない)。外せなければ
   終了コード 2 と、手で外す手順を出す。

写しの木とテープは `<work>` に残る。後始末は、つなぎが残っていないことを `cmd /c dir /AL /S <work>` で確かめてから、
`<work>` だけを指す 1 つのコマンドで消す。

## 写すファイルの一覧の決め方と、取りこぼしの防ぎ方

エンジンは `src` の外の追跡ファイルをリポの根から読む(`Path(__file__).parents[k]`・`resolve_repo_path`・`_repo_root`・
`*_RELPATH` の定数)。写しの木にそれが無いと、規則の表が空になったり錨が無かったりして、final が基準と違って見える。

- `tree.TRACKED_READS`(写す)・`tree.DATA_READS`(つなぎで見せる・有無だけ確かめる)・`tree.NOT_COPIED`(src に道筋の
  文字列として現れるが写さない=引用の文字列・構築側・19 構成が使わない腕。理由つき)・`tree.ROOT_READERS`(リポの根を
  求めるファイルと、それが読むもの)。
- **試験で防ぐ**: `tree.scan_path_refs` が src の AST から道筋の文字列(`"docs/…"`・`root / "docs" / …`・
  `("docs", "bench", …)`・f 文字列・`joinpath(*T, NAME)`・定数の名を通した結合)を集める。試験は、`docs`・`tools`・`tests`
  の道筋がすべて `TRACKED_READS` か `NOT_COPIED` に載ること、`tree.scan_root_anchors` の見つけたファイルが
  `ROOT_READERS` と同じこと、一覧の行が今も src に現れることを確かめる。src がリポの根から新しいファイルを読み始めると
  CI の ci-1 が落ち、一覧に足すまで通らない。
- **ランで防ぐ**: 各ランは監査フックで開いたファイルを記録する。side は「`TRACKED_READS` に無い追跡ファイルを開いた」
  (`tree_reads_unlisted`)・「写しの木に無いファイルを開こうとした」(`tree_reads_absent`)・「写しの側が道具のリポの
  ファイルを開いた」(`foreign_reads`)を誤りにする。

古い commit を基準にするときに、その版のエンジンが今の一覧に無いファイルを読むなら(例: 2-4 V6 より前の錨
`hunger_energy_anchors_v0.json`)、`--extra-path docs/bench/anchors/hunger_energy_anchors_v0.json` で足す。
今の版に無い引数を持つ構成は、`--kw` で旧値の再現の切替口を渡す(前の道具と同じ口)。

## 出力の読み方

`--out-dir` に 3 本(絶対パスは書かない。誤りの文の道筋は `<repo>`・`<tree>`・`<scratch>`・`<home>`・`<python>` に伏せる):

- `<組>_base_<commit 7 桁>.json`・`<組>_<label>.json`(side): `runs` に構成ごとの全欄。`src`(写し/作業木)・`commit`
  (比べる側は作業木の HEAD。src に未 commit の変更があれば `+dirty`)・`env`(切替口の環境変数の値)・`env_hidden`
  (値を書かない変数の名)・`tree_reads`(開いた `src` の外の追跡ファイル)。`--only` で回したときは `<組>_only_…`。
- `<組>_compare_base_<commit>_vs_<label>.json`: `summary`(構成の数・25 欄すべて同じ・動いた・誤り・final が同じ・
  `result`・`exit_code`)・`checks`(両側の誤り)・`rows`(構成ごとの `same`=同じ欄・`moved`=動いた欄と前後の値・
  呼数などの差)。

標準出力の最後の 2 行に要約が出る。動いた構成は名と動いた欄の名が出る。

## 所要時間の目安

この機械(Core Ultra 7 265K・20 コア・31 GB)で `--set all19 --jobs 6`(2026-11-09・HEAD 14b151a): 基準の側 210 秒・
比べる側 203 秒・全体 414 秒(約 7 分)。1 ランは 31〜93 秒。1 ランの最大メモリは約 0.53 GB(v3-0a の §5)。`<work>` に
残るのは写しの木 約 19 MB とテープ 約 174 MB。`--jobs` を上げると速くなるが、壁時計は比べないので結果は変わらない。

19 構成のランで写しの木から開いた `src` の外の追跡ファイルは 5 本(規則の表・つなぎの台帳・予算の宣言・空腹の構築側の錨・
活動の事前分布)。`TRACKED_READS` の残り 3 本(検証側の錨・知覚の契約・パターン台帳)は、src の静的な読み口から載せている
(このランでは開かれなかった)。

## 下の口

```
python tools/bytecheck/cli.py side --label <名> --scratch <テープの置き場> --out <side.json> [--src <src>] [--set …] [--only …] [--jobs N] [--kw …]
python tools/bytecheck/cli.py compare --a <side.json> --b <side.json> --out <compare.json> [--note …]
```

意味は前の道具と同じ。違い: `--src` が無いときも作業木の `src` を `PYTHONPATH` に置く・`SHIBUYA_BUDGET_MD` を置かない
(写しの木の宣言の表を読む)・誤りがあれば終了コード 2。前の道具の side の JSON(v3-0a の記録など)も compare で比べられる。
