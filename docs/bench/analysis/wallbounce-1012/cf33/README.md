# 第 3 期 3-3 反実仮想の器の実装の記録

- 実装役 Opus 5.5。作業木の枝 `3-3/experiment-form`(作った時の土台 `740508c` → 検収の後に本体 `21cd044`(2-2・2-1 と文書を取り込んだ後)へ rebase=§15)。commit は親。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-5(CP5-1〜CP5-6・CP12・CP14・探索と確認・複数ランの作り方)・§1-1(CP6=実験が世界に入れるのは「決定」だけ)・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) の 3-3 の行と §4 の CP14 の親案・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3(新しい問いは既定 off の腕で仮採用)・[答申 R-71](../../../../research/v2-r71-stochastic-comparison-statistics.md) §1-6(4 つの確認)・§2(対の並べ替え検定・本数と p の下限)。
- **§0〜§13 は検収と rebase の後の今の形**(直したところは §14・rebase は §15)。検収の記録は [review.md](review.md)(検収役)。
- 数は実測。生の出力(テープ・状態のファイル・side の JSON)は作業木の `_bc/`(git の外・取り込みの前に消す)。比べた結果と道具だけをこのフォルダに置く。道具は `tools/branch_example.py`(§4 の分岐の例)。byte-check は既存の `10e/byte_check_10e.py`。

## 0. 結論

