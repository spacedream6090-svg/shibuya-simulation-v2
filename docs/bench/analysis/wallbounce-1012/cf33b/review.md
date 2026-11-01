# 第 3 期 3-3b 反実仮想の器の残り 独立検収の記録

- 検収役 Opus 5.5(実装は見ていない)。対象は作業木の枝 `3-3b/counterfactual-rest`(土台 `0239a3b`・未 commit)。本体の HEAD `35aa748`(3-1 の取り込みの後)と比べた。
- 読むだけで確かめた。書いたのはこの 1 本だけ。作業用の置き場(`_bc_review/`)は終わってから消した(data へのつなぎと試験用のつなぎは .NET の `Directory.Delete` で先に外した)。
- 封印した層・holdout・検証側の錨の値は開いていない。`tests/c7` は回していない。子サブは起動していない。

## 判定

**条件つき受入**。既定(申込書なし)の結果は変わらない(実装役の 19 構成+自分の 4 構成+2 日+再開)。T からの切り替え・(d) の分け・CP5-1/5-3・慣らしの器・技量スコアの隣の点数・HM の器は、発注文の項目どおりに入っている。ただし中の欠陥 2 件(慣らしの計器の指標の表で累積の値を流量と宣言している・計器の読む守りが大文字小文字とつなぎで抜ける)を直してから取り込むことを勧める。どちらも計器の側の数行の直しで、既定の結果には触らない。

