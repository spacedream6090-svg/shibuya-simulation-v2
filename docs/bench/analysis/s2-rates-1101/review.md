# s2-rates-1101 の独立検収(率の形の規則を外す・11-01 段 2 の 3・4)

> 検収役(Opus 5.5)。実装は見ていない。読んだのは作業木の枝 `stage/s2rates-1101`(土台 `c0729a4`)の差分と記録 [README.md](README.md)。
> 発注の正: 指示書 11-01 段 2 の 3・4・回答 11-01 §2・§3・回答 10-13b §0-6・棚卸し 10-31 §1・行き先 11-01 §6-B。
> 対照のランの出力は検収役の作業場所(リポの外)に置いた。`data/` には書いていない。絶対パス・ホスト名・個人名は書かない。

## 0. 判定

**条件つき受入**。

- 外した 8 件は表どおり。残すべきもの(200% の上限・会場の抽選と開催の行・duties の担当の廃棄・出動の過程)も残っている。
- legacy は土台と 1 バイトも変わらない。final・behavior-hash・full-hash・4 つの checkpoint・呼数・テープ 2 本の sha が一致した(§2)。
- off の件数は自己申告どおり。催し・ポイ捨て・売れ残り・宅配・倒れた人・出動がすべて 0 だった。再開の検査は 3 通りとも止まり、off → off の再開は通しのランと同じ final になった。

受入の条件(commit の前):
1. 欠陥 M1(店の廃棄の帯が既定のランで毎回 NG になる)を、直すか宣言する。
2. M2(過程の宣言 `first_batch.py` が既定の挙動と食い違う)を、S2-ledger の段で同じ版上げのうちに閉じると決める。
3. 版上げの性能の記録(§3)と、直前の commit のタグを付ける。これは親の作業。

## 1. 欠陥

### 高

なし。

### 中

