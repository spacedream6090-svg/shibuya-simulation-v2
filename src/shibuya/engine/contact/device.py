"""engine.contact.device — 道具の状態と通知の刺激の形(第 6 期 6-4 C1・決定 10-12 §4-4 CT0 の共通の決まり 2・3)。

正: CT0「持ち物はエンジンが持つ世界の状態。初めは実データ(母集団の側)、途中は本人の行動と物理(電池など)で動く」「道具の
状態(電池・電波・マナーモード・かばんの中)を持つ」「耳は、イヤホンの音を SNR の周りの音として足します」・CT3「マナーモードや
かばんの中なら弱い刺激」。形は R-78(声の伝わり方)§5-2 の SNR(信号 − 雑音)と段の閾値(Lazarus の「足りる」の境 −3 dB・
既存答申の検知 −10 dB)。

持ち主 :class:`Devices`(状態台帳の腕の行 ``CT1D``=軸 1 behavior・軸 2 required・腕 c1 のランだけ)。体ごとの配列:

- ``_on``(電源)・``_battery``(電池の残り 0〜1・float32)・``_manner``(マナーモード)・``_place``(今の置き場 手/ポケット/かばん)・
  ``_home``(使っていないときの置き場=取り出す前の場所)・``_ear``(イヤホンをしているか)。
- 電波は舞台の全域で届く(配列を持たない=:func:`signal_ok`)。

通知の刺激(:meth:`Devices.stimulus`)=チャネルごとの段の形(係数を掛けない):

- 音(マナーモードでないとき): 耳の位置の着信音 ``RING_DB_1M − PLACE_ATTEN_DB[置き場]`` と、周りの騒音(W10 の騒音の段 →
  ``NOISE_STAGE_DB``=描画の帯の語の値)にイヤホンの音を電力で足した雑音の差=SNR。SNR ≥ ``SNR_CLEAR_DB`` で強い・
  ≥ ``SNR_DETECT_DB`` で弱い・それより下は届かない。
- 振動(マナーモードのとき): 手かポケットなら弱い・かばんは届かない。
- 画面: 視線が画面なら強い(画面の上の通知=見ている)。
- 刺激の段=チャネルの段の最大(0=届かない・1=弱い・2=強い)。

電池(物理): 1 刻みごとに 使い方(通話>画面>待ち受け)の減り方で減り、0 になると電源が切れる(切れた体へのメッセージは網で
預かる・電話は不通)。充電は本人の行動(本段に無い=つなぎの台帳 ``DOC-ct-c1-no-charging``)。
〔第 6 期 6-2 カレンダー 3 の後・つなぎ ``BR-CT1-CHARGE-AT-HOME``〕充電は本人の行動になるまで(判断モデルの段 6-6)エンジン規則で
つなぐ(決定 10-12 §2 の 2「まだ人の行動で作れない変化はエンジン規則でつなぐ=conf 宣言つき」): 体が家に居る刻みは電池が
``CHARGE_PER_HOUR`` で増える(:meth:`Devices.charge`)・電池が 0 でなくなった体は電源が入る(充電中に電源が入る=宣言)。職場では
増えない(本人の行動=判断モデルの後)。家に居る=住まいのセルに居る(範囲の中)か、住まいが範囲の外の体が範囲の外で寝ている刻み
(住まいの場所が無い=宣言)。

**未リサーチ(expedient)**の値(記録 ct_c1/README.md の表とつなぎの台帳 ``DOC-ct-c1-device-*``): 最初の電池 100%・マナーモードの
人の割合 0.5・かばんに入れている人の割合 0.5・イヤホンの人の割合 0.2(どれも実データが無い=最初の世界の状態の仮の値・母集団の
側の乱数で体ごとに引く)・着信音 70 dB(1 m)・置き場の減衰(手 0・ポケット 6・かばん 15 dB)・イヤホンの音 75 dB・電池の減り
(待ち受け 1%/時・画面 12%/時・通話 8%/時)・電波は全域で届く・通知の音はイヤホンに流さない(本体の音=イヤホンは周りの音を
覆う)。

逐次ループ宣言: なし(体の配列の演算)。
"""

from __future__ import annotations

import re
from typing import Any, Final

import numpy as np