- **作った**: 新しい置き場 `src/shibuya/engine/experiment/` に、申込書 `form.py`・効かせる口 `apply.py`・ランに置く口と系と manifest の `layer.py`・T0 で切り替える分岐と R-71 の 4 つの確認 `branch.py`・探索と確認の封印(単位=初期状態)とランの入口の検査と事前登録(CP14)と対の差の形 `ensemble.py`。ランの種類 `counterfactual`・CLI の 4 つの引数・manifest の末尾 `experiment`・状態台帳の行 `X`・系 `experiment`(申込書を渡したランだけ立つ)。
- **使わないとき不変**: 申込書を渡さないランは byte-check で、rebase の前 **19/19 構成**・rebase の後 **4/4 構成**とも 25 欄が本体と同じ(§7)。
- **効かせる口**: L0(天気の日付の差し替え・祝日)と L1(営業時間の変更・休業・催しの告知)を実装。L2〜L4 は欄だけ(「宣言して未実装」と記録して続ける)。決定は出来事ログに 1 回(原因=実験の条件・口は `gate.admit` だけ)・告知は宛先ごとの「届いた情報」の行。効かせていない改変は理由つきで数えて続く(§3)。
- **分岐と 4 つの確認**(rebase の後・世界資産・2 日・T0=2 日目の正午・200 店の休業): 1,000 体と 5,000 体の両方で (a)(b)(d) が通り、(c) 世界の最初の食い違い=**刻み 2,160・系 `world`・欄 `pois.open_now`**(と営業時間の過程の計数)。(c) は T0 以後の全 checkpoint を走査して窓を決める形にした(検収 L1)。
- **実行の内訳**(親の判断 M3・4 つの確認とは別の欄 `executed_by_agents`): 1,000 体は担当 0 人=対象の店の開け閉め 200 件が全部つなぎ。5,000 体(担当のいる店 2,337)は対象の 200 店すべてに担当がいるが、**担当が実行した 1 件・つなぎ 199 件**(担当が店のセルに居ない)=`executed_by_agents` は偽(§4)。§1-1 の「分岐でフォールバックを使わない」は 6-6 まで宣言のまま。
- **見つけたこと**: (1) 担当がいても正午の店にはほぼ居ない=開け閉めはほぼつなぎ(2) manifest の設定の節に再開で必ず動く計器 `group_norms.cost.ticks` がある((a) で宣言した値のときだけ許した)(3) 系ごとの指紋の代わりの digest(`X:`)は物の番号を含み、ランをまたいで比べられない=(c) から外して名を報告。
- 試験 90 本(`tests/engine/experiment/` 5 ファイル・slow 1 本)。範囲の試験(rebase の後)1,376 passed。仮採用と限界は §11(**規律の記録: 1 回目の全体の試験で `tests/c7` を回した**)、親に確かめてほしいことは §12。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/experiment/form.py`(新) | 申込書 `ExperimentForm`(凍結・入れ子も `MappingProxyType`/tuple・直に作っても `__post_init__` が同じ検査=検収 L3)・決定の表 `DECISIONS`(L0〜L4・実装したか)・`from_dict`/`from_json`/`load`/`to_json`(鍵の昇順・区切りの空白なし)・`sha256`・`registration_digest`(CP14 の登録の指紋)・`aa`(改変を空にした A/A の枝・元の登録の指紋を `aa_of` に残す=検収 L4)・`start_step`(T0 の刻み=切り上げ) |
| `src/shibuya/engine/experiment/apply.py`(新) | 効かせる口 `apply(form, world, t)`(唯一の口)・`WorldHandle`(口が触る世界の物の束と控え `rec`)・`ApplyRecord`(控え=計数 `tallies`)・L0 と L1 の実装・効かせていない理由の表 `REASONS`・決定の実装の表 `_IMPL`(どちらも読み取り専用=検収 L6)・`targets_of` |
| `src/shibuya/engine/experiment/layer.py`(新) | 申込書の受け渡し `staged`/`current`(文脈の変数=`run_day` の引数は増やさない)・封印の入口 `entrance`・持ち主 `ExperimentLayer`(欄は 1 回だけ置ける・4 つの確認の結果は口 `record_checks` で 1 回だけ=検収 M4)・組み立ての口 `make_layer`・系の関数 `sys_experiment`・再開の検査 `check_resume`・見出しの欄 `state_header`・manifest の `manifest_fields` |
| `src/shibuya/engine/experiment/branch.py`(新) | `BranchSpec`・T0 で切り替える LLM の口 `BranchClient`(計器 `replay_meter`)・`run_branch`(4 本のラン・4 つの確認・実行の内訳・`branch_report.json`)・確認の関数(`input_match`・`pre_t0_match`・`first_divergence_coarse`・`probe_first_divergence`・`aa_match`・`choose_state`・`execution_breakdown`・`executed_by_agents`) |
| `src/shibuya/engine/experiment/ensemble.py`(新) | 封印 `seal`/`Seal`(単位=初期状態・指紋と数だけを持つ=親の判断 M2)・`members`(自分の半分だけ)・ランの入口の検査 `entrance`(親の判断 M1)・`seal_record`・`preregister`(CP14 の公開の記録の JSON)・`paired_values`/`metrics_spec`(`salt_compare.py` の形)・`pairs_status`・`skill_score`/`skill_container`(器だけ) |
| `src/shibuya/engine/experiment/gate.py` | `admit` に `via`・`received_ns` の欄(既定は 1-3 と同じ)。呼び手は `apply.py` だけ(docstring) |
| `src/shibuya/engine/experiment/__init__.py` | 置き場の説明 |
| `src/shibuya/engine/events/vocab.py` | 族 `実験`(末尾)・語 `改変`(60)・`届いた情報`(61)・版 `events-vocab/3-3`(2-1 までの 60 語のコードは不変) |
| `src/shibuya/engine/calendar.py` | `SimCalendar.set_holiday`(祝日の表を書く唯一の口=検収 L5。呼ぶのは `apply.py` だけ) |
| `src/shibuya/engine/processes/opening.py` | `set_plan_rows`(対象の店の営業時間の表の行を差し替える)・`restore_plan_rows`(その日の W7 の行に戻す)。呼ぶのは `apply.py` だけ |
| `src/shibuya/engine/processes/environment.py` | `set_replay_date`(その日の再生日を W13 の別の日に・日の出と影は暦の日付のまま)。呼ぶのは `apply.py` だけ |
| `src/shibuya/engine/systems/table.py` | 系 `experiment`(刻みの中の最初・`when="experiment"`・`paths="X:experiment.* E:events.* O56:runner.environment.*"`)・day_close・drain・close_final の `reads` に `layers.experiment`(検収 L7) |
| `src/shibuya/engine/systems/conductor.py` | 立つ条件 `WHEN["experiment"]`(持ち主が居るランだけ) |
| `src/shibuya/engine/systems/boxes.py` | `Layers.experiment`・`Fixtures.experiment`(既定 None)・`OWNER_NAMES` の末尾(2-2 の `proximity` の後)に `experiment` |
| `src/shibuya/engine/systems/build.py` | `current()` で申込書を受け取る・世界を触る前に封印の入口の検査・再開の見出しの検査・`make_layer`(分岐なら LLM の口を包む)・箱に置く |
| `src/shibuya/engine/systems/state_io.py` | `hash_owners` の末尾に `experiment`・申込書つきのランだけ状態の見出しに `experiment`(2-2 の `proximity`・2-1 の `economy_stage2` の後) |
| `src/shibuya/engine/systems/run_end.py` | `result.experiment_layer`(manifest が読む) |
| `src/shibuya/engine/run.py`・`manifest_sections.py` | manifest の末尾 `experiment`(鍵 119・混ざった辞書=設定 17・観測 7) |
| `src/shibuya/engine/state_ledger.py` | 行 `X`(diag・discardable・外の状態の末尾=2-1 の `EM` の後)・持ち主 `experiment`・除外 2 行 |
| `src/shibuya/engine/run_kind.py` | `decide(counterfactual=)`(試験 > 反実仮想 > 腕 > 再現)。expedient の段落の文は変えず後ろに段落を足した(つなぎの台帳の行の写しの元) |
| `src/shibuya/cli.py` | `cli.run(experiment=, experiment_aa=, experiment_branch=, experiment_model=)`・`--experiment`・`--experiment-branch`・`--experiment-model`・`--experiment-aa`・`run` の呼び出しを `run_kwargs` に組んでから呼ぶ形に(分岐に同じ引数を渡すため・引数は同じ)・ランの種類の決め方に 2-2 の近接の腕の条件と `counterfactual` を合わせた |
| `docs/design/bridging-ledger.json` | 行を 12 足した(§10) |
| 凍結の表と数の試験(増えた分だけ) | §9 |
| `tests/engine/experiment/`(新) | §8 |

## 2. 申込書の欄

知らない欄は `ValueError`(一番上・`subject`・`notice`・`metrics` と各指標・`ensemble`・決定の欄・`preregistration`=試験 8 形)。`to_json` は鍵の昇順・区切りの空白なしの正準の JSON(既定を埋めた形=同じ申込書は同じ指紋)。`ExperimentForm(...)` を直に作っても同じ検査が走る(正準の形でない=並びの崩れた番号なども `ValueError`)。

| 欄 | 型と中身 | 既定 |
|---|---|---|
| `schema` | `shibuya.engine.experiment/form/1` | 省略可 |
| `kind` | `explore`(探索)/`confirm`(確認)。日本語の `探索`・`確認` も受ける | 必須 |
| `subject` | `level`(L0〜L4)・`ids`(対象の番号=L1 は POI の番号・L0 は空)・`category`(POI の種別の名=申込書の値で受ける・W7 の資産の `poi_cat_names` と照合) | `ids` 空・`category` null |
| `content` | 決定の列 `{"decision": 名, …欄}`。名と欄は `DECISIONS`。水準は `subject.level` と同じでなければエラー。空の列=A/A の枝 | 空 |
| `start` | 始まり T0(通しの時刻のナノ秒・0=最初から)。T0 の刻みは切り上げ | 0 |
| `end` | 終わり(ナノ秒・`start` より後)。null=ランの終わりまで | null |
| `notice` | 告知=`to`(体の番号か `staff`=対象の店の担当)・`at`(ナノ秒・`start` 以後・`end` より前・null=始まり)・`via`(1-3 の `VIA_WORDS` から「無し」を除く) | null |
| `question` | 問い(空でない文) | 必須 |
| `metrics` | `primary`(主 1 つ)・`secondary`(副の列)。各指標 `id`・`path`(checkpoints の JSON の道筋)・`direction`(`greater`/`less`/null)・`description` | `primary` 必須 |
| `ensemble` | `initial`・`model`(札の列)・`chance`・`aa`・`seed0` | 1・`["mock"]`・1・true・1 |
| `preregistration` | 確認だけ=`seal_sha256`・`registration_sha256`(16 進 64 字)。探索に書くとエラー・確認に無いとエラー・`registration_sha256` が `registration_digest()` と違うとエラー | null |
| `aa_of` | A/A の枝の印=元の申込書の登録の指紋(`aa()` が置く)。置いた申込書は改変と告知が空。確認の A/A の枝は事前登録を引き継ぎ、`aa_of` が事前登録の `registration_sha256` と同じでなければエラー | null |

決定の表(`DECISIONS`):

| 水準 | 決定 | 欄 | 実装 |
|---|---|---|---|
| L0 | `weather_date` | `replay_date`(W13 の日) | ○ |
| L0 | `holiday` | `date`・`on`(既定 true)・`name`(既定「休日」) | ○ |
| L1 | `opening_hours` | `hours`([[開く分, 閉じる分], …]・閉じる分は翌日の分まで=W7 と同じ) | ○ |
| L1 | `closure` | なし | ○ |
| L1 | `event` | `at`・`until`(ナノ秒・任意) | ○(決定と告知の行まで) |
| L2 | `passage`・`barrier` | `open` / なし | 宣言だけ |
| L3 | `construction` | なし | 宣言だけ |
| L4 | `fare`・`service_suspension`・`new_store`・`visitors` | `amount_yen` / なし / なし / `scale` | 宣言だけ |

地名と業種名はコードに書かない: `engine/experiment/` の全ファイルの本文と文字列の値を、試験の側に置いた日本語の固有名詞(地名・施設名・店の名 34 語)と業種名(33 語)の一覧と突き合わせる(負の対照つき)。対象は番号か申込書の値の種別名で受ける。

## 3. 効かせる口の対象

- 口は `apply(form, world, t)` の 1 つ。系 `experiment`(刻みの中の最初=日の頭の後)が毎刻み 1 回呼ぶ。決定が始まる刻み(`start` 以後の最初の刻み)に 1 回だけ、決定を世界の「表」に入れ、出来事ログに `実験:改変` を 1 行書く(原因=実験の条件 `"<申込書の指紋の先頭 16 字>:<決定の番号>"`・口は `gate.admit`)。効いている間は日が替わるごとに表へ当て直し(過程が日の頭で W7・W13 から張り直すため)、`end` の刻みで表を元に戻す。
- 表を実行するのは世界の中の過程と人(営業時間の表は `OpeningProcess.step` が担当の従業者に開け閉めさせる・居なければ今の conf 0.5 のつなぎ)。エンジンが申込書のために代わりに実行する仕組みは足していない。実行の内訳は分岐の報告に出す(§4)。
- 告知: 宛先ごとに `実験:届いた情報` を 1 行(`whom`=宛先・`via`・`received_ns`=届いた時刻・原因 `"<指紋>:notice"`)。`staff` は対象の店の担当(権利台帳の雇用の行)。
- 口を呼ぶのは系 `experiment` だけ。`gate.admit` を呼ぶのは `apply.py` だけ。表の書き口(`set_plan_rows`・`restore_plan_rows`・`set_replay_date`・暦の `set_holiday`)を呼ぶのも `apply.py` だけ(AST の試験・負の対照=別名と直の import・別の物の `admit` は数えない)。1-3 の負の対照(口の外から実験の条件を作れない)は残る。

| 水準 | 決定 | 世界の表 | 当て直し | 終わり |
|---|---|---|---|---|
| L0 | 天気の日付の差し替え | 再生日(`EnvironmentProcess.set_replay_date`=天気は差し替えた日・日の出と影は暦の日付・日ごとの記録の `how=experiment`) | 日ごと(日の頭の引き直しの後) | その日の天気を引き直す |
| L0 | 祝日 | 暦の祝日の表(`SimCalendar.set_holiday`=ランごとに読んだ表・翌日以後の日付だけ=当日の表は日の頭で張り直し済み) | なし(再開は組み立ての中で先に当てる) | なし |
| L1 | 営業時間の変更・休業 | 対象の店の営業時間の表の行(`OpeningProcess.set_plan_rows`) | 日ごと | その日の W7 の行に戻す |
| L1 | 催し | 表は変えない(決定と告知の行) | なし | なし |
| L2〜L4 | 宣言だけ | — | — | — |

効かせていない改変は記録して続ける(計器 `unapplied`・行に理由の鍵と文・同じ決定は 1 回だけ数える・試験 8 形):

| 理由の鍵 | 文 |
|---|---|
| `no_target` | 対象が無い(番号が世界に無い) |
| `no_category` | 対象の種別が世界に無い |
| `no_w7` | 営業時間の表(W7)が無い世界(合成の世界) |
| `no_w13` | 気象の資産(W13)が無い世界 |
| `no_replay_date` | 再生日が W13 に無い |
| `before_begin` | 期間の外(分岐の元の状態より前に始まる) |
| `after_end` | 期間の外(終わりの後) |
| `past_day` | 期間の外(当日以前の暦) |
| `holiday_table` | 祝日の表が書けない |
| `not_implemented` | 宣言して未実装(L2・L3・L4) |
| `no_recipient` | 告知の宛先が無い |
| `not_started` | 期間の外(ランの終わりまでに始まらない=終わったランの manifest で数える) |

## 4. 分岐と 4 つの確認(R-71 §1-6)

**組み立て**(`branch.run_branch(form, 基準のランの記録, runner=cli.run, run_kwargs=…)`・CLI `--experiment <申込書> --experiment-branch <記録>`):

- 基準のランの記録=既存の引数で作れる置き方: `tape/`(`--tape`)・`state/`(`--state-out`・日の境目の状態)・`checkpoints.json`(`--checkpoints-out`)。
- T0 より前の最後の日の境目の状態(`next_T < T0`・`finished: false`)から再開する(無ければ 0 から)。T0 と同じ境目は使わない(T0 より前の窓が要る)。
- LLM の口を `BranchClient` に包む(組み立ての中・`bridge.client`)。T0 より前の呼はテープの完全一致(`Replay.lookup`)で答える=LLM を呼ばない。テープ外は数えて `TapeMiss`(橋が数えて空の応答=実 LLM へは落とさない)。古典の方策(`ClassicalPolicy`=内部の状態を持つエンジンの方策)は T0 より前も方策に答えさせ(状態を同じに進める)、テープの答えとの食い違いを数える。T0 からは今の方策。
- **4 本のラン**(検収 L1): 第 1 段=A/A の枝 a と改変の枝を指紋なしで回し、T0 以後の全 checkpoint を走査して最初に behavior-hash が食い違った checkpoint と、その前で一致した最後の checkpoint を見つける。第 2 段=A/A の枝 b と改変の枝をもう 1 本、その間の刻みの窓(最大で checkpoint の間隔)に系ごとの指紋(`engine.systems.probe.Probe` の帰属をそのまま使い、行に欄ごとの digest を残す)をかけて回す。食い違いが無ければ第 2 段の改変の枝は回さない。
- engine は cli を import できない(cli は economy を import する=層の契約)ので、ランを回す口は呼び手が渡す(`runner=cli.run`)。`tools/c7/salt_compare.py` は import しない(確認の関数は同じ形を engine の中に持つ・検定は §5 の形で道具に渡す)。

**4 つの確認**(毎回・結果は `<記録>/branches/<申込書の指紋の先頭 16 字>/branch_report.json` と、改変の枝の manifest の `experiment.checks`=持ち主の口 `record_checks` で 1 回だけ書く):

| 確認 | 中身 | 合格の条件 |
|---|---|---|
| (a) 入力の一致 | 基準と各枝の manifest の設定の節の差(節の表は基準の manifest の `manifest_sections`)・seed の 3 つ・最初の checkpoint の母集団と日課のハッシュ | 設定の差が腕の欄(`run_kind`・`experiment`)と決定から導かれる欄(天気 → `replay_date`・`weather`/祝日 → `calendar`)と、再開で動く欄の宣言どおりの値(`group_norms.cost.ticks`=基準 2,880・枝 1,440)だけ |
| (b) T0 より前の一致 | 刻み < T0 の全 checkpoint の behavior-hash(各枝と基準)・T0 より前のテープ外の呼・古典のテープとの食い違い・基準の自己一致(再開に使った基準の状態の見出しのハッシュ=基準の manifest のその日の締めの後のハッシュ・欄 `base_state_matches_base_end_of_day`=検収 L2) | 全部同じ・0・0・同じ(T0 より前の checkpoint が無ければ「未検査」=None) |
| (c) T0 以後の最初の食い違い | 粗い比べ(T0 以後の全 checkpoint で最初に behavior-hash が違う checkpoint と違うハッシュの名)と、その窓の系ごとの指紋の行の最初の食い違い (刻み, 系, 欄)。申込書の欄(`X:`)と出来事の記録(`E:`)を除いた「世界」と、除かない「全部」の 2 つ。ランをまたいで比べられない digest(物の番号を含む代わりの digest `X:`=`O61:runner.log`・`O63:renderer._tickc`・`X:experiment.handle`)は外して名を報告。改変の枝の回し直しの final が 1 本目と同じか(`branch_repeat_same`) | 報告(合否なし)。見つからなければ None と理由 |
| (d) A/A | A/A の枝 2 本の全 checkpoint(刻み・behavior・full)と final が厳密に同じ・A/A の枝の final が基準の final と同じ | 全部同じ |

**実行の内訳**(親の判断 M3・`execution` と summary の `executed_by_agents`): 対象の店の T0 以後の開け閉め(ActualLog の `store_opening` の行)のうち、担当の従業者の役割行動とつなぎ(conf 0.5)の件数・担当のいる店の数。`executed_by_agents`=表を実行する決定(営業時間・休業)があり開け閉めが 1 件以上あるとき、つなぎが 0 件なら真。決定 10-12 §1-1「分岐の実験ではフォールバックを使わない」の判定で、summary の `ok`(4 つの確認だけ)には入れない。

**分岐の例**(rebase の後・世界資産・seed 1・2 日・語彙 v3・checkpoint 60 刻み・道具 `tools/branch_example.py`): T0=2 日目の正午(刻み 2,160)。申込書=L1 の休業(正午に W7 で開いている 2,059 店のうち番号の小さい 200 店)・告知は宛先 `staff`(対象の店の担当)と体 1・2・3・道具 メッセージ。

| | 1,000 体([branch_example_rebased.json](branch_example_rebased.json)) | 5,000 体([branch_example_5000_rebased.json](branch_example_5000_rebased.json)) |
|---|---|---|
| (a) | ok(A/A・改変とも)。設定の差=`experiment.*`・`run_kind`(reproduction → counterfactual)・`group_norms.cost.ticks`(2,880 → 1,440=宣言どおり) | 同じ |
| (b) | ok。再開 `state-T00001440.npz`(基準の自己一致 ok)・T0 より前の checkpoint 12 本が全部同じ・テープから答えた呼 5,260・テープ外 0 | ok。同じ形・テープから 31,302 呼・テープ外 0 |
| (c) | 粗い比べ=刻み 2,219(T0 以後で最初の checkpoint・5 つのハッシュが違う)・窓 2,160〜2,219・**世界=刻み 2,160・系 `world`・欄 `pois.open_now`・`opening.n_events`・`opening.n_fallback`**・全部=刻み 2,160・系 `experiment`・回し直しの final は同じ | 粗い比べ=2,219・窓 2,160〜2,219・**世界=刻み 2,160・系 `world`・欄 `pois.open_now`・`opening.n_events`・`n_fallback`・`n_role_actions`・`shelf.n_no_backroom`・`agents.last_result_tick`**・全部=2,160・系 `experiment`・回し直しの final は同じ |
| (d) | ok。A/A の final `fc2fde3a…`=基準の final。改変の枝の final `afc8b298…` | ok。A/A の final `912446bd…`=基準の final。改変の枝の final `1af4c968…` |
| 実行の内訳 | 担当のいる店 0・対象の店の担当 0/200・**役割行動 0・つなぎ 200**(A/A の同じ店はつなぎ 168)→ `executed_by_agents`=偽 | 担当のいる店 2,337・対象の店の担当 200/200・**役割行動 1・つなぎ 199**(A/A の同じ店は役割行動 0・つなぎ 168)→ `executed_by_agents`=偽 |
| 告知 | 3 行(体 1・2・3・担当は 0 人) | 77 行(対象の店の担当と体 1・2・3) |
| 呼数(A/A → 改変) | 13,825 → 13,866 | 75,316 → 75,478 |
| 壁時計 | 基準 19.9 秒・分岐の 4 本 89.6 秒(指紋の窓の 2 本が 33〜36 秒) | 基準 79.2 秒・分岐の 4 本 293.2 秒(指紋の窓の 2 本が 109〜110 秒) |

- 5,000 体では対象の店すべてに担当がいるが、正午に担当が店のセルに居たのは 1 店だけ=休業の開け閉めはほぼつなぎが実行した。§1-1 の条件(フォールバックを使わない)を満たすには、担当の勤務と居場所(6-6・カレンダー 3)が要る。
- 合成の世界の小さな分岐(試験): 決定と告知の行だけの改変は世界を変えない=粗い比べで食い違いが無く、第 2 段の改変の枝は回さない((c) は None と理由「食い違いが無い」)。古典の方策の分岐(60 体・記憶と関係 on)は T0 より前に方策が数百の呼に答え(80 体の試し回しで 672 呼)、テープとの食い違い 0。CLI の通し(`--tape`・`--state-out`・`--checkpoints-out` で記録 → `--experiment`・`--experiment-branch`)も通る。

## 5. 探索と確認・封印(単位=初期状態)と入口・事前登録(CP14)・対の差の形・技量スコア

- アンサンブル: 初期状態 × モデル × 偶然。初期状態の番号 i → 母集団と環境の seed=`seed0 + i`・偶然の番号 c → 動きの seed(salt)=`seed0 + c`(10f の seed の 3 分割)・モデルは札。
- **封印**(親の判断 M2): 単位=初期状態。アンサンブルの指紋(sha256)と初期状態の正準の JSON の sha256 の昇順で並べ、先頭 `n // 2` の初期状態を封印する。探索の半分と確認の半分は初期状態を共有せず、モデルの札と偶然の seed は各半分の中で組む。封印の指紋 `sealed_sha256`(封印した初期状態の一覧の sha256)だけを記録に書く。`Seal` は指紋と数(`n_initial`・`n_sealed_initial`・`n_members`)だけを持ち、封印した初期状態の一覧を持たない(欄は付け替えられない)。初期状態が 1 つのアンサンブルは封印が空(確認には初期状態が 2 つ以上要る)。
- `members(form)` は**自分の半分だけ**(探索=封印していない半分・確認=封印した半分で、事前登録の `seal_sha256` がこの封印の指紋と同じときだけ)。探索の申込書で封印の半分を求めると `PermissionError`・確認の申込書で探索の半分を求めても `PermissionError`。
- **ランの入口**(親の判断 M1・`ensemble.entrance`・組み立てが世界を触る前に呼ぶ): ランの seed の 3 つとモデルの札(`experiment_model`・札が 1 つなら省略可)をアンサンブルと突き合わせ、メンバーと半分を決める。探索の申込書が封印した半分の初期状態で回ろうとした・確認の申込書が探索の半分で回ろうとした・確認の事前登録の封印の指紋が違う・アンサンブルの外の seed・モデルの札が決まらない、はどれも `ValueError`(止める=試験の負の対照)。manifest の `experiment` に `member`(初期状態・モデル・偶然と seed)と `half`(explore/confirm)を書く。
- 事前登録 `preregister(下書き, 封印)` → (記録, 確認の申込書)。記録の欄: `schema`(`shibuya.engine.experiment/preregistration/1`)・`registration_sha256`(申込書(種類=確認・事前登録の欄を除く)と指標の定義の正準の JSON の sha256=`ExperimentForm.registration_digest()`)・`registration_blake3`(同じ文の blake3=計画 §4 の親案の blake3 も並べた)・`seal_sha256`・`ensemble_sha256`・`question`・`metrics`(正準の JSON)・`form_sha256`・`registered_at`(呼び手の時刻の文字列=指紋に入らない)・`skill`(技量スコアの器)・`record_sha256`(時刻を除いた記録の指紋)。公開の記録の置き場(`docs/predictions/`)は作っていない(書くのは呼び手=外に出す予測の段)。
- 対の差の形: `paired_values(form, [(基準の payload, 改変の payload), …])` → `{指標の id: {"base": […], "arm": […]}}`=`tools/c7/salt_compare.py --values` の形・`metrics_spec(form)` → `--metrics` の形(主・副・向きの事前登録の印は確認の申込書だけ)。6 対の合成の値(差が全部正)で `salt_compare.analyze` の両側の p=2/64=0.03125・状態「検定」・3 対は「記述のみ(本数不足)」(試験)。`pairs_status`: 両側 6 対・向きを事前登録した片側 5 対(R-71 §2-3)。
- 技量スコア(CP14)は器だけ: `skill_container` は指標ごとに単純な基準 3 つ(`last_year_same_day`・`mean`・`previous_week`)の誤差と値の欄(値は全部 null)・`skill_score(誤差, 基準の誤差)`=1 − 誤差/基準の誤差(基準の誤差 0 は `ValueError`)。

