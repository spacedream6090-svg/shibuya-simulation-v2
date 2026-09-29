"""engine.norm_meter — **群・規範の計器**(D-107 (a)・第255 決定・第256 R-42 Q4 親検収)。**読むだけ**。

正典: ``docs/design/v2-minutes-audit-2026-09-23.md`` §I-9(計器を先に・機構は C10/C11 の後)・
``docs/design/v2-decisions-for-user-2026-09-24.md`` D-107 (a)。規範は **Bicchieri の 2 層**で測る:
**経験的期待**(文脈ごとの行動分布のエントロピーと最頻行動の占有率=D-68 と同じ計算)と**規範的期待**
(他者の逸脱への反応の有無)。**いまは逸脱への反応を測る機構が無い=片方だけ=「慣習」と宣言する**。

計器(manifest ``group_norms``・値を記録するだけ=判定しない)
    (a) **同行検出**: 同セル ∧ 同じ移動先(目的地つき移動=``activity`` MOVING かつ ``target_node`` ≥ 0 が同じ)∧
        距離 2 m 内、が**連続 5 分以上**の組(R-36 の同席と同じ粒度)。組の数(5 分に達した回数と異なる組の数)・
        同行中の体・分の割合(照合値 Moussaïd 2010: 歩行者の 55%/70% が集団=第256 親が逐語確認・記録だけ)・
        同行の群の大きさ(組をつないだ連結成分の体数)の分布。A1 会話グループの大きさの分布(記録だけ・holdout)。
    (b) **文脈別行動エントロピー**: 場所の種別(駅/店/街路)× 時間帯(1 時間)ごとの、適用した行為の分布の
        エントロピー[bit]と最頻行為の占有率。
    (c) **役割語/NO_PERMISSION**: 役割語の行為(語彙の役割語)の件数・結果(成立/権限なし/その他)・種別の内訳。
    (d) **伝播到達**: 看板の露出・口コミ・顕著行為の社会伝播(気づき・出動)の**既存の計数の集約**。

**場所の種別(宣言・expedient)**: 店=在店(``poi_ref`` ≥ 0)か列(``queue_poi`` ≥ 0)/駅=駅出口セル(W11)か
ホームのセル/街路=それ以外の在圏(舞台外・乗車中は数えない)。行為は**応答を適用する時点**の場所で数える。

逐次ループ宣言(P4): なし(体・組・呼の配列演算)。組の列挙は (セル, 移動先) の群ごとの対を**配列で**作る。
群の対の総数が ``PAIR_CAP`` を超える tick は同行の計数を**飛ばして数える**(``cowalk_ticks_skipped``=宣言)。
群の連結成分はラベルの伝播(``np.minimum.at`` の反復=群の直径ぶん)。
"""

from __future__ import annotations

import time
from typing import Any, Final, Mapping

import numpy as np

from shibuya.agents.state import Activity, AgentState, ResultCode

__all__ = [
    "PLACE_KINDS",
    "COWALK_METERS",
    "COWALK_MINUTES",
    "PAIR_CAP",
    "MOUSSAID_2010_GROUP_SHARE",
    "GroupNormMeter",
    "entropy_bits",
    "role_code_table",
]

#: 場所の種別(索引の順)。
PLACE_KINDS: Final[tuple[str, ...]] = ("街路", "店", "駅")
#: 同行の距離[m]と連続時間[分](R-36 の同席と同じ粒度=宣言)。
COWALK_METERS: Final[float] = 2.0
COWALK_MINUTES: Final[int] = 5
#: 1 tick の対の候補の上限(超えたら同行の計数を飛ばす=宣言・費用の上限)。
PAIR_CAP: Final[int] = 2_000_000
#: 照合値(記録だけ): 歩行者のうち集団で歩く割合(Moussaïd 2010・集団 A 55%/集団 B 70%・第256 親が逐語確認)。
MOUSSAID_2010_GROUP_SHARE: Final[tuple[float, float]] = (0.55, 0.70)


