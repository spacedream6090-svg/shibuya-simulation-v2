"""mind.percept.notice — 割る段で ``perception/renderer.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``world/model/percept_scene.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from shibuya.mind.percept.attention import gate_stage1
from shibuya.foundation.text.salience import strip_imperatives
from shibuya.foundation.time_consts import MINUTES_PER_HOUR


def check_signage_p_see(value: float) -> float:
    """看板の注視確率を検査して返す(0.0〜1.0 の外は ``ValueError``)。

    Example:
        >>> check_signage_p_see(0.3)
        0.3
    """
    p = float(value)
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"signage_p_see は 0.0〜1.0 の確率(いま {value!r})")
    return p


class SignageNotice:
    """看板に気づく側(注視の抽選と看板の文)。"""

    def _signage_body(self, cell: int) -> str | None:
        """看板(a)の**本文**(命令文除去済み・枠の切り詰め前)。

        ablation ⑥(§8 第1陣「広告ゼロ」)は ``signage_enabled=False`` でここを ``None`` に
        する。**固定枠と単一ランキングの両方**がこの 1 本を材料にしているので、腕は 1 箇所で
        効く(固定枠 → ``_signage`` が ``B2.signage_empty``・ランキング → 候補が空列)。
        D-59 (b) の注視ゲートも**同じ 1 本**の手前で切る(``_signage``/``_cell_candidates``)。

        Returns:
            見える表示が**無い**セルは ``None``、在るが命令文除去で本文が消えた場合は ``""``
            (この 2 つは描画が違う=前者は「見える表示はありません」・後者は素性タグだけの行)。
        """
        j = self._signage_poi(cell)
        if j < 0:
            return None
        A = self.assets
        w = self.world
        frozen = A.poi_signage[j] if j < len(A.poi_signage) else ""
        if frozen:
            return strip_imperatives(frozen).kept
        frm = int(w.pois.open_from[j]) // MINUTES_PER_HOUR
        to = int(w.pois.open_to[j]) // MINUTES_PER_HOUR
        return strip_imperatives(f"{A.poi_name[j]}の表示。営業は{frm}時から{to}時。").kept

    def _signage_seen(self, agent_id: int, cell: int, tick: int) -> bool:
        """**看板の注視ゲート**(知覚契約書 §4 段1・D-59 (b) ユーザー決定 2026-09-17)。

        体×看板×tick の**決定論的ベルヌーイ**。乱数は ``attention.gate_stage1``
        (``core.rng.stream`` の Philox4x64・ドメイン ``perception.attention.p_see``・
        カウンタ ``(tick, agent_id, poi_id)``)なので、

        - 同じ ``(seed, tick, agent_id, poi_id)`` は**常に同じ結果**(テープから再現できる)、
        - 体を増やしても既存の体の列は動かない(カウンタベースの性質・運用設計書 §1.4 T4)、
        - tick・体・看板のどれが違えば独立な抽選になる。

        既定(``p_see=1.0``)と**看板の無いセル**では抽選を引かない(描画が変わらないため)。
        帯の出典は §4 段1(中小媒体 ``P_SEE_MEDIUM_RANGE`` 0.14-0.40・大型ビジョン 0.63-0.78)。

        逐次ループ宣言(P4): **1 起床につき 1 回**(``render`` の中の 1 回・個体数ぶんの
        ループは持たない)。既定のランでは 0 回。

        〔第 1 期 1-2〕5 段目 5c の活動の種別の乗数(実効 p_see=min(1, p_see × 乗数))と種別ごとの計数は消した
        (決定 10-12 §1-6)。p_see は 1 つの値だけ(抽選の有無も乱数の列も乗数の表が全部 1.0 だった 1-2 の前と同じ)。
        """
        poi = self._signage_poi(cell)
        p = float(self.signage_p_see)
        if p >= 1.0:
            return True
        if poi < 0:
            return True  # 見える看板が無いセル=ゲートの対象外(描画は同じ)
        self.signage_gate_draws += 1
        if p <= 0.0:
            return False  # random() は [0,1) なので ``< 0.0`` は常に偽=短絡と同値
        ok = bool(
            gate_stage1(
                1,
                p,
                seed=self.seed,
                domain_counters=(int(tick), int(agent_id), int(poi)),
            )[0]
        )
        if ok:
            self.signage_gate_shown += 1
        return ok