## 6. ランの種類・manifest・状態台帳・再開

- 申込書の受け渡し: `cli.run(experiment=…)` が `layer.staged(form, branch=…, model=…)` の中で `run_day` を呼び、組み立てが `current()` で受け取って `Fixtures.experiment` に申込書を、`Layers.experiment` に持ち主を置く。`run_day` の引数と設定の指紋は変わらない(分岐が基準のランの状態のファイルから再開できる)。
- ランの種類: 申込書を渡した `cli.run` は `counterfactual`(順は試験 > 反実仮想 > 腕 > 再現。試験の中は `test`。腕の条件は本体の発話の口と 2-2 の近接の腕のまま)。`cli.main` は申込書を渡したときだけ `run` に欄を足す(既定の引数は今のまま=腕の数え方の試験も今のまま)。
- manifest: 一番上の鍵の末尾(119 個目・2-2 の `proximity` の後)に `experiment`。申込書の無いランは null。設定の子 17(`schema`・`form_sha256`・`kind`・`level`・`aa`・`decisions`・`t0_ns`・`t0_step`・`end_ns`・`notice`・`registration_sha256`・`preregistration_sha256`・`seal_sha256`・`branch_t0_step`・`member`・`half`・`aa_of`)・観測の子 7(`applied`・`unapplied`・`applied_rows`・`unapplied_rows`・`meter`・`replay`=T0 より前の再生の計器・`checks`=4 つの確認の結果の要約)。設定の道筋の golden(`CONFIG_PATHS_SHA256`)は本体の `f78dd574…` → `415620b0…`。
- 状態台帳の行 `X`(`experiment.handle`=口が触る世界の物の束と改変の控え `handle.rec`・`experiment.xchecks`=4 つの確認の結果)=軸 1 diag・軸 2 discardable(外の状態の末尾=2-1 の `EM` の後・外 112・全体 203)。控えを読むのは持ち主のメソッド(`manifest`・`targets`)と口 `apply` だけ(10f の外の状態の軸 1 の AST の検査が通る形)。控えの中の決定の番号の集合(記録した・効いている・日ごとに当てた・終わった)は当て直しの印だが、申込書と時刻と世界の資産から決まる派生で、世界に入った結果は世界の側(店の開閉の旗・天気の再生日 O56・暦)にある=どちらのハッシュにも状態のファイルにも入らない。だから申込書つきの A/A の枝の final は基準のランと同じになる(§4 (d))。台帳の版は上げていない(1-3〜2-1 と同じ仮採用)。持ち主のクラスの属性は行 X の道筋か除外の一覧(定数 7・参照 1)にある(静的と実行時の網羅の試験)。持ち主の欄は 1 回だけ置ける(付け替え・消去は `AttributeError`)・`xchecks` は口 `record_checks` で 1 回だけ書く(読み取り専用の辞書)。
- 再開: 申込書つきのランの状態の見出しに `experiment`(申込書の指紋・T0 の刻み)。再開のランは (1) 親が申込書つきで申込書が違う・申込書を渡さない → 止める (2) 親が申込書なし(基準のラン)で申込書を渡す → 分岐(始まりが再開の時刻より前の決定は `before_begin`) (3) 同じ申込書 → 引き継ぐ(始まりが再開の時刻より前の決定は表へ当てるだけ=出来事と告知は親のランが書いた・祝日は組み立ての中で日の頭より前に当てる)。申込書の無いランの見出しは今のまま。