## 欠陥(重さの順)

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | `tools/instruments/warmup_gauge.py:83`(指標 `conversations`) | 道筋 `probe.conv.opened` を `kind: "flow"` と宣言している。md23 の道具の probe の行の `conv.opened` は `ConversationManager.n_opened`(`engine/conversation.py:451` で足すだけで戻さない=ランの頭からの累計)。md23 の道具自身も表を作るときに前の日を引いて日ごとの数に直している(`multiday_md23.py` の `day_rows`)。このままでは、規則 `cumulative: reject` が禁じる累積の系列に MSER を当てることになる。宣言の `kind` だけを見て拒む作りなので、検査は黙って通る。再現: 1 日 20 件+慣らし 7 日を植えた合成の md23 の形(5 対・先行 28 日・20 種)で、宣言のままだと 20 種中 14 が「要延長」(d* が 25〜30 に寄る)・7 日に当たるのは 1。日ごとの差に直すと 20 種中 15 が 7 日目に当たる | `conversations` を累計の印(例 `kind: "counter"`=日ごとの差に直す)にするか、`stock` と同じ変換に通す。md23 の形の累計で当たらないことを示す試験を 1 本足す |
| M2 | 中 | `tools/instruments/warmup_gauge.py:118`・`tools/instruments/hm_gauge.py:70`(`check_path`) | 封印と検証側の語を、渡した文字列そのままで大文字小文字を区別して照らすだけ。`read_guard.deny_hit` は小文字にそろえて照らし、当たらなければ実体の道筋(つなぎ・symlink を解いた形)でも照らす(検収 L8 の教訓)。負の対照を自分で植えた結果: `data/KDDI_LA/x.json`・`docs/bench/anchors/Presence_Validation_Anchors_v0.json`・`data/REALWORLD_LIVE/x.json`(Windows では同じファイル)と、名に語を含まないつなぎ(実体は語を含む偽のフォルダ)の 4 形が、両方の計器で通った。`read_guard.deny_hit` は 4 形とも落とした | `check_path` の中身を `rg.deny_hit(path)` に替える(1 行ずつ)。大文字の形とつなぎの形の負の対照を試験に足す |
| L1 | 低 | `src/shibuya/engine/experiment/switch.py:157-164`(`_box_enter`) | 再生の箱は先に空にしてから「残った数」を数えるので、今の実装では `box_carried` と `box_at_switch` は作りから 0 になる。箱はどこからも読まれない(答えはテープか仮のモデルが返す)。負の対照(空にしない写し)で (b) が落ちるのは計器が数えるからで、ランの動きは変わらない(自分の再現: 空にしない写しで `box_left` 104,644・(b) 偽・a と d は真・T より前の behavior の食い違い 0・final は空にする写しと同じ `9a745705…`)。刻みの外へ物を持ち越さない守りの実体は、艦隊で録ったテープ(到着待ちの行)を拒む方(`tape_crossing`)と、プロジェクトの語の「再生の箱」=O96 `run_day.replay_inbox` | 記録 §0・§2 の「(b) の条件」を「箱の計器(作りから 0・空にする処理の退化を捕まえる)」と書き分け、守りの本体は到着待ちの行を拒むことだと明記する。あるいは T の刻みで O96 が空であることを (b) の条件に加える |
| L2 | 低 | `src/shibuya/engine/experiment/branch.py:588-613` | summary の `d` の意味が、札が mock・古典でない口では「A/A の厳密一致」から「T より前の一致だけ」に変わった。3-3 の契約(`v2-foundation-contracts-2026-10-13.md` §3-3 の約束 (4)(d)=A/A の差が厳密に 0)と食い違う。注入した決定論の口(試験の stub など)も、札から決めるので既定では非決定の扱いになり、(d) が弱くなる(`deterministic=True` で戻せる)。`d` は `None` もとりうる | 契約の約束 (4)(d) を「決定論の札は厳密一致・非決定は T より前の一致と床の分布」に親が書き直す。注入した口の既定の扱いを記録 §12 に 1 行足す |
| L3 | 低 | `tools/instruments/warmup_gauge.py` `_bundle` | 在庫の指標は流量に直すと最初の日が落ち、`first_day` が 1 になる。`d_star` はその系列の中の位置なので、慣らしの終わりの日は `first_day + d_star`。束ねの W は `d_star` の最大をそのまま取るので、在庫の指標が最大のとき問い 1 の W が 1 日短くなる。再現: 6 日間ふえる在庫(7 日目から定常)で `first_day` 1・`d_star` 6・W 6(正しくは 7) | 束ねでは日の番号(`first_day + d_star` − 系列の頭の日)で比べる。在庫の指標の W を確かめる試験を足す |
| L4 | 低 | 記録 `README.md:130`・`tests/tools/test_warmup_gauge.py:78` の注 | 延長の例を「22 で 12(無効)」と書いているが、実際は n=22 で d*=16(無効)。自分の MSER の実装でも計器でも 20 → 22 → 25 で d* は 12・16・12。試験の主張(長さの列と有効/無効の列)は正しい | 記録と注の数を直す |
| L5 | 低 | `src/shibuya/engine/experiment/warmup.py:66`・`:70-77` | `q2.fine_steps: 15` は「15 分ごと」を刻みの数で書いている(刻みの幅 60 秒が前提=T0 の直書き禁止の趣旨に触れる。計算には使っていない)。`MARKS` に印の無い規則の項がある(`statistic`・`q1.series`・`q2.series`・`q2.bounds`) | 秒(時間の定数の積)で持つか刻みの幅から出す。印の無い項に印を足すか、印が要らない理由を書く |
| L6 | 低 | `branch.py`(c) の第 2 段 | 非決定の口では、指紋の窓の回し直し(A/A の枝 b と改変の枝の 2 本目)も新しい種で答えるので、`branch_repeat_same` は作りから偽になる。第 1 段の 2 本で決めた窓が、2 本目の対の食い違いを挟む保証もない。自分の再現でも改変の枝の final は 1 本目 `7f184c9c…`・2 本目 `3180734e…` | 記録 §12 に「非決定の口では (c) の系と欄は床の揺らぎと混ざる(報告だけ)・`branch_repeat_same` は偽になる」と宣言する |
| L7 | 低 | `tools/instruments/skill_gauge.py:175` | 入力の道筋に読む守りが無い。答え合わせの段では観測を読むので、どの側の値を読んでよいかの線が要る | 親が線を決める(較正側だけなら warmup・HM と同じ守りを入れる) |
| L8 | 低 | `switch.py`(`ReplaySwitch`)・`warmup_gauge.py`(`METRICS`) | (b) が頼る計器の数(`box_carried` など)は普通の属性で、外から書き換えられる(3-3 の `BranchClient` と同じ扱い)。`METRICS` は dict の tuple で中身を書き換えられる(指紋は呼ぶたびに計算するので変更は指紋に出る) | 必要なら `__setattr__` の守りか `MappingProxyType`。急がない |
| L9 | 低 | `src/shibuya/engine/state_ledger.py:1409`・つなぎの台帳の 3 行 | 状態台帳の行 `experiment` の参照 `branch` の説明は「BranchClient」のまま(今は `ReplaySwitch` もありうる)。台帳の文に空白の抜け(「告知が無いかunexpected=true」「checks のpersona_naming」「札はmock」) | 親が文を直す(発注の範囲では行の追加だけだった) |
| L10 | 低 | 作業木の `_bc/`(未追跡・.gitignore の外・約 201 MB) | 実装役の byte-check の置き場が残っている。`git archive` で写した錨 3 本(検証側の錨のファイルを含む)も中にある | 取り込みの前に消す(明示の道筋でしか add しないので commit には入らないが、置いたままにしない) |