from shibuya.core.rng import k19_counter_array, philox_array, unit_float
from shibuya.core.time_consts import SECONDS_PER_HOUR
from shibuya.engine.contact.arm import LEDGER_ARM
from shibuya.perception import templates as _T

__all__ = [
    "PLACE_HAND", "PLACE_POCKET", "PLACE_BAG", "PLACE_WORDS", "LEVEL_NONE", "LEVEL_WEAK", "LEVEL_STRONG",
    "LEVEL_WORDS", "CH_SOUND", "CH_VIBRATION", "CH_SCREEN", "CHANNEL_WORDS", "DEVICE_DOMAIN", "INITIAL_BATTERY",
    "MANNER_SHARE0", "BAG_SHARE0", "EARPHONE_SHARE0", "RING_DB_1M", "PLACE_ATTEN_DB", "EARPHONE_DB", "SNR_CLEAR_DB",
    "SNR_DETECT_DB", "NOISE_STAGE_DB", "DRAIN_PER_HOUR", "CHARGE_PER_HOUR", "USE_STANDBY", "USE_SCREEN", "USE_CALL", "Devices",
    "signal_ok", "power_sum_db", "noise_db_of_stage", "channel_words", "PROVISIONAL_VALUES",
]

PLACE_HAND: Final[int] = 0
PLACE_POCKET: Final[int] = 1
PLACE_BAG: Final[int] = 2
PLACE_WORDS: Final[tuple[str, ...]] = ("手", "ポケット", "かばん")

LEVEL_NONE: Final[int] = 0
LEVEL_WEAK: Final[int] = 1
LEVEL_STRONG: Final[int] = 2
LEVEL_WORDS: Final[tuple[str, ...]] = ("届かない", "弱い", "強い")

#: 刺激のチャネルのビット(音・振動・画面)。
CH_SOUND: Final[int] = 1
CH_VIBRATION: Final[int] = 2
CH_SCREEN: Final[int] = 4
CHANNEL_WORDS: Final[tuple[tuple[int, str], ...]] = ((CH_SOUND, "音"), (CH_VIBRATION, "振動"), (CH_SCREEN, "画面"))

#: 最初の道具の状態の乱数の用途名(母集団の側=``engine.run.POPULATION_RNG_DOMAINS``)。
DEVICE_DOMAIN: Final[str] = "contact.device"
_F_MANNER, _F_BAG, _F_EAR = 1, 2, 3

# ---- 値(未リサーチ=expedient・つなぎの台帳 DOC-ct-c1-device-*) ----
INITIAL_BATTERY: Final[float] = 1.0
MANNER_SHARE0: Final[float] = 0.5
BAG_SHARE0: Final[float] = 0.5
EARPHONE_SHARE0: Final[float] = 0.2
#: 着信音の大きさ[dB・1 m・A 特性]。
RING_DB_1M: Final[float] = 70.0
#: 置き場ごとの減衰[dB](手・ポケット・かばん)。
PLACE_ATTEN_DB: Final[tuple[float, float, float]] = (0.0, 6.0, 15.0)
#: イヤホンの音(耳の位置)[dB]。周りの音に電力で足す(R-78 の SNR の形)。
EARPHONE_DB: Final[float] = 75.0
#: 強い/弱いの境[dB](R-78 §5-2: Lazarus の「足りる」の境 −3 dB・検知 −10 dB=既存答申の自前の設定で錨なし)。
SNR_CLEAR_DB: Final[float] = -3.0
SNR_DETECT_DB: Final[float] = -10.0
#: 騒音の段(W10・``perception.templates.NOISE_STAGE_VOCAB``)→ 代表の dB(描画の帯の語 ``NOISE_BAND_WORDS`` の値)。
NOISE_STAGE_DB: Final[tuple[float, ...]] = tuple(float(re.match(r"\d+", w).group()) for w in _T.NOISE_BAND_WORDS)
#: 電池の減り[1 時間あたりの割合](待ち受け・画面・通話)。
USE_STANDBY, USE_SCREEN, USE_CALL = 0, 1, 2
DRAIN_PER_HOUR: Final[tuple[float, float, float]] = (0.01, 0.12, 0.08)
#: 〔つなぎ BR-CT1-CHARGE-AT-HOME〕家での充電の速さ[1 時間あたりの割合](満充電まで 2 時間相当=仮の値・expedient)。
CHARGE_PER_HOUR: Final[float] = 0.5