## 7. 結果不変(byte-check)

- **rebase の前: 申込書を渡さないラン 19/19 構成で 25 欄とも HEAD と同じ**([byte_check_cf33.json](byte_check_cf33.json)・`10e/byte_check_10e.py`・5,000 体・seed 1・1 日・テープつき)。head=本体 HEAD `740508c` の src の写し(錨はエンジンが開く 3 本だけ)・cf33=作業木の src(`src_is_worktree` 19 本とも真)。比べた欄: final・呼数・blocks・テープの全部の列の sha と列の名・行動の件数・起床の内訳・顕著行為・出動・食事・behavior/full の最後・締めの後の 2 本・暦・frozen_sources。既定 v3 の final `5f7ae9ff24005314`(1-8b の記録と同じ)。
- **rebase の後: 4/4 構成で 25 欄とも本体 `21cd044` と同じ**([byte_check_cf33_rebased.json](byte_check_cf33_rebased.json)・`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`・final `5f7ae9ff…`・`e0054a83…`・`24375ee3…`・`73a78288…`)。head=`21cd044` の src の写し(`src_is_worktree` 偽)・作業木の src(真)。検収の直しの後の src で回した。
- 既定のランで変わるもの(byte-check の欄の外): manifest の一番上の鍵が 1 つ増える(`experiment: null`)・`bridges_count`(328 → 340)と `bridges_version`(つなぎの台帳の行を足したため)。状態のファイルの見出し・テープ・2 つのハッシュは変わらない(系 `experiment` は立たない・行 X はハッシュに入らない)。
- 申込書つきのランの結果の不変: A/A の枝(改変が空)・効かせていない改変・決定と告知の行だけの申込書は final と全 checkpoint が申込書なしと同じ(試験 `test_forms_that_change_no_table_keep_every_checkpoint`)・分岐の A/A の final が基準の final と同じ(§4 (d))・申込書つきのラン(休業)を日の境目で止めて同じ申込書で再開すると通しと同じ(試験 `test_world_resume_with_the_same_form_equals_straight`・300 体・2 日)。

