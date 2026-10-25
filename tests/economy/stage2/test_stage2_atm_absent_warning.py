# -*- coding: utf-8 -*-
"""〔第335・CI の直し〕ATM の取得物(``data/realworld/osm/…``)が無い写しの注記は ``DataAbsentWarning``(UserWarning 系)で、
``RuntimeWarning`` ではない。

根拠: 2-4 V4 で経済の段階 2 が既定 on になり、data の無い CI では ``build_atm_table`` が「取得物が無い写し」の注記を出す。
tests/c6 の予算の試験は ``RuntimeWarning`` を失敗に昇格するので、CI-1 が赤になった(run 38592394723・d35a9b6)。
注記の種類を分けた=結果(final・テープ)は変わらない(警告は出力に入らない)。
"""

from __future__ import annotations

import warnings

import pytest

from shibuya.engine import economy_stage2 as ES2


def _no_world_lookup(monkeypatch):
    # 取得物が無いときは表を作らず戻るので、世界は要らない=セルの引き当てを空に差し替える
    monkeypatch.setattr(ES2, "_cell_lookup", lambda world: ({}, 0))


def test_absent_osm_file_warns_data_absent_not_runtime(tmp_path, monkeypatch):
    """取得物が無い写し: ``DataAbsentWarning`` が 1 回出て、``RuntimeWarning`` を失敗に昇格しても落ちない。"""
    _no_world_lookup(monkeypatch)
    absent = tmp_path / "absent_tags.json"
    assert not absent.exists()
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)  # tests/c6 と同じ昇格
        with pytest.warns(ES2.DataAbsentWarning, match="が無い写し"):
            t = ES2.build_atm_table(None, tags_path=absent, hours_path=tmp_path / "absent_hours.json")
    assert t.cell.size == 0 and t.n_cells == 0 and t.sources == {}


def test_data_absent_warning_is_user_warning_not_runtime():
    assert issubclass(ES2.DataAbsentWarning, UserWarning)
    assert not issubclass(ES2.DataAbsentWarning, RuntimeWarning)
    assert "DataAbsentWarning" in ES2.__all__
