# 機能のカタログ グループ C 基盤(把握の資料 段 2)

> 発注は [返事その 6](../../../design/prompt-2026-11-05-reply6.md) §3-1 の 3 です。担当は基盤の機能で、体と街はグループ A、人の中身はグループ B が書きます。今のコードの現状を書き、あるべき姿は書きません([仕様書](../../../design/spec/)の担当です)。
> 正はコードです。HEAD `15b6bbd` を読みました。既定の値は `shibuya.cli` の引数の定義と各モジュールの腕の関数を Python で読み出して確かめ、ランは回していません。`data/` は開いていません。数値には出どころを添えます。

## 0. 読み方

### 0-1 状態の語

| 語 | 意味 |
|---|---|
| 既定 | 既定のラン(引数なし・`SHIBUYA_*` なしの `python -m shibuya.cli`)で動く |
| 腕 | 既定では動かず、切替口を立てると動く。ランの外で動かす道具は「腕(ランの外)」と書く |
| 器だけ | 口や欄はあるが、既定のランの結果を変えない(呼び手が無い・値が空・行が 0) |
| 無いと宣言 | [absent.py](../../../../src/shibuya/world/processes/absent.py) に宣言の行がある |
| 無い(宣言なし) | コードに無く、absent.py にも行が無い。発注の 4 区分の外なので別に書く |

既定のランは [段 1](../day-flow.md) §0-2 と同じです。入口が違うと既定も違います。`shibuya.cli` は台帳つき・語彙 v3・空腹 energy・呼数の上限なしで、ライブラリの `run_day` は語彙 v1・空腹 v1・呼数の按分です(`cli.arm_baseline`)。`python -m shibuya.engine.run` は台帳なしの入口です(`cli.py` の docstring)。

### 0-2 語

用語集([v2-glossary.md](../../../design/v2-glossary.md))の語で書き、見出しに旧名を添えます。呼び出し(旧: 起床)・呼び出しの割り当て(旧: 繰り延べアービタ)・再呼び出しの間隔(旧: 不応期)・見送り(旧: 抑止)・後回し(旧: 繰り延べ)・優先上げ(旧: 昇格)・簡略応答(旧: 縮退)・応答の記録(旧: テープ)・LLM サーバー群(旧: 艦隊)・同義語辞書(旧: 段 0 辞書)です。コードの識別子はそのまま書きます。

### 0-3 欄の書き方

- 元の決定は [索引](../../../design/decision-id-index.md) の形(`10-12/CP4`)と [IMPLEMENTED](../../../../IMPLEMENTED.md) の番号(`#91`)で書きます。`D-58` のような旧い番号は索引に無いので、載っている `#N` で書きます。
- 棚卸しの指紋は [仕分けの表 11-04](../../behavior-audit-triage-2026-11-04.md) の行 ID と親案の区分です。`A05 V` は行 A05 が区分 V という意味で、「割れる」は同じ表の §4 の行です。表の行番号は HEAD `90258ef` の読みなので、今のコードと行がずれることがあります。行が無い機能は「該当の行なし」と書きます。
- つなぎの台帳の ID(`DOC-…`・`BR-…`)は [bridging-ledger.json](../../../design/bridging-ledger.json) の行です。
- ファイルごとの公開の関数・呼び手・読む試験は [カード](../cards/README.md) で引けます(段 3・本体への取り込み待ち)。

## 1. 機能の一覧

C1〜C2・C3・C5・C6・C8・C10〜C11・C13〜C14 が発注の機能です。ほかは近い機能として足しました。

| # | 機能 | 状態 | 主なファイル |
|---:|---|---|---|
| C1 | 経済と台帳 | 既定(信用と価格形成は器だけ) | `economy/ledger.py`・`economy/ops.py`・`economy/goods.py`・`economy/stage2.py` |
| C2 | 権利 | 既定(営業許可は器だけ) | `engine/rights/` |
| C3 | 計器 | 既定(読むだけ)と腕(ランの外の道具) | `engine/systems/observe.py`・`engine/norm_meter.py`・`tools/instruments/`・`tools/c7/`・`tools/c8/` |
| C4 | manifest とランの種類 | 既定 | `engine/run.py`・`engine/manifest_sections.py`・`engine/run_kind.py`・`manifest/` |
| C5 | 実験と分岐 | 腕(L2〜L4 は器だけ) | `engine/experiment/` |
| C6 | 応答の記録(テープ) | 腕 | `engine/tape.py`・`engine/llm_bridge.py` |
| C7 | 出来事の記録 | 既定(メモリの中だけ) | `engine/events/` |
| C8 | 保存と再開 | 既定はハッシュだけ・ファイルと再開は腕 | `engine/resume.py`・`engine/state_codec.py`・`engine/state_hashes.py` |
| C9 | 状態の台帳 | 既定(読むだけ) | `engine/state_ledger.py`・`engine/state_ledger_ast.py` |
| C10 | LLM サーバー群と推論(艦隊) | 腕 | `llm/fleet.py`・`engine/systems/llm_io.py`・`tools/night5070/` |
| C11 | 判断の口と考える担い手 | mock は既定・口は腕・判断モデルは無い | `engine/decision/`・`llm/mock.py`・`engine/classical.py` |
| C12 | 語彙と読み取り | 既定 | `llm/contract.py`・`llm/parser.py`・`llm/undefined.py` |
| C13 | 知覚 | 既定(空の欄は器だけ) | `perception/` |
| C14 | 呼び出し(起床)=変化の検出と割り当て | 既定 | `engine/change_detect.py`・`engine/arbiter.py`・`engine/systems/judge.py` |
| C15 | 行為の解決(二段階の確定) | 既定 | `engine/commit.py`・`engine/resolve.py` |
| C16 | 進行役・系の表・書きの許可 | 既定 | `engine/systems/` |
| C17 | 時計と窓 | 既定は幅 60 秒・細かい時計は腕 | `engine/batching.py`・`core/time_consts.py` |
| C18 | 乱数と決定論 | 既定 | `core/rng.py`・`core/hashing.py` |
| C19 | 構築 | 腕(ランの外)・成果物を既定のランが読む | `build/` |
| C20 | 母集団 | 既定 | `agents/population.py`・`build/pop/` |
| C21 | ビューア | 無い(宣言なし) | なし |
| C22 | 道具の台帳 | 器だけ | `engine/tools/` |
| C23 | つなぎの台帳と「無い」の宣言 | 既定(読むだけ) | `engine/bridging/`・`world/processes/absent.py` |

ファイルの道筋は `src/shibuya/` を省きました(`tools/` はリポの根から)。

## 2. 本文

### C1 経済と台帳

#### 何をしているか

お金と物の帳簿です。金の台帳は世帯・店舗・雇用主・銀行・政府・外界の 6 部門の残高と、科目 15 個の取引フロー行列と生ログを持ちます。残高を書くのは基本操作 `ops.transfer` だけで、帳簿の口は検査をしてからそこへ渡します。世帯の現金は `agents.money` と同じ配列です。物の台帳は SKU 別の棚・廃棄ビン・世帯の合計を持ち、`move_goods` を単一の口と宣言しています。

経済の段階 2 は賃金(給料日)・引き出し(ATM)・支払いの方法(現金か口座)・レジの消費税・来街者の口座の 5 部品です。日の締めで保存則の検算(`accounts.FLOW_REGISTRY` の登録 20 本・読み出し)と日次センサスを計算します。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 金と物の台帳・`ops.transfer` | 既定 | 切替口なし。`shibuya.cli` の入口で組む(`build_ledger_bundle`) |
| 経済の段階 2 の 5 部品 | 既定 | `--economy-stage2`(引数の既定 None → `economy_stage2.DEFAULT_ARM`=on)・`SHIBUYA_ECONOMY_STAGE2`・`--economy-stage2-parts`(既定は全部)。off は旧道 |
| 職業ごとの賃金 | 既定(1 日のランには給料日が来ない) | `DEFAULT_WAGE`=`occupation`。切替口は消した。`SHIBUYA_WAGE` を与えると止まる |
| 給与の天引き・店の預かり消費税 | 既定 | `SHIBUYA_RULES_42`=on・`SHIBUYA_RULES_42B`=on(環境変数だけ)。off は旧道 |
| 日次センサス・保存則の検算 | 既定 | ファイルは `--census-out` のときだけ(既定は空)。月次の T3 は 30 日の区切りでだけ走る(`census.MONTH_DAYS`) |
| 参入資本 | 既定 | 経済センサスの按分。`--store-capital` で一律 |
| 世帯の初期の財布 | 既定 | `anchors.initial_wallets`。`--no-population` で mock の値 |
| 信用(`CreditBook`・`repay_due`・総量規制・利息の上限) | 器だけ | `Ledger.attach_stage2` が `CreditBook(capacity=0)` を作る。行は足されない |
| 価格形成(`pricing.py`) | 器だけ | `goods.py` が定数 `K_*` を読むだけ |
| 軽減税率(`taxes.reduced_rate`) | 器だけ | docstring に呼び手なしとある |
| 家賃 | 器だけ | 科目 `RENT` はあるが払う行為が無い(`BR-RENT-BLANK`) |
| 値段を変える・値段を見て見送る・品と数を選ぶ・採用と解雇・売れ残りの廃棄 | 無いと宣言 | `absent.change_price`・`absent.price_balk`・`absent.item_qty`・`absent.hiring_firing`・`absent.discard_unsold` |
| 発注・納品 | 無いと宣言(言い換え) | `absent.ordering`=初期の予定・`absent.inbound_delivery`=入力 |

#### ファイル

- [src/shibuya/economy/ledger.py](../../../../src/shibuya/economy/ledger.py) 金の台帳(帳簿の口の検査・日の締め・世帯の現金の配列の採用)
- [src/shibuya/economy/ops.py](../../../../src/shibuya/economy/ops.py) 基本操作 `transfer`(残高・流れの表・生ログを書く唯一の関数)
- [src/shibuya/economy/accounts.py](../../../../src/shibuya/economy/accounts.py) 部門・科目・faucet と sink の表・流れの登録
- [src/shibuya/economy/checks.py](../../../../src/shibuya/economy/checks.py) 検算 2 本・T3・残差ゲート・保存則の検算
- [src/shibuya/economy/census.py](../../../../src/shibuya/economy/census.py) 日次センサス・月次 MER・ゲート判定
- [src/shibuya/economy/goods.py](../../../../src/shibuya/economy/goods.py) 物の台帳
- [src/shibuya/economy/stage2.py](../../../../src/shibuya/economy/stage2.py) 段階 2 の中身(賃金・引き出し・支払い・税・来街者)
- [src/shibuya/economy/wages.py](../../../../src/shibuya/economy/wages.py)・[src/shibuya/core/wage_formula.py](../../../../src/shibuya/core/wage_formula.py) 職業 × 性 × 年齢 × 雇用形態の賃金
- [src/shibuya/economy/taxes.py](../../../../src/shibuya/economy/taxes.py)・[src/shibuya/economy/tax_deposit.py](../../../../src/shibuya/economy/tax_deposit.py) 規則の表の読み手(天引きほか)・預かり消費税
- [src/shibuya/economy/anchors.py](../../../../src/shibuya/economy/anchors.py)・[src/shibuya/economy/entry_capital.py](../../../../src/shibuya/economy/entry_capital.py) 金額の錨と初期の財布・参入資本
- [src/shibuya/economy/credit.py](../../../../src/shibuya/economy/credit.py)・[src/shibuya/economy/pricing.py](../../../../src/shibuya/economy/pricing.py) 器
- [src/shibuya/engine/ledger_api.py](../../../../src/shibuya/engine/ledger_api.py) engine から台帳を呼ぶ口の型(engine は economy を import できない)
- [src/shibuya/engine/economy_stage2.py](../../../../src/shibuya/engine/economy_stage2.py)・[src/shibuya/engine/economy_rules.py](../../../../src/shibuya/engine/economy_rules.py) 腕・ATM の表・賃金と加入の判定の材料
- [src/shibuya/engine/events/links.py](../../../../src/shibuya/engine/events/links.py) 金の移動から出来事を書く口(`MoneyEventLink`)
- [src/shibuya/cli.py](../../../../src/shibuya/cli.py) 台帳の組み立て(`build_ledger_bundle`・`_HouseholdWalletLedger`)
- [src/shibuya/census/\_\_init\_\_.py](../../../../src/shibuya/census/__init__.py) 中身なし(4 行)