def entropy_bits(counts: np.ndarray) -> float:
    """度数 → シャノンエントロピー[bit](D-68 の M3b と同じ計算)。度数 0 は 0。"""
    c = np.asarray(counts, dtype=np.float64)
    tot = float(c.sum())
    if tot <= 0:
        return 0.0
    p = c[c > 0] / tot
    return max(0.0, float(-(p * np.log2(p)).sum()))  # 1 種だけのとき -0.0 にしない


class GroupNormMeter:
    """群・規範の計器(読むだけ)。``engine.run`` が tick の骨格の決まった位置で呼ぶ。"""

    def __init__(self, agents: AgentState, world: Any, *, role_codes: Mapping[str, int],
                 code_words: Mapping[int, str], tick_seconds: int = 60, process_assets: Any = None) -> None:
        self.agents = agents
        self.tick_seconds = int(tick_seconds)
        n_cells = int(getattr(world, "n_cells", 0))
        station = np.zeros(max(1, n_cells), dtype=bool)
        # 駅セル=W11 駅出口セル+ホームのセル(世界過程の資産 ``ProcessAssets``。無いラン=駅は 0 セル=街路に入る)
        for src in (process_assets, getattr(world, "assets", None)):
            for name in ("station_exit_cell", "line_platform_cell"):
                arr = getattr(src, name, None) if src is not None else None
                if arr is not None:
                    a = np.asarray(arr, dtype=np.int64)
                    a = a[(a >= 0) & (a < station.size)]
                    station[a] = True
        self.n_station_cells = int(station.sum())
        self._station_cell = station
        self.role_codes = {str(w): int(c) for w, c in role_codes.items()}
        self._role_word_by_code = {c: w for w, c in self.role_codes.items()}
        self._code_words = {int(k): str(v) for k, v in code_words.items()}
        # (b) 場所 × 時 × 行為コード(コードは疎=辞書 → 配列は summary で作る)
        self._ctx: dict[int, np.ndarray] = {}  # code → (3, 24) の度数
        self.n_actions_counted = 0
        self.n_actions_off_stage = 0
        # (c) 役割語: 語 → 結果 → 件数 / 語 → 種別 → 件数
        self._role_rows: tuple[np.ndarray, np.ndarray] | None = None
        self.role_result: dict[str, dict[str, int]] = {}
        self.role_by_kind: dict[str, dict[int, int]] = {}
        self.no_permission_total = 0
        # (a) 同行
        self._pair_keys = np.empty(0, dtype=np.int64)
        self._pair_len = np.empty(0, dtype=np.int64)
        self.cowalk_episodes = 0
        self._cowalk_pairs_seen: list[np.ndarray] = []
        self.cowalk_agent_minutes = 0
        self.moving_agent_minutes = 0
        self.cowalk_ticks_skipped = 0
        self.cowalk_pairs_max_tick = 0
        self.group_size_minutes: dict[int, int] = {}
        self.seconds = 0.0

    # ------------------------------------------------------------------ (b)+(c) 応答の適用
    def _place_kind(self, ids: np.ndarray) -> np.ndarray:
        r = self.agents.registry
        cell = np.asarray(r.cell)[ids].astype(np.int64)
        on = (cell >= 0) & (np.asarray(r.transit_state)[ids] == 0)
        kind = np.full(ids.size, -1, dtype=np.int64)
        store = on & ((np.asarray(r.poi_ref)[ids] >= 0) | (np.asarray(r.queue_poi)[ids] >= 0))
        st = on & ~store & self._station_cell[np.clip(cell, 0, self._station_cell.size - 1)]
        kind[on] = 0
        kind[store] = 1
        kind[st] = 2
        return kind

    def observe_actions(self, tick: int, agent_ids: np.ndarray, codes: np.ndarray) -> None:
        """応答を適用する直前(``resolve.apply`` の前)。場所の種別 × 時 × 行為を数え、役割語の行を控える。"""
        t0 = time.perf_counter()
        ids = np.asarray(agent_ids, dtype=np.int64)
        cc = np.asarray(codes, dtype=np.int64)
        if ids.size:
            kind = self._place_kind(ids)
            hour = (int(tick) * self.tick_seconds // 60 // 60) % 24
            on = kind >= 0
            self.n_actions_off_stage += int((~on).sum())
            self.n_actions_counted += int(on.sum())
            if on.any():
                u, inv = np.unique(cc[on], return_inverse=True)
                for j, code in enumerate(u.tolist()):  # 逐次: 行為コードの種類ぶん(≤ 26)
                    arr = self._ctx.setdefault(int(code), np.zeros((len(PLACE_KINDS), 24), dtype=np.int64))
                    arr[:, hour] += np.bincount(kind[on][inv == j], minlength=len(PLACE_KINDS))
            role = np.isin(cc, np.asarray(list(self.role_codes.values()), dtype=np.int64))
            self._role_rows = (ids[role], cc[role]) if role.any() else None
        else:
            self._role_rows = None
        self.seconds += time.perf_counter() - t0

    def observe_results(self, tick: int) -> None:
        """``resolve.apply`` の後: 控えた役割語の行の結果(``last_result``)を数える。"""
        if self._role_rows is None:
            return
        t0 = time.perf_counter()
        ids, cc = self._role_rows
        r = self.agents.registry
        res = np.asarray(r.last_result)[ids].astype(np.int64)
        fresh = np.asarray(r.last_result_tick)[ids].astype(np.int64) == int(tick)
        kinds = np.asarray(r.field("kind"))[ids].astype(np.int64)
        for code, res_k, fr, kd in zip(cc.tolist(), res.tolist(), fresh.tolist(), kinds.tolist()):
            # 逐次: 役割語の行の数ぶん(1 tick に数件・体数に比例しない)
            word = self._role_word_by_code.get(int(code), f"({code})")
            if not fr:
                label = "結果なし(この tick に書かれない)"
            elif res_k == int(ResultCode.OK):
                label = "成立"
            elif res_k == int(ResultCode.NO_PERMISSION):
                label = "権限なし"
                self.no_permission_total += 1
            else:
                label = ResultCode(res_k).name if res_k in ResultCode._value2member_map_ else f"({res_k})"
            self.role_result.setdefault(word, {})
            self.role_result[word][label] = self.role_result[word].get(label, 0) + 1
            self.role_by_kind.setdefault(word, {})
            self.role_by_kind[word][kd] = self.role_by_kind[word].get(kd, 0) + 1
        self._role_rows = None
        self.seconds += time.perf_counter() - t0

    # ------------------------------------------------------------------ (a) 同行
    def observe_tick(self, tick: int) -> None:
        """tick の終わり(位置が確定した後)。同セル ∧ 同じ移動先 ∧ 2 m 内の組を数えて連続時間を伸ばす。"""
        t0 = time.perf_counter()
        r = self.agents.registry
        n = int(self.agents.n)
        act = np.asarray(r.activity)
        tgt = np.asarray(r.target_node).astype(np.int64)
        cell = np.asarray(r.cell).astype(np.int64)
        mov = (act == int(Activity.MOVING)) & (tgt >= 0) & (cell >= 0) & (np.asarray(r.transit_state) == 0)
        ids = np.flatnonzero(mov)
        self.moving_agent_minutes += int(ids.size)
        new_keys = np.empty(0, dtype=np.int64)
        if ids.size >= 2:
            key = cell[ids] * np.int64(1 << 32) + tgt[ids]
            order = np.argsort(key, kind="stable")
            ids, key = ids[order], key[order]
            starts = np.flatnonzero(np.concatenate(([True], key[1:] != key[:-1])))
            sizes = np.diff(np.append(starts, key.size))
            ends = np.repeat(starts + sizes, sizes)
            cnt = ends - np.arange(key.size) - 1  # 同じ群で自分より後ろの数
            total = int(cnt.sum())
            self.cowalk_pairs_max_tick = max(self.cowalk_pairs_max_tick, total)
            if total > PAIR_CAP:
                self.cowalk_ticks_skipped += 1
                self._pair_keys = np.empty(0, dtype=np.int64)
                self._pair_len = np.empty(0, dtype=np.int64)
                self.seconds += time.perf_counter() - t0
                return
            if total:
                a_pos = np.repeat(np.arange(key.size), cnt)
                first = np.cumsum(cnt) - cnt
                b_pos = a_pos + 1 + (np.arange(total) - np.repeat(first, cnt))
                A, B = ids[a_pos], ids[b_pos]
                xy = np.asarray(r.xy)
                d = xy[A].astype(np.float64) - xy[B].astype(np.float64)
                near = (d * d).sum(axis=1) <= COWALK_METERS * COWALK_METERS
                lo, hi = np.minimum(A[near], B[near]), np.maximum(A[near], B[near])
                new_keys = np.unique(lo * np.int64(n) + hi)
        # 連続時間
        if new_keys.size and self._pair_keys.size:
            pos = np.searchsorted(self._pair_keys, new_keys)
            pos_c = np.minimum(pos, self._pair_keys.size - 1)
            hit = self._pair_keys[pos_c] == new_keys
            length = np.where(hit, self._pair_len[pos_c] + 1, 1)
        else:
            length = np.ones(new_keys.size, dtype=np.int64)
        reached = new_keys[length == COWALK_MINUTES]
        if reached.size:
            self.cowalk_episodes += int(reached.size)
            self._cowalk_pairs_seen.append(reached)
        self._pair_keys, self._pair_len = new_keys, length
        grp = new_keys[length >= COWALK_MINUTES]
        if grp.size:
            a, b = grp // n, grp % n
            members = np.unique(np.concatenate([a, b]))
            self.cowalk_agent_minutes += int(members.size)
            # 連結成分(ラベルの伝播)→ 群の大きさ × 分
            ia, ib = np.searchsorted(members, a), np.searchsorted(members, b)
            lab = np.arange(members.size)
            while True:  # 逐次: 群の直径ぶん(ふつう 1〜2 回)
                m = np.minimum(lab[ia], lab[ib])
                new = lab.copy()
                np.minimum.at(new, ia, m)
                np.minimum.at(new, ib, m)
                new = new[new]
                if np.array_equal(new, lab):
                    break
                lab = new
            _u, sz = np.unique(lab, return_counts=True)
            for s, c in zip(*np.unique(sz, return_counts=True)):  # 逐次: 大きさの種類ぶん
                self.group_size_minutes[int(s)] = self.group_size_minutes.get(int(s), 0) + int(c)
        self.seconds += time.perf_counter() - t0

    # ------------------------------------------------------------------ 要約
    def summary(self, *, conv: Any = None, result: Any = None) -> dict[str, Any]:
        """manifest ``group_norms``(**判定しない**=値と照合値を並べるだけ)。"""
        pairs = (np.unique(np.concatenate(self._cowalk_pairs_seen)) if self._cowalk_pairs_seen
                 else np.empty(0, dtype=np.int64))
        size_hist = dict(sorted(getattr(conv, "size_hist", {}).items())) if conv is not None else {}
        ctx_rows = []
        by_place: dict[str, dict[str, Any]] = {}
        codes = sorted(self._ctx)
        if codes:
            cube = np.stack([self._ctx[c] for c in codes])  # (codes, 3, 24)
            for k, place in enumerate(PLACE_KINDS):
                tot = cube[:, k, :].sum(axis=1)
                if tot.sum():
                    top = int(np.argmax(tot))
                    by_place[place] = {"n": int(tot.sum()), "entropy_bit": round(entropy_bits(tot), 4),
                                       "mode_action": self._code_words.get(codes[top], f"({codes[top]})"),
                                       "mode_share": round(float(tot[top] / tot.sum()), 4)}
                for h in range(24):
                    col = cube[:, k, h]
                    if col.sum() == 0:
                        continue
                    top = int(np.argmax(col))
                    ctx_rows.append({"place": place, "hour": h, "n": int(col.sum()),
                                     "entropy_bit": round(entropy_bits(col), 4),
                                     "mode_action": self._code_words.get(codes[top], f"({codes[top]})"),
                                     "mode_share": round(float(col[top] / col.sum()), 4)})
        prop: dict[str, Any] = {}
        if result is not None:
            fam = dict(getattr(result, "familiarity_summary", {}) or {})
            wom = dict(getattr(result, "wom", {}) or {})
            fc = dict(fam.get("counts", {}) or {})
            prop = {
                # 看板の露出(#56・親しみの層=``--familiarity on`` のランだけ)
                "signage_exposure": {
                    **{k: int(v) for k, v in fc.items() if "exposure" in str(k)},
                    **{k: v for k, v in fam.items() if str(k).startswith("exposures_")},
                },
                # 口コミ(#63・店の記憶=``--store-memory on`` のランだけ)
                "word_of_mouth": {
                    **{k: int(v) for k, v in dict(wom.get("counts", {}) or {}).items()},
                    **{k: wom[k] for k in ("extracted_share", "store_rows_with_wom", "store_events_wom") if k in wom},
                },
                # 顕著行為の社会伝播(気づき・出動=世界過程 salient)
                "salient": {"events": int(getattr(result, "salient_events", 0)),
                            "noticed": int(getattr(result, "noticed", 0)),
                            "dispatches": int(getattr(result, "dispatches", 0))},
            }
        moving = max(1, self.moving_agent_minutes)
        return {
            "declared": {
                "cowalk": f"同セル ∧ 同じ移動先(MOVING かつ target_node ≥ 0)∧ 距離 ≤{COWALK_METERS:g} m が連続 "
                          f"{COWALK_MINUTES} 分以上(R-36 の同席と同じ粒度)",
                "place_kinds": "店=在店か列 / 駅=駅出口セル(W11)かホームのセル / 街路=それ以外の在圏(舞台外・乗車中は数えない)",
                "n_station_cells": int(self.n_station_cells),
                "norm_layers": "Bicchieri の 2 層: 経験的期待(文脈別エントロピー・最頻行為の占有率)は測る/規範的期待"
                               "(逸脱への反応)は機構が無く測れない=**「慣習」と宣言**(規範とは言わない)",
                "reference": {"moussaid_2010_group_share": list(MOUSSAID_2010_GROUP_SHARE)},
                "judgement": "判定しない(値と照合値を並べるだけ・A1 は holdout)",
            },
            "cowalk": {
                "episodes_5min": int(self.cowalk_episodes),
                "distinct_pairs_5min": int(pairs.size),
                "cowalk_agent_minutes": int(self.cowalk_agent_minutes),
                "moving_agent_minutes": int(self.moving_agent_minutes),
                "cowalk_share_of_moving_minutes": round(self.cowalk_agent_minutes / moving, 6),
                "group_size_minutes": dict(sorted(self.group_size_minutes.items())),
                "pairs_candidates_max_per_tick": int(self.cowalk_pairs_max_tick),
                "ticks_skipped_over_pair_cap": int(self.cowalk_ticks_skipped),
            },
            "conversation_group_size_a1": {str(k): int(v) for k, v in size_hist.items()},
            "context_entropy": {"by_place": by_place, "by_place_hour": ctx_rows,
                                "actions_counted": int(self.n_actions_counted),
                                "actions_off_stage": int(self.n_actions_off_stage)},
            "role_words": {"by_word_result": {w: dict(sorted(d.items())) for w, d in sorted(self.role_result.items())},
                           "by_word_kind": {w: {str(k): v for k, v in sorted(d.items())}
                                            for w, d in sorted(self.role_by_kind.items())},
                           "no_permission": int(self.no_permission_total),
                           "role_actions": int(sum(sum(d.values()) for d in self.role_result.values()))},
            "propagation": prop,
        }


def role_code_table(vocab_version: str) -> dict[str, int]:
    """語彙の版 → 役割語 → 行動コード(``llm.contract``)。"""
    from shibuya.llm import contract as C

    if str(vocab_version) == "v3":
        return dict(C.ROLE_ACTION_CODES_V3)
    return dict(C.ROLE_ACTION_CODES)