## 8. 試験

新しい試験 90 本(`tests/engine/experiment/`・slow は 5,000 体の分岐の 1 本だけ=426 秒):

| ファイル | 本数 | 中身 |
|---|---|---|
| `test_x33_form.py` | 30 | 欄と既定・知らない欄は `ValueError`(8 形)・JSON の往復と決定的な並び・日本語の種類・矛盾 12 形・事前登録の有無と指紋・A/A と T0 の刻み・決定の表・地名と業種名がコードに無い(負の対照つき)・直に作っても検査が走る(L3)・確認の申込書の A/A が JSON の往復で通る(L4) |
| `test_x33_apply.py` | 23 | 合成の世界(手書きの W7・W13)で L1 の休業(1 回だけ記録・過程が開閉を実行)・日ごとの当て直しと終わりの戻し・営業時間と催し・告知の行(宛先・道具・届いた時刻・1 回だけ)・宛先無し・L0 の天気の差し替えと当て直し・祝日・効かせていない 8 形・分岐の期間の外・引き継ぎ(当てるだけ・prime)・口は 1 つ(AST・暦の書き口を含む・負の対照)・1-3 の負の対照が残る・語彙(60・61)・表が読み取り専用(L6)・暦の口を通す(L5) |
| `test_x33_run.py` | 17 | 申込書なしは系が呼ばれない・manifest は null・申込書つきでも表を変えない 4 形は全 checkpoint 不変・期間の外・manifest の節の子の鍵・行 X はハッシュに入らない・ランの種類の規則・`cli.run` の counterfactual と A/A・CLI の引数・状態の見出しと再開の検査 3 形・段 B(宣言の中・宣言を外すと見つかる)・持ち主の属性の実行時の網羅(負の対照つき)・持ち主の守りと `record_checks`(M4)・封印の入口がランで効く(M1・負の対照 3 形) |
| `test_x33_branch.py` | 13 | 世界資産 1,000 体・2 日の分岐の 4 つの確認(窓・回し直し・実行の内訳と `executed_by_agents`)・再生の計器と manifest・報告のファイル(絶対パスなし)・合成の世界の小さな分岐(A/A だけ・上書きの拒否)・T0 の範囲外・確認の関数の負の対照 3 本・`choose_state`・CLI の通し・古典の方策の分岐・申込書つきの再開=通し(300 体・2 日)・**slow**: 5,000 体(担当のいる世界)の分岐の実行の内訳 |
| `test_x33_ensemble.py` | 7 | 自分の半分だけ・初期状態を共有しない(M2)・封印は指紋だけ・探索は封印を読めない・確認の事前登録と封印の照合・ランの入口(M1・負の対照 4 形)・`salt_compare.analyze` に 6 対で p=2/64(3 対は記述のみ)・技量スコアの器 |