**M1 店の廃棄の帯が既定のランで毎回 NG になる**(計器が外した規則の期待値と比べ続けている)
- `runner.py:540-560` の `waste_sink` は `band_ok` を `goods.store_waste_band()`(初期在庫 × SKU の廃棄率=外した #99 の静的な期待 0.911 t/日 ±30%)と店の回収量で比べる。off では店の回収が 0 なので `band_ok=False` になり、ランの要約に「店の帯 (band 0.64-1.18) NG」と出る。月次センサスの `waste_band_ok`(`economy/census.py:440`)も同じ形で、30 日のランでは偽になる。`tools/c7/c7lib.py:819` は要約の OK/NG を読んでいる。
- 帯は「報告だけ」でゲートではない。ただ、既定のランが毎回 NG を出し、その原因が外した規則であることはどこにも宣言されていない。README §3 の表には「廃棄の射影 1.390 → 0.396」はあるが、帯の NG は書かれていない。
- 再現: `SHIBUYA_RATE_RULES` を付けずに `python -m shibuya.cli --llm mock`(5,000 体・1 日)を回す。要約の C4 後半の行が `…店の帯 (band 0.64-1.18) NG(自己整合性の検査=…)` になる。legacy では OK。
- 直し方の案: off では帯を「外した規則の帯=非該当」(`band_ok=None` と理由)にする。または宣言の一覧(段 2 の 6)に「店の廃棄の帯は売れ残りの廃棄が無いので NG=予期した不合格」を足す。

**M2 過程の宣言が既定の挙動と食い違ったまま**(本段の範囲外として申し送り済み・閉じる時期が未定)
- `world/processes/first_batch.py` の `large_event`(`update_rule`=「来街者の増分と占有セルを与える」・`contributes=("D1′","D4′")`)、`delivery_last_mile`(`gate_condition`=W2 の band・`contributes=("W2",)`)、`public_service_dispatch`(W3 の band)、`street_cleaning`(W1 の内訳)は、既定(off)ではどれも動かない。README §6 に変更案の表はある。ただ、本段だけを commit すると、宣言(とその宣言から作る台帳・計器)が既定の挙動と合わない版ができる。
- 規律上、本段は `world/processes/` に触れない。だから実装の欠陥ではなく、版上げの単位の問題として扱う。親が S2-ledger を同じ版上げで入れるか、本段の版の IMPLEMENTED に「宣言の食い違い 4 過程・閉じる段」を書くかを決める必要がある。
- 回答 11-01 段 2 の 3 の「宅配=**過程を外し**」に対し、本段は過程を組んだまま予定を 0 にした(`active` が偽)。外したと言えるかの読みも同じところで決めてほしい(問い 2)。

**M3 版上げの性能の記録が足りない**(10-13b §0-7)
- README §3 の性能は、3 本を同時に回した壁時計だけ。刻みあたりの時間と最大メモリが無い。検収役が単独で測った値は §3 に置いた(退化は無い)。版上げの記録には体数・日数・seed・機械と一緒に載せる。

### 低

- **L1 Calvo の AST の試験が別名の import を見ない**。`test_calvo_is_not_wired_into_the_engine` が捕まえるのは `pricing.X` の属性と `from …pricing import X` だけで、`import shibuya.economy.pricing as P; P.calvo_draw(...)` や完全修飾の呼び出しは通ってしまう。検収役の grep では、いま `pricing` を import しているのは `economy/goods.py:60` だけで、使っているのは `K_VOLUME`・`K_AVERAGE`・`K_PREMIUM` だけだった(自己申告どおり・結線 0)。直すなら、`pricing` を import するモジュールの集合を `{economy/goods.py}` に固定する試験にする。
- **L2 ランの manifest の試験(off)が弱い**。`test_run_manifest_has_the_rate_rules_section_off` は 40 体 × 30 刻みで回すので、18:00 の催し・05:00 の廃棄・宅配の時間帯のどれも窓に入らない。legacy でも counts は 0 になる(倒れる率を除く)。off で counts が 0 になることの実効の確かめは 5,000 体のラン(§2-2)だけ。過程ごとの単体の試験(正と負の対照)はあるので、低とした。
- **L3 倒れる率の試験の口が印と食い違う**。`salient_rate_per_10k` を直に渡すと、off でも倒れる人が出る。それでも `removed.rate_rule_collapse_removed` は 1 のまま(腕だけで決まる印)。README と `removed_flags` の docstring には書いてあり、`counts` に実効の率が出る。印を「腕 off かつ実効の率 0」で決める形のほうが計器として正直になる。口を次の版上げで消す(`DOC-s2rates-collapse-test-knob`)なら、このままでよい。
- **L4 切替口が 1 つで 8 件をまとめている**。10-13b §0-6 の「旧値の再現のためだけの道」としては 1 つで足りる。ただ、規則ごとの寄与は分けられない。呼数の差 −1,110 の内訳(催しか倒れる事象か)が空欄なのはこのため。規則ごとの寄与を測るのは 35 万体のとき(回答 11-01 §12)になるので、その時点で腕を分けるかを決めればよい。
- **L5 試験 3 本が旧道に固定された**(`test_du_runs::test_discard_is_a_closing_task_and_the_morning_bridge_skips_it`・`test_cp2_event_links::test_run_rows_and_events_are_one_to_one`・`test_resume_10d::test_daily_tables_are_relaid_from_the_calendar_day`)。次の版上げで legacy を消すと、この 3 本は書き直しになる。特に cp2 は「off の 200 体では棚が補充点を割らず、補充の行が 0」が理由なので、off で補充の行を作る合成の場面が要る。次の版上げの作業の一覧に載せておくとよい。
- **L6 新しい識別子に `tick` が 1 つある**。`civic.LargeEventProcess._log_held(self, tick)` の引数。隣の `_arrive(self, tick)` に合わせた形で、src の新しい名はほかに無い(`rate_rules.py` は 0)。記録の道具 `compare_s2rates.py` にも局所の名 `tick` が 1 つある。規則を「新しく定義する名」に当てるなら、この 2 か所は直す。既存の API の名を参照するだけなら当たらない。
- **L7 `PlanExecutor` の引数 `kind`・`agent_id` が使われなくなった**(「呼び手の形のために残す」と注にある)。次の版上げで消す行に入れておくとよい。

## 2. 検収役の対照

### 2-1 legacy の 1 バイト不変(a)と負の対照(d)

5,000 体 × 1 日・mock・seed 1・CLI の既定(`--llm mock` とテープだけ)。「土台」は `c0729a4` の src を `git archive` で取り出したもの、「legacy」と「off」は作業木の src。3 本は同時に回した。

| 量 | 土台 | legacy | off |
|---|---|---|---|
| final | `7bfe215641b792ac` | `7bfe215641b792ac` | `73aa01d9afb206d0` |
| behavior-hash | `7bfe215641b792ac` | 同じ | `73aa01d9afb206d0` |
| full-hash | `5de598882f4b7977` | 同じ | `704112949e6816be` |
| checkpoint 4 点の final | — | 4 点とも土台と一致 | — |
| 呼数 | 62,176 | 62,176 | 61,066 |
| テープ `blocks.parquet`・`calls.parquet` の sha256 | — | 土台と一致 | 2 本とも違う |
| テープ `run_meta.json` | — | 違うのは環境の欄だけ(`git_commit`・`git_diff_sha256`・`git_dirty`・`env_id`=土台は git の外で回したため) | — |
| run_kind | reproduction | arm | reproduction |
| manifest の `attendance_rate` | ある | 無い | 無い |
| 催しの人の注入/退出 | 200 / 200 | 200 / 200 | 0 / 0 |
| 宅配の予定/配達 | 9,292 / 7,967 | 同じ | 0 / 0 |
| 倒れた人/出動/顕著行為の事象/気づき | 5 / 5 / 10 / 780 | 同じ | 0 / 0 / 0 / 0 |
| 街路ごみ 生じた/掃いた[g] | —/81,911 | 141,658 / 81,911 | 0 / 0 |
| 売れ残りのビンの行/収集[g] | 1,544 / 910,750 | 同じ | 0 / 0 |
| 当日の廃棄 sink[g] | 1,308,400 | 同じ | 395,850 |
| sink の内訳[t](店/世帯の消費/街路) | 0.911 / 0.398 / 0.082 | 同じ | 0 / 0.39585 / 0 |
| 乗車の申込/乗り残し/確率で断られた | 4,202 / 0 / — | 4,202 / 0 / 0 | 4,051 / 0 / 0 |
| ActualLog の行 | 27,886 | 27,886 | 25,276 |
| 店の廃棄の帯 | OK | OK | **NG**(M1) |

off の当日の sink 395,850 g は全部が世帯の消費(#41・19 時に持ち物のある全員が 1 個)だった。duties は既定ではないので、担当の体が捨てる分は 0。自己申告の「duties の担当の分は残る」は腕 duties のランについての話で、既定のランの sink には入っていない。

### 2-2 off の計器(b)

off のランの manifest の `rate_rules`: `mode=off`、`removed` は 9 件とも 1、`counts` は `attendance_absent`・`event_injection_arrived`・`arrival_spread_moved`・`board_accept_refused`・`litter_generated_g`・`leftover_waste_bin_rows`・`parcels_delivered`・`collapse_events`・`collapse_rate_per_10k`・`calvo_draws` が全部 0。legacy では `removed` の 1 は attendance と calvo だけで、counts は 200・141,658.3 g・1,544・7,967・5・3 が戻る。過程の counters の印(`rate_rule_*_removed`)も off で 1・legacy で 0。

### 2-3 再開の検査(c)

500 体 × 2 日で、off と legacy の状態のファイルを日の締め(T=1440)に書いた。見出しの `rate_rules` は off だけにあり(`{"mode": "off"}`)、legacy には無い。

| 状態のファイル | 再開の腕 | 結果 |
|---|---|---|
| off | `SHIBUYA_RATE_RULES=legacy` | 止まる(rc 1・「再開の率の規則の腕が親と違う(親 off・今 legacy)」) |
| off | `--rate-rules legacy` | 止まる(同じ文) |
| legacy | 既定(off) | 止まる(親 legacy・今 off) |
| off | 既定(off) | 通る。final `2b3072f4aba59da6` は通しの 2 日のランと一致 |

### 2-4 識別子(e)

変えた .py 43 本(新規 3 本を含む)について、土台との差で新しく出た名(関数・クラス・引数・名前・属性・キーワード・import の別名)を AST で集めた。src で `open`/`tick` を含む新しい名は 0 件だった。ただし `_log_held` の引数 `tick` は、同じファイルに前から同じ名があるので差には出ない(L6)。試験と道具に出たのは、既存の API の名の参照(`dep_tick`・`arrival_tick`・`LITTER_G_PER_PERSON_TICK` など)と、道具の局所の名 `tick` だけ。

### 2-5 設定の節の指紋(f)

`MS.config_paths()` を土台と作業木で出して比べた。sha256 は土台が `94d2cc0c…7e481ffa`、作業木が `94e8ae4c…3f52756f4` で、試験の値と一致した。一覧の差は `attendance_rate` が 1 行消え、`rate_rules.mode`・`rate_rules.removed`・`rate_rules.rules`・`rate_rules.schema` の 4 行が増えただけ(申告どおり)。`manifest_keys_frozen.json` の差も、`attendance_rate` を消して末尾に `rate_rules` を足しただけ。

### 2-6 つなぎの台帳の道具

`add_bridges_s2rates.py` を台帳の写しに 2 回当てた。1 回目は「閉じた 1・注 13・足した 3」で 676 行になり、2 回目は変更 0 で md5 も同じだった(冪等)。作業木全体の写しにこの道具を当てた木で、`tests/engine/bridging` と新しい試験を回すと全部通った。作業木の台帳そのものは土台から変わっていない。

## 3. 試験

| 範囲 | 結果 |
|---|---|
| `tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/bridging`・`tests/engine/rules`・`tests/economy/cp2`・`tests/tools`(`-n 8`) | 408 本を集めて 408 本 passed(新しい試験は 20 本) |
| golden 3 本(`test_state_ledger_10b::test_t7_hash_cost_within_the_declared_cap[v3_default]`・`test_presence_executor::test_v3_default_reproduces_the_recorded_checkpoint`・`test_nav1_world::test_nav1_golden_w6_v3_default_on_the_activated_world[None]`) | `SHIBUYA_RATE_RULES=legacy` では 3 本とも PASSED。環境変数なしでは 3 本とも FAILED |
| 差分で触った試験のファイル全部と `tests/engine/processes`・`tests/engine/calendar`・`tests/engine/time`(既定の腕) | 594 本を集めて 590 本 passed・4 本 failed。落ちたのは `test_presence_executor` の golden 4 本(null arm・v3 既定・l4×1・空腹 v1)だけで、実装役の §5-3 の一覧に入っている。カレンダー 1b(`tests/engine/calendar`)は全部通った |

性能(単独で回した 5,000 体 × 1 日・mock・seed 1・Windows 11・x86-64・論理 CPU 20): 土台は 42.5 秒・29.5 ms/刻み・最大の作業集合 503.8 MB・呼数 62,176。off は 41.6 秒・28.9 ms/刻み・502.3 MB・呼数 61,066。legacy は 43.0 秒・29.9 ms/刻み・呼数 62,176(最大メモリは測り損ねた)。刻みあたりは 1 シミュ日 1,440 刻みの壁時計を割った値。退化は無い。

## 4. 自己申告との差

- 申告どおり: 外した 8 件と残したもの・legacy の 1 バイト不変(final と呼数。検収役は full-hash・checkpoint・テープの sha まで確かめた)・off の final と呼数と件数・再開の検査・`CONFIG_PATHS_SHA256` の差・Calvo が結線されていないこと・台帳の道具の冪等。
- 申告に無かったもの: 店の廃棄の帯が既定で NG になる(M1)。off の sink 395,850 g は世帯の消費だけで、duties の担当の分は既定のランでは 0。
- 申告の「E8 と受け入れ確率は 5,000 体では発火しない」は確かめた(off と legacy で `arrival_spread_moved`・`board_accept_refused` が 0)。効き目は合成の試験で見ている(席より多い 60 体を E1 便に乗せる/180% と 195% の受け入れ)。正と負の対照がそろっているので足りる。
- カレンダー 1b: `_absent` は `absent_on(day)` を読む形になった。旧の既定 1.0 でも全員 False だったので、1b の結果は変わらない。1b の試験に final の golden は無い。1b の試験(`tests/engine/calendar`)は既定の腕で全部通った。

## 5. 問い

1. M1 の帯を off で「非該当」にするか、宣言の一覧に「予期した NG」として書くか。
2. 宅配の「過程を外し」(指示書 段 2 の 3)を「組んだまま予定 0」で満たすと読むか。満たさないなら、レジストリから外すのは `world/processes/` に触れるので S2-ledger の段になる。
3. golden 12 本の扱い。実装役の問い 1 と同じ。検収役としては、legacy の 1 バイト不変を確かめたので、golden を off の値に更新して、legacy の値は安定版のタグで再現する形(10-13b §0-6)を推す。
4. 回答 11-01 §3「W3 を検証から外す」と指示書「W3 は錨に残す」の読み(実装役の問い 2)は、台帳の書き方を S2-ledger で決めてほしい。
