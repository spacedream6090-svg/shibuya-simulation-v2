# 10f 第 3 段の再検収(U1〜U7 の直し)

> 検収役(Opus 5.5)の記録。前回の検収は [review-10f-stage3.md](review-10f-stage3.md)、直しの記録は [README](README.md) の第 3 段 §8。作業木の追跡しているファイルは書き換えていない(前と後で `git diff` の sha256 は同じ `1b113a6d…`)。壊す検査と HEAD の写しは作業用の場所で行った。パスは `src/shibuya/` を省く。

## 結論

- **受入**。条件だった U1 は直っている。下に挙げた 24 通りの経路のどれでも `pickle.loads`・`pickle.load`・`pickle.Unpickler` は呼ばれず、印のファイルもできなかった。切替口と `.pkl` がそろったときだけ開く。HEAD `129da80` で書いた `.pkl` からの再開は、通しと全点一致した。
- 既定の結果は変わっていない。既定 v3 の 1 日と 2 日のランを HEAD の写しと作業木で回し、final・呼数・テープが一致した(テープはファイルのバイトまで一致)。
- 残ったのは低い 3 件(V1〜V3)。どれも記録か限界の明記で済み、コミットを止める理由にはならない。

## 1. U1(条件だったもの)

作業木の src を読む写しの場所で、`__reduce__` で印のファイルを作る悪い pickle を使った。10d の形の先頭の行(sha256 は中身から計算)と、ラン ID の合う写しの `.json` を添えた。`pickle.loads`・`load`・`Unpickler` を包み、呼ばれたら記録するようにした。

| 経路 | 結果 | pickle の呼び出し | 印のファイル |
|---|---|---|---|
| 名前 `.npz`・切替口なし(前回の再現) | `StateFormatError`(pickle の形式・開かない) | 0 | なし |
| 名前 `.npz`・切替口あり | 同上 | 0 | なし |
| 名前 `.pkl`・切替口なし | 同上 | 0 | なし |
| 名前 `.PKL`・`.Pkl`・切替口あり | 同上(`suffix` は大文字と小文字を区別する) | 0 | なし |
| `.pkl.npz`・`.json`・拡張子なし・末尾が空白の `.pkl `・切替口あり | 同上 | 0 | なし |
| 先頭の行の無い生の pickle(プロトコル 0・1)・`.pkl`・切替口あり | `StateFormatError`(npz の印が無い) | 0 | なし |
| 同(プロトコル 2・5) | `StateFormatError`(先頭の行に印が無い) | 0 | なし |
| 中身は正しい npz・写しの `.json` が旧の形式を名乗る | `StateFormatError`(形式の版が違う) | 0 | なし |
| 写しの `.json` の中身が悪い pickle | `UnicodeDecodeError`(V2) | 0 | なし |
| npz の部品の npy が object の dtype(中身は悪い pickle) | `StateFormatError`(部品が object の dtype) | 0 | なし |
| 同・構造化の dtype に `O` の欄 | 同上 | 0 | なし |
| 同・`meta.npy` が object の dtype | 同上 | 0 | なし |
| 上の 3 つで部品の検査 `_check_members` を外す(numpy の `allow_pickle=False` だけで止まるかを見る) | `StateFormatError`(numpy の「Object arrays cannot be loaded when allow_pickle=False」) | 0 | なし |
| `run_day` の再開・`.npz`・切替口なし/あり | `StateFormatError` | 0 | なし |
| `run_day` の再開・`.pkl`・切替口なし | `StateFormatError` | 0 | なし |
| 対照: `.pkl`・切替口あり | 開く(設計どおり)。`loads` 1 回・印のファイルができる | 1 | あり |

- `np.load` は `state_codec.loads` の 1 か所だけで、`allow_pickle=False` が付いている。部品は同じ `NpzFile` から読むので、この設定が全部の読みに効く。上の表のとおり、部品の検査を外しても numpy が止める(二重の守り)。
- 旗の既定: `read_state(allow_legacy_pickle=False)`・`run_day(resume_legacy_pickle=False)`・CLI の `--resume-legacy-pickle` は `store_true` で、付けないと kwargs に入らない。`shibuya.cli` も同じ `add_calendar_args` を使っている。
- **切替口つきの `.pkl` の再開**: HEAD `129da80` の `git archive` の写しに祝日の CSV を写し、合成世界 60 体・記憶+関係・2 日を T=750 と T=1440 で止めて `.pkl` を書いた。作業木で切替口つきで再開すると、T 以後の checkpoint(36 点と 24 点)の final・behavior-hash・full-hash が通しと全部一致し、`LegacyStateFormatWarning` が出た。切替口なしでは `StateFormatError` で止まった。
  - 試験 `test_u1_resume_from_a_pkl_written_by_the_pickle_commit` は、この機械では pytest の一時ディレクトリのパスが長すぎて、numba の置き場で落ちた(前回の検収と同じ Windows のパスの長さの上限。src の問題ではない)。だから同じ手順を短いパスで手で回した。
- 対象の試験: `test_state_format_10f.py` の U1・旧の pickle・U3・U4 の 9 件が passed。

## 2. U3〜U7

