"""W21 段 2「世帯と人」の合成の単体(小さな町丁目 3 つ・材料の表は使わない)。

- 町丁目の周辺 → 世帯の数え(整数化・合計・単独世帯=人員 1 人)。
- 世帯 → 人(続き柄の並び・家族の整合=子は親より 15 歳以上若い・世帯主 15 歳以上・世帯主 1 人)。
- 決定性(同じ seed で同じ・seed を変えると変わる)。
- 詰め on/off(on は誤差が減る・off は動かさない・同じ類型と人員の数えは町丁目ごとに保たれる)。
- 外国人の数・建物への配置の落とし先。
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from shibuya.build.pop import w21_households as H
from shibuya.build.pop import w21_tables as T

NT = len(T.FAMILY_TYPES)
TI = {t: i for i, t in enumerate(T.FAMILY_TYPES)}


def _ward() -> T.Ward2025:
    shape = np.ones((2, T.N_AGE))
    hh = np.zeros((NT, T.SIZES))
    hh[TI["3"], 0] = 60
    hh[TI["111"], 1] = 20
    hh[TI["112"], 2] = 10
    hh[TI["112"], 3] = 6
    hh[TI["114"], 1] = 4
    hh[TI["1202"], 2] = 2
    hh[TI["1209"], 1] = 1
    hh[TI["2"], 1] = 2
    head = {}
    for t in T.FAMILY_TYPES:
        h = np.zeros((2, 15, 4))
        h[:, 2:12, :] = 1.0  # 25〜74 歳
        head[t] = h
    members = {}
    for rel in ("03", "04", "05", "06", "07", "08", "09", "10", "11", "12"):
        for ck in ("111", "11", "12", "2", "3"):
            m = np.ones((2, 21, 4))
            if rel == "03":
                m[:, 6:, :] = 0.0  # 子は 0〜29 歳
                m[:, :3, 1:] = 0.0
            members[(rel, ck)] = m
    members[("01", "3")] = np.ones((2, 21, 4))
    ages = np.arange(T.N_AGE)
    couples = np.exp(-0.5 * ((ages[None, :] - (ages[:, None] - 2)) / 3.0) ** 2)
    couples[:15, :] = 0.0
    couples[:, :15] = 0.0
    return T.Ward2025(
        shape=shape, foreign_share=np.full((2, T.N_AGE), 0.05), pop_total=1000.0,
        age16_sex=np.ones((16, 2)), pop15_by_sex=np.ones(2), marital3_sex=np.ones((3, 2)), hh_type_size=hh,
        hh_total=float(hh.sum()), gh_persons=0.0, head=head, members=members, couples=couples,
        inst_sex_age=np.ones((2, T.N_AGE)), unknown_age16=np.ones((2, 16)) / 16, unknown_marital3=np.ones((2, 3)) / 3,
        unknown_group=np.ones(6) / 6, pop2020=1000.0, foreign_total=50.0,
    )


def _targets() -> T.Targets:
    C = 3
    size = np.array([[30, 12, 6, 3, 0, 0, 0], [20, 10, 6, 4, 0, 0, 0], [10, 8, 8, 2, 0, 0, 0]], dtype=float)
    grp = np.array([[30, 8, 7, 3, 2, 1], [20, 7, 8, 2, 2, 1], [10, 6, 9, 2, 1, 0]], dtype=float)
    grp = grp * (size.sum(axis=1) / grp.sum(axis=1))[:, None]
    age = np.ones((C, 16, 2))
    age[:, 5:9, :] = 4.0
    persons = np.array([80.0, 75.0, 70.0])
    age = age / age.sum(axis=(1, 2), keepdims=True) * persons[:, None, None]
    mar = np.ones((C, 3, 2)) * (persons * 0.8 / 6)[:, None, None]
    return T.Targets(
        stage_idx=np.array([0, 1, 2]), coverage=np.ones(C), persons=persons, age16_sex=age, marital3_sex=mar,
        hh_size=size, hh_group=grp, institution=np.array([1.0, 0.0, 2.0]), foreign=np.array([5.0, 2.0, 0.0]),
        tenure=np.ones((C, 6)), building=np.ones((C, 8)), ratios={}, ipf_residual={},
    )


KEYS = [13113001001, 13113001002, 13113001003]


def _draw(seed=1, target=True):
    ward, tg = _ward(), _targets()
    ints, real, info = H.household_cells(tg, ward)
    hd = H.make_households(ints, np.array([1, 0, 2]), KEYS)
    hd = H.compose_members(hd)
    hd = H.draw_members(hd, ward, seed, tg.age16_sex if target else None)
    return ward, tg, ints, hd


def test_household_cells_hit_the_chome_margins_and_are_integers():
    ward, tg = _ward(), _targets()
    ints, real, info = H.household_cells(tg, ward)
    assert ints.dtype.kind == "i" and (ints >= 0).all()
    assert int(ints.sum()) == int(round(tg.hh_size.sum()))
    assert info["ipf_max_residual"] < 1e-2  # 合成の周辺は境界の解(構造のゼロ)で収束が遅い=実データは 1e-9 台(記録)
    for c in range(3):
        # 単独世帯=人員 1 人(家族類型の表を正)
        assert ints[c, TI["3"], 0] == ints[c, :, 0].sum()
        assert abs(ints[c, TI["3"]].sum() - tg.hh_group[c, 0]) <= 1.0
        # 世帯人員の周辺(単独の差し替えの後)は 1 世帯以内
        cols = tg.hh_size[c].copy()
        assert np.abs(ints[c].sum(axis=0)[1:] - cols[1:] * (real[c].sum(axis=0)[1:].sum() / cols[1:].sum())).max() <= 1.0
    # 構造のゼロ(単独は人員 1 人だけ・夫婦のみは 2 人だけ)
    assert ints[:, TI["3"], 1:].sum() == 0 and ints[:, TI["111"], [0, 2, 3, 4, 5, 6]].sum() == 0


def test_composition_and_family_consistency():
    ward, tg, ints, hd = _draw()
    H_ = hd.n_households
    assert hd.m_hh.size == int(hd.hh_size.sum())
    heads = np.bincount(hd.m_hh[hd.m_slot == H.HEAD], minlength=H_)
    assert (heads == 1).all()
    spouses = np.bincount(hd.m_hh[hd.m_slot == H.SPOUSE], minlength=H_)
    assert spouses.max() <= 1
    gen = hd.hh_type[hd.m_hh] >= 0
    assert (hd.m_age[(hd.m_slot == H.HEAD) & gen] >= 15).all()
    head_age = np.full(H_, -1)
    head_age[hd.m_hh[hd.m_slot == H.HEAD]] = hd.m_age[hd.m_slot == H.HEAD]
    sp_age = np.full(H_, -1)
    sp_age[hd.m_hh[hd.m_slot == H.SPOUSE]] = hd.m_age[hd.m_slot == H.SPOUSE]
    ch = hd.m_slot == H.CHILD
    young = np.where(sp_age[hd.m_hh[ch]] >= 0, np.minimum(head_age[hd.m_hh[ch]], sp_age[hd.m_hh[ch]]),
                     head_age[hd.m_hh[ch]])
    assert (young - hd.m_age[ch] >= H.CHILD_GAP_MIN).all()
    par = hd.m_slot == H.PARENT
    assert (hd.m_age[par] >= head_age[hd.m_hh[par]] + H.PARENT_GAP[0]).all()
    # 夫婦は異性・配偶者は有配偶
    sp = hd.m_slot == H.SPOUSE
    head_sex = np.full(H_, -1)
    head_sex[hd.m_hh[hd.m_slot == H.HEAD]] = hd.m_sex[hd.m_slot == H.HEAD]
    assert (hd.m_sex[sp] != head_sex[hd.m_hh[sp]]).all() and (hd.m_marital[sp] == 1).all()
    # 女親と子の世帯主は女
    t114 = hd.hh_type[hd.m_hh] == TI["114"]
    assert (hd.m_sex[t114 & (hd.m_slot == H.HEAD)] == 1).all()
    # 15 歳未満の配偶関係は空欄
    assert (hd.m_marital[hd.m_age < 15] == -1).all() and (hd.m_marital[hd.m_age >= 15] >= 0).all()
    assert hd.fallbacks["composition_truncated"] == 0


def test_draws_are_deterministic_and_seed_sensitive():
    _, _, _, a = _draw(seed=11)
    _, _, _, b = _draw(seed=11)
    _, _, _, c = _draw(seed=12)
    for f in ("m_sex", "m_age", "m_marital", "m_rel"):
        assert np.array_equal(getattr(a, f), getattr(b, f)), f
    assert not (np.array_equal(a.m_age, c.m_age) and np.array_equal(a.m_sex, c.m_sex))


def test_singles_follow_the_chome_residual_targets():
    """単独世帯の世帯主は町丁目の残りの目標で引く=町丁目の年齢 × 男女の誤差が、区の分布だけで引くより小さい。"""
    _, tg, _, with_t = _draw(seed=3, target=True)
    _, _, _, without = _draw(seed=3, target=False)
    tv = H.anneal_targets(tg)

    def err(hd):
        V = H.anneal_vectors(hd)
        S_ = np.zeros_like(tv)
        np.add.at(S_, hd.hh_chome, V)
        return float(np.abs(S_ - tv)[:, :32].sum())

    assert err(with_t) < err(without)


def test_anneal_on_reduces_error_off_keeps_and_counts_are_kept():
    _, tg, ints, hd = _draw(seed=5, target=False)
    tv = H.anneal_targets(tg)
    off = dataclasses.replace(hd, hh_chome=hd.hh_chome.copy())
    i_off = H.anneal(off, tv, H.AnnealParams(enabled=False), 5)
    assert i_off["error_after"] == i_off["error_before"] and np.array_equal(off.hh_chome, hd.hh_chome)
    on = dataclasses.replace(hd, hh_chome=hd.hh_chome.copy())
    i_on = H.anneal(on, tv, H.AnnealParams(n_iter=20_000), 5)
    assert i_on["error_after"] < i_on["error_before"] and i_on["accepted"] > 0
    # 同じ家族類型 × 人員の世帯の数は町丁目ごとに保たれる(入れ替えだけ)
    def cnt(ch):
        m = hd.hh_type >= 0
        out = np.zeros((3, NT, 8), dtype=int)
        np.add.at(out, (ch[m], hd.hh_type[m], hd.hh_size[m]), 1)
        return out
    assert np.array_equal(cnt(on.hh_chome), cnt(hd.hh_chome))
    # 決定性
    again = dataclasses.replace(hd, hh_chome=hd.hh_chome.copy())
    H.anneal(again, tv, H.AnnealParams(n_iter=20_000), 5)
    assert np.array_equal(again.hh_chome, on.hh_chome)
    # 施設等の人は動かない
    inst = hd.hh_type < 0
    assert np.array_equal(on.hh_chome[inst], hd.hh_chome[inst])


def test_foreign_count_per_chome_is_hit_without_overshoot():
    ward, tg, _, hd = _draw(seed=2)
    f = H.choose_foreign(hd, tg.foreign, ward, 2)
    per = np.bincount(hd.hh_chome[hd.m_hh[f]], minlength=3)
    assert (per <= np.round(tg.foreign)).all() and per.sum() >= tg.foreign.sum() - 2
    # 世帯ごと(世帯員はそろって外国人か否か)
    hh_f = np.zeros(hd.n_households)
    np.add.at(hh_f, hd.m_hh, f)
    assert set(np.unique(hh_f / hd.hh_size).tolist()) <= {0.0, 1.0}


def test_assign_categories_counts_by_largest_remainder():
    ch = np.array([0, 0, 0, 0, 1, 1])
    out = H.assign_categories(ch, np.array([[3.0, 1.0], [1.0, 1.0]]), np.linspace(0, 1, 6), np.ones(6, bool))
    assert np.bincount(out[:4], minlength=2).tolist() == [3, 1]
    assert np.bincount(out[4:], minlength=2).tolist() == [1, 1]


def test_place_households_by_level_class_with_fallbacks():
    # 町丁目 0: 2 階の住居(床 100)と 12 階の住居(床 900)・町丁目 1: 建物なし(被覆セルへ)
    b_chome = np.array([0, 0])
    b_cell = np.array([5, 6])
    b_res = np.array([True, True])
    b_floor = np.array([100.0, 900.0])
    b_lv = np.array([2, 12])
    cover = [(np.array([5, 6]), np.array([1, 1])), (np.array([9]), np.array([4]))]
    names = list(H.LEVEL_CLASS)
    hh_ch = np.array([0, 0, 0, 1])
    bt = np.array([names.index("detached"), names.index("apartment_11plus"), names.index("apartment_3_5"),
                   names.index("detached")])
    b, c, st = H.place_households(hh_ch, bt, np.array([0, 1]), b_chome, b_cell, b_res, b_floor, b_lv, cover,
                                  np.arange(4) / 4)
    assert b[:2].tolist() == [0, 1] and c[:2].tolist() == [5, 6]
    assert st["class_fallback"] == 1 and st["by_covered_area"] == 1 and b[3] == -1 and c[3] == 9


@pytest.mark.parametrize("t", T.FAMILY_TYPES)
def test_composition_table_covers_every_type_and_size(t):
    fixed, fill = H.COMPOSITION[t]
    if t == "3":
        assert fixed == () and fill is None
    else:
        assert fill is not None
    s = H._SLOTS[T.FAMILY_TYPES.index(t)]
    for size in range(1, H.MAX_SIZE + 1):
        assert s[size, 0] == H.HEAD and (s[size, :size] >= 0).all() and (s[size, size:] == -1).all()


def test_feasible_other_relations_keep_every_window_non_empty():
    """〔検収 L2〕窓が空になる続き柄は引かない: 孫と祖父母は世帯主と 30 歳(親子の最小の差 × 2)以上・子の配偶者は世帯主 30 歳以上。"""
    assert H.GRANDCHILD_GAP_MIN == H.GRANDPARENT_GAP_MIN == 2 * H.CHILD_GAP_MIN == 30
    heads = np.arange(15, T.MAX_AGE + 1)
    ok = H.feasible_other(heads)
    codes = list(H.OTHER_REL_CODES)
    assert (ok[:, codes.index("07")] == (heads >= 30)).all() and (ok[:, codes.index("04")] == (heads >= 30)).all()
    assert (ok[:, codes.index("08")] == (heads + 30 <= T.MAX_AGE)).all()
    assert ok[:, codes.index("09")].all() and ok[:, codes.index("10")].all()
    for ci, code in enumerate(codes):
        h = heads[ok[:, ci]]
        slot = np.full(h.size, H.OTHER_REL)
        lo, hi = H.windows(slot, np.full(h.size, code, dtype=object), h, np.full(h.size, -1), np.full(h.size, -1),
                           np.full(h.size, -1))
        assert (lo <= hi).all(), code
    # 子の窓: 母との差の上限で下の端が上の端を越えても、子は若い方の親より 15 歳以上若い
    lo, hi = H.windows(np.array([H.CHILD]), np.array(["03"], dtype=object), np.array([20]), np.array([72]),
                       np.array([72]), np.array([20]))
    assert lo[0] == 0 and hi[0] == 5


def test_draws_have_no_empty_windows_and_heads_with_parents_stay_under_the_cap():
    ward, tg, ints, hd = _draw(seed=9)
    assert hd.fallbacks["window_empty"] == 0
    par_hh = np.unique(hd.m_hh[hd.m_slot == H.PARENT])
    heads = hd.m_age[(hd.m_slot == H.HEAD) & np.isin(hd.m_hh, par_hh)]
    assert heads.size and heads.max() <= T.MAX_AGE - H.PARENT_GAP[0]
    gc = hd.m_rel == "07"
    head_age = np.full(hd.n_households, -1)
    head_age[hd.m_hh[hd.m_slot == H.HEAD]] = hd.m_age[hd.m_slot == H.HEAD]
    assert (head_age[hd.m_hh[gc]] - hd.m_age[gc] >= 30).all()