## 1. 結果不変 ✓

- 実装役の byte-check(`byte_check_cf33b.json`): 19 構成とも 25 欄が全部同じ。side の JSON(作業木の `_bc/`)で、head は 19 本とも `src_is_worktree` 偽・cf33b は 19 本とも真・`tree_missing` は空・切替口の環境変数は空=腕の既定は今の道。比べた head は `0239a3b`(作業木の土台)。
- **自分の 4 構成**(`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`・5,000 体・seed 1・1 日・テープつき): head=本体の HEAD `35aa748` の写し(`git archive` で src と `HEAD_TREE_FILES` の追跡ファイル+本体の data へのつなぎ・本体の最新の `byte_check_10e.py`=作業木の写しと 1 バイトも違わないことを diff で確認)と作業木の src。**4/4 構成で 25 欄とも同じ**。final は `b8eadcb51e8705e7`・`c88ba9104f45f897`・`e1288e092ddaca86`・`768b2262e3b0999e`、呼数は 64,528・50,006・51,655・67,794。head 側は `src_is_worktree` 偽・作業木側は真。3-1 を取り込んだ HEAD とも同じなので、rebase の後も既定の結果は変わらない見込み。

## 2. 口と約束 ✓(違いは L2)

- 3-3b の口の約束は契約書(`v2-foundation-contracts-2026-10-13.md`)に節が無いので、発注文と本検収の発注の名を正とした。`switch.ReplaySwitch`・`SwitchSpec`・`window_head_step`・`tape_crossing`・`vs_aa`・`determinism`、`ensemble.floor_values`・`floor_summary`・`skill_container` の `raw`・`evidence_container`、申込書の `unexpected`・`known_to_model`(既定のときは正準の形に書かない)、manifest の `experiment` の設定の子の末尾 4 つ(`switch`・`start0`・`known_to_model`・`warmup`)、`engine/experiment/warmup.py` の `RULE`・`MARKS`、`tools/instruments/{warmup,skill,hm}_gauge.py` が名のとおりにある。
- 〔決定〕仮-24 の各項は反映されている: (d) の分け・MSER の作法(後半なら無効で 10% 延長・累積は使わない・複数本を平均してから・1 日でまとめる)を差の系列に・原系列は感度の腕+宣言・在庫は流量(計器の側の欄=置き場)・月の周期は推移の指標・HM は離散の seed の組だけ・封印の証拠は git+push の欄(値は空)・CP5-1 は警告と記録で拒まない・技量スコアの隣に fair CRPS・rank histogram・spread/skill。食い違いは L2(3-3 の契約の (d) の文)だけ。
- 試験の無い約束: 非決定の口の (c) の第 2 段の扱い(L6)・在庫の指標の W(L3)・累計の道筋の扱い(M1)・守りの大文字とつなぎ(M2)。そのほかの約束には試験がある。

## 3. 発注文の各項