- **rebase の後の範囲の試験**(`tests/engine/experiment tests/engine/events tests/engine/systems tests/engine/time tests/engine/bridging tests/engine/proximity tests/engine/speech tests/economy tests/llm tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_env_and_sections_10f.py tests/test_cli.py`・`-m "not gpu and not slow" -n 4 --dist loadfile`): **1,376 passed・0 failed(544 秒)**。slow の 5,000 体の分岐は別に回して通った(426 秒)。`lint-imports` 5 契約とも KEPT。
- rebase の前の全体の試験(`--ignore=tests/c7`・土台 `740508c`): 4,717 passed・1 failed・1 xfailed(18 分 38 秒)。落ちた 1 本は `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(junction 由来の既知の落ち=本体 HEAD の src の写しでも同じく落ちることを確かめた)。
- rebase の前の全体の試験の 1 回目(`--ignore=tests/c7` を付け忘れ・別の重いランと同時)は 24 failed だった: 3 本は本段の欠陥(10f の外の状態の軸 1 の AST の検査に名の衝突で当たった=名を替えて直した・§9)・1 本は語彙の族の末尾の固定(`test_c0_tool_registry.py`=増えた分だけ直した)・19 本は子のプロセスが起動できない Windows の落ち(返り値 `0xC0000142`=同時に走らせたランが多すぎた)で、直した後の単独の再実行と 2 回目の全体の試験で通った・1 本は上の既知の落ち。

## 9. 触った共有ファイル

発注の「共有のファイル」で触った所(rebase の後の並び):

| 共有のファイル | 触った所 |
|---|---|
| `engine/systems/table.py` | 系 `experiment` を刻みの中の最初に 1 つ足した(`when="experiment"`・刻みの中 26)・day_close・drain・close_final の `reads` に `layers.experiment`(2-2 の `layers.proximity` の後)・見出しの段落(2-1 の段落の後) |
| 状態台帳 `engine/state_ledger.py` | 行 `X`(外の状態の末尾=`EM` の後)・`OWNER_CLASSES["experiment"]`(`proximity` の後)・`EXCLUDED` に 2 行・`LEDGER_VERSION` の注(版は上げない) |
| 凍結の表 | `tests/engine/systems/writes_soa_frozen.json`(`experiment: []`)・`tests/engine/events/writes_paths_events.json`(先頭に `experiment`)・`tests/engine/time/manifest_keys_frozen.json`(末尾=`proximity` の後に `experiment`) |
| `cli.py` | `run` の引数 4 つ・`_experiment_form`・CLI の 4 つの引数(2-2・2-1 の引数の後)・ランの種類の決め方・`run(...)` を `run_kwargs` に組んでから呼ぶ形(2-2・2-1 の環境変数の腕の設定はその前のまま・既定の引数は同じ) |
| manifest の末尾 | `engine/run.py`(`experiment`=`proximity` の後)・`engine/manifest_sections.py`(混ざった辞書 `experiment`=`proximity` の後) |
| つなぎの台帳 | `docs/design/bridging-ledger.json` の末尾に 12 行(本体 328 → 340・既存の行は不変) |
| 語彙の表 | `engine/events/vocab.py` の末尾(2-1 の `金:カード` の後)に族 `実験` の 2 語(60・61)・版 `events-vocab/3-3` |

ほかに触った src(共有の一覧の外): `engine/systems/{boxes,conductor,build,state_io,run_end}.py`・`engine/run_kind.py`・`engine/calendar.py`・`engine/experiment/gate.py`・`engine/processes/{opening,environment}.py`(呼ぶのは `apply.py` だけの書き口 1〜2 個)。

数を固定した既存の試験(増えた分だけ直した): `tests/engine/systems/test_systems_table.py`(順と刻みの中 26)・`tests/engine/test_state_ledger_10b.py`(外 112・全体 203・行 X)・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/test_env_and_sections_10f.py`(`X33_KEYS`・`CONFIG_PATHS_SHA256`)・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/perception/facts/test_percept_schema.py`(manifest の末尾)・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/tools/test_c0_tool_registry.py`(語彙の族の末尾)・`tests/economy/stage2/test_stage2_account_and_conservation.py`(2-1 の語の位置と版)。

名の衝突の直し(rebase の前の全体の試験で見つけた): 属性の名が既存の台帳の行の属性と同じだと、1-8b の AST の検査(`test_speech_writers_ast.py`=`meter` への書きを発話の口の外で落とす)と 10f の外の状態の軸 1 の検査(`test_state_checks_10f.py`=no/diag の属性の名を持ち主の外で読むと落とす・名の衝突は理由の表 `EXT_NAME_COLLISIONS` が要る)に当たった。共有の表を増やさず、名を替えた: 控えの計数 `tallies`(元 `meter`→`counts`)・口の束の控え `rec`(元 `record`)・行 X の道筋 `experiment.handle`・`experiment.xchecks`(元 `record`・`checks`)・再生の計器のメソッド `replay_meter`(元 `meter`)。manifest の欄の名(`meter`・`checks`)はそのまま。

## 10. つなぎの台帳の行(12 行・`declared_in`=この記録・2026-10-14)

| id | 中身 | 外す段 | 宣言 |
|---|---|---|---|
| `DOC-cf33-notice-rows-only` | 告知は「届いた情報」の出来事の行まで(住人の受け取りの段は無い) | 6-4 | plan |
| `DOC-cf33-fallback-executes` | 担当のいない店(担当が店のセルに居ないときを含む)の休業・営業時間の変更は conf 0.5 のつなぎが実行する。§1-1「分岐でフォールバックを使わない」は 6-6 まで宣言のまま・報告に実行の内訳と `executed_by_agents` | 6-6 | inferred |
| `DOC-cf33-start-zero-order` | 始まり 0 は 0 の刻みの頭で当てる(CP5-1 の順・CP5-3 のペルソナの点検は未実装) | 4-1 | inferred |
| `DOC-cf33-burn-in-not-judged` | 慣らしの自動判定(CP5-6・MSER-5)と 3 区間の事前登録は未実装 | 7 | inferred |
| `DOC-cf33-skill-empty` | 技量スコアは器だけ(値は空)・公開の記録の置き場は作っていない | 7 | plan |
| `DOC-cf33-l2-declared` | L2 は欄だけ | 5-2 | plan |
| `DOC-cf33-l3-declared` | L3 は欄だけ | 6-6 | inferred |
| `DOC-cf33-l4-declared` | L4 は欄だけ | 4-2 | inferred |
| `DOC-cf33-branch-fleet` | 艦隊(非同期の実 LLM)の分岐は未実装 | 6-7 | plan |
| `DOC-cf33-branch-probe` | (c) は T0 以後の全 checkpoint を走査して窓を決め、指紋の窓をかけて 2 本を回し直す(ランは 4 本)・ランをまたいで比べられない digest を外す・状態は T0 より前の最後の日の境目から | 7 | inferred |
| `DOC-cf33-reapply-unit` | 当て直しは日ごと・祝日は翌日以後だけ・終わりに戻す形 | 6-2 | inferred |
| `DOC-cf33-ensemble-seeds` | アンサンブルの seed の割り振りと封印の並べ方(単位=初期状態) | 7 | inferred |

- 件数: 台帳 本体 328 → 340 行(manifest の `bridges_count`・`bridges_version` は動く=台帳の行を足す段の既定の扱い)。コードの宣言(`scan.count_by_form`)は増やしていない(新しいコードの expedient は「未リサーチ(expedient)」の注記と DOC の行で宣言=1 対 1 の試験の数は今のまま)。

## 11. 限界と仮採用(10-13b §0-3=既定 off・戻せる形・PENDING §1-1 の候補)