#: 本モジュールの仮の値の宣言(記録とつなぎの台帳の行 DOC-ct-c1-device-* と 1 対 1=文を変えたら台帳も直す)。
PROVISIONAL_VALUES: Final[tuple[str, ...]] = (
    "最初の道具の状態: 電池 100%・マナーモード 0.5・かばん 0.5・イヤホン 0.2(実データなし・母集団の側の乱数で体ごと)",
    "着信音 70 dB(1 m)・置き場の減衰 手 0/ポケット 6/かばん 15 dB・イヤホンの音 75 dB(周りの音に電力で足す)",
    "電池の減り 待ち受け 1%/時・画面 12%/時・通話 8%/時(充電は本人の行動=本段に無い)",
    "電波は舞台の全域と外で届く・通知の音はイヤホンに流さない(本体の音)",
)


def signal_ok(cells: Any) -> np.ndarray:
    """電波が届くか(本段は全域で届く=つなぎ ``DOC-ct-c1-device-signal``)。"""
    return np.ones(np.shape(cells), dtype=bool)


def power_sum_db(a: Any, b: Any) -> np.ndarray:
    """2 つの音の電力の和[dB](``10 lg(10^(a/10) + 10^(b/10))``)。"""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return 10.0 * np.log10(np.power(10.0, a / 10.0) + np.power(10.0, b / 10.0))


def noise_db_of_stage(stage: Any) -> np.ndarray:
    """騒音の段 → 代表の dB(段の外は端に寄せる)。"""
    s = np.clip(np.asarray(stage, dtype=np.int64), 0, len(NOISE_STAGE_DB) - 1)
    return np.asarray(NOISE_STAGE_DB, dtype=np.float64)[s]


def channel_words(bits: int) -> tuple[str, ...]:
    """チャネルのビット → 語の組(音・振動・画面の順)。"""
    return tuple(w for b, w in CHANNEL_WORDS if int(bits) & b)


