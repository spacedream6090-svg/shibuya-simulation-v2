# src/shibuya/engine/space

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/space/__init__.py)

engine.space — 第 5 期 空間の段(段 1: ナビメッシュの上の移動 ``nav1``)。

## [nav1.py](../../../../../../../../src/shibuya/engine/space/nav1.py)

engine.space.nav1 — 第 5 期 空間の段 1: ナビメッシュの上を衝突なしで進む移動(切替口 ``--space {legacy,nav1}``)。

- 公開の関数とクラス
  - `NavMeter`(クラス): 移動の計器(ランの通算・manifest の ``space`` と記録の材料)。
  - `NavSpace`(クラス): 段 1 の移動の道具(1 つのランで 1 つ)。書き込みはしない=新しい値を返し、書くのは ``engine.resolve``。
  - `RoutePool`(クラス): 体ごとの経路の点の並び(点・階・その点までの時間・区間の接続口・通った W1 の節)。状態ではない(作り直せる)。
  - `add_space_args`(関数): CLI の旗 ``--space``・``--slope``・``--turn-weight``。
  - `advance_kernel`(関数): 移動中の体を 1 刻みぶん進める(体ごとに経路の区間を進む・接続口の前で許しが無ければ止まる)。
  - `arms_on`(関数): 坂・曲がる重み・密度の推定の腕が既定と違うか(ランの種類を arm にする=結果が変わる腕・nav1 のランだけ効く)。
  - `cell_contacts`(関数): 同じ階の歩ける升(0.5 m)が辺か角で接する 2 つのセルの印 ``(n_cells, n_cells)`` uint8(対称・対角は 0)。
  - `check_density_mode`(関数)
  - `check_slope_model`(関数)
  - `check_space`(関数)
  - `check_turn_weight_mode`(関数)
  - `density_arm`(関数): 〔段 5-1b〕密度の推定の腕(環境変数 ``SHIBUYA_NAV1_DENSITY``・既定 ``neighborhood``)。組み立てのときに読む(nav1 のときだけ効く)。
  - `is_production_world`(関数): 本番の世界か(``build_manifest.json`` に ``build_hash`` を持つ世界=構築の段で組んだ世界・〔段 1 の検収 問い 4〕)。
  - `load_space`(関数)
  - `manifest_section`(関数): manifest の ``space``(設定=頼んだ値・実際の値・理由・坂の式・曲がる重み・ナビメッシュの大きさ/観測=計器)。
  - `neighborhood_pairs`(関数): 近傍の表 → (行のセル, 足すセル) の組の配列(自分自身を含む)と manifest の数。
  - `set_slope_arm`(関数)
  - `set_turn_arm`(関数)
  - `slope_arm`(関数): 坂の式の腕(``wood``=既定・``tobler``)。組み立てのときに読む(環境変数 ``SHIBUYA_SLOPE``・``--slope``)。
  - `slope_factor_max`(関数): 坂の係数の最大(下りのゆるい坂で平地より速い=受入の試験の速さの上限に掛ける)。
  - `slope_speed_factor`(関数): 勾配(上り正)→ 平地に対する歩く速さの比(Wood 2023 舗装路 / Tobler)。
  - `space_available`(関数): この世界の置き場で nav1 が回せるか(ナビメッシュの資産が全部ある)。
  - `space_env_override`(関数): 頼んだ移動の値: 引数(``run_day(space=…)``・``--space``)があればそれ・無ければ環境変数 ``SHIBUYA_SPACE``・それも無ければ
  - `space_from_args`(関数): CLI の値 → ``run_day(space=…)``。坂と曲がる重みの腕はここで選ぶ(組み立てが読む・指定は環境変数より強い)。
  - `summary_line`(関数)
  - `turn_arm`(関数): 曲がる重みの腕(``fixed``=既定 50 m・``person``=人ごとに 32〜62 m)。環境変数 ``SHIBUYA_TURN_WEIGHT``・``--turn-weight``。
  - `turn_weights`(関数): 体ごとの曲がる重み[m]\(fixed=50 m・person=32〜62 m の一様=母集団の seed と体の番号だけの決定論・ランの乱数列を引かない)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.geometry`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.world.navmesh`・`shibuya.world.navmesh_route`・`shibuya.world.state`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/space/test_nav1_density.py`・`tests/engine/space/test_nav1_units.py`
- CLI の引数
  - `--slope`: 坂の速さの式の腕(SR12 (d)・既定 wood=Wood 2023 舗装路・tobler=Tobler・環境変数 SHIBUYA_SLOPE と同じ)
  - `--space`: 第 5 期 空間の段 1 の移動の切替口。nav1=ナビメッシュの上を衝突なしで進む(既定・位置は (x, y, 階)・合成の世界では legacy で回して manifest の space.effective に書く・本番の世界で資産 nav1_* が無ければ止める・密度の推定は環境変数 SHIBUYA_NAV1_DENSITY=neighborhood(既定)/cell/unscaled)/legacy=前のセルの移動(旧値の再現だけ・次の版上げで消す)。環境変数 SHIBUYA_SPACE より強い
  - `--turn-weight`: 曲がる重みの腕(SR12 (a)・既定 fixed=50 m・person=人ごとに 32〜62 m の一様・環境変数 SHIBUYA_TURN_WEIGHT と同じ)
- 環境変数: `SHIBUYA_NAV1_DENSITY`・`SHIBUYA_SLOPE`・`SHIBUYA_SPACE`・`SHIBUYA_TURN_WEIGHT`
- 決定の ID: 10-03/§8・10-06・10-13b/§0-6・R-61・R-63・R-64
