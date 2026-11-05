# src/shibuya/engine/duties

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/duties/__init__.py)

engine.duties — 店の仕事を働く人の体へ(第 6 期 6-6 ② 第 1 部=開閉店・補充(品出し)・廃棄・腕 ``--duties arm``・既定 off)。

## [arm.py](../../../../../../../../src/shibuya/engine/duties/arm.py)

engine.duties.arm — 店の仕事の腕(第 6 期 6-6 ② 第 1 部=開閉店・補充・廃棄を担当の体の判断に)。

- 公開の関数とクラス
  - `arm`(関数): いまの腕(``off``=既定・``arm``)。組み立てのときに読む。
  - `config`(関数): 設定の指紋と manifest の設定の子に出す腕の組(腕 off は ``None``=指紋に何も足さない)。
  - `is_on`(関数)
  - `set_arm`(関数): 腕を選ぶ(CLI ``--duties``・試験の切替口)。
- 呼び手: `shibuya.cli`・`shibuya.engine.duties.layer`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/duties/_du.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/duties/test_du_units.py`
- 環境変数: `SHIBUYA_DUTIES`・名前を読めない所 1 か所

## [knowledge.py](../../../../../../../../src/shibuya/engine/duties/knowledge.py)

engine.duties.knowledge — 店の決まり(営業時間)の問い合わせの口(第 6 期 6-6 ② 第 1 部・決定 10-12 §1-4)。

- 公開の関数とクラス
  - `ShopRules`(クラス): 店の決まりの口(休業日の枠=親クラス+営業時間)。担当だけが自分の店の営業時間を引ける。
  - `origin_mark`(関数): 記録の ``origin`` に入れる出どころの印(``store_rules:<出どころ>``)。
  - `rules_line`(関数): 常識の文の 1 行(「店の決まり: 営業 10:00〜22:00。」の形・知らなければ空)。
- import している内部モジュール: `shibuya.core.time_consts`・`shibuya.engine.calendar3.knowledge`・`shibuya.engine.rights.ledger`
- 呼び手: `shibuya.engine.duties.layer`
- 読む試験: `tests/engine/duties/test_du_units.py`
- 決定の ID: 10-12/§1-4

## [layer.py](../../../../../../../../src/shibuya/engine/duties/layer.py)

engine.duties.layer — 店の仕事を働く人の体へ(開閉店・補充(品出し)・廃棄)の持ち主と系 ``duties``(第 6 期 6-6 ② 第 1 部・腕 ``--duties arm``・既定 off)。

- 公開の関数とクラス
  - `DutiesLayer`(クラス): 店の仕事の持ち主(状態台帳の腕の行 ``DU*``)。
  - `audit_causes`(関数): 負の対照の監査: 族 ``仕事`` の出来事の原因が判断の呼び(LlmCall)か。本段の判断の呼び(この層の形の call_id)は源と番号
  - `first_per_store`(関数): 〔検収 M1〕雇用の行(店の順・店の中は台帳の行の順)のうち ``eligible`` の行の、店ごとの最初の行。返り値は
  - `issued_key`(関数)
  - `manifest_fields`(関数): manifest の ``duties``(腕 arm のランだけ・ほかは空=欄を出さない)。
  - `sys_duties`(関数): 系 duties(刻みの中・腕 arm のランだけ立つ)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.rng`・`shibuya.core.time_consts`・`shibuya.engine.calendar3.layer`・`shibuya.engine.decision.port`・`shibuya.engine.duties.arm`・`shibuya.engine.duties.knowledge`・`shibuya.engine.duties.port`・`shibuya.engine.events.log`・`shibuya.engine.events.vocab`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.resolve`・`shibuya.engine.rights.ledger`・`shibuya.world.processes.records`
- 呼び手: `shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.table`
- 読む試験: `tests/engine/duties/test_du_runs.py`・`tests/engine/duties/test_du_units.py`・`tests/engine/duties/test_du_world.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 状態台帳の行
  - 持ち主 `duties`(`DutiesLayer`)
    - `DUG` DutiesLayer が系の間に渡す値(主の判断の役割語の控え・第 6 期 6-6 ② 第 1 部)(挙動 behavior・復元 required・腕 duties) 道筋 `duties._role_asks` 書ける系: decide・duties・llm_receive
    - `DUM` 店の仕事の計器(計数・遅れの分布・前の刻みの店の開閉・雇用の行の店に居た分・日の数・第 6 期 6-6 ② 第 1 部)(挙動 diag・復元 required・腕 duties) 道筋 `duties._days`・`duties._du_hist`・`duties._du_meter`・`duties._du_minutes`・`duties._du_over`・`duties._du_prev` 書ける系: duties・world
    - `DUQ` 発行した店の仕事の判断の呼びの控えと呼び数・役割語の道の call_id(監査の突き合わせ・第 6 期 6-6 ② 第 1 部)(挙動 diag・復元 required・腕 duties) 道筋 `duties._du_issued`・`duties._du_issued_n`・`duties._du_role_ids` 書ける系: duties
    - `DUS` DutiesLayer の閉店の作業の印(雇用の行の体が閉めた店・売れ残りを捨てた店・第 6 期 6-6 ② 第 1 部)(挙動 behavior・復元 required・腕 duties) 道筋 `duties._binned`・`duties._closed_by_me` 書ける系: duties
- 書きの許可
  - 系 `duties`(群 仕事・時 `tick`・立つ条件 `duties`・関数 `sys_duties`)
    - 呼んでよい resolve の口: `discard_to_bin`・`request_open_close`・`restock`
    - 書いてよい SoA の列(閉包): `agents.last_result`・`agents.last_result_tick`・`pois.open_now`・`pois.stock`
    - 書いてよい外の道筋: `A:ledger.*`・`DU*:duties.*`・`E:events.*`・`EM:ledger.*`・`O5[23]:runner.*`・`O5[7-9]:ledger.*`・`O60:ledger.*`・`O61:runner.*`・`O73:runner.*`・`O7[7-9]:ledger.*`・`O8[01]:ledger.*`・`O9[23]:ledger.*`
- 決定の ID: 10-12/§1-5・10-13b/§0-3

## [port.py](../../../../../../../../src/shibuya/engine/duties/port.py)

engine.duties.port — 店の仕事の本人の判断(候補の口 J0 の形)の仮のモデルと候補の語(第 6 期 6-6 ② 第 1 部)。

- 公開の関数とクラス
  - `DutiesPort`(クラス): 店の仕事の判断の仮のモデル(mock・判断モデルの代わり)。乱数の鍵はその刻みのその体の判断の通し番号。
  - `call_id_of`(関数): 判断の呼びの id(テープの形 ``<刻み>:<体>:<−通し番号>``)。
  - `cand`(関数): 候補 1 つ(源は語から・id は省略で語)。語が閉じた表の外なら ``KeyError``。
  - `parse_call_id`(関数): 店の仕事の判断の呼びの id → ``(刻み, 体, 通し番号)``(この形でなければ ``None``)。
  - `purpose_of_serial`(関数)
  - `serial_of`(関数): 判断の通し番号(``SERIAL_BASE``+その刻みのその体の k 回目 × 16+判断の種類)。上限を超えたら ``ValueError``。
- import している内部モジュール: `shibuya.core.rng`・`shibuya.engine.decision.port`・`shibuya.llm.contract`
- 呼び手: `shibuya.engine.duties.layer`
- 読む試験: `tests/engine/duties/_du.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/duties/test_du_units.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 決定の ID: 10-12/§1-5