| # | 自分で確かめたこと | 結果 |
|---|---|---|
| U3 | `PendingInvite` の meta に余分な欄 `evil` を足す/欄 `__dict__` を足す/欄を 1 つ消す | 3 つとも `StateFormatError`(余分 `['evil']`・`__` で始まる・足りない `['inviter']`) |
| U4 | `__ns` の `\|i1` に 1000 を置く/深さ 10 万の JSON の配列 | 2 つとも `StateFormatError`(中は `OverflowError`・`RecursionError`) |
| U5 | src の写しの `run.py` に、許可した行 `prev_tape_misses = bridge.n_tape_misses` を挙動の分岐の関数で足す | 「当たる数が 3(宣言は 2)」で落ちる。写しをそのまま検査すると問題 0。限界は V3 |
| U6 | `state_ledger_ast.py` の限界のコメント(566 行目あたり)と README §8-1 | 「衝突の 20 属性は受け手の名前が持ち主と違えば見えない」と書いてある。試験 `test_t4_axis1_collision_needs_the_owner_receiver` が passed |
| U7 | 試験の T=1439・1441 と、`_ipf_cache`・`_pulled_in_today` の 2 件 | `test_state_checks_10f.py` の U5・U7・衝突・T の 7 件が passed(95 秒) |
| U2 | `rng_audit.py` の `K19_ALLOW` の上の注 | 「1 ブロック(4 語)ずらした写し」「10e まで、2 日以上のランのこれらの日ごとの差を主張に使わない」と書いてある。README §8 の U2 の行にもある。§3-2 と §7 の 2 には無い(V1) |

## 3. 既定の結果の不変

HEAD `129da80` の `git archive` の写し(src・anchors・予算の宣言・w6-regen)に祝日の CSV を写した。その写しと作業木で、既定 v3(`w6_v3_default` の引数)・世界資産 5,000 体・seed 1・テープつきを回した。

| ラン | HEAD の写し | 作業木 | 一致 |
|---|---|---|---|
| 1 日 | final `993276d5e5bb5cbe`・69,978 呼 | 同じ | final・呼数・blocks の sha `268129bf…`・calls の 14 列の sha・`calls.parquet` と `blocks.parquet` のバイトの sha256 |
| 2 日 | final `47e0a85b02797e23`・142,043 呼 | 同じ | final・呼数・blocks の sha `4fc9becc…`・calls の 14 列の sha・2 つの parquet のバイトの sha256 |

- `byte_check_stage3_fix.json` の既定 v3 の行(`993276d5e5bb5cbe`・69,978 呼・14 列一致)と、`two_day_check_stage3_fix.json`(`47e0a85b02797e23`・142,043 呼・`blocks_sha` `4fc9beccec9b175f`)の主張と合う。19 構成のうち、回し直したのは既定 v3 だけ。

## 欠陥(どれも低い)

### V1(低・記録): README §8 の U2 の行は「§3-2・§7 の 2 に書いた」と言うが、そこに注が無い

- 第 3 段 §3-2 の「気づいたこと」と §7 の 2 は、今も「日をまたいだ乱数の相関」「10e で直す範囲に入れるか」のままになっている。「写し」と「10e まで日ごとの差を主張に使わない」は、§8 の表の U2 の行と `rng_audit.py` の注にしかない。
- 案: §3-2 と §7 の 2 に〔訂正(検収 U2)〕を 1 行ずつ足し、§8 を指す。§4-3 の U1 の書き方と同じ形にする。

### V2(低): 写しの `.json` が壊れていると、拒否が `StateFormatError` にそろわない

- `resume._read_side` は `read_text(encoding="utf-8")` と `json.loads` を包んでいない。JSON の文法が壊れていると `JSONDecodeError`、UTF-8 でないと `UnicodeDecodeError` が出る(実測)。どちらも `ValueError` の子なので読みは止まり、コードは動かない。ただし `read_state` の docstring と README §8 の U4 にある「拒否は全部 `StateFormatError`」とは合わない。
- 案: `_read_side` で `(OSError, UnicodeDecodeError, json.JSONDecodeError)` を `StateFormatError` に包む。手間は 2 行。

### V3(低・限界の明記): 場所ごとの許可の「当たる数」は、行を写すと捕まえるが、移すと捕まえない

- src の写しで、`run.py` にある `prev_tape_misses = bridge.n_tape_misses` の 2 か所のうち 1 つを無害な行に替え、同じ行を挙動の分岐の関数に置いた。当たる数は 2 のままなので、検査は問題 0 で通った。
- U5 の直しが言う範囲(写すと落ちる)は正しい。ただ「数を固定する」だけでは、同じ文字列の行の置き場所までは固定できない。
- 案: 10e までは README §8-1 の限界に 1 行足す。直すなら、許可の項に関数の名前(行を囲む `def`)を持たせる。

## 確かめたが欠陥でなかったもの

- 拡張子の判定は `Path.suffix == ".pkl"`(大文字と小文字を区別する)なので、`.PKL` も `.pkl ` も開かない。保守的な側に倒れている。
- 中身が正しい npz なら、写しの `.json` に何が書いてあっても pickle の口には入らない。口を選ぶのはファイルの先頭のバイトと、切替口と拡張子だけ。
- プロトコル 0・1 の pickle は先頭が `0x80` ではないが、npz の印も無いので止まる。

## 使った道具(作業用の場所・リポには入れていない)

U1 の 24 通りの検査、U3・U4・U5 の再現、HEAD の写しで `.pkl` を書いて作業木で再開する手順、既定 v3 の 1 日と 2 日を HEAD の写しと作業木で回す子のスクリプト。
