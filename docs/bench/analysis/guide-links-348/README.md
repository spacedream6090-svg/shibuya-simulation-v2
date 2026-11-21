# 手書きの案内のリンクの引き直し(第348・返事その 9 §1 の 25)

発注: [返事その 9](../../../design/prompt-2026-11-20-reply9.md) §1 の 25(割る段が全部済んだので、手書きの案内のリンクを移した先の表で機械で引き直す)。経緯は [第347 の報告](../../../ops/report-347-2026-11-16.md) §11 と判断待ちの 25。

## したこと

- 対象: `docs/reference/repo-guide/` の手書きの 6 本(`README.md`・`day-flow.md`・`can-say.md`・`catalog/` の 3 本)。`cards/` は自動で作るので外した。
- 拾ったのは行の中の `[文字](向け先)` の形の相対リンク。外のサイトと、ファイルの中の `#見出し` だけのリンクは外した(6 本とも 0 本だった)。参照の形 `[x]: 道` と `<道>` の形も 0 本。
- 直したのは、向け先が今の木に無いリンクだけ。在る道を指すリンクは触っていない。案内の文とリンクの文字は 1 字も変えていない。
- 対応の表は `tools/pkgmove/map.toml`(移す道具と割る道具の表)を台本が直に読んだ。
  - `move` の行: 新しい道へ(1 対 1)。
  - ディレクトリ(2 本): 古いディレクトリのファイルが全部同じ新しいディレクトリへ移ったときだけ、そのディレクトリへ(`engine/body/` → `world/body/`・`engine/processes/` → `world/laws/`)。表では 1 対 1 に数えた。
  - `split` の行(割ったファイル): リンクの文字、無ければその行の文で `` ` `` に囲まれた名を拾い、今の木の `src/shibuya` で頂上の定義(関数・クラス・代入・頂上の if と try の中を含む)がちょうど 1 か所に在り、その場所がその行の割り先の 1 つであるものを探した。当たった割り先が 1 つならそこへ(名で割り先へ)。名が無い・2 つ以上の割り先に当たるときは表の主な割り先(`new`)へ(主な割り先へ)。名で向けたものは、表の名ごとの割り先(`names`)と今の木の定義の場所を突き合わせ、食い違いは 0 件だった。
  - `delete` の行(消した物): 向け先を作らず残した(1 本)。
- 行の錨(`#L42` の形)は 6 本の中に 1 本も無かった。台本には付け替えと外しの道を入れたが、使っていない。

## 数の表

| ファイル | 拾った | 在る | 無い | 1 対 1 で直した | 名で割り先へ | 主な割り先へ(うち複数に当たった) | 消えた物で残した |
|---|---|---|---|---|---|---|---|
| README.md | 13 | 13 | 0 | 0 | 0 | 0 | 0 |
| day-flow.md | 107 | 28 | 79 | 62 | 2 | 15(0) | 0 |
| can-say.md | 30 | 29 | 1 | 1 | 0 | 0 | 0 |
| catalog/a-body-and-town.md | 198 | 64 | 134 | 107(うちディレクトリ 2) | 9 | 18(2) | 0 |
| catalog/b-people.md | 116 | 16 | 100 | 73 | 16 | 11(7) | 0 |
| catalog/c-foundation.md | 213 | 75 | 138 | 109 | 13 | 15(1) | 1 |
| 計 | 677 | 225 | 452 | 352 | 40 | 59(10) | 1 |

行の錨: 付け替え 0・外した 0(もともと 0 本)。第347 の数え(420〜428 本)と違うのは、数え方の違いと思われる(この台本は 6 本の `[文字](向け先)` を全部、1 本ずつ数えた)。

残した 1 本: `catalog/c-foundation.md` の 109 行目 `src/shibuya/census/__init__.py`(表の `delete` の行。消す段で消した)。

主な割り先へ向けたうち、名が 2 つ以上の割り先に当たった 10 本(`dryrun_report.json` の `how` が `main_many_line`): a-body-and-town 184(presence)・188(resolve)、b-people 80(resolve)・81(commit)・137(poi_target)・138(chooser)・199(resolve)・357(speech/port)・596(relations)、c-foundation 273(run)。

## 台本と出力

- [tools/relink.py](tools/relink.py): 引数=リポの根。既定は書かずに数と差分だけ。`--apply` で書く。
- [tools/verify.py](tools/verify.py): 書いた後の確かめ(`git show HEAD:` の版と比べる)。
- 書かない実行の出力: [dryrun_report.json](dryrun_report.json)(ファイルごとの数・直したリンクの全部と方法と当たった名・残したリンク)と [dryrun.diff](dryrun.diff)。
- 書いた実行の出力: [apply_report.json](apply_report.json) と [apply.diff](apply.diff)(書かない実行の差分とバイトで同じ)。
- 確かめの出力: [verify.json](verify.json)。

## 確かめ方

1. 書かない実行の後、14 本を抜き出して今の木のファイルを開いて確かめた。名で向けた 7 本(`rail_arrive` → `act/ops/rail.py`・`talk_partners` → `act/intake/from_words.py`・`MOCK_UTTERANCE` → `foundation/vocab/actions.py`・`load_table` → `world/facts/w20_calendar_reader.py`・`WakeCondition` → `foundation/vocab/agent_codes.py`・`DEFAULT_WORLD_START` → `world/facts/calendar.py`・`_apply_help` → `act/apply.py`)は、その名の定義が向け先に在ることを grep で見た。1 対 1 の 7 本(`absent.py`・`weekly.py`・`rules/table.py`・`systems/judge.py`・`contact/calls.py`・`templates.py`・`core/rng.py`)は、向け先のファイルの docstring の最初の行が古いモジュールの名で始まることを見た。ディレクトリの 2 本は向け先が在ることを見た。
2. 書いた後に `verify.py` を回した: 6 本とも行の数と見出しの数が前と同じ・CR なし・リンクの括弧の外の字が違う行 0・在る道のリンクが変わった数 0・無い道を指すリンクは 1 本(上の残した 1 本)だけ。直したリンクは 451 本。
3. `git diff --word-diff=plain --word-diff-regex='[^()]+'` で、変わった語 451 個が全部「`src/shibuya/` の道 → `src/shibuya/` の道」であることを数えた。
4. 書いた後の木で書かない実行をもう 1 度回し(出力は記録の外へ)、拾った 677・在る 676・無い 1(残した 1 本)・差分 0 を見た。
5. `verify.py` の比べ方(リンクの向け先を印に替えて比べる)は、リンクの外の字とリンクの文字を 1 字変えた行で違いを見つけることを確かめた。

## 確かめていないこと

- 主な割り先へ向けた 59 本が、文の言う中身に一番合う割り先かどうか(名が無いので、表の主な割り先に任せた)。
- リンクの文字(古い道の名が残る 298 本ほど)と、文の中の `` ` `` で書いた古い道(156 か所ほど)。文の直しは範囲の外(段 8 の材料)。
- docs のほかの場所のリンク。