1. **申込書の受け渡しを文脈の変数に**(`layer.staged`/`current`): `run_day` の引数を増やさない発注に合わせた。`run_day` を直に呼ぶ試験も `staged` の中で呼べば同じ。設定の指紋には入れず、状態の見出しに申込書の指紋を書いて再開で突き合わせる(§6)。
2. **系 `experiment` を刻みの中の最初に足した**(刻みの中の系 25 → 26・`when="experiment"`=申込書の無いランでは立たない)。日の頭(day_head)の後なので、日の頭で過程が張り直した表に当て直せる。
3. **語彙の族 `実験` と 2 語**(`改変`・`届いた情報`)=実行役の構成(未リサーチ(expedient))。
4. **行 X は diag・discardable**: 控えの決定の番号の集合を「申込書と時刻と世界の資産から決まる派生」と宣言した。世界に入った結果は世界の側の状態にある(§6)。
5. **告知は「届いた情報」の出来事の行まで**(CP6・発注どおり)。住人が受け取って本人が変わる段は無い。段取り(組織の中の準備・世間の準備・落ち着く)も無い。
6. **改変の水準は L0・L1 だけ実装**・L2〜L4 は欄だけ。合成の世界(`World.synthetic`)には W7・W13 が無いので営業時間・休業・天気は効かない(`no_w7`・`no_w13`)=「合成の世界で効く」の試験は手書きの W7・W13 を足した合成の世界(`tests/engine/processes/conftest.py` の材料)で行った。
7. **表を実行するのは今の過程**(親の判断 M3): 営業時間の表は担当の従業者が開け閉めし、居なければ今の conf 0.5 のつなぎ。§1-1「分岐の実験ではエンジンが代わりに実行する仕組みを使わない」は 6-6 まで宣言のまま(台帳 `DOC-cf33-fallback-executes`)。そのあいだ分岐の報告に実行の内訳と `executed_by_agents` を出す(summary の `ok` は 4 つの確認だけ)。5,000 体でも担当が実行したのは 1 件だけだった(§4)。
8. **祝日は暦の口 `SimCalendar.set_holiday` で書く**(検収 L5): 祝日の表はランごとに読み直す辞書=そのランの中だけ。翌日以後の日付だけ(当日の表は日の頭で張り直し済み)。複数日の合成の世界(W17 が無い)で活動層つきのランは、休日で計画境界の表が変わると 10d の範囲の外(`NotImplementedError`=K9)で止まる(今の作りの限界・祝日の改変に限らない)。書き口 4 つは AST の検査だけで、実行時の守り(呼び手のフレームの検査)は付けていない。
9. **「最初から」の順(CP5-1)・ペルソナの点検(CP5-3)・慣らしの自動判定と 3 区間(CP5-6)は未実装**(宣言・台帳の行)。始まり 0 は 0 の刻みの頭で当てる。
10. **技量スコアは器だけ**(値は空)。事前登録の記録は JSON を返すだけで、公開の置き場(`docs/predictions/`)は作っていない。計画 §4 の親案は blake3・発注は sha256=記録に両方を並べた(指紋の主は sha256)。
11. **分岐の口**: 艦隊(非同期の実 LLM)は未対応(組み立てで止める)・注入した同期の LLM の口は通る(試験は mock と古典)・腕 `--decision-port port` の mock は口が mock を直に持つので T0 より前も mock が答える(結果は同じ=(b) で確かめる・試験はしていない)。
12. **(c) の窓**: T0 以後の全 checkpoint を走査し、一致した最後の checkpoint の次から最初に食い違った checkpoint までに指紋をかける(ランは 4 本・回し直しの final が 1 本目と同じことも確かめる)。ランをまたいで比べられない digest(`X:`)は外した(宣言)。(d) は checkpoint と final の比べ(A/A の枝の指紋の比べはしない)。状態は T0 より前の最後の日の境目から(日中の保存は足していない=計画 §4 の CP5-2 の親案どおり)。
13. **再開で動く設定の欄 `group_norms.cost.ticks`**: 10f の節の表で設定に入っている計器。(a) は宣言した値(基準=通しの刻みの数・枝=再開からの刻みの数)と同じときだけ許した(§12)。
14. **封印の単位=初期状態**(親の判断 M2)・**入口の検査**(M1): 申込書つきのランはアンサンブルのメンバーでなければ回らない(seed の 3 つとモデルの札)。モデルの札が 2 つ以上の申込書は `experiment_model`(CLI `--experiment-model`)を渡す。モデルの札と方策の対応(札 → `policy` など)は呼び手が持つ(札を方策に写す口は作っていない)。
15. ランの種類: 試験の中は `test` のまま(試験 > 反実仮想)。
16. **規律の記録(`tests/c7`)**: rebase の前の全体の試験の 1 回目で、発注の「`tests/c7` は回さない」に反して `tests/c7` を含めて回した(`--ignore=tests/c7` の付け忘れ)。気づいて止めようとしたが、背景の pytest の子のプロセスは止まらず(`taskkill` は使わない規律)最後まで回った。`tests/c7` には封印した層の名を引く試験が 3 本(`test_presence_yardstick`・`test_holdout_compare`・`test_prereg_v13`)あり、`test_presence_yardstick` は `presence_anchors_v0.json` を読むので、封印した層を読んだ可能性が高い。値は記録にも報告にも使っていない。以後の試験は全部 `--ignore=tests/c7`(親の判断 A5)。

いずれも既定 off(申込書を渡さないランは何も変わらない=§7)なので戻せる。PENDING §1-1 の仮採用の候補は 1・2・3・4・8・13・14。

## 12. 親に確かめてほしいこと

1. **`group_norms.cost.ticks` が manifest の設定の節にある**: 再開のランで必ず動く計器。(a) では宣言した値で許したが、10f の節の表を観測に直すのが本筋か。
2. **担当がいても開け閉めはほぼつなぎ**(5,000 体で担当の実行 1・つなぎ 199): §1-1 の条件を満たすには担当の勤務と居場所(6-6・カレンダー 3)が要る。`executed_by_agents` を判断待ちの計器として PENDING に置くか。
3. **モデルの札と方策の対応**: 申込書の `ensemble.model` は札の文字列だけ。札を方策(mock・古典・LLM)に写す口を申込書の欄に足すか、呼び手が持つままにするか。
4. 計画 §4 の CP14 の blake3 と発注の sha256 の扱い(両方を並べた)。

## 13. 再現の手順(リポの根で・`$D`=このフォルダ・`$W`=作業用の短いディレクトリ)

```
B=docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py
git archive 21cd044 src docs/bench/anchors/hunger_energy_anchors_v0.json \
    docs/bench/anchors/ssb2021_activity_prior_v0.json docs/bench/anchors/commute_time_dist_r3.json \
    docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head2_src
mkdir -p $W/head2_src/data/calendar && cp data/calendar/syukujitsu.csv $W/head2_src/data/calendar/
ONLY=w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel
python $B side --src $W/head2_src/src --label rhead --scratch $W --out $W/rhead.json --only $ONLY --jobs 4
python $B side --src src --label rcf33 --scratch $W --out $W/rcf33.json --only $ONLY --jobs 4
python $B compare --a $W/rhead.json --b $W/rcf33.json --out $D/byte_check_cf33_rebased.json
# 分岐の例(PYTHONPATH=作業木の src)
python $D/tools/branch_example.py --scratch $W/ex1000 --out $D/branch_example_rebased.json
python $D/tools/branch_example.py --agents 5000 --scratch $W/ex5000 --out $D/branch_example_5000_rebased.json
# 試験
python -m pytest -q -p no:cacheprovider -o addopts="" -rf -m "not gpu and not slow" tests/engine/experiment
python -m pytest -q -p no:cacheprovider -o addopts="" -rf tests/engine/experiment/test_x33_branch.py -k 5000
# CLI の分岐(基準のランを記録してから)
python -m shibuya.cli --sim-days 2 --tape $W/base/tape --state-out $W/base/state --checkpoints-out $W/base/checkpoints.json
python -m shibuya.cli --sim-days 2 --experiment form.json --experiment-branch $W/base
```