| 項 | 判定 | 根拠 |
|---|---|---|
| 1 T からの切り替え | ✓ | T より前はテープ(LLM を呼ばない)・T から仮のモデル・T は窓の頭(違えば止める=自分の再現で正午+20 秒は ValueError・基準のランを幅 20 秒で録れば同じ時刻を受け、切り替えの刻みは 2,161)・艦隊の到着待ちの行は拒む・保存の間隔は不変。箱の計器は L1 |
| 2 (d) の分け | ✓ | `d_determinism`・`d_floor`・(c) の `aa_coarse`・`vs_aa`。3-3 の欄は名も並びもそのまま(意味の変化は L2) |
| 3 CP5-1 | ✓ | 始まり 0・改変あり・(告知なし か `unexpected: true`)で `ExperimentWarning` と `experiment.start0`。拒まない。「最初から」の順番は宣言と欄だけ |
| 4 CP5-3 | ✓ | `known_to_model`(自己申告・空なら正準の形に書かない)・名指しと混入を同じ道具 `naming_hits` で探す。ランの中では走らない(宣言あり) |
| 5 慣らしの器 | △ | 規則・事前登録の形・合成の試験は発注どおり。指標の表の宣言に誤り(M1)・在庫の W(L3)・読む守り(M2) |
| 6 技量スコアの隣の点数 | ✓ | 既知の値と解析解で確かめた(§6) |
| 7 HM の器 | △ | 式・閾値・2 番目に大きい値・候補と観測の守りは正しい。道筋の守りに抜け(M2) |
| 8 manifest・状態台帳・台帳 | ✓ | §5 |

- 「できなかったこと」の申告(実際のランの対での慣らしの判定・pymser との値の照合・実 LLM の床)は実態と合う。試験の本数(新規 45)も数え直して合った(11+12+6+1+8+4+3)。

## 4. 守り

- 書く口: manifest の `experiment.start0`・`warmup`・`switch` は `ExperimentLayer.manifest` の 1 か所。4 つの確認の結果は 3-3 の `record_checks` のまま(1 回だけ)。`RULE`・`MARKS` は入れ子まで `MappingProxyType`(試験が代入の TypeError を確かめる)・`SwitchSpec` と申込書は凍結の dataclass。計器の数と `METRICS` は L8。
- 負の対照: 窓の頭でない T・到着待ちの行・空にしない箱(口の単体と合成の世界の分岐)・累積の系列・係数の候補・検証側の観測・封印の道筋は試験にある。**自分で植えた負の対照**: 空にしない箱(`_box_reset` を何もしない関数に差し替え=実装役の写しと別の形)で (b) が偽・`box_left` 104,644(合成の世界 60 体・2 日)。読む守りの大文字とつなぎは抜けた(M2)。

## 5. 宣言と凍結 ✓

- 系の表・`writes.paths`/`writes.soa` は触っていない(新しい系は無い)。状態台帳の行は足していない(切り替えの口は既存の行 `experiment` の参照 `branch` の先=3-3 の `BranchClient` と同じ扱い・説明の文は L9)。
- 凍結の表: `CONFIG_PATHS_SHA256` を作業木の src で計算し直して `5de319d8…faee132b` と一致。足した 4 本を外すと `8c1610ad…5209d43` に戻ることを確かめた(増えた分だけ)。manifest の一番上の鍵と既存の子の値は不変(既定のランは `experiment` が null)。既定のランで動くのは `bridges_count`(398 → 407)と `bridges_version` だけ(つなぎの台帳の行を足したため・byte-check の欄の外・記録 §8 に宣言あり)。
- つなぎの台帳: 末尾に 9 行。全部に `remove_at`・`conf`・`declared_in`・`remove_basis` がある。発注の指定(CP5-1 の順と HM の候補は 4-1・差の系列と 5 本は expedient・最低 1 週間は未リサーチ)と合う。

## 6. 同値と独立の再計算