#### 元の決定

`10-12/CP1`・`10-12/CP2`・`10-12/§4-11`・`10-13b/§3`(K17=生ログの輪)・`10-13b/§7`(賃金)・`11-01/§5`(最低賃金の読み)・`#13`・`#14`・`#24`・`#35`・`#91`(1-9)・`#98`(2-1)・`#101`(既定 on)・`#115`・`#120`・`#122`・`#131`。

#### 棚卸しの指紋

`M18 K`・`M27 E`(保存則)・`M28 E`(制度の手順)・`S12 E`(保存則)・`S13 E`(保存則)・`A58 V`(腕 port の支払いの注)。仕分けの表 §1-2 は M27・S12・S13 を「今の挙動が式を破っている=直す対象」と書いています。

#### 既知の穴

- 日課由来の移動と、計画の退出で歩いて乗る体は運賃を払いません(M27・[段 1](../day-flow.md) §3)。
- 払い出しは最大 8 スロットで、9 スロット以上の店は偽の品切れになります(S12)。持ち物は 255 で頭打ちです(S13)。
- 世帯の物は全世帯の合計だけで、誰が何を持つかは答えられません(`goods.py` の docstring)。
- 物の生ログに出来事の id が入るのは補充だけで、販売・廃棄ビン・回収・消費は空です(同)。
- 賃金の原資は外界から同額を入れる外生です(`DOC-ec21-employer-funding-exogenous`)。店の外界の売上は 0 です(`DOC-ec21-external-store-sales-zero`)。
- 天引きの納付は給料日の締めに即時です(`DOC-rules42-remit-timing`)。
- 呼の控えは状態のファイルに入りません(`DOC-ec21-call-memo-not-saved`)。
- 旧道 `--economy-stage2 off`・`SHIBUYA_RULES_42=off`・`SHIBUYA_RULES_42B=off` は [11-05/§3-2](../../../design/prompt-2026-11-05-reply6.md) で消す予定です。
- 再開の `RunResult.conserved` が偽になる件は C8 に書きます。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 段階 2 は既定 off | 既定 on | `stage2.py` の冒頭(段 1 §11 #10)・`systems/build.py` の組み立ての注(「既定 off=何もしない」) |
| 給与の天引きは器だけ(規則の表に行が無い=0) | `SHIBUYA_RULES_42=on` で天引きする(`economy_stage2.attach` が `law` を渡す) | `stage2.py` の部品の表 |
| 切替口 `--wage w17`(次の版上げで消す) | 消した。CLI に無く、`SHIBUYA_WAGE` は止まる | `stage2.py` の docstring |
| 層の名 `census`(診断行・センサス) | 中身なし。センサスは `economy/census.py` | `census/__init__.py` |

### C2 権利

#### 何をしているか

誰が何にどんな権利を持つかの台帳です。1 行は持ち主・対象・種類(所有・賃借・雇用・許可・信用)・期間・相手・出どころ・原因です。組み立てで 1 回作り、ランの間は行が増えません(`grant` の呼び手は `rights/initial.py` だけ・`revoke` は src に呼び手なし)。持ち主は開閉の過程(`OpeningProcess`)です。

権利に反する行動は止めません。開閉店を権利の無い体が行うと、止めずに出来事の記録へ `行為:許可のない行動` を 1 行書いて数えます。読み手は開閉と補充の担当の表・カレンダー 3 と店の仕事の腕・段階 2 の給料日の雇用の行です。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 器と最初の中身(雇用・店の担当・店の賃借) | 既定 | 切替口なし。世界過程の無いランには無い |
| 住まいの行 | 既定(差し替えの世界に表があるときだけ) | `w21_rights_run.parquet` を読む(`load_run_rows`)。件数は #118 の記録で 27,491(data は未確認) |
| 許可のない行動の記録 | 既定 | 開閉店だけが書く。件数は `record.py` の docstring で既定は 0 行 |
| 役割語の権利の確かめ(`RoleActCheck`) | 既定(mock の道)・判定は数えるだけ | 効果の先が無いので役割語は安全弁の語へ落ちる |
| 営業許可 | 器だけ | 行は 0(`BR-RIGHTS-LICENCE-BLANK`) |
| 信用・道路の区間・看板の権利 | 器だけ | 種類の表にあるが行は 0(`rights/ledger.py` の docstring) |
| 違反に気づいた人・持ち主・警察の反応 | 無い(宣言なし) | `record.py` に「後の段」とある |

#### ファイル

- [src/shibuya/engine/rights/ledger.py](../../../../src/shibuya/engine/rights/ledger.py) 台帳の器(`Right`・`Rights`・書く口 2 つ)
- [src/shibuya/engine/rights/initial.py](../../../../src/shibuya/engine/rights/initial.py) 最初の中身・担当の丸振り・差し替えの世界の表
- [src/shibuya/engine/rights/record.py](../../../../src/shibuya/engine/rights/record.py) 許可のない行動の記録・役割語の確かめ・manifest の欄
- [src/shibuya/engine/processes/opening.py](../../../../src/shibuya/engine/processes/opening.py) 持ち主。開閉の権利を聞いて記録の口へ渡す
- [src/shibuya/engine/processes/runner.py](../../../../src/shibuya/engine/processes/runner.py) `rights`・`role_act_check`・`rights_fields`

#### 元の決定

`10-12/CP3`・`10-12/CP4`・`10-12/§1-4`・`10-12/§4-5`・`#91`(1-5)・`#118`(差し替えの世界)・`#120`(4-2)。

#### 棚卸しの指紋

`S26 E`(物理的に止める仕組み・止める仕組みが無いので止めない)。役割語が安全弁の語へ落ちる行は C12 の `A27 D` です。

#### 既知の穴

- 担当の丸振りが残っています(店 j → 従業者の j mod 人数 番目)。組織台帳との対応はありません(`initial.py` の expedient)。差し替えの世界では、表に担当のいない店だけ丸振りです。
- 区画の番号は POI の番号で代用し、家賃と貸し手は空欄です(`initial.py`)。
- 店の持ち主の行(`own → store`)は閉じた表に足しましたが、`in_closed_table` の列は世界の作り直しまで偽のままです(`rights/ledger.py`)。
- LLM サーバー群の道には確かめの口を挿していません(`BR-RIGHTS-FLEET-ROLE-CHECK`)。
- 丸振りの廃止は版上げ 5 回目の題です([PENDING](../../../../PENDING.md) §2 の 8)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 住まいの行は 0(空欄) | 表があれば読む | `BR-RIGHTS-DWELLING-BLANK`(active のまま)・`initial.py` の表の行。同じ docstring の〔段 10〕は読むと書く |
| 役割語は権限があるときだけ成立し、権限が無ければ失敗 | 権限によらず安全弁の語へ落ちる(腕 duties の補充と開閉店は別) | `perception/templates.py` の `ROLE_WORDS_LINE`(プロンプトの文・コードの注に記載あり) |

### C3 計器

#### 何をしているか

ランの中で数を取る部品と、ランの記録を読む道具です。ランの中の計器は結果を変えない約束で、値は `RunResult` と manifest に載ります。判定はしません。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 診断の行(`DIAG_RUN_COLUMNS`) | 既定 | 系 `observe`。切替口なし |
| 群・規範の計器(`GroupNormMeter`) | 既定 | `--group-norms`=on |
| 層の記録(`layer_counts`) | 既定 | mock も層 2 に数える(`build.py` の `_call_layer`) |
| 状態成長の検査(`check_growth`) | 既定 | 結果は `growth_report` に置きラン要約に載る |
| 在圏 journal | 腕 | `--occupancy-every`=0・`--occupancy-out` |
| 体の段の境目の計器 | 腕 | `SHIBUYA_BODY_BOUNDARY_GAUGE`=1 |
| 系ごとの全欄の差と指紋(`probe`) | 腕(試験と分岐) | `SHIBUYA_SYSTEMS_CHECK` |
| 受入と比較の道具(`tools/c6`・`tools/c7`) | 腕(ランの外) | 記録を読むか、別プロセスでランを回す |
| 忠実度の計器盤(`tools/c8/dashboard.py`) | 腕(ランの外) | Markdown と JSON を 1 枚に書く。画面は無い(C21) |
| ablation と感度試験(`tools/c8/ablation_runner.py`・`sensitivity.py`) | 腕(ランの外) | |
| 較正側の錨の計器(`tools/instruments/anchor_gauge.py`) | 腕(ランの外) | `read_guard.py` が封印の層を開く前に落とす |
| 判断モデルの評価(`tools/instruments/dm_eval/`) | 器だけ(ランの外) | 実装のある当て口は mock・古典・テープ。Clef ほかは口だけ(`__init__.py` の docstring) |
| 漏洩の検査(`tools/instruments/leak_check/`) | 器だけ(ランの外) | 実行は vLLM の後(PENDING §2 の 18) |
| 技量スコア・慣らし・ヒストリーマッチングの計器 | 器だけ(ランの外) | C5 |
| 事象の固定費・速さの試作(`tools/bench/event_cost/`・`tools/bench_spikes/`) | 腕(ランの外) | |

#### ファイル

- [src/shibuya/engine/systems/observe.py](../../../../src/shibuya/engine/systems/observe.py) 系 observe と checkpoint
- [src/shibuya/engine/systems/report.py](../../../../src/shibuya/engine/systems/report.py) ランの結果の組み立て
- [src/shibuya/engine/norm_meter.py](../../../../src/shibuya/engine/norm_meter.py) 群・規範の計器(同行・文脈別の行動エントロピー・役割語・伝播)
- [src/shibuya/core/growth.py](../../../../src/shibuya/core/growth.py)・[src/shibuya/engine/growth_decl.py](../../../../src/shibuya/engine/growth_decl.py) 状態成長の宣言と外挿の検査
- [src/shibuya/core/budget.py](../../../../src/shibuya/core/budget.py) 予算宣言表の読み取り
- [src/shibuya/engine/systems/probe.py](../../../../src/shibuya/engine/systems/probe.py) 系ごとの差(試験のときだけ)
- [tools/c7/c7_accept.py](../../../../tools/c7/c7_accept.py) 受入表・[tools/c7/holdout_compare.py](../../../../tools/c7/holdout_compare.py) 封印の照合(`--open-seal` を明示しないと読まない)・[tools/c7/salt_runs.py](../../../../tools/c7/salt_runs.py) と [tools/c7/salt_compare.py](../../../../tools/c7/salt_compare.py) salt の比較・[tools/c7/seed_ensemble.py](../../../../tools/c7/seed_ensemble.py) seed の帰無参照
- [tools/c8/dashboard.py](../../../../tools/c8/dashboard.py) 計器盤・[tools/c8/ablation_runner.py](../../../../tools/c8/ablation_runner.py)・[tools/c8/sensitivity.py](../../../../tools/c8/sensitivity.py)・[tools/c8/ensemble.py](../../../../tools/c8/ensemble.py)(ラン構成の生成だけ)
- [tools/instruments/anchor_gauge.py](../../../../tools/instruments/anchor_gauge.py)・[tools/instruments/read_guard.py](../../../../tools/instruments/read_guard.py)・[tools/instruments/batch_width_gauge.py](../../../../tools/instruments/batch_width_gauge.py)・[tools/instruments/dm_eval/cli.py](../../../../tools/instruments/dm_eval/cli.py)・[tools/instruments/leak_check/cli.py](../../../../tools/instruments/leak_check/cli.py)

#### 元の決定

`10-12/CA8`・`10-13b/§1-8`(較正側の錨)・`#35`・`#74`・`#75`(D-107 (a))・`#76`(感度の対照)・`#93`(2-0)・`#107`(6-1)・`#129`・`#130`・`#137`。CLAUDE.md §4 の計器盤の条項は [10-03/§6](../../../design/v2-wallbounce-decisions-2026-10-03.md) です。

#### 棚卸しの指紋

`S50 D`(割れる・M/M/c の観測の欄)。S46・S50 は「計器を 4 区分のどこに置くか」の問いとして §4 に上がっています。ほかの計器の行はありません。

#### 既知の穴

- 円/シミュ日の計器はありません(PENDING §2 の 7)。出来事の記録をファイルに書く口と S4 の計器もありません(PENDING §4)。
- 計器は呼数を判断・割り込み・持ち越した起床に分けていません(PENDING §2 の 20)。
- 計器の「LLM の呼数」は mock を含みます([段 1](../day-flow.md) §4-4)。
- 規範は経験的期待だけで、規範的期待(逸脱への反応)を測る機構がありません(`norm_meter.py` は「慣習」と宣言)。

#### 文書とコードの差

見つけていません。段 1 §11 #5 の呼数の古い値はここにも関わります。

### C4 manifest とランの種類

#### 何をしているか

ランの同定と設定と観測をまとめた辞書を作ります。実体は `RunResult.run_manifest_fields` で、欄を設定・観測・環境の 3 節に分ける表(`manifest_sections`)が付きます。ファイルに書くのは `--checkpoints-out` のときです(`cli.checkpoints_payload` の `manifest`)。ランの種類は再現・反実仮想・腕・試験の 4 つで、記録するだけです。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| manifest の辞書・節の表 | 既定 | ファイルは `--checkpoints-out`(既定は空) |
| ランの種類(`run_kind`) | 既定 | `cli.run` が決める。`run_day` を直に呼ぶと `None` |
| 実行モード(`--mode`) | 腕 | 既定 `smoke`。`cache_salt` の分離で、LLM サーバー群の設定にだけ入る |
| 型つきの manifest(`manifest.schema.RunManifest`) | 器だけ | src と tools に作る所が無い。試験 2 本だけ |
| 世界カタログ(`manifest/world_catalog.py`) | 既定(読むだけ) | 世界被覆指標の分母。呼び手は `build.audit.w18_coverage`・`world.processes.registry` |

#### ファイル

- [src/shibuya/engine/run.py](../../../../src/shibuya/engine/run.py) `RunResult`・`run_manifest_fields`・`summary`・`run_day`・CLI の共通の引数
- [src/shibuya/engine/manifest_sections.py](../../../../src/shibuya/engine/manifest_sections.py) 節の表
- [src/shibuya/engine/run_kind.py](../../../../src/shibuya/engine/run_kind.py) ランの種類
- [src/shibuya/cli.py](../../../../src/shibuya/cli.py) `run_arms`・`arm_baseline`・`checkpoints_payload`
- [src/shibuya/manifest/schema.py](../../../../src/shibuya/manifest/schema.py)・[src/shibuya/manifest/canonical.py](../../../../src/shibuya/manifest/canonical.py)・[src/shibuya/manifest/world_catalog.py](../../../../src/shibuya/manifest/world_catalog.py) 型・正規化・分母

#### 元の決定

`10-12/CP5-5`・`10-12/CP10`・`10-12/TM9`・`#84`(10f 第 1 段)・`#91`。

#### 棚卸しの指紋

該当の行なし。

#### 既知の穴

- 既定のランは manifest をファイルに書きません(標準出力の要約だけ)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| manifest は「全員が読む」・13 節の型 | ランが使うのは `schema` の `Mode` と `DIAG_COLUMNS` で、manifest は別の辞書 | `manifest/__init__.py`・`manifest/schema.py` |

### C5 実験と分岐

#### 何をしているか

反実仮想を回す仕組みです。申込書(`ExperimentForm`)に改変の決定と問いと指標を書いて渡すと、刻みの最初の系 `experiment` が決定を世界の表へ入れ、出来事に 1 行書きます。実験の条件を原因にできるのは `gate.admit` だけです。

分岐は「T0 までテープを再生し、T0 から今の方策」で回します。A/A の枝と改変の枝を回して 4 つの確認(入力の一致・T0 より前の一致・最初の食い違い・A/A の一致)を `branch_report.json` に書きます。アンサンブルは初期状態 × モデル × 偶然で、初期状態の半分を封印して探索と確認に分けます。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 申込書の無いラン | 既定 | 系 `experiment` は立たない(`conductor.WHEN`) |
| 水準 L0(`weather_date`・`holiday`)・L1(`opening_hours`・`closure`・`event`) | 腕 | `--experiment`=申込書の JSON(既定は空) |
| 水準 L2〜L4(`passage`・`barrier`・`construction`・`fare`・`service_suspension`・`new_store`・`visitors`) | 器だけ | `implemented=False`。効かせる口が「宣言して未実装」と記録して続ける |
| 告知(`notice`) | 腕(出来事の行まで) | 住人には届かない(`DOC-cf33-notice-rows-only`) |
| 分岐と 4 つの確認 | 腕 | `--experiment-branch`=基準のランの記録のディレクトリ・`--experiment-aa` |
| T からの切り替え(`ReplaySwitch`)・(d) の分け | 腕 | 分岐の中で使う |
| 封印と事前登録 | 腕 | `--experiment-model`。入口の検査 `ensemble.entrance`。公開の記録を書く呼び手は無い |
| 技量スコア・生の点数・慣らしの判定・ヒストリーマッチング | 器だけ | `ensemble.skill_container`(値は空)・`tools/instruments/skill_gauge.py`・`warmup_gauge.py`・`hm_gauge.py` |
| 過程と腕を切る ablation | 腕 | `--ablate`(既定は空)・`--budget-mode`・`--pnotice-d50-scale`・`--refractory-scale`・`--no-signage` |
| 天気を揺らす | 腕 | `--weather-perturb` |
| seed の 3 分割 | 既定 | `--seed`=1・`--population-seed` と `--environment-seed` は省略で `--seed` と同じ |
| salt の比較 | 腕(ランの外) | `tools/c7/salt_runs.py`・`salt_compare.py` |
| LLM サーバー群の分岐 | 無い(宣言なし) | 組み立てで止める(`DOC-cf33-branch-fleet`)。艦隊で録ったテープも拒む |

#### ファイル

- [src/shibuya/engine/experiment/form.py](../../../../src/shibuya/engine/experiment/form.py) 申込書と決定の表
- [src/shibuya/engine/experiment/apply.py](../../../../src/shibuya/engine/experiment/apply.py) 改変を世界の表へ入れる唯一の口
- [src/shibuya/engine/experiment/gate.py](../../../../src/shibuya/engine/experiment/gate.py) 実験が世界に入る口 `admit`
- [src/shibuya/engine/experiment/layer.py](../../../../src/shibuya/engine/experiment/layer.py) 組み立て・系 `experiment`・manifest の節・再開の照合
- [src/shibuya/engine/experiment/branch.py](../../../../src/shibuya/engine/experiment/branch.py) 分岐と 4 つの確認
- [src/shibuya/engine/experiment/switch.py](../../../../src/shibuya/engine/experiment/switch.py) T からの切り替え
- [src/shibuya/engine/experiment/ensemble.py](../../../../src/shibuya/engine/experiment/ensemble.py) 封印・事前登録・対の差の形・技量スコアの器
- [src/shibuya/engine/experiment/checks.py](../../../../src/shibuya/engine/experiment/checks.py) 申込書の点検(拒まない)
- [src/shibuya/engine/experiment/warmup.py](../../../../src/shibuya/engine/experiment/warmup.py) 慣らしの規則の事前登録

#### 元の決定

`10-12/§1-1`(CP6)・`10-12/§4-5`・`10-12/CP5`・`10-12/CP5-1`〜`10-12/CP5-6`・`10-12/CP12`・`10-12/CP14`・`#85`(seed の 3 分割)・`#99`(3-3)・`#108`(3-3b)。答申は R-71・R-117 です。

#### 棚卸しの指紋

該当の行なし。

#### 既知の穴

- 担当が店のセルに居ない店の開閉は代打(`set_open_flags`・conf 0.5)が実行します(`DOC-cf33-fallback-executes`)。報告は `execution_breakdown` と `executed_by_agents` に出ますが、`ok` には入りません。
- 「最初から」(始まり 0)は 0 の刻みの頭で当てるだけで、改変を当ててから経験を作る順は未実装です(`DOC-cf33-start-zero-order`・`DOC-cf33b-start0-order`)。
- ペルソナの文の名指しの検査と混入の疑いの検査は道具だけです(`DOC-cf33b-persona-check-caller`)。
- 決定の当て直しは日が替わるごとで、祝日は翌日以後だけです(`DOC-cf33-reapply-unit`)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 分岐の実験ではエンジンが代わりに実行しない | 担当の不在の店は代打が実行する(上の穴) | CLAUDE.md §3 |
| A/A の枝 2 本と改変の枝 1 本 | 食い違いがあれば改変の枝を 2 本(指紋の窓の回し直し)で計 4 本 | `cli.py` の `--experiment-branch` の help |
| 同じ組み立てで 4 本回す | 食い違いが無ければ 3 本(`run_branch` の第 2 段は A/A の枝 b だけ) | `branch.py` の docstring |

### C6 応答の記録(テープ)

#### 何をしているか

LLM の 1 呼び出しを 1 行の Parquet に残し、同じ鍵(体・刻み・種類・プロンプトのハッシュ)で答えを引いて再実行します。答えが返らなかった呼び出しも 1 行にします。共有のプロンプトブロックは内容のハッシュで 1 回だけ保存します。脇の `run_meta.json` に応答の遅れ・乱数の方式・暦の規則・環境を書きます。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 録画 | 腕 | `--tape`=ディレクトリ(既定は空=書かない) |
| 再生 | 腕 | `--replay`=ディレクトリ(既定は空)。`mode="replay"` になる |
| 版 4・21 列(`shibuya.tape/4`) | 録画のときの形 | `len(CALLS_SCHEMA)`=21(読み出し) |
| 腕の列 `recalled_event_ids` | 腕 | `--memory-store events` のランだけ足す |
| `recalled_source` | 器だけ | 列の予約で、記憶の作り直しまで空 |
| 複数日のラン・状態の口との組み合わせ | 無い(宣言なし) | 組み立てで `ValueError` |

#### ファイル

- [src/shibuya/engine/tape.py](../../../../src/shibuya/engine/tape.py) `TapeWriter`・`Tape`・`Replay`・`TapeRow`
- [src/shibuya/engine/llm_bridge.py](../../../../src/shibuya/engine/llm_bridge.py) 同期の道の録画と再生(`LLMBridge`)
- [src/shibuya/llm/mock.py](../../../../src/shibuya/llm/mock.py) `TapeLLM`
- [src/shibuya/llm/fleet.py](../../../../src/shibuya/llm/fleet.py) LLM サーバー群の道の録画(`TapeSink`)
- [src/shibuya/engine/run.py](../../../../src/shibuya/engine/run.py) `check_replay_tape`
- [tools/vocab/registry_from_tape.py](../../../../tools/vocab/registry_from_tape.py)・[tools/c6/t6_bit_reproduce.py](../../../../tools/c6/t6_bit_reproduce.py) テープを読む道具の例

#### 元の決定

`10-03/§3-4`(A8)・`10-13b/§3`・`#17`(D-58=版 2)・`#61`(版 3)・`#87`(E5=版 4)・`#88`・`#91`(腕の列)。

#### 棚卸しの指紋

該当の行なし。

#### 既知の穴

- 手元の実テープ(版 1〜2・52 本)は 10e より前の録画で、今の版では再生できません(`check_replay_tape` の docstring)。旧値の再現の切替口は消しました。
- テープ外の呼び出しは空の応答になり、未定義行動の道へ流れます。数は診断に出ます。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| テープ外は失敗 | `TapeMiss` を橋が受けて空の応答で続ける(実 LLM へは落とさない)。分岐の T0 より前も同じ | `tape.py` の docstring と `llm_bridge.py` |

### C7 出来事の記録

#### 何をしているか

世界で起きたことを 5W1H の列で残すログです。原因は `LlmCall`・`Process`・`Experiment` の 3 種類だけで、第 4 の型は作れません。書く口は `EventLog.append` の 1 つで、語彙は閉じた表です(118 語・読み出し)。書く系は `E:events.*` を宣言します。金の移動・過程の ActualLog の行は、出来事の id を目印の列に持ちます。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 記録 | 既定 | `--events`=on・`SHIBUYA_EVENTS`。結果を変えず、設定の指紋にもハッシュにも状態のファイルにも入らない |
| 保持 | 既定 | メモリの中に 7 日(`RETENTION_DAYS`)。1 行 72 B(`ROW_BYTES`) |
| ファイルへの書き出し | 無い(宣言なし) | PENDING §4 に持ち越しとある |
| 体の出来事 | 腕 | `--memory-store events` のランだけ |
| 看板を読んだ出来事 | 腕 | `SHIBUYA_TOOL_EVENTS`(既定 off)。作り物の印 `signboard:synthetic` |

#### ファイル

- [src/shibuya/engine/events/log.py](../../../../src/shibuya/engine/events/log.py) `Event`・`EventLog`・原因の 3 型
- [src/shibuya/engine/events/vocab.py](../../../../src/shibuya/engine/events/vocab.py) 語彙の表
- [src/shibuya/engine/events/links.py](../../../../src/shibuya/engine/events/links.py) ActualLog と金の行に目印を付ける口
- [src/shibuya/engine/events/body.py](../../../../src/shibuya/engine/events/body.py) 体の出来事の口
- [src/shibuya/world/processes/actual_log.py](../../../../src/shibuya/world/processes/actual_log.py) 過程の実績の記録(本体はグループ A の世界過程)

#### 元の決定

`10-12/CP12`・`10-12/CT9`・`10-12/§4-5`・`10-13b/§1-3`・`#91`(1-3)・`#100`(2-3)。

#### 棚卸しの指紋

該当の行なし。

#### 既知の穴

- 再開のランは空から書くので、記憶の器の目印の先が記録に無い行が出ます(`DOC-md23-pointer-after-resume`)。
- 語彙 v1/v2 の降車・待機・休憩と「その他」は判断の出来事に書かず数えます(`decision/layer.py`)。

#### 文書とコードの差

見つけていません。

### C8 保存と再開

#### 何をしているか

状態のハッシュを定期的に取り、頼まれれば状態を 1 ファイルに書き、そこから続きを回します。final は behavior-hash です。full-hash は復元に要る範囲のハッシュで、再開の検算に使います。状態のファイルは npz と JSON で、pickle は開かずに止めます。再開では設定の指紋(`fingerprint`)と見出しの腕を親と突き合わせ、違えば止めます。`finished: true` のランへは再開しません。LLM サーバー群へ出して返っていない呼び出しは保存し、再開で同じ call_id で出し直します。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| checkpoint(ハッシュだけ) | 既定 | `--checkpoint-every`=360。ファイルは `--checkpoints-out` |
| behavior-hash・full-hash | 既定 | `FINAL_DEFINITION`=`behavior`。切替口 `--hash-scheme` は消した |
| 複数日の通しラン | 腕 | `--sim-days`=1 |
| 状態のファイル | 腕 | `--state-out`(既定は空)。各日の締めの後とランの最後に書く |
| 再開 | 腕 | `--resume-from`(既定は空) |
| 日の途中で止める | 腕(CLI なし) | `stop_at_tick` は `cli.run` と `run_day` の引数だけ |
| `core/serialize.py` | 器だけ | src に呼び手なし。試験だけ |

#### ファイル

- [src/shibuya/engine/resume.py](../../../../src/shibuya/engine/resume.py) 状態の書き出しと読み込み・設定の指紋・環境の欄
- [src/shibuya/engine/state_codec.py](../../../../src/shibuya/engine/state_codec.py) npz と JSON の直列化(許可したクラスだけ組み立てる)
- [src/shibuya/engine/state_hashes.py](../../../../src/shibuya/engine/state_hashes.py) 2 つのハッシュ
- [src/shibuya/engine/systems/state_io.py](../../../../src/shibuya/engine/systems/state_io.py) `save_state`・`ledger_close`・`close_day_midrun`・`rebuild_derived`
- [src/shibuya/engine/systems/day.py](../../../../src/shibuya/engine/systems/day.py) 日の頭と日の終わりの条件
- [src/shibuya/engine/systems/run_end.py](../../../../src/shibuya/engine/systems/run_end.py) `drain`・`close_final`
- [src/shibuya/engine/resolve.py](../../../../src/shibuya/engine/resolve.py) `restore_soa`・`restore_items`
- [src/shibuya/core/serialize.py](../../../../src/shibuya/core/serialize.py) 器

#### 元の決定

`10-03/§3-6`(A10)・`10-03/§3-7`(A11)・`#81`(10b)・`#83`(10d)・`#84`・`#86`(npz)・`#87`(final の切り替え)・`#88`。

#### 棚卸しの指紋

該当の行なし。

#### 既知の穴

- 再開の `RunResult.conserved` が偽です(起点のずれ)。再開の後の full-hash もずれ、比べる物は behavior-hash です(PENDING §4)。
- `--memory-people memory` と `--memory-grain day` は再開に対応しません(`DOC-mr65-m1-people-limits`・`DOC-mr65-grain-day`)。
- 刻みの途中の状態は保存しません。止める位置は刻みの手前です。
- 記録と計器は状態に入らず、再開のランは 0 から数えます(C7・C9)。

#### 文書とコードの差

見つけていません。

### C9 状態の台帳

#### 何をしているか

世界の状態の全部の欄を 1 表に宣言します。軸 1「挙動」(behavior・no・diag)と軸 2「復元」(required・derivable・discardable・unknown)を持ち、ハッシュと状態のファイルはこの表から作ります。AST の検査が読み手の有無と軸を突き合わせ、揺らし試験が動的に確かめます。読み出すと全 254 行で、SoA が 99 行(agents 82・cells 5・pois 9・知覚 3)、外の状態が 155 行、腕の行が 41 行です。

#### 状態

既定です(読むだけで切替口なし)。版は `state-ledger/10e-ret` です。

#### ファイル

- [src/shibuya/engine/state_ledger.py](../../../../src/shibuya/engine/state_ledger.py) 台帳の宣言
- [src/shibuya/engine/state_ledger_ast.py](../../../../src/shibuya/engine/state_ledger_ast.py) AST の検査

#### 元の決定

`#81`(10b)・`#87`・`#88`(K15 の列の削除)。

#### 棚卸しの指紋

該当の行なし。

#### 既知の穴

- AST の検査は、配列を関数に渡した先の読みと `getattr(obj, 変数)` を追い切れません(`state_ledger_ast.py` の docstring)。
- 同じ名の列は軸 1 が同じでなければならない制約があります(同)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| `LEDGER` は 207 行の組・SoA 91 行(agents 74) | 254 行・SoA 99 行(agents 82) | `state_ledger.py` の docstring |

### C10 LLM サーバー群と推論(艦隊)

#### 何をしているか

実の vLLM へ非同期で呼び出しを投げるクライアントです。進行役は `submit` で投げて止まらず、次の刻みの系 `llm_receive` が `poll` で受け取ります。答えは `max(発射の刻み + 考える時間, 届いた刻み)` に適用します。考える時間の既定は段 L1 の 2.6 秒で、1 刻みへ切り上げます。接続エラーは同じレプリカ 1 回と別のレプリカ 1 回まで再試行し、タイムアウトと満杯は後回しにして次の刻みの候補へ戻します。書式エラーは温度 0 で 1 回作り直します。ランの終わりに残りを吸い切ります。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 既定のランの LLM | 既定は mock(この機能は動かない) | `--llm`=mock |
| `FleetClient`・`FleetBridge` | 腕 | `--llm fleet`+`--endpoints`(必須) |
| 復号の設定 | 腕 | `--temperature`=0.7・`--max-tokens`=96・`--model`=空 |
| 待ち方 | 腕 | `--fleet-wait-s`=0(待たない)。受理待ちの枠 `--fleet-queue-capacity`=0(既定の枠) |
| API key | 腕 | `SHIBUYA_FLEET_API_KEY`(空ならヘッダを付けない) |
| 書式の記録 | 腕 | `--fleet-debug-dir`=空 |
| 考える時間の段 L2〜L4 | 器だけ | `run_day(lane=)` の引数だけ。既定 `L1`。CLI に切替口なし |
| 5070 の夜の実験 | 腕(ランの外) | `tools/night5070/`。E1 の開始はユーザーの合図(PENDING §1-1) |
| 1 回限りの生成の運搬 | 腕(ランの外) | `tools/gen/fleet_gen.py`(構築の段の外) |

既定の並行度は `core.budget` が読む L6 で、合計は `per_replica × レプリカ数` です(`fleet.py` の docstring)。呼数の上限なしのランでは、枠の未指定を体数へ広げます(`cli.apply_fleet_queue_default`)。

#### ファイル

- [src/shibuya/llm/fleet.py](../../../../src/shibuya/llm/fleet.py) クライアントと橋・`FleetConfig`・`plan_batch`・`fleet_auth_headers`
- [src/shibuya/engine/systems/decide.py](../../../../src/shibuya/engine/systems/decide.py) LLM サーバー群の道の発射
- [src/shibuya/engine/systems/llm_io.py](../../../../src/shibuya/engine/systems/llm_io.py) 到着の受け取り(系 `llm_receive`)
- [src/shibuya/engine/systems/run_end.py](../../../../src/shibuya/engine/systems/run_end.py) 残りの吸い切り
- [src/shibuya/engine/llm_bridge.py](../../../../src/shibuya/engine/llm_bridge.py) 考える時間の表(`LANE_SECONDS`・`delta_think_ticks`)
- [tools/night5070/night_run.py](../../../../tools/night5070/night_run.py)・[tools/night5070/register_task.py](../../../../tools/night5070/register_task.py) 夜の実験とタスクの登録
- [tools/gen/fleet_gen.py](../../../../tools/gen/fleet_gen.py) 生成の運搬役

#### 元の決定

`#16`(C6)・`#17`(D-55・D-58)・`#55`(枠の既定)・`#127`・`#128`・`10-25/§6-0`・`11-01g`・`11-02r/§1`(#1=API key)・`10-25/§2-7`(再送の穴の確認)。

#### 棚卸しの指紋

`A09 V`(考えた時間を刻みへ切り上げ)・`A26 V`(間隔を発射の時点で付ける)・`A67 V`(5 刻みの帯)・`S21 V`(後回しで間隔を 0 に戻す)・`S31 V`(再投入の就寝の例外)。

#### 既知の穴

- 返事を待っている体にも新しい呼び出しを送ります(`DOC-fleet-resend-while-waiting`・PENDING §4)。
- 判断の口を通りません(C11)。分岐もできません(C5)。役割語の確かめも挿していません(C2)。
- 会話の番の発話の道は mock で通らないので段 B で確かめていません(`DOC-ca2-fleet-turn-unchecked`)。
- 今の既定の構成を実 LLM で 1 日回した記録は確認できません([段 1](../day-flow.md) §12)。往復の秒は艦隊が立った後に測ります(PENDING §2 の 21)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| API key は src の差分 1 件=判断待ち | `fleet_auth_headers` が入っている(PENDING §2 の 20 は済と書く) | `tools/night5070/README.md`・PENDING §1-1 の行・`docs/bench/analysis/night5070-1101/fleet_auth_pending.patch` |
| 艦隊=7 GPU の vLLM | `--endpoints` の本数で決まり、固定ではない。PENDING §0 は 5070 で再開の準備中 | 用語集 2-3 |
| 既定は起床のたびに全部 L2 | コードの段の既定は L1(語の衝突・段 1 §11 #14) | `absent.deliberate` |

### C11 判断の口と考える担い手

#### 何をしているか

呼び出された体の答えを作る部分です。既定は mock で、プロンプトを読まず語彙から一様に引きます。候補の口(`DecisionPort`)は、知覚の事実から 5 つの源(経験・周りが示すできること・近い予定・続ける・よく考える)と語彙の残りで候補を作り、並べ替えて番号を振り、選ばれた番号を元の id に戻す口です。実装は mock・古典・LLM の 3 つで、結果は今の道と同じです。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| mock | 既定 | `--policy`=mock・`--llm`=mock |
| 古典の方策(`ClassicalPolicy`) | 腕 | `--policy classical`・`--activity-region`・`--classical-social`・`--meal-gate` |
| 実 LLM | 腕 | C10 |
| 候補の口 | 腕 | `--decision-port`(引数の既定 None → `legacy`)・`SHIBUYA_DECISION_PORT`。`port` は結果を変えない |
| 判断モデル | 無い(宣言なし) | `ports.PORT_NAMES` は `llm`・`mock`・`classical` だけ。評価の器は `tools/instruments/dm_eval/` |
| 驚き・迷い・連続値・本人の予想 | 器だけ | `Choice` と `DecisionContext` の欄。どの実装も空 |
| 支払いの方法の答え(`Choice.payment`) | 器だけ | 3 つの実装は答えない |
| 候補「よく考える」 | 器だけ | 候補には載るが、選ばれても上の層を呼ぶ道が無い |
| 人物の文(`persona.py`)・短い版と長い版(`compose`) | 器だけ | `load_persona` は src に呼び手なし。`compose` の呼び手は `dm_eval/situations.py` だけ |
| よく考える | 無いと宣言 | `absent.deliberate` |
| 予定を考え直す・予想と違って直す | 無いと宣言 | `absent.replan`・`absent.plan_fix_surprise` |

#### ファイル

- [src/shibuya/engine/decision/port.py](../../../../src/shibuya/engine/decision/port.py) 型と提示の仕組み
- [src/shibuya/engine/decision/ports.py](../../../../src/shibuya/engine/decision/ports.py) 3 つの実装
- [src/shibuya/engine/decision/sources.py](../../../../src/shibuya/engine/decision/sources.py) 候補の 5 つの源
- [src/shibuya/engine/decision/layer.py](../../../../src/shibuya/engine/decision/layer.py) 腕・層・計器・判断の出来事
- [src/shibuya/engine/decision/persona.py](../../../../src/shibuya/engine/decision/persona.py) 人物の欄(器)
- [src/shibuya/llm/mock.py](../../../../src/shibuya/llm/mock.py) `MockLLM`
- [src/shibuya/engine/classical.py](../../../../src/shibuya/engine/classical.py) 古典の方策
- [src/shibuya/engine/systems/decide.py](../../../../src/shibuya/engine/systems/decide.py) 系 decide
- [tools/instruments/dm_eval/](../../../../tools/instruments/dm_eval/__init__.py) 評価の器

#### 元の決定

`10-12/§4-7`(DM-0・DM4・DM5・DM13)・`10-12/§4-12`(C-2)・`10-13b/§1-8`・`10-13b/§4-2`・`#48`(mock v3)・`#58`(古典)・`#91`(1-8)・`#92`(候補の源の結線)・`#107`。答申は R-108・R-113 です。

#### 棚卸しの指紋

`A34 V`(候補の源の優先)・`A35 K`(できることの規則)・`A55 V`(並べ替えの鍵)・`A56 D`(腕 port の mock の口)・`A57 V`(見出しと番号)・`A58 V`(支払いの注)。古典の選び手の `A38 K` はグループ B の購入の担当です。

#### 既知の穴

- 候補に「語彙の残り」が設計者の一覧として残っています(`DOC-j0-candidates-vocab`)。
- 道具 → 語彙の語の表 `TOOL_ACTION_WORDS` は空です(C22)。
- `MockPort.pick` が v3-0a の範囲から漏れています(PENDING §2 の 22)。
- LLM サーバー群の道は口を通らず数えるだけです(`note_fleet_calls`)。
- 計器「その他」の割合の既定は置かず未計測です(`OTHER_SHARE_DEFAULT`=None)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 人物の欄の短い版と長い版を `compose` が読む | ランの中に呼び手なし(`persona.py` の docstring は正しく書いている) | [IMPLEMENTED](../../../../IMPLEMENTED.md) #118 |

### C12 語彙と読み取り

#### 何をしているか

答えの形を決め、読む部分です。語彙 v3 は 12 語(移動・乗車・購入・食事・会話・退去・通報・手伝い・断る・就寝・並ぶ・なし)で、答えは理由・行動・対象・活動・まで の 5 ラベルです。パーサはラベル基準で寛容に読み、例外を投げません。語彙の外の語は同義語辞書で写し、写せなければ記録して安全弁の語(v3 は「なし」)へ落とします。語彙に足すかの判定はランの後に別の道具で行います。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 語彙 v3・5 ラベル | 既定 | `--vocab-version`=v3(ライブラリの既定は v1)。v1/v2 は旧の再現 |
| 自由意図の腕 | 腕 | `--intent-mode`=vocab。`open`・`hint` は v1/v2 と一緒のときだけ |
| パーサ・同義語辞書・未定義の台帳 | 既定 | 台帳のファイルは `--undefined-out`(既定は空) |
| 語彙の判定(5 段の 2〜3) | 腕(ランの外) | `tools/vocab/adjudicate.py` |
| 役割語 | 既定で効果なし | `--role-words`=on は B0 に行を出すだけ。腕 `--duties arm` の補充と開閉店は別 |
| ひと言の欄 | 腕 | `--speech-port on` の会話の番だけ(グループ B) |
| 接客・値段を変える・手伝いと断るの効果 | 無いと宣言 | `absent.serve_customer`・`absent.change_price`・`absent.help_refuse_effect` |

#### ファイル

- [src/shibuya/llm/contract.py](../../../../src/shibuya/llm/contract.py) 語彙・契約表・対象の型の正典
- [src/shibuya/llm/parser.py](../../../../src/shibuya/llm/parser.py) 2 行形と 5 ラベルの読み取り
- [src/shibuya/llm/undefined.py](../../../../src/shibuya/llm/undefined.py) 語彙外の 5 段階処理・同義語辞書・台帳
- [src/shibuya/llm/\_\_init\_\_.py](../../../../src/shibuya/llm/__init__.py) クライアントの契約と再輸出
- [src/shibuya/engine/llm_bridge.py](../../../../src/shibuya/engine/llm_bridge.py) プロンプト → 答え → 行動コードの接点
- [tools/vocab/adjudicate.py](../../../../tools/vocab/adjudicate.py)・[tools/vocab/registry_from_tape.py](../../../../tools/vocab/registry_from_tape.py) ラン後の語彙の判定

#### 元の決定

`#25`(D-71 段 2〜3)・`#26`(v2)・`#33`・`#41`・`#44`(役割語の行)・`#45`・`#46`〜`#48`(D-116 の二層)・`10-12/D3`。

#### 棚卸しの指紋

`A27 D`・`A28 D`・`A64 D`・`A65 D`・`A66 D`・`M25 D`(この 6 行は仕分けの表で「9-2 待ち」の印)・`A41 K`(「まで」の既定 60 分)。

#### 既知の穴

- 行動の欄で最初に現れた語彙語を取り、否定を読みません(A28)。
- 語彙の外の答えは対象の欄を捨てます(A64)。
- 理由 40 字とひと言 20 字より先は切ります(A65)。
- 同義語辞書が移す語は意味を失います(用語集「同義語辞書」)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 種別横断 12 語(降車・待機・休憩を含む) | CLI の既定は v3 の 12 語(なしを含む) | `llm/__init__.py` の docstring(v1 の語) |
| 役割語 12 語 | v3 の B0 は 11 語(`ROLE_WORDS_V3`=並ぶを除く) | `cli.py` の `--role-words` の help |

### C13 知覚

#### 何をしているか

呼ばれた体の状態を、構造を持った事実 `Percept` にしてから文に描きます(`Renderer.perceive` → `render_percept` → `draw`)。文は B0(役割と規則)・B1(種別)・B2(場所)・B3(時間と天候)・B4(場所の様子)・B4b(近くの様子)・B5(本人)・B6(直前の結果)です。テンプレートは凍結で版が付き(`v1.4`)、ブロックごとのトークンの上限(`CHANNEL_LIMITS` 12 行)で行を落とします。セルごとの欄は刻みごとに前計算し、変化の検出もその欄を読みます。描画は mock のランでも走ります。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 描画と知覚の事実 | 既定 | 切替口なし。試験用に `renderer="stub"` |
| 固定枠の配分 | 既定 | `--budget-mode`=fixed。`ranking` は腕 |
| 看板 | 既定は全部載せる | `--signage-p-see`=1.0・`--no-signage` |
| 空腹の語の幅 | 既定は空腹以上 | `--hunger-words`=hungry |
| W14・W15 の凍結文 | 既定(資産があれば) | 無ければ合成の文(`PerceptionAssets.load_or_synthetic`) |
| 気づく確率(`p_notice`) | 器だけ | 呼び手は `processes/salient.py`。既定は倒れる人も出動も無く通らない。`--pnotice-d50-scale`=1.0・`--ablate AB-PNOTICE-A…` |
| 空の欄 10 個(`EMPTY_FIELDS`) | 器だけ | `eye_dir`・`mind_dir`・`belongings`・`tool_state`・`watched_by`・`heard_speech`・`nearby_change`・`acquaintance_seen`・`prediction`・`heard_referents`。腕 `--contact c1` は `mind_dir`・`tool_state` に値を入れる |
| 周辺視と通知の行(`contact_view.py`) | 腕 | `--contact c1` |
| 注意の段 3(`content_cap_chars`・`gaze_seconds`・効果の上限) | 器だけ | `perception/__init__.py` の再輸出の外に呼び手なし |
| 看板を見る確率の段(`attention.gate_stage1`) | 既定で素通し | p_see が 1.0 のとき常に載せる |
| 再送抑止(ハッシュ三役の 1 つ) | 無い(宣言なし) | 列を消した。`state.py` は「作るときに改めて宣言」と書く |

#### ファイル

- [src/shibuya/perception/renderer.py](../../../../src/shibuya/perception/renderer.py) 描画の本体・`PerceptionAssets`
- [src/shibuya/perception/facts.py](../../../../src/shibuya/perception/facts.py) `Percept`
- [src/shibuya/perception/templates.py](../../../../src/shibuya/perception/templates.py) 凍結の文面と段階の語
- [src/shibuya/perception/channels.py](../../../../src/shibuya/perception/channels.py) トークンの上限と切り詰め
- [src/shibuya/perception/normalize.py](../../../../src/shibuya/perception/normalize.py) バイト一致の規約 9 項
- [src/shibuya/perception/hashes.py](../../../../src/shibuya/perception/hashes.py) 描画のハッシュと欄の行
- [src/shibuya/perception/attention.py](../../../../src/shibuya/perception/attention.py) 看板を見る確率・顕著性・命令文の除去
- [src/shibuya/perception/p_notice.py](../../../../src/shibuya/perception/p_notice.py) 気づく確率
- [src/shibuya/perception/state.py](../../../../src/shibuya/perception/state.py) 向きと課題従事の SoA
- [src/shibuya/perception/contact_view.py](../../../../src/shibuya/perception/contact_view.py) 連絡の腕の知覚
- [src/shibuya/engine/systems/perceive.py](../../../../src/shibuya/engine/systems/perceive.py) 系 `perceive_prepare`・`detect`
- [src/shibuya/engine/llm_bridge.py](../../../../src/shibuya/engine/llm_bridge.py) `PerceptionRendererAdapter`・`StubRenderer`

#### 元の決定

`#6`・`#7`(知覚契約書 v1)・`#12`(C3)・`#36`(看板)・`#44`・`#59`(係数は後に 1-2 で消した)・`10-12/§1-6`・`10-12/§1-13`・`10-12/§4-4`・`10-13b/§4-2`・`#91`(1-2)。

#### 棚卸しの指紋

行が多い機能です。区分ごとに並べます。

- V(題 9-1 などで形が変わる) `A05 V`・`A06 V`・`A07 V`(割れる)・`A10 V`・`A13 V`・`A15 V`・`A33 V`・`A39 V`・`A43 V`・`A44 V`・`A45 V`・`A46 V`・`A47 V`・`A51 V`・`A52 V`・`A53 V`・`A61 V`・`A68 V`・`A72 V`(割れる)・`M22 V`・`S48 V`・`S49 V`
- D(仕組みの無い文言) `A08 D`・`A11 D`・`A12 D`・`A29 D`・`A30 D`・`A31 D`・`A32 D`(割れる)・`A36 D`・`A59 D`・`A60 D`・`A62 D`・`A70 D`・`A74 D`
- E `A24 E`(物理)・`A48 E`(物理・割れる)・`A49 E`(制度の手順・割れる)・`A50 E`(物理)・`A63 E`(物理)・`A71 E`(物理)

M22・S48・S49・A15 は `processes/crowd.py` の行で、グループ A の席と列にも関わります。

#### 既知の穴

- 人物像・日課の中身・既定の記憶はプロンプトに載りません([段 1](../day-flow.md) §4-5)。
- 見える店の上位を選ぶ処理と描く処理が同じ部品にあり、世界の事実と本人の注意を分けていません(A05・A06・A10)。
- 被注視は値を作る仕組みが無く常に「あなたを見ている人はいません」と書きます(A60)。B4b の「25メートル以内」の判定もありません(A59)。
- 値段は買えなかった後にしか見えません(`absent.price_balk`)。
- 看板の文は W14 で LLM が書いた作り物です(`BR-SIGNAGE-FICTION`)。
- 内受容の閾値 `INTERO_UP_EDGES` は `change_detect.py` と二重定義です(`renderer.py` の docstring)。
- B2 の W15 の枠の読みは親の判断待ちのままと注にあります(`renderer.py` の docstring)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 流れは既定 0・方向データが無い | `processes/crowd.py` が流れを計算して描画へ渡す(`sys_perceive_prepare` の `flow=runner.flow`) | `renderer.py`・`change_detect.py` の docstring |
| 欄ハッシュ=密度段・騒音段・営業中 POI 数 | 欄は LOS 段・騒音段・流れ・顕著行為のダイジェスト | `hashes.py` の docstring(`change_detect.py` は POI 数を外したと書く) |
| ハッシュ三役(キャッシュ鍵・変化検出・再送抑止) | 再送抑止は無い | `hashes.py`・`renderer.py` の docstring |
| B5 近接人物 `max_items=3` | 知人の常掲・会話の参加者・焦点で 3 を超えうる | `channels.py`(コードの注に記載あり) |

### C14 呼び出し(起床)=変化の検出と割り当て

#### 何をしているか

誰を今の刻みに呼ぶかを決めます。変化の検出は内受容 3 変数の段(4/7/9・ヒステリシス 1)とセルの欄の変化を見て候補を作り、世界には書きません。候補の源は計画の切れ目・変化の検出・会話の番・顕著行為・答えが返らなかった呼び出し・活動の満了です。

割り当ては舞台の外の見送り → 就寝の見送り → 再呼び出しの間隔 → 待ち時間での優先上げ → 同じ体の合流 → 固定優先の整列 → 予算の切りの順です。種類は会話 > 計画の切れ目 > 個体の変化 > 場所の変化の 4 つで、間隔は条件ごとに 11 行あります(`REFRACTORY_MINUTES`=0/360/150/60/15/45/10/15/5/5/30)。呼び出し条件は活動の満了を足して 12 種です。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 変化の検出(内受容・セルの欄) | 既定 | 切替口なし |
| 割り当て | 既定 | 切替口なし |
| 呼数の上限 | 既定は無制限 | `--l4-scale`=0(1 刻みの枠=体数)。1.0 で旧の按分。10 呼/体/日は監査の線 |
| 見送りの帰無腕 | 腕 | `--no-sleep-suppression`・`--no-outside-suppression` |
| 間隔の倍率 | 腕 | `--refractory-scale COND=FACTOR` |
| 活動の満了・活動中と歩行中の抑え | 既定 | `--activity`=on |
| 知人の出現 | 腕 | `--relations on`(`--memory on` も要る)と `--rel-acq-wake`=on(系 `relations_wake`) |
| 変化の印の体だけ見る | 腕 | `--step-scope changed` |
| 近接の入れ替わり・被注視・傍受の 3 条件 | 器だけ | 表に行と間隔があるが検出しない(`change_detect.py`) |
| 簡略応答 | 器だけ | 予算不足のとき数えるだけで、小さいモデルや短い観測へ替える道が無い(`selected_degraded` の読み手は engine に無い) |
| 眠気や明るさで目を覚ます | 無い(宣言なし) | 目を覚ますのは日課の切れ目(段 1 §4-1) |

#### ファイル

- [src/shibuya/engine/change_detect.py](../../../../src/shibuya/engine/change_detect.py) 変化の検出
- [src/shibuya/engine/arbiter.py](../../../../src/shibuya/engine/arbiter.py) 割り当て
- [src/shibuya/engine/scheduler.py](../../../../src/shibuya/engine/scheduler.py) 待ち行列の保管庫(`DeferralQueue`)と予約の輪(`Scheduler`)
- [src/shibuya/agents/state.py](../../../../src/shibuya/agents/state.py) `WakeCondition`・`REFRACTORY_MINUTES`・`WAKE_CONDITION_CLASS`
- [src/shibuya/engine/systems/judge.py](../../../../src/shibuya/engine/systems/judge.py) 系 `wake_sources`・`wake_filter`・`wake_assemble`・`arbiter`
- [src/shibuya/engine/systems/perceive.py](../../../../src/shibuya/engine/systems/perceive.py) 系 `detect`
- [src/shibuya/engine/systems/body.py](../../../../src/shibuya/engine/systems/body.py) 系 `plan_boundary`
- [src/shibuya/engine/step_scope.py](../../../../src/shibuya/engine/step_scope.py) 腕 `changed`

#### 元の決定

`#10`(C2)・`#12`・`#17`(D-56)・`#18`(D-66)・`#38`(D-99)・`#55`(D-110)・`#95`(間隔を外した腕の計測)・`09-25`・`10-13b/§4-1`・`10-13b/§4-2`。

#### 棚卸しの指紋

- V `A03 V`・`A04 V`(割れる)・`A14 V`・`A26 V`・`A73 V`・`M12 V`・`S16 V`・`S21 V`・`S30 V`・`S31 V`
- K `A16 K`・`M26 K`
- D `A25 D`・`M13 D`・`S27 D`・`S28 D`・`S29 D`・`S52 D`

#### 既知の穴

- セルの欄が 1 つでも変わると在席者全員が候補になります(A03)。最初の検出は全セルが変化になります(A25)。
- 間隔は名は分ですが刻みとして使います(A04)。発射の時点で付くので、後回しや答えの遅れでも消費します(A26)。
- 間隔の 11 行と種類の表はつなぎです(`BR-REFRACTORY-*`・`BR-WAKE-CONDITION-CLASS`。外す段は T3)。
- 傍受の同じ話者 30 分は未実装です(`agents/state.py` の注)。
- 答えが返らなかった顕著行為は、寝ている間は蒸し返しません(`judge.py` の注)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 平均 10 呼/体/日が制御目標 | CLI の既定は上限なしで監査の線 | `arbiter.py` の docstring(段 1 §11 #7) |
| 起床条件 (ii) に知人・近接・被注視・傍受 | 検出するのは内受容だけ(`change_detect.py` に記載あり) | 知覚契約書 §6 の引用 |

### C15 行為の解決(二段階の確定)

#### 何をしているか

答えを世界へ書く順を決めます。意図を集め(`phase_a`)、席や棚の取り合いを決着させ(`phase_b`)、確定した分だけ書きます(`phase_c`)。世界へ書く口は `engine/resolve.py` が担うと宣言し、`writable()` の解除と許可の列で機械的に縛ります。個別の行為の中身はグループ A とグループ B の担当です。

#### 状態

既定です。切替口は `--queue-service`=on・`--report-precondition`=on(どちらも帰無腕)と、旧道の `--defect-fixes-1103`(引数の既定 None → on)です。

#### ファイル

- [src/shibuya/engine/commit.py](../../../../src/shibuya/engine/commit.py) 意図の収集と資源ごとの決着
- [src/shibuya/engine/resolve.py](../../../../src/shibuya/engine/resolve.py) 世界の状態への書き込み・再開の戻し
- [src/shibuya/engine/systems/act.py](../../../../src/shibuya/engine/systems/act.py) 系 `phase_a`・`phase_b`・`phase_c`
- [src/shibuya/engine/intent.py](../../../../src/shibuya/engine/intent.py) 意図の保持(歩いて着いたら呼ばずに実行)

#### 元の決定

`#10`(C2)・`#54`(意図の保持)・`#138`(欠陥 4 件)・`11-03/§3`。

#### 棚卸しの指紋

`A18 V`・`B1 V`・`M7 V`・`M8 V`・`M9 V`・`S8 V`・`S9 V`・`S10 D`。購入・席・列・移動の行はグループ A と B の担当です。

#### 既知の穴

- 同じ刻みの席と最後の 1 個は行の順で決まります(M8)。
- 再試行の回は容量 0 で、第 2 希望がありません(S9)。
- F1〜F4(会話の番で別の行為を選んだ体・列の処理の順・招待の帳尻・列の印の残る道)は仕分けの表 §5-3 にあります。

#### 文書とコードの差

見つけていません。段 1 §11 #1 の刻みの順はここにも関わります。

### C16 進行役・系の表・書きの許可

#### 何をしているか

刻みの中の処理を「系」に分け、宣言の表の順に呼びます。表は 36 系(組み立て 1・日の頭 1・刻みの中 30・日の終わり 1・ランの終わり 3)で、既定のランで立つのは刻みの中の 22 系です([段 1](../day-flow.md) §1-2)。系ごとに読む欄と書く欄を宣言し、書く SoA の列は `resolve_ops` の静的な閉包から機械で作ります。実行時に許可の外を書くと落ちます。状態は箱(`RunConfig`・`SoAState`・`Layers`・`LlmIo`・`DayTables`・`Buffers`・`TickScratch`・`RunStats`・`Fixtures`)に分けます。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 進行役・表・組み立て | 既定 | 切替口なし |
| 書きの許可 | 既定 | `SHIBUYA_WRITE_GUARD`=on(外しても結果は同じ) |
| 段 B と番兵の検査 | 腕(試験) | `SHIBUYA_SYSTEMS_CHECK` |
| AST の検査・負の対照(`static_check.py`・`overrides.py`) | 腕(試験) | src に呼び手なし |
| 層の契約 | 既定(CI) | `pyproject.toml` の import-linter に 5 本。CI は `ci-0`・`ci-1`・`ci-2` の 3 段(`.github/workflows/ci.yml`) |

#### ファイル

- [src/shibuya/engine/systems/conductor.py](../../../../src/shibuya/engine/systems/conductor.py) 進行役
- [src/shibuya/engine/systems/table.py](../../../../src/shibuya/engine/systems/table.py) 系の表
- [src/shibuya/engine/systems/build.py](../../../../src/shibuya/engine/systems/build.py) 組み立て
- [src/shibuya/engine/systems/boxes.py](../../../../src/shibuya/engine/systems/boxes.py) 状態の箱
- [src/shibuya/engine/systems/spec.py](../../../../src/shibuya/engine/systems/spec.py)・[src/shibuya/engine/systems/allow.py](../../../../src/shibuya/engine/systems/allow.py) 宣言の口と閉包
- [src/shibuya/engine/systems/guard.py](../../../../src/shibuya/engine/systems/guard.py)・[src/shibuya/core/write_permit.py](../../../../src/shibuya/core/write_permit.py) 書きの許可
- [src/shibuya/engine/systems/probe.py](../../../../src/shibuya/engine/systems/probe.py)・[src/shibuya/engine/systems/static_check.py](../../../../src/shibuya/engine/systems/static_check.py)・[src/shibuya/engine/systems/overrides.py](../../../../src/shibuya/engine/systems/overrides.py) 試験の口
- [src/shibuya/engine/owner_guard.py](../../../../src/shibuya/engine/owner_guard.py) 外の状態の持ち主の守り
- [src/shibuya/core/soa.py](../../../../src/shibuya/core/soa.py) SoA のレジストリとバイト予算
- [src/shibuya/engine/run.py](../../../../src/shibuya/engine/run.py) `run_day` の入口

#### 元の決定

`#9`(C0)・`#89`(1-0)・`#90`(1-0b)・`10-13b/CI-1`・`10-13b/§0-4`。

#### 棚卸しの指紋

該当の行なし。

#### 既知の穴

- 閉包は `resolve.py` の外へ出る呼び出しをたどらず、手の表 `ALIAS_WRITES` に頼ります(`allow.py` の docstring)。
- 同じ名の列が余分に入り、閉包は上限です(同)。
- 静的な検査は層のメソッドの中の読みを見ません(`static_check.py` の docstring)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 刻みの中 25 系 | 30 系 | `table.py`(段 1 §11 #8) |
| 系 31 | 全 36 系 | IMPLEMENTED #89(当時の値) |

### C17 時計と窓

#### 何をしているか

時間の持ち方と進め方です。進行役は「次に処理する時刻の窓」を持ち、窓の中の事象を時刻順に処理します。既定の世界の事象は刻みの事象だけで、幅は 60 秒です。暦の口は日付・曜日・祝日・給料日を引く 1 か所です。時間の定数は `core/time_consts.py` に集めました。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 窓の待ち行列 | 既定 | `--batch-width-s`(引数の既定 None → 60)・`SHIBUYA_BATCH_WIDTH_S` |
| 暦の口 | 既定 | `--start-date`=空(2026-07-13)・`--holiday-csv`・`--school-holidays` |
| 会話の時計 | 腕(計器だけ) | `--talk-clock`=table。`mora` |
| 何かあった体だけ | 腕 | `--step-scope`=all。`changed` |
| 体の予約 | 腕 | `--body-schedule`=sweep。`reserve` |
| 場所ごとの時計 | 腕 | `--clock`=global。`regional` |
| 混合の時計 | 器だけ | `--clock mixed` は組み立てで `NotImplementedError` |
| `engine/clock.py` の `SimClock` | 器だけ | 呼び手は `engine/__init__.py` の再輸出だけ(カード) |

#### ファイル

- [src/shibuya/engine/batching.py](../../../../src/shibuya/engine/batching.py) 窓の待ち行列
- [src/shibuya/engine/calendar.py](../../../../src/shibuya/engine/calendar.py) 暦の口
- [src/shibuya/core/time_consts.py](../../../../src/shibuya/core/time_consts.py)・[src/shibuya/core/types.py](../../../../src/shibuya/core/types.py) 時間の定数と時刻の型
- [src/shibuya/engine/speech_clock.py](../../../../src/shibuya/engine/speech_clock.py)・[src/shibuya/engine/step_scope.py](../../../../src/shibuya/engine/step_scope.py)・[src/shibuya/engine/regional_clock.py](../../../../src/shibuya/engine/regional_clock.py) 時計の段 T2〜T4 の腕
- [src/shibuya/engine/body/schedule.py](../../../../src/shibuya/engine/body/schedule.py) 体の予約の腕
- [src/shibuya/engine/clock.py](../../../../src/shibuya/engine/clock.py) 器

#### 元の決定

`10-12/§4-2`・`10-12/TM1`・`10-12/TM3`〜`10-12/TM8`・`10-03/§3-1`・`10-03/§7-5`・`#80`(10a)・`#91`(T0)・`#103`(T1)・`#105`・`#114`。

#### 棚卸しの指紋

`A68 V`(時計の既定=分=刻み)・`A69 V`(引数の既定に刻み 60 秒)・`A47 V`(5 分切り捨て)。

#### 既知の穴

- 事象の時刻の粒度は 60 秒です(`DOC-tm32-event-time-60s`)。世界の時刻は刻みでしか進みません(`core/types.py`)。
- 「1 つの会話の中はまとめない」は、会話の番が刻みに 1 回の形のままです(`DOC-tm32-conversation-not-batched`)。
- 刻みの番号で作る鍵の残りは C18 に書きます。

#### 文書とコードの差

見つけていません。

### C18 乱数と決定論

#### 何をしているか

同じ設定なら同じ結果になる仕組みです。乱数は Philox4x64 のカウンタ方式で、鍵は (seed, 用途)、カウンタ側に刻みと体を置きます(`RNG_SCHEME`=counter・読み出し)。seed は動き・母集団・環境の 3 つに分かれます。同じ時刻の順序づけは blake3 の鍵です。v3-0a で、届く 18 か所の鍵は世界の時刻 t_ns から作る形にしました(値は不変)。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| カウンタ方式の乱数 | 既定 | 切替口なし(`stateful` の道は消した) |
| seed の 3 分割 | 既定 | C5 |
| 流れの重なりの検査(`rng_audit.py`) | 腕(試験) | src に呼び手なし |

#### ファイル

- [src/shibuya/core/rng.py](../../../../src/shibuya/core/rng.py) 乱数の口(`stream`・`philox`・`k19_counters`・`key_time_from_t_ns`)
- [src/shibuya/core/hashing.py](../../../../src/shibuya/core/hashing.py) 優先度キーと決定論のハッシュ
- [src/shibuya/engine/run.py](../../../../src/shibuya/engine/run.py) `run_salt_for`・`POPULATION_RNG_DOMAINS`・`ENVIRONMENT_RNG_DOMAINS`・`MOTION_RNG_DOMAINS`
- [src/shibuya/engine/rng_audit.py](../../../../src/shibuya/engine/rng_audit.py) K19 の検査

#### 元の決定

`10-12/TM7`・`11-04/§2`(その 1=v3-0a 案 A)・`#82`(10c)・`#85`・`#86`(K25)・`#87`(E4)・`#88`・`#139`。

#### 棚卸しの指紋

`A52 V`・`A53 V`・`A54 V`・`A55 V`・`S39 V`(どれも鍵)。

#### 既知の穴

- 刻みの番号から作る鍵が約 27 か所残っています(PENDING §2 の 22・v3-0b)。
- 実 LLM は同じ設定でも A/A が食い違います(`experiment/switch.py`)。決定論の札は mock と古典だけです。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| `--rng-scheme counter`(既定) | CLI に `--rng-scheme` は無い | `rng_audit.py` の docstring |
| `--calendar-weekday`・`--rng-scheme` を足す | `add_calendar_args` に無い | `cli.py` の注 |
| 既定は `--calendar-weekday real`・`--weather-scheme calendar` | どちらも消した(`check_replay_tape` の docstring) | `run.py` の docstring |

### C19 構築

#### 何をしているか

ランの前に世界の資産を作る工程です。段階は W0〜W20 で、`build/run.py` が依存順に回し、全段の出力のハッシュから `build_hash` を作ります。LLM は呼ばず、プロンプトを書いて応答の jsonl を取り込みます。実行時に `build` は import されません(import-linter の契約)。

W21(ペルソナと人口の作り直し)とナビメッシュ(`build/space/navmesh1.py`)は別の入口です。ランは `--world`(既定 `data/world/v2`)の成果物を読みます。資産が無い場所では合成の小さな世界で回します(`--cells`=139)。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 構築の工程 | 腕(ランの外) | `python -m shibuya.build.run`・`--stage`・`--keep-stage`。W17 は明示しない限り上書きを拒む |
| 成果物の読み込み(`world/assets.py`・`world/state.py`) | 既定 | `--world`・`--area-source`=legacy |
| 検証の封印(W19) | 既定のランは開かない | 照合は `tools/c7/holdout_compare.py` が `--open-seal` のときだけ行う |

| 段 | 中身 | ファイル |
|---|---|---|
| W0〜W6・W11 | 原点・歩行グラフ・セル・距離・建物・入口・POI と組織・駅の出口 | `build/geo/` |
| W7・W10・W12・W13 | 営業時間・騒音・外界(鉄道ほか)・気象 | `build/field/` |
| W8・W9 | 可視性・影 | `build/vis/` |
| W14・W15 | 看板文・場所の定型文 | `build/lang/` |
| W16 | 母集団 | `build/pop/w16_population.py` |
| W17 | 日課表 | `build/sched/`(`trial.py --promote` で昇格) |
| W18〜W20 | 被覆・凍結・検収 | `build/audit/` |
| W20cal | カレンダー 1a の表 | `build/sched/w20_calendar_1a.py` |
| W21 | ペルソナと人口の作り直し | `build/pop/w21_*.py`(`w21_build`・`w21_apply`) |
| 段 1 ナビメッシュ | 歩ける面 | `build/space/navmesh1.py` |

#### ファイル

- [src/shibuya/build/run.py](../../../../src/shibuya/build/run.py) 通し実行と `build_manifest.json`
- [src/shibuya/build/catalog_freeze.py](../../../../src/shibuya/build/catalog_freeze.py) 世界カタログの凍結
- [src/shibuya/world/assets.py](../../../../src/shibuya/world/assets.py)・[src/shibuya/world/state.py](../../../../src/shibuya/world/state.py) 資産の読み込み・世界の SoA・合成世界
- [tools/gen/fleet_gen.py](../../../../tools/gen/fleet_gen.py) 生成の運搬
- [tools/world_data/estat_fetch.py](../../../../tools/world_data/estat_fetch.py)・`tools/realworld_fetch/`・`tools/build_geo/`・`tools/spatial/` 材料の取得と集計

#### 元の決定

`#11`(C1)・`#15`(C5)・`#19`(W17 v2)・`#49`・`#94`・`#102`・`#104`・`#109`・`#111`・`#118`・`#124`・`#126`・`10-25/§2-1`・`10-25/§2-4`。

#### 棚卸しの指紋

`A24 E`(物理・歩ける面積の下限)。ほかの行は資産を読む側の機能に載っています。

#### 既知の穴

- 段 0 の取得の残りがあります(PENDING §2 の 10)。孤立の断片 20 セルは段 2 の後です(PENDING §4)。
- W14 の看板は作り物です(`BR-SIGNAGE-FICTION`)。西武渋谷店は床と入口だけの 1 部屋です(PENDING §2 の「つなぎ」)。
- 全国の材料だけで組む腕はありません(PENDING §1-1 と §3 の段 0 の汎用化)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 資産ビルド W0〜W20 の 21 段階 | W21 とナビメッシュが別の入口であり、`build/run.py` の `ALL_STAGES` に入らない | 用語集 2-4 |
| セル数 139・453・520 | `--cells` の既定は合成世界の 139。実データの値は `world/assets.py` が食い違いとして記載 | 予算行 P6 ほか |

### C20 母集団

#### 何をしているか

住民の表を読み、ランの体の数へ抽出します。母集団は 345,858 体です([版上げの履歴](../../../ops/version-history.md) 3 回目)。W16 の残す行と W21 の人でできています(#118)。抽出は二層で、機能に要る定員を先取りし、残りを種別 × 年齢階級 × 性別で最大剰余法の比例配分にします。抽出と体の定数の乱数は母集団の seed です。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 母集団と抽出 | 既定 | `--agents`=5,000・`--population-seed`=None(`--seed` と同じ) |
| 合成個体(下限対照) | 腕 | `--no-population`。資産の無い世界でも同じ道 |
| 人物の文(短い版・長い版) | 器だけ | C11。賃金は母集団の列 `wage_monthly` と `persona_pool_v2` の職業の語を読む(`wage_inputs`) |

#### ファイル

- [src/shibuya/agents/population.py](../../../../src/shibuya/agents/population.py) 読み込みと二層抽出
- [src/shibuya/agents/state.py](../../../../src/shibuya/agents/state.py) 体の SoA
- [src/shibuya/agents/schedule.py](../../../../src/shibuya/agents/schedule.py) mock 専用の合成日課
- [src/shibuya/build/pop/w16_population.py](../../../../src/shibuya/build/pop/w16_population.py)・[src/shibuya/build/pop/w21_build.py](../../../../src/shibuya/build/pop/w21_build.py)・[src/shibuya/build/pop/w21_apply.py](../../../../src/shibuya/build/pop/w21_apply.py) 構築の側

#### 元の決定

`#14`・`#15`・`#104`・`#109`・`#111`・`#118`・`10-25/§2-6`。

#### 棚卸しの指紋

該当の行なし(種別の語の `A07 V` は C13)。

#### 既知の穴

- W21 に W17 の行が無く、提供者の 7 日の行を写します(#118 のつなぎ)。
- 通学者は W16 のつなぎです。外の雇用主は都市圏化で消えるつなぎです(PENDING §2)。
- 席の偏りの確認が残っています(PENDING §2 の 19)。人口の組み直しは版上げ 5 回目です(同 8)。
- 実データの行数と分布は `data/` を開いていないので確かめていません。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 個体の状態「既定 345,858 体」 | `--agents` の既定は 5,000 | 概要の詳細版(段 1 §11 #2) |

### C21 ビューア

#### 何をしているか

ありません。`src/` と `tools/` にビューアの実装は無く、grep で当たるのは `engine/memory_trace.py` の語だけです。近いものは [tools/c8/dashboard.py](../../../../tools/c8/dashboard.py) で、計器盤を Markdown と JSON に書きます。

#### 状態

無い(宣言なし)。着手は止まる地点の 1 つです。

#### ファイル

なし。文書は [ビューアの設計ラウンド 草案](../../../design/v2-viewer-design-round-draft.md) と答申 [R-74](../../../research/v2-r74-viewer-rebuild-survey.md) です。

#### 元の決定

`10-13b/S7`(ビューアの着手)・`10-25/§3-4`(書き出し口)・`10-12/§4-3`・`10-03/§6`(計器盤を最初の画面に)。

#### 棚卸しの指紋

該当の行なし。

#### 既知の穴

- 書き出し口とビューアは PENDING §2 の 15 に実装待ちです。答申 R-H(10-25 の側)は未発注です(PENDING §3)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 忠実度の計器盤をビューアの最初の画面にする | ビューアが無い(計器盤は Markdown と JSON の 1 枚) | CLAUDE.md §4(GPU が常時使えるようになってからの条項) |

### C22 道具の台帳

#### 何をしているか

世界にある道具(`DEFAULT_TOOLS` の 9 行=看板・掲示・電話・連絡先・グループ・乗換案内・地図・時計・天気予報)を 1 行ずつ載せる台帳と、グループの一覧・店の番号の表です。組み立てで毎回作りますが、既定のランでは誰も結果に使いません。

#### 状態

| 部分 | 状態 | 切替口と既定 |
|---|---|---|
| 台帳と一式(`build_fixture`) | 器だけ | 切替口なし。読むのは腕 port・1b・c1 |
| 看板を読んだ出来事 | 腕 | `SHIBUYA_TOOL_EVENTS` |
| 店の番号の表(`places.py`) | 器だけ | 空の表 |
| 道具 → 語彙の語(`TOOL_ACTION_WORDS`) | 器だけ | 空の表 |
| 道具の使用 | 腕 | `--contact c1`(グループ B の連絡) |

#### ファイル

- [src/shibuya/engine/tools/registry.py](../../../../src/shibuya/engine/tools/registry.py) 道具の台帳
- [src/shibuya/engine/tools/record.py](../../../../src/shibuya/engine/tools/record.py) 記録の欄と一式
- [src/shibuya/engine/tools/groups.py](../../../../src/shibuya/engine/tools/groups.py)・[src/shibuya/engine/tools/contacts.py](../../../../src/shibuya/engine/tools/contacts.py)・[src/shibuya/engine/tools/places.py](../../../../src/shibuya/engine/tools/places.py) 一覧と印

#### 元の決定

`10-12/CT0`・`10-12/CT5`・`10-12/CT9`・`10-12/CT10`・`#92`(1-7)。

#### 棚卸しの指紋

該当の行なし。

#### 既知の穴

- 持ち物の台帳がありません(`Percept.belongings` は空で、要るもののある道具は満たされない扱い=`decision/layer.py`)。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 最初の中身は看板から地図までの 7 行 | 9 行(時計と天気予報は 6-2 の段で足した行) | `engine/tools/registry.py` の docstring |

### C23 つなぎの台帳と「無い」の宣言

#### 何をしているか

expedient のつなぎを 1 行ずつ載せ、外す段を書く台帳です。正は [bridging-ledger.json](../../../design/bridging-ledger.json) で、読み出すと active 763 行・removed 31 行です。コードの宣言(6 形)と台帳の行を AST で 1 対 1 に突き合わせます。件数は manifest に載ります。[absent.py](../../../../src/shibuya/world/processes/absent.py) は「無い」の宣言を 26 行持ちます(主体が居ない 8・言い換え 2・口が無い 13・率を外した 2・補足 1)。どちらも読むだけで、挙動を変えません。

#### 状態

既定です(組み立ての頭で 1 回読む。無い写しは警告して null=`build.py`)。一覧を出す計器 `tools/instruments/absent_declarations.py` は腕(ランの外)です。

#### ファイル

- [src/shibuya/engine/bridging/ledger.py](../../../../src/shibuya/engine/bridging/ledger.py) 読み口と件数
- [src/shibuya/engine/bridging/scan.py](../../../../src/shibuya/engine/bridging/scan.py) コードの宣言を数える(src に呼び手なし・試験が使う)
- [src/shibuya/world/processes/absent.py](../../../../src/shibuya/world/processes/absent.py)・[src/shibuya/world/processes/inputs.py](../../../../src/shibuya/world/processes/inputs.py) 宣言と入力の宣言
- [tools/instruments/absent_declarations.py](../../../../tools/instruments/absent_declarations.py) 一覧の出力

#### 元の決定

`10-12/CA8`・`10-13b/§3`・`10-13b/§4-2`・`11-01/§2`・`11-01p`・`#91`(1-4)・`#133`。

#### 棚卸しの指紋

該当の行なし。

#### 既知の穴

- 件数は宣言の行の数で、一意のつなぎの数ではありません(`bridging/ledger.py` の docstring)。
- 11-05/9-3d と 9-5 の宣言はまだ absent.py にありません(段 1 §11 #15)。
- 「無い」の過程の中身はグループ A の世界過程の担当です。

#### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| ごみ収集ほか 5 件はエンジンの規則が動いたまま(`engine_stopped=False`) | `engine_stopped=True`・既定 stopped(#136 で止めた) | PENDING §1-1 の「まだ動く『無い』の過程」の行 |
| 既定は起床のたびに全部 L2 | 段の既定は L1 | `absent.deliberate`(段 1 §11 #14) |

## 3. 読んでいないファイル

- 全文を読んだもの: `cli.py`・`engine/systems/decide.py`・`engine/systems/conductor.py`・`engine/rights/initial.py`・`engine/rights/record.py`・`engine/decision/ports.py`・`world/processes/absent.py`。
- 一部だけ読んだもの: `engine/run.py`(冒頭・`check_replay_tape`・CLI の共通の引数)・`engine/systems/build.py`(4 区間)・`engine/systems/judge.py`・`engine/systems/state_io.py`・`engine/systems/llm_io.py`・`engine/systems/run_end.py`・`engine/systems/perceive.py`・`engine/arbiter.py`(割り当ての本体)・`engine/decision/layer.py`・`engine/decision/port.py`・`engine/decision/sources.py`・`engine/experiment/branch.py`・`engine/processes/opening.py`・`engine/processes/salient.py`・`engine/economy_stage2.py`・`perception/templates.py`・`agents/state.py`。
- docstring と定数だけ読み、本文を読んでいないもの: `economy/` の全ファイル・`engine/experiment/` の残り・`engine/tape.py`・`engine/resume.py`・`engine/state_codec.py`・`engine/state_hashes.py`・`engine/state_ledger.py`・`engine/state_ledger_ast.py`・`engine/events/`・`engine/change_detect.py`・`engine/scheduler.py`・`engine/commit.py`・`engine/resolve.py`・`engine/batching.py`・`engine/llm_bridge.py`・`engine/norm_meter.py`・`engine/manifest_sections.py`・`engine/bridging/`・`engine/tools/`・`perception/` の残り・`llm/`・`core/`・`manifest/`・`agents/population.py`・`world/assets.py`・`world/state.py`・`build/` の各 `run.py`。
- 開いていないもの: `build/` の段の本体・`tests/` の全部・`tools/` の本体(docstring の頭だけ読んだ分を除く)・`tools/c6/` の大半・`tools/fig/`・`tools/quality_probe_v0/`・`tools/realworld_fetch/`・`tools/spatial/`・`tools/hunger/`・`tools/ledger/`・`tools/w17/`・`world/processes/` の残り・`world/navmesh*.py`・`docs/design/` の指示書と答申の原文(発注文と決定の索引を除く)・[技術マップ](../../tech-map-2026-11-03.md) の本文(grep だけ)。
- 発注で開かないと決まっているもの: `data/`(封印の層を含む)。

## 4. 未確認

- ランを回していないので、既定のランで各部品が通ることは、コードの読みと段 1 の記録に基づきます。今の既定で許可のない行動が 0 行という値は `record.py` の docstring のままです。
- 権利台帳の差し替えの世界の行数(店の担当 9,833・住まい 27,491・外の雇用主 29,979)と母集団 345,858 体は、IMPLEMENTED #118 と版上げの履歴の値で、`data/` では確かめていません。
- 実 LLM の道(`--llm fleet`)はコードの読みだけで、5070 の vLLM が今動くかは確かめていません。
- 語彙の判定の結果を次のランが読む口(5 段の 4)は確かめていません。
- `check_growth` の結果を CI の門として使うかは、試験の中身を読んでいないので確かめていません。
- `attention.py` の関数のうち、描画が使うものは `strip_imperatives`・`rank_by_saliency`・`gate_stage1` を確かめました。ほかの関数の試験での使い方は見ていません。
- 棚卸しの行の中身は仕分けの表の記述のままで、今のコードの行番号と照らしていません。C13・C14 の行の割り当ては文書役の読みです。
- 元の決定は docstring・カード・IMPLEMENTED の見出しから辿りました。原文の条項の中身までは読んでいません。カードの決定の ID は機械の読みで、誤って拾った番号を含むことがあります。
- 発注の「10-25 §6-1 の (i) の一覧」とは突き合わせていません。
- カードは作業木 `wt_repoguide` の版を読みました。本体へ取り込む前なので、リンク先は取り込みの後に効きます。