rebase の前の 19 構成の byte-check は同じ手順で土台 `740508c` の写しと全構成(`--only` なし)で回した([byte_check_cf33.json](byte_check_cf33.json))。

## 14. 検収の直しと親の判断([review.md](review.md)=条件つき受入・中 4・低 10)

| 番号 | 中身 | 直し方(場所) | 試験 |
|---|---|---|---|
| M1(親の判断 A2) | 封印がランの口で効かない | 組み立てが世界を触る前に `ensemble.entrance`(seed の 3 つとモデルの札でメンバーと半分を決め、探索の申込書が封印した半分の初期状態なら `ValueError`)。manifest に `member`・`half`。`Seal` は指紋と数だけ・`members()` は自分の半分だけ(`ensemble.py`・`layer.py`・`build.py`・`cli.py` の `experiment_model`) | `test_entrance_lets_each_form_run_only_its_half`・`test_the_seal_is_enforced_at_the_run_entrance`(負の対照) |
| M2(親の判断 A1) | 封印の単位が 1 本のメンバー | 単位=初期状態(母集団の seed)。探索と確認は初期状態を共有しない・モデルの札と偶然は各半分の中で組む(`ensemble.py`・台帳の行 `DOC-cf33-ensemble-seeds`) | `test_members_are_my_half_of_initial_times_model_times_chance` |
| M3(親の判断 A3) | つなぎが実行した分岐を ok と読み違える | `branch_report` に `execution`(役割行動・つなぎ・担当のいる店)と summary の別の欄 `executed_by_agents`(`ok` は 4 つの確認だけ)。5,000 体の分岐(slow)で記録。台帳の行 `DOC-cf33-fallback-executes` を「担当のいない店の休業はつなぎが実行(6-6)」に | 世界 1,000 体の試験・`test_world_branch_with_staff_5000`(slow) |
| M4(親の判断 A4) | 持ち主に守りが無い・`xchecks` を外から付け替える | `ExperimentLayer.__setattr__`/`__delattr__`(欄は 1 回だけ)・`record_checks`(1 回だけ・読み取り専用)・台帳の行 X の注 | `test_owner_fields_cannot_be_replaced_and_checks_are_written_once` |
| A5 | 名の衝突の直し・X の digest を (c)(d) から外す・`tests/c7` | 可(宣言)・§11 の 16 に規律の記録 | — |
| L1 | (c) の窓が T0 から 15 刻みの固定 | T0 以後の全 checkpoint を走査して窓を決め、2 本を回し直す(見つからなければ None と理由) | 世界と合成の分岐の試験 |
| L2 | `behavior_hash_same` の名と中身 | `base_state_matches_base_end_of_day`(基準の自己一致)と注 | 世界の分岐の試験 |
| L3 | 直に作ると検査を通らない | `ExperimentForm.__post_init__` が `from_dict` と同じ検査 | `test_direct_construction_is_checked_too` |
| L4 | 確認の申込書の `.aa()` が JSON の往復で落ちる | 欄 `aa_of`(元の登録の指紋)・確認の A/A は事前登録を引き継ぐ | `test_aa_of_a_confirm_form_round_trips` |
| L5 | 祝日の辞書を直に書く | 暦の口 `SimCalendar.set_holiday` を通す(書き口の一覧に足した) | `test_the_calendar_is_written_through_its_one_mouth` |
| L6 | モジュールの表が素の dict | `_IMPL`・`REASONS`・`DERIVED_BY_DECISION`・`RESUME_DERIVED` を `MappingProxyType` | `test_module_tables_are_read_only` |
| L7 | `day_close` の `reads` に `layers.experiment` が無い | day_close と drain(どちらも状態を書く)に足した | 系の表の試験 |
| L8 | README §9 に `test_c0_tool_registry.py` が無い | 足した | — |
| L9 | `branch_example.json` の区切り | 道具で posix の形(`data/world/v2`)に。古い `branch_example.json` は消し、rebase の後の 2 本(1,000・5,000)を置いた | — |
| L10 | 作業木の `_bc/` | git の外(`git add` しない)。取り込みの前に消す | — |

## 15. rebase(本体 `21cd044`=2-2・2-1 と文書を取り込んだ後)

- 手順(1-7 と同じ): 変えたファイル 33 本の自分の版と土台 `740508c` の版を `_bc/` に控え → `git checkout` で土台に戻す → `git merge --ff-only 21cd044`(早送り)→ 3 方向の `git merge-file`(自分・土台・本体)。新しいファイル(`engine/experiment/` の 5 本・`tests/engine/experiment/`・この記録)は本体に無い(衝突なし)。
- 衝突: 22 本(src 10 本・試験 10 本・JSON 2 本=つなぎの台帳と manifest の鍵の凍結の表)。衝突しなかった並びの表(系の表の試験・`writes_*` の凍結の表・`test_c0_tool_registry.py`)と本体の新しい試験(2-1 の `test_stage2_account_and_conservation.py`)も増えた分だけ直した。どれも「末尾に足した所」の取り合いで、本体の並びの後ろに 3-3 を置いた(検収役の案 §(f)):
  - 語彙: 本体の 58 `金:引き出し`・59 `金:カード` の後に **60 `実験:改変`・61 `実験:届いた情報`**(版 `events-vocab/3-3`・族の並びの末尾に `実験`)。
  - manifest: 末尾=… → `speech_port` → `proximity` → **`experiment`(119)**・節の表も `proximity` の後・`CONFIG_PATHS_SHA256` は計算し直した(`415620b0…`)。
  - 状態台帳: … `EC`・`ATM`・`CR`・`EM` → **`X`(外 112・全体 203)**・`OWNER_CLASSES` は `proximity` の後。
  - 箱: `OWNER_NAMES` は `… "speech", "proximity", "experiment"`・`Layers.experiment` は `proximity` の後・`Fixtures.experiment` は 2-1 の `atms` の後。
  - `state_io`: `hash_owners` は `proximity` の後・状態の見出しは `proximity`・`economy_stage2` の後に `experiment`。
  - 系の表: 刻みの中は本体も 25 → `experiment` を足して 26。day_close・drain・close_final の `reads` は `layers.proximity` の後に `layers.experiment`。
  - `cli.run` のランの種類: 本体の `arms_on=… or _proximity.arm() != MODE_CELL` に `counterfactual=exp_form is not None` を合わせた(申込書があれば counterfactual が先)。`main` の `run(...)` を `run_kwargs` に組む形は、本体の `--proximity`・`--proximity-d`・`--economy-stage2`・`--economy-stage2-parts`(環境変数の口=`run` の引数でない)の設定の後に置いた。
  - つなぎの台帳: 本体 328 行の末尾に 12 行(340)。
  - 末尾の並びの試験(1-7・1-8b・2-2・2-1 の分)と語彙の位置の試験(2-1 の `test_stage2_account_and_conservation` を含む)を増えた分だけ直した(§9)。
- rebase の後の確かめ: 範囲の試験 1,376 passed・`lint-imports` KEPT・byte-check 4/4 構成 25 欄同じ(§7)・分岐の 4 つの確認(1,000 体)を回し直して通った・5,000 体の分岐(親の判断 A3)も通った(§4)・slow の試験 1 本も通った。