class Devices:
    """体ごとの道具の状態(状態台帳の腕の行 ``CT1D``・持ち主の道筋 ``contact.dev``)。"""

    LEDGER_ARM: Final[str] = LEDGER_ARM

    def __init__(self, n_agents: int, population_seed: int | str) -> None:
        n = int(n_agents)
        self.n = n
        ids = np.arange(n, dtype=np.uint64)
        u = [unit_float(philox_array(population_seed, DEVICE_DOMAIN,
                                     k19_counter_array(ids, np.full(n, f, dtype=np.uint64)), words=1))[:, 0]
             for f in (_F_MANNER, _F_BAG, _F_EAR)]
        self._on = np.ones(n, dtype=bool)
        self._battery = np.full(n, INITIAL_BATTERY, dtype=np.float32)
        self._manner = u[0] < MANNER_SHARE0
        self._home = np.where(u[1] < BAG_SHARE0, PLACE_BAG, PLACE_POCKET).astype(np.int8)
        self._place = self._home.copy()
        self._ear = u[2] < EARPHONE_SHARE0

    # ------------------------------------------------------------------ 読む口
    def on(self, a: Any) -> np.ndarray:
        return self._on[np.asarray(a, dtype=np.int64)]

    def battery(self) -> np.ndarray:
        v = self._battery.view()
        v.flags.writeable = False
        return v

    def place(self, a: int) -> int:
        return int(self._place[int(a)])

    def view_fields(self, a: int) -> dict[str, Any]:
        """1 体の道具の状態(本人が知っている自分の持ち物=CT0 の 2)。"""
        i = int(a)
        return {"battery_pct": int(round(float(self._battery[i]) * 100.0)), "on": bool(self._on[i]),
                "manner": bool(self._manner[i]), "place": PLACE_WORDS[int(self._place[i])],
                "earphones": bool(self._ear[i])}

    # ------------------------------------------------------------------ 刺激(System 1)
    def stimulus(self, a: Any, noise_db: Any, gaze_screen: Any) -> tuple[np.ndarray, np.ndarray]:
        """体の配列 ``a`` に届く通知の刺激 → (段 0/1/2・チャネルのビット)。電源の切れた体は 0。係数は掛けない(段の形)。"""
        a = np.asarray(a, dtype=np.int64)
        manner = self._manner[a]
        place = self._place[a].astype(np.int64)
        ring = RING_DB_1M - np.asarray(PLACE_ATTEN_DB, dtype=np.float64)[place]
        noise = np.asarray(noise_db, dtype=np.float64)
        noise = np.where(self._ear[a], power_sum_db(noise, EARPHONE_DB), noise)
        snr = ring - noise
        sound = np.where(~manner, np.where(snr >= SNR_CLEAR_DB, LEVEL_STRONG,
                                           np.where(snr >= SNR_DETECT_DB, LEVEL_WEAK, LEVEL_NONE)), LEVEL_NONE)
        vib = np.where(manner & (place != PLACE_BAG), LEVEL_WEAK, LEVEL_NONE)
        screen = np.where(np.asarray(gaze_screen, dtype=bool), LEVEL_STRONG, LEVEL_NONE)
        level = np.maximum(np.maximum(sound, vib), screen)
        level = np.where(self._on[a], level, LEVEL_NONE).astype(np.int8)
        bits = ((sound > 0) * CH_SOUND | (vib > 0) * CH_VIBRATION | (screen > 0) * CH_SCREEN).astype(np.int8)
        bits = np.where(self._on[a], bits, 0).astype(np.int8)
        return level, bits

    # ------------------------------------------------------------------ 本人の行動と物理(書く口)
    def take_out(self, a: Any) -> None:
        """取り出す(画面を見る・電話に出る=本人の行動)。"""
        self._place[np.asarray(a, dtype=np.int64)] = PLACE_HAND

    def put_back(self, a: Any) -> None:
        """しまう(顔を上げる・通話の終わり=本人の行動)。元の置き場へ。"""
        a = np.asarray(a, dtype=np.int64)
        self._place[a] = self._home[a]

    def drain(self, use: np.ndarray, step_seconds: int) -> int:
        """1 刻みの電池の減り(物理)。``use``=体ごとの使い方(``USE_*``)。新しく電源が切れた体の数を返す。"""
        rate = np.asarray(DRAIN_PER_HOUR, dtype=np.float32)[np.asarray(use, dtype=np.int64)]
        dt = np.float32(int(step_seconds) / SECONDS_PER_HOUR)
        live = self._on
        nb = np.where(live, self._battery - rate * dt, self._battery).astype(np.float32)
        np.maximum(nb, np.float32(0.0), out=nb)
        self._battery[:] = nb
        off = live & (nb <= np.float32(0.0))
        n_off = int(np.count_nonzero(off))
        if n_off:
            self._on[off] = False
        return n_off

    def charge(self, at_home: np.ndarray, step_seconds: int) -> tuple[int, np.ndarray]:
        """〔つなぎ BR-CT1-CHARGE-AT-HOME〕1 刻みの家での充電(エンジン規則=本人の行動になるまで)。``at_home``=体ごとの家に居るか。
        電池が 0 でなくなった体は電源が入る。→(充電した体の数・新しく電源が入った体の番号)。"""
        home = np.asarray(at_home, dtype=bool)
        dt = np.float32(int(step_seconds) / SECONDS_PER_HOUR)
        need = home & (self._battery < np.float32(INITIAL_BATTERY))
        n = int(np.count_nonzero(need))
        if n:
            nb = np.minimum(self._battery + np.float32(CHARGE_PER_HOUR) * dt, np.float32(INITIAL_BATTERY))
            self._battery[:] = np.where(need, nb, self._battery).astype(np.float32)
        back = np.flatnonzero(~self._on & (self._battery > np.float32(0.0))).astype(np.int64)
        if back.size:
            self._on[back] = True
        return n, back

    def summary(self) -> dict[str, Any]:
        """計器: 電池の最小・平均・電源の切れた数・初めの状態の数。"""
        b = self._battery.astype(np.float64)
        return {
            "battery_min": round(float(b.min()), 4) if b.size else None,
            "battery_mean": round(float(b.mean()), 4) if b.size else None,
            "off": int(np.count_nonzero(~self._on)),
            "battery_zero": int(np.count_nonzero(self._battery <= np.float32(0.0))),
            "manner": int(np.count_nonzero(self._manner)),
            "bag_home": int(np.count_nonzero(self._home == PLACE_BAG)),
            "earphones": int(np.count_nonzero(self._ear)),
            "in_hand": int(np.count_nonzero(self._place == PLACE_HAND)),
        }
