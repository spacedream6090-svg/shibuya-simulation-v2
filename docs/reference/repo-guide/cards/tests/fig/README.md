# tests/fig

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/fig/__init__.py)

tests.fig — 論文用の図(``tools/fig``)の煙検査。

## [test_fig_smoke.py](../../../../../../tests/fig/test_fig_smoke.py)

``tools/fig`` の煙検査。

- 公開の関数とクラス
  - `style`(関数)
  - `test_declutter_keeps_order_and_gap`(関数)
  - `test_fig1_draws`(関数)
  - `test_fig1_draws_without_wake_panel`(関数): a(h) が台帳に無いときは副パネルを落として描ける。
  - `test_fig1_output_bytes_are_reproducible`(関数): 同じ入力を 2 回描いたら PNG も SVG も**同じバイト列**(作り直しの差分をゼロにする)。
  - `test_fig1_yardstick_check_flags_mismatch`(関数): 突き合わせは**差が出たら ok=False** になる(黙って通さない)。
  - `test_fig2_draws`(関数)
  - `test_fig2_event_classes_match_src`(関数): 和名表が ``EventClass`` を**全部**覆っている(src が増えたら落ちる)。
  - `test_fig3_draws`(関数)
  - `test_fig3_entropy_bits_is_pure`(関数)
  - `test_fig4_draws`(関数)
  - `test_fig4_summarize_is_symmetric_and_bounded`(関数)
  - `test_fig5_draws`(関数)
  - `test_fig5_fold_meal_and_entropy_are_pure`(関数)
  - `test_fig6_draws`(関数)
  - `test_fig6_share_pct_is_pure`(関数)
  - `test_fig7_draws`(関数)
  - `test_fig7_summarize_is_consistent`(関数)
  - `test_fig8_draws`(関数)
  - `test_fig8_summarize_is_pure_division`(関数)
  - `test_fig9_draws`(関数)
  - `test_fig9_reuses_fig6_arm_definitions`(関数)
  - `test_rel_never_returns_absolute`(関数): ``rel`` はリポジトリ相対 / 外のものはファイル名だけ(絶対パスを出さない)。
  - `test_tables_build_markdown_and_render`(関数)
  - `test_write_sidecar_is_utf8_lf`(関数)
- import している内部モジュール: `shibuya.core.types`・`tools/fig/_style.py`・`tools/fig/fig_ab6b_signage.py`・`tools/fig/fig_ab6c_uncapped.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/fig/fig_ab8_budget.py`・`tools/fig/fig_calls_by_hour.py`・`tools/fig/fig_d91_ride_chain.py`・`tools/fig/fig_presence_24h.py`・`tools/fig/fig_seed_pair.py`・`tools/fig/tbl_ablation.py`
- 決定の ID: 第 235・第 248