- **1,000 体の分岐の例**(自分の道具=店の選び方・雑音の口・床の数え直しを自分で書いた・世界資産・seed 1・2 日・v3・checkpoint 60): 申込書の指紋は実装役と同じ `1406365e…`(200 店)・基準の final `425c22a3…`。mock の腕: a・b・d・ok が真・(c) 粗い比べ 2,219・世界 2,160(`pois.open_now`・`O73:runner.opening.n_events`・`n_fallback`)・A/A の食い違いなし・床 0・T より前と後の checkpoint 各 12 本・再生の計器 5,190/8,502/箱の最大 358/0/0・最初に仮のモデルが答えた刻み 2,160。実装役の数と全部同じ。毎回種の違う mock の腕: 札は非決定・(d) 真(厳密一致は求めない)・T 以後の 12 本が全部食い違い(最初 2,219)・`vs_aa` の差 0・呼数の差 −74(実装役は −5=種が違うので値は違ってよい)。床は自分で payload から数え直して `d_floor` と一致。
- **MSER**: 原典の定義 MSER(n, d) = S²(n, d)/(n − d)(S² は 1/(n − d) の分散)=Σ(y − Ȳ)²/(n − d)² を、後ろからの累積和で計算する別の書き方で実装し、候補 d ≤ n − 5・d* > n/2 で無効・10% 延長(切り上げ・最低 1)・3 回で未収束の規則を自分で書いた。植えた 7 日(5 本の平均・40 日): 300 種で計器と d* が 300/300 一致・7 を下回る 0・ちょうど 7 が 182(60.7%)・中央値 7・90 分位 19・1 本だけは 164(54.7%)。延長 20 → 22 → 25(d* 12・16・12=L4)。累積の負の対照 42/50 対 2/50。差の系列 27/40 対 原系列 0/40(計器の問い 1 と規則の d* が 40/40 一致)。小さな系列の曲線の差の最大 0.0。
- **技量スコアの隣の点数**(解析解): N(0,1) の 5 メンバーと N(0,1) の観測で、fair CRPS の期待値 1/√π=0.56419 に対し、40 万例・3 種で 0.56321・0.56404・0.56413(標準誤差 0.0008・ずれは最大でその 1.2 倍)。通常の CRPS は (2 − (M−1)/M)/√π=0.67703 に対し 0.67534(20 万例・同じ標本の fair は 0.56258=どちらも −0.0017 前後の同じずれ)。計器の fair CRPS は自分のベクトル計算と 4,000 例で一致。点の予測の CRPS は絶対誤差(√(2/π)=0.798 に対し 0.802)。広がりと誤差の比は補正つきで 1.002・補正なしで 0.915(√(M/(M+1))=0.913)。広がり不足の例(メンバーの SD 0.5)で 0.54。rank histogram は 6 つの枠の割合が 1/6 から最大 0.5 点のずれ。N(0,1) の y=0.5 の閉じた形 0.331404 に対し、分位点 4,000 本のアンサンブルの通常の CRPS 0.331404。
- **HM**: 手で計算した I(z=12・3 本 10/11/13・観測の分散 0.25・食い違いの分散 0.5)=0.37966 が計器と一致。I がちょうど 3 は残し 3.5 は除く(2 番目に大きい値)。係数の欄・小数の seed・真偽の seed は ValueError、検証側と side の欠けは PermissionError。
- **2 日のラン・再開**(自分の道具・5,000 体・2 日・v3・checkpoint 360): 作業木と HEAD `35aa748` の写しで final `b346bb6e…`・呼数 138,946・checkpoint 8 本(behavior と full)が全部同じ。作業木で 1 日目の終わりで止めて再開したランの final と 2 日目の 4 本が通しと同じ。`experiment` は null。
- **AST**: 3-3b の口を呼ぶ所は `cli.main`(`--experiment-branch` のときだけ `run_branch`)・`make_layer`(申込書が無ければ最初に `None` を返す・その後で `warn_start0` と `make_client`)・`ExperimentLayer.manifest`・`ensemble.preregister` だけ。申込書の無いランはどこも通らない。

## 7. 試験

