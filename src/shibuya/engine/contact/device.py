"""engine.contact.device — 道具の状態と通知の刺激の形(第 6 期 6-4 C1・C2・決定 10-12 §4-4 CT0 の共通の決まり 2・3)。

正: CT0「持ち物はエンジンが持つ世界の状態。初めは実データ(母集団の側)、途中は本人の行動と物理(電池など)で動く」「道具の
状態(電池・電波・マナーモード・かばんの中)を持つ」「耳は、イヤホンの音を SNR の周りの音として足します」・CT3「マナーモードや
かばんの中なら弱い刺激」。形は R-78(声の伝わり方)§5-2 の SNR(信号 − 雑音)と段の閾値(Lazarus の「足りる」の境 −3 dB・
既存答申の検知 −10 dB)。

持ち主 :class:`Devices`(状態台帳の腕の行 ``CT1D``=軸 1 behavior・軸 2 required・腕 c1 のランだけ)。体ごとの配列:

- ``_on``(電源)・``_battery``(電池の残り 0〜1・float32)・``_manner``(マナーモード)・``_place``(今の置き場 手/ポケット/かばん)・
  ``_home``(使っていないときの置き場=取り出す前の場所)・``_ear``(イヤホンをしているか)。
- 〔C2〕``_plugged``(充電器に差しているか)・``_low_known``(電池が少ないと本人が知っているか)・``_home_prev``(前の刻みに家に
  居たか=家に着いた刻みを見る)。
- 電波は舞台の全域で届く(配列を持たない=:func:`signal_ok`)。

通知の刺激(:meth:`Devices.stimulus`)=チャネルごとの段の形(係数を掛けない):

- 音(マナーモードでないとき): 耳の位置の着信音 ``RING_DB_1M − PLACE_ATTEN_DB[置き場]`` と、周りの騒音(W10 の騒音の段 →
  ``NOISE_STAGE_DB``=描画の帯の語の値)にイヤホンの音を電力で足した雑音の差=SNR。SNR ≥ ``SNR_CLEAR_DB`` で強い・
  ≥ ``SNR_DETECT_DB`` で弱い・それより下は届かない。
- 振動(マナーモードのとき): 手かポケットなら弱い・かばんは届かない。
- 画面: 視線が画面なら強い(画面の上の通知=見ている)。
- 刺激の段=チャネルの段の最大(0=届かない・1=弱い・2=強い)。

電池(物理): 1 刻みごとに 使い方(ビデオ通話>画面>通話>待ち受け)の減り方で減り、0 になると電源が切れる(切れた体へのメッセージは
網で預かる・電話は不通)。
〔第 6 期 6-4 C2=充電を本人の行動に(CT0 の共通の決まり 2・3)〕充電器は家にある(持ち物の実データが無い=全員 1 台・宣言)。
充電する/やめるは本人の判断(``engine.contact.layer`` の判断の口)で、このモジュールは物理だけを持つ: 差した体(``_plugged``)は
電池が減らず(家の電源)``CHARGE_PER_HOUR`` で増える(満充電で止まる=:meth:`Devices.charge_plugged`)・電池が 0 でなくなった体は
電源が入る(充電中に電源が入る=宣言)・家を離れたら抜ける(充電器は家にある=物理=``engine.contact.layer``・家=住まいの
セル/住まいが範囲の外の体は範囲の外に居る刻み=〔親の判断 2026-10-23〕)。「電池が少ない」は
道具の状態からの通知(``LOW_ALERTS`` の閾値を下に越えた刻み=:meth:`Devices.low_alerts`)・満充電も通知(どちらも System 1 の
刺激=通知と同じ段)。本人は自分の持ち物を知っている(``_low_known``=通知に気づいた・画面で見た・電源が切れた)。カレンダー 3 で
入れたつなぎ ``BR-CT1-CHARGE-AT-HOME``(家に居ると電池が増えるエンジン規則)は本段で外した。

**未リサーチ(expedient)**の値(記録 ct_c1/README.md・ct_c2/README.md の表とつなぎの台帳 ``DOC-ct-c1-device-*``・
``DOC-ct-c2-*``): 最初の電池 100%・マナーモードの人の割合 0.5・かばんに入れている人の割合 0.5・イヤホンの人の割合 0.2(どれも
実データが無い=最初の世界の状態の仮の値・母集団の側の乱数で体ごとに引く)・着信音 70 dB(1 m)・置き場の減衰(手 0・ポケット 6・
かばん 15 dB)・イヤホンの音 75 dB・電池の減り(待ち受け 1%/時・画面 12%/時・通話 8%/時・〔C2〕ビデオ通話 20%/時)・〔C2〕充電器は
家に全員 1 台・充電の速さ 50%/時(つなぎの値をそのまま)・電池の知らせの閾値 20%・10%・電波は全域で届く・通知の音はイヤホンに
流さない(本体の音=イヤホンは周りの音を覆う)。

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
    "SNR_DETECT_DB", "NOISE_STAGE_DB", "DRAIN_PER_HOUR", "CHARGE_PER_HOUR", "USE_STANDBY", "USE_SCREEN", "USE_CALL",
    "USE_VIDEO", "LOW_ALERTS", "CHARGERS_AT_HOME", "Devices",
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

# ---- 値(未リサーチ=expedient・つなぎの台帳 DOC-ct-c1-device-*・DOC-ct-c2-*) ----
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
#: 電池の減り[1 時間あたりの割合](待ち受け・画面・通話・〔C2〕ビデオ通話=通話より大きい=仮の値)。
USE_STANDBY, USE_SCREEN, USE_CALL, USE_VIDEO = 0, 1, 2, 3
DRAIN_PER_HOUR: Final[tuple[float, float, float, float]] = (0.01, 0.12, 0.08, 0.20)
#: 〔C2〕充電器に差した体の電池の増え方[1 時間あたりの割合](物理=カレンダー 3 のつなぎ BR-CT1-CHARGE-AT-HOME の値をそのまま=
#: 満充電まで 2 時間相当・仮の値)。
CHARGE_PER_HOUR: Final[float] = 0.5
#: 〔C2〕「電池が少ない」の通知の閾値(電池の割合がこの値を下に越えた刻みに道具が知らせる・仮の値)。
LOW_ALERTS: Final[tuple[float, ...]] = (0.20, 0.10)
#: 〔C2〕家にある充電器の数(持ち物の実データが無い=全員 1 台・宣言)。
CHARGERS_AT_HOME: Final[int] = 1

#: 本モジュールの仮の値の宣言(記録とつなぎの台帳の行 DOC-ct-c1-device-*・DOC-ct-c2-* と 1 対 1=文を変えたら台帳も直す)。
PROVISIONAL_VALUES: Final[tuple[str, ...]] = (
    "最初の道具の状態: 電池 100%・マナーモード 0.5・かばん 0.5・イヤホン 0.2(実データなし・母集団の側の乱数で体ごと)",
    "着信音 70 dB(1 m)・置き場の減衰 手 0/ポケット 6/かばん 15 dB・イヤホンの音 75 dB(周りの音に電力で足す)",
    "電池の減り 待ち受け 1%/時・画面 12%/時・通話 8%/時・ビデオ通話 20%/時",
    "充電器は家に全員 1 台(持ち物の実データなし)・差した体の電池は 50%/時で増える・電池の知らせは 20% と 10%",
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
        #: 〔C2〕充電器に差しているか(本人の行動で差す・抜く/家を離れたら抜ける=物理)。
        self._plugged = np.zeros(n, dtype=bool)
        #: 〔C2〕電池が少ないと本人が知っているか(通知に気づいた・画面で見た・電源が切れた → 閾値より上に戻ったら消える)。
        self._low_known = np.zeros(n, dtype=bool)
        #: 〔C2〕前の刻みに家に居たか(家に着いた刻み=充電の判断の機会の 1 つ)。
        self._home_prev = np.zeros(n, dtype=bool)

    # ------------------------------------------------------------------ 読む口
    def on(self, a: Any) -> np.ndarray:
        return self._on[np.asarray(a, dtype=np.int64)]

    def battery(self) -> np.ndarray:
        v = self._battery.view()
        v.flags.writeable = False
        return v

    def place(self, a: int) -> int:
        return int(self._place[int(a)])

    def is_low(self, a: int) -> bool:
        """〔C2〕電池が少ない(最初の知らせの閾値以下か電源が切れている)。"""
        i = int(a)
        return (not bool(self._on[i])) or float(self._battery[i]) <= float(np.float32(LOW_ALERTS[0]))

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
        """1 刻みの電池の減り(物理)。``use``=体ごとの使い方(``USE_*``)。〔C2〕充電器に差した体は減らない(家の電源)。
        新しく電源が切れた体の数を返す(電源が切れたことは本人が知る=``_low_known``・宣言)。"""
        rate = np.asarray(DRAIN_PER_HOUR, dtype=np.float32)[np.asarray(use, dtype=np.int64)]
        dt = np.float32(int(step_seconds) / SECONDS_PER_HOUR)
        live = self._on & ~self._plugged
        nb = np.where(live, self._battery - rate * dt, self._battery).astype(np.float32)
        np.maximum(nb, np.float32(0.0), out=nb)
        self._battery[:] = nb
        off = live & (nb <= np.float32(0.0))
        n_off = int(np.count_nonzero(off))
        if n_off:
            self._on[off] = False
            self._low_known[off] = True
        return n_off

    def low_alerts(self, before: np.ndarray) -> np.ndarray:
        """〔C2〕この刻みに「電池が少ない」の閾値(``LOW_ALERTS``)を下に越えた体(電源が入っている体だけ=道具が知らせる)。"""
        b0 = np.asarray(before, dtype=np.float32)
        b1 = self._battery
        hit = np.zeros(self.n, dtype=bool)
        for thr in LOW_ALERTS:  # 閾値の数ぶん(2)
            t = np.float32(thr)
            hit |= (b0 > t) & (b1 <= t)
        return np.flatnonzero(hit & self._on).astype(np.int64)

    def know_low(self, a: Any) -> None:
        """〔C2〕電池が少ないと本人が知った(通知に気づいた・画面で見た)。"""
        self._low_known[np.asarray(a, dtype=np.int64)] = True

    def plug(self, a: Any) -> None:
        """〔C2〕充電器に差す(本人の行動)。"""
        self._plugged[np.asarray(a, dtype=np.int64)] = True

    def unplug(self, a: Any) -> None:
        """〔C2〕充電器から抜く(本人の行動・家を離れた=物理)。"""
        self._plugged[np.asarray(a, dtype=np.int64)] = False

    def charge_plugged(self, step_seconds: int) -> tuple[int, np.ndarray, np.ndarray]:
        """〔C2〕1 刻みの充電(物理): 差した体の電池が ``CHARGE_PER_HOUR`` で増える(満充電で止まる)。電池が 0 でなくなった体は
        電源が入る。電池が最初の閾値より上に戻った体は「少ない」を知っている印が消える。
        →(増えた体の数・新しく電源が入った体・この刻みに満充電になった体)。"""
        dt = np.float32(int(step_seconds) / SECONDS_PER_HOUR)
        full = np.float32(INITIAL_BATTERY)
        need = self._plugged & (self._battery < full)
        n = int(np.count_nonzero(need))
        reached = np.zeros(0, dtype=np.int64)
        if n:
            nb = np.minimum(self._battery + np.float32(CHARGE_PER_HOUR) * dt, full)
            new = np.where(need, nb, self._battery).astype(np.float32)
            reached = np.flatnonzero(need & (new >= full)).astype(np.int64)
            self._battery[:] = new
        back = np.flatnonzero(~self._on & self._plugged & (self._battery > np.float32(0.0))).astype(np.int64)
        if back.size:
            self._on[back] = True
        self._low_known[self._battery > np.float32(LOW_ALERTS[0])] = False
        return n, back, reached

    def summary(self) -> dict[str, Any]:
        """計器: 電池の最小・平均・電源の切れた数・初めの状態の数・〔C2〕充電器に差している数・少ないと知っている数。"""
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
            "plugged": int(np.count_nonzero(self._plugged)),
            "low_known": int(np.count_nonzero(self._low_known)),
        }