- 範囲の試験(発注の範囲=`tests/engine/experiment`・`tests/tools`・`systems`・`batching`・`body`・`time`・`events`・`bridging`・`test_resume_10d.py`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/economy/cp2`・`tests/c8`・`tests/llm`・`-m "not slow"`・2 並列・`--dist loadfile`): **1,397 passed・failed 0・skip 0(18 分 52 秒)**。集めた数は 1,424(slow の 27 を外した)。実装役の「発注の範囲だけの 1 回目」1,412 との差 15 は `tests/test_cli.py` の本数(15)と合う。slow(5,000 体の分岐)は回していない(1,000 体の分岐は §6 で自分の道具で回した)。
- `lint-imports`(作業木の src・248 ファイル): 5 契約とも KEPT・0 broken。
- `tests/c7` は回していない。

## 8. 抜け道と記録

- (a) 既定の不変: §1・§6(19 構成+4 構成・2 日・再開・AST)。`run_branch` の既定が `ReplaySwitch` になったのは分岐のときだけで、申込書の無いランは `make_layer` が最初に `None` を返す。
- (b) T からの切り替え: §3 の 1。負の対照(空にしない箱)を自分で再現(§4)。箱の意味は L1。
- (c) (d) の分け: §6 の 1,000 体の例で再現。3-3 の申込書の指紋は `known_to_model` が空・`unexpected` が null のとき 3-3 の正準の形と同じ(試験と読みで確認)。
- (d) CP5-1・CP5-3: §3。
- (e) 慣らしの器: §6 の MSER。M1・L3・L4・L5。候補の範囲 d ≤ n − 5 は R-117 §4-6 のとおりだが、R-117 §4-4 の pymser の説明(「n − 3 番目まで=最後の 2 つを除く」)と同じ数え方なら「最後の 5 つを除く」は d ≤ n − 6 になる(1 つずれる)。親が原典で確かめる項。
- (f) 技量スコアの隣の点数: §6。封印の証拠の欄は値が空・第三者の時刻印は偽。
- (g) HM: §6。読む守りは M2。
- (h) 共有ファイルと台帳: `git diff --stat` の 9 ファイル+新しいファイルと記録 §10 の一覧が合う(共有は `manifest_sections.py`・`test_env_and_sections_10f.py`・`bridging-ledger.json` の 3 本)。識別子に新しい `open`/`tick` は無い(`request.tick`・テープの列 `tick`/`observed_tick`・md23 の道筋の文字列 `probe.conv.opened` は既存の名)。記録に絶対パス・ホスト名・個人名は無い(LF)。
- 3-3 の台帳の 3 行: `DOC-cf33-start-zero-order`(CP5-1 の点検と CP5-3 の道具はできた=残りは順番の口と組み立ての中の点検)・`DOC-cf33-burn-in-not-judged`(判定の器と規則の登録はできた=残りは実際のランの対での判定)・`DOC-cf33-skill-empty`(生の点数の欄と計器はできた=残りは値と公開の置き場 `docs/predictions/`)。どれも「未実装」と書いた文が古くなった。外す段は 3-3b の行と同じ(4-1・7・7)なので、親が文を「残り」に書き直すか、3-3b の行を指して閉じるかを決める(材料: 重なりは `DOC-cf33-burn-in-not-judged` と `DOC-cf33b-warmup-difference-series`/`-counts` が最も大きい)。
- **rebase の見込み**(本体 `0239a3b` → `35aa748` の間に 3-1 が入った): (1) `docs/design/bridging-ledger.json` の末尾=3-1 の 12 行と 3-3b の 9 行が両方とも末尾に足すので衝突する(両方残すと 419 行・`bridges_count` 410 → 419)。(2) `tests/engine/test_env_and_sections_10f.py` の `CONFIG_PATHS_SHA256` とその注=衝突する。両方の設定の子(3-1 の `calendar_shadow` 4 つ+3-3b の `experiment` 4 つ)を入れた値は、作業木の `config_paths()` に 3-1 の 4 本を足して並べ直した計算で `63a87f2f1fcfd2e7dcd14e17f8f7bfe03338785a46282fff31ec1d0d40eab3ed`(同じ計算で 3-3b の 4 本を外すと本体の `68c3ffd0…` に戻ることを確かめた)。(3) `src/shibuya/engine/manifest_sections.py` は別の塊(3-1 は body の後に calendar_shadow・3-3b は experiment の子)なので自動でまとまる見込み。(4) 3-1 が直した `tests/engine/bridging/*`・`tests/c8`・`tools/c8/sensitivity_v1.json` は 3-3b が触っていない。

## 親に確かめてほしいこと

1. M1・M2 を直してから取り込むか(どちらも計器の側・既定の結果は不変)。
2. 3-3 の契約の約束 (4)(d) の書き直し(L2)と、注入した決定論の口の既定の扱い。
3. 3-3 の台帳の 3 行の扱い(§8 (h))。
4. 慣らしの候補の範囲 d ≤ n − 5 か n − 6 か(§8 (e)・実装役の記録でも △)。
5. 窓の頭でない T を止める形(3-3 では切り上げて受けていた=CLI の `--experiment-branch` の振る舞いが変わる)でよいか。
6. 箱の計器の位置づけ(L1)と、技量スコアの計器の読む線(L7)。
