"""engine.run — 1 シミュ日の mock ラン(予算行 **W2**)と CLI。

正典
- 予算宣言表 **W2**: 「壁時計/シミュ日(Phase 2・**5千体・CPU・mock LLM**)**≤10分**。
  mock は呼び出しコストゼロ級=**エンジン性能の検収値**」。
- 運用設計書 §2.2/§2.4: tick の骨格 =
  ① 前 tick までに届いた LLM 応答を **apply_key 昇順**で適用(=Phase A の intent 源)
  ⓪ 知覚の tick 前計算(``Renderer.prepare_tick``・**B4 描画欄はここで 1 本作る**)
  ② 変化検出(P6)→ 起床候補(⓪ の欄をそのまま読む=描画と検出が同じ 1 本)
  ③ 繰り延べアービタ(§6)→ 呼ぶ個体
  ④ LLM 呼(応答は ``pending_apply`` へ・t_apply=起床+δ_perc+δ_think を分tickへ切り上げ)
  ⑤ Phase A(LLM 由来 intent + エンジン継続)→ ⑥ Phase B(資源裁定)→ ⑦ Phase C(resolve)
- 運用設計書 §1.4 T1/T2: 「同一 manifest×2 で**全 checkpoint ハッシュ一致**」。
- 運用設計書 §1.4 T4: 「n=5,000 と 5,001 で既存個体の乱数列が不変」(``agents.schedule``)。
- 世界過程設計書 §6 D-R2-6: 状態成長宣言の 24step→1日/30日 外挿ゲート。

**run_salt**(親の指定): ``blake3(master_seed の正規表現 ‖ 0x1f ‖ "engine")`` の先頭 16 バイト。
**RNG カウンタの class_rank**: ``class_rank + 1``(INSTITUTION −1 → 0)。

逐次ループ宣言(P4)
1. ``run_day``: **tick 数**ぶんのループ(1,440)。1 tick の中身は全て配列演算。
2. ``_call_llm``: **選抜された呼数**ぶんのループ(平均 35/tick・L4 の制御目標)。
   LLM クライアントは 1 呼=1 関数呼び出しの契約(``llm.LLMClient``)なので束ねられない。
   実艦隊では httpx の並行発射(C6)に置き換わる。

**C3 の結線(第3弾)**
- LLM 呼は ``engine.llm_bridge.LLMBridge`` 一本を通る(録画テープ・δ_think レーン・
  2行形パース・未定義行動5段が1か所に集まる)。``mode="replay"`` はテープ完全一致で回し、
  テープ外は**計数して待機へ落とす**(実LLMへは落とさない=運用設計書 §2.5)。
- 会話は ``engine.conversation.ConversationManager``(行動契約書 §3)。resolve が作った
  会話成立を招待として受け、話者に**会話ターン起床(不応期0)**を毎tick出す。終了はエンジン。

expedient(本モジュール分)
- δ_think は認知設計書 §1 のレーン表を分tickへ切り上げ(L1=**1 tick**=2.6秒の切り上げ)。
  既存定数 ``DELTA_THINK_TICKS=1`` と同値。①(応答適用)が④(LLM呼)より前にあるため
  ``t_apply=tick`` と ``tick+1`` は同じ tick で適用される(親指示「L1=0 tick」との差分を報告済み)。
- プロンプトは既定で**本物の ``perception.renderer.Renderer``**(B0-B6)。``renderer="stub"``
  で ``StubRenderer``(``[a<agent>|c<cell>|t5<tick//5>|w<class>]``)へ落とせる(安いテスト用)。
- 世界内日時は暦の口(``engine.calendar.SimCalendar.datetime_of``)= ``start_sim_datetime +
  T × tick_seconds``。``start_sim_datetime`` を渡さないランは ``DEFAULT_WORLD_START``(2026-07-13)+ ``day_index`` 日
  (〔第330・RET〕10e より前の「気象の再生実日を世界の日付にする」導き方は消した)。manifest に ``tick_seconds``・
  ``start_sim_datetime`` を書く(10a)。
- **通しの時刻 T**(10a・A1): ループの変数 ``tick`` は ``T = 日 × 1 日の tick 数 + 日の中の tick``。乱数とハッシュの
  鍵・call_id・テープの tick 欄・tick を値に持つ状態は T を使い、日の中の時刻で引く表(計画境界・食事の予定など)は
  ``T % 1 日の tick 数`` で引く。1 日のラン(既定)では T = tick なので値は今と同じ。
- 顕著行為(B4 の「顕著行為の到達」)は C3 では**常に空**(世界過程が C4)。流れも 0。
- 会話の招待は「resolve が ``会話`` を成立させた対」を入口にする(契約書 §3 の順序
  「招待→応答判定」の応答判定を resolve の直後に置いた)。相手側の ``activity`` は
  resolve が変えないため、相手の離脱は ``cell`` 監視で検出する。
- 週の曜日は ``day_index``(既定 0=月曜)。週 7 日表は C4 の PlanSpec。10a からは曜日・土休・祝日を引く箇所は
  すべて暦の口を通す(〔第330・ACT〕既定は ``--calendar-weekday real``・``--weather-scheme calendar``・開始日
  2026-07-13(月)=``engine.calendar.CALENDAR_UNIFIED``)。
- **応答の遅れ**(10a・A9): 既定 ``response_delay=1``=艦隊/再生の到着の受け取りを①(反映)の直前に置き、
  下限を ``max(t_apply, tick)`` にする=tick T に発射した呼は T+1 の①で反映される。``2`` は旧(受け取りは
  ④′・下限 ``tick + 1``=T+2)で、旧い実 LLM テープ(17 本)の再生のために残す。mock は同期で既に +1。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Final, Mapping
import blake3 as _blake3
import numpy as np
import dataclasses
from shibuya.world.facts.population_reader import Population, load_population, sample_population
from shibuya.foundation.vocab.agent_codes import (
    N_WAKE_CONDITIONS_ALL,
    Activity,
    WakeCondition,
)
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.foundation.rng import RNG_SCHEME
from shibuya.foundation.types import DEFAULT_TICK_SECONDS, MINUTES_PER_SIM_DAY
from shibuya.act.intake import from_words as CW
from shibuya.foundation.vocab import act_codes as CV
from shibuya.act.ops import talk as R
from shibuya.act.activity import payload_of
from shibuya.world.facts.calendar import (
    DEFAULT_HOLIDAY_CSV,
    WEATHER_SCHEME,
    WEEKDAY_MODE,
    SimCalendar,
)
from shibuya.act.intent import INTENT_MAX_TICKS
from shibuya.mind.memory.familiarity import FAMILIARITY_K
from shibuya.mind.memory.memory import MEMORY_N, RECALL_TAU
from shibuya.mind.memory.wom import DEFAULT_WOM_SOURCE
from shibuya.foundation.vocab.relations import (
    REL_D,
    REL_K,
    REL_TENURE_WEEKS,
)
from shibuya.mind.memory.store_memory import DEFAULT_STORE_DECAY, STORE_MEMORY_N
from shibuya.world.body.energy import DEFAULT_ENERGY_RATE, DEFAULT_HOME_MEAL, DEFAULT_HUNGER_MODEL, DEFAULT_MEAL_SLEEP_DEFER
from shibuya.runtime.arbiter import call_budget_per_tick
from shibuya.mind.judge.chooser import DEFAULT_CHOOSER, HABIT_P, RANK_TAU
from shibuya.mind.judge.classical import (
    DEFAULT_ACTIVITY_REGION,
    DEFAULT_CLASSICAL_SOCIAL,
    DEFAULT_MEAL_GATE,
    DEFAULT_POLICY,
)
from shibuya.world.model.geometry import DEFAULT_GEOMETRY
from shibuya.foundation.ports.ledger import LedgerBundle
from shibuya.world.laws.opening import rows_of_day as _opening_rows_of_day
from shibuya.act.target import MOVE_SEARCH_RADIUS_CELLS
from shibuya.runtime.inference.bridge import DEFAULT_LANE, delta_think_ticks
from shibuya.foundation.queues.scheduler import DIAG_COLUMNS
from shibuya.runtime.inference.tape import Replay, read_run_meta
from shibuya.foundation.vocab.actions import TargetKind
from shibuya.runtime.inference.fleet import FleetClient
from shibuya.runtime.inference.mock import MockLLM
from shibuya.foundation.text.channels import BudgetMode
from shibuya.perception.renderer import (
    DEFAULT_HUNGER_WORDS,
    SIGNAGE_P_SEE_DEFAULT,
)
from shibuya.foundation.text.templates import INTENT_MODES, VOCAB_VERSIONS
from shibuya.world.model.assets import DEFAULT_AREA_SOURCE
from shibuya.world.model.state import World
from shibuya.foundation.time_consts import MINUTES_PER_DAY, SECONDS_PER_MINUTE
from shibuya.runtime.result import DEFAULT_RESPONSE_DELAY, RUN_DEFAULT_L4_SCALE, RUN_DEFAULT_VOCAB_VERSION, RunResult

__all__ = [
    "DIAG_DAY_ROWS", "DELTA_THINK_TICKS", "run_salt_for", "run_day", "l4_budget", "resolve_l4_scale",
]


#: δ_think(分tickへ切り上げ後)。既定レーン L1=2.6 秒 → 1 tick(認知設計書 §1)。
DELTA_THINK_TICKS: Final[int] = delta_think_ticks(DEFAULT_LANE, DEFAULT_TICK_SECONDS)


def resolve_l4_scale(l4_scale: float | None, budget: float | None) -> float:
    """〔Q13 (a′)〕渡さなかった倍率(``None``)の決め方=``run_day`` と ``cli.run`` の 1 つの規則。

    予算を直に渡したランは 1.0(倍率より予算が優先=manifest に「0=無制限」と書かない)/渡さないランは
    ``RUN_DEFAULT_L4_SCALE``(0=無制限)。渡した倍率はそのまま返す(型も変えない=設定の指紋は前のまま)。
    """
    if l4_scale is None:
        return 1.0 if budget is not None else float(RUN_DEFAULT_L4_SCALE)
    return l4_scale


def l4_budget(n_agents: int, l4_scale: float) -> float:
    """〔Q13〕呼数の倍率 → 1 刻みの呼数上限(``budget`` を渡さない ``run_day`` と ``cli.run`` が使う 1 つの式)。

    倍率 0 → 体数(**無制限**=アービタは合流後に体あたり高々 1 件に畳むので体数で足りる・``inf`` は置かない)/
    倍率 > 0 → ``call_budget_per_tick(n_agents) × 倍率``(1.0=L4 按分=旧の既定)。負・NaN・無限大は止める(〔Q13 検収 L-2〕
    予算が NaN・無限大のまま黙って回らない)。
    """
    scale = float(l4_scale)
    if not 0.0 <= scale < float("inf"):  # NaN は比べると偽=ここで止まる
        raise ValueError(f"l4_scale は 0 以上の有限の値(0=無制限・いま {l4_scale!r})")
    return float(n_agents) if scale == 0.0 else call_budget_per_tick(n_agents) * scale

#: 診断表の列(``DIAG_COLUMNS`` の 4 列 + 運用列)。
#: 艦隊の順序制御グループ「時間帯」の刻み[tick](知覚契約書 §2.4 ⑨「時刻表記は5分丸め」)。
#: 同一(セル, 5分帯)の呼は同時に発射し、同一 GPU に寄せない(実装計画書 §7・BN-4)。
TIME_BUCKET_TICKS: Final[int] = 5

#: 診断行「シミュ日あたり」の必須行(§9.1 C3 受け入れ「診断行5本」+ 運用列)。
DIAG_DAY_ROWS: Final[tuple[str, ...]] = (
    *DIAG_COLUMNS,  # 繰り延べ / 昇格 / 縮退 / 抑止
    "parse_error_rate",
    "undefined_action_count",
    "tape_miss_count",
    "conversation_sessions",
)
_ENTRANCE_PLAN: Final[int] = 2
_ENTRANCE_EXPIRY: Final[int] = 4
#: 起床条件 → 起床入口の索引。
_ENTRANCE_OF_CONDITION: Final[np.ndarray] = np.array(
    [
        {
            "CELL_BLOCK": 0, "INTEROCEPTION": 1,
            "PLAN_SLEEPING": 2, "PLAN_WORKING": 2, "PLAN_GENERAL": 2, "PLAN_TRANSIT": 2,
            "CONVERSATION_TURN": 3, "ACTIVITY_EXPIRY": 4,
        }.get(WakeCondition(i).name, 5)
        for i in range(N_WAKE_CONDITIONS_ALL)
    ],
    dtype=np.int64,
)


#: 応答の遅れ(10a・A9)=1(発射 +1 tick で反映)だけ。〔第 4 期 4-3 版上げ 3 回目の第 2 部〕旧(+2 tick・10a より前の
#: テープの再生用)の切替口 ``--response-delay 2`` は消した=10a より前のテープ(meta に値が無い・2 の記録)は再生しない
#: (旧値の再現は安定版のタグ)。manifest の ``response_delay`` とテープの meta の値は 1 のまま書く(読み手の互換)。
RESPONSE_DELAYS: Final[tuple[int, ...]] = (1,)


def _resolve_response_delay(mode: str, replay: Any) -> int:
    """応答の遅れの値(1)。再生ではテープの脇の meta(``run_meta.json``)の ``response_delay`` が 1 でなければ止める
    (値の無いテープ=10a より前の録画・2 の録画=消した旧の道)。"""
    v = DEFAULT_RESPONSE_DELAY
    if mode != "replay" or replay is None:
        return v
    tape_dir = _replay_tape_dir(replay)
    rec = read_run_meta(tape_dir).get("response_delay")
    if rec is None or int(rec) != v:
        raise ValueError(
            f"応答の遅れがテープと違う: テープは response_delay={rec}(None=10a より前の録画)・今は {v}"
            "=旧(+2 tick)の再生の切替口は消した(安定版のタグで回す)"
        )
    return v


def _replay_tape_dir(replay: Any) -> Path:
    """再生の入力(``Replay`` かテープのディレクトリ)→ テープのディレクトリ。"""
    if isinstance(replay, Replay):
        return Path(replay.tape.path)
    return Path(getattr(replay, "path", None) or replay)


#: 10e(検収 L1): テープの脇の meta に書く乱数の鍵の配置の印。10c〜10f の counter(K19 の並べ方の前)と見分ける。
RNG_LAYOUT: Final[str] = "10e"


def check_replay_tape(mode: str = "record", replay: Any = None) -> None:
    """〔第330・RET〕再生するテープが今の版で録られたかを確かめる(違えば止める=警告ではなく例外)。

    テープの脇の meta(``run_meta.json``)が ``rng_scheme="counter"``・``rng_layout="10e"``・``calendar_weekday="real"``・
    ``weather_scheme="calendar"`` を持つテープだけを再生する。10e より前の録画(乱数 stateful・10c〜10f の counter の
    並べ方・記録の無いテープ)と、版上げ 1 回目の活性化より前の録画(暦の規則の記録が無い・day_index・legacy)は、
    それを再現する切替口(``--rng-scheme stateful``・``--calendar-weekday day_index``・``--weather-scheme legacy``)を
    版上げ 1 回目の後に消したので再生できない。手元の実テープ(版 1〜2・52 本)はどれも 10e より前の録画
    (10e の記録 §RET)。録画・mock では何もしない。
    """
    if mode != "replay" or replay is None:
        return
    tape_dir = _replay_tape_dir(replay)
    meta = read_run_meta(tape_dir)
    got = {k: meta.get(k) for k in ("rng_scheme", "rng_layout", "calendar_weekday", "weather_scheme")}
    want = {"rng_scheme": RNG_SCHEME, "rng_layout": RNG_LAYOUT, "calendar_weekday": WEEKDAY_MODE,
            "weather_scheme": WEATHER_SCHEME}
    if got != want:
        bad = ", ".join(f"{k}={got[k]!r}(要 {want[k]!r})" for k in want if got[k] != want[k])
        raise ValueError(
            f"このテープは 10e より前(または版上げ 1 回目の活性化より前)の録画で、今の版では再生できない"
            f"({tape_dir.name}: {bad})。旧値の再現の切替口は版上げ 1 回目の後に消した"
        )


def _count_intero_crossings(det: Any, agents: AgentState, acc: np.ndarray) -> None:
    """5 段目 5a(診断): この tick の内受容の跨ぎを 変数 × 上げ/下げ × 全体/起きて範囲内 で数える。

    ``write_b4_hash``・``write_intero_stages`` の**前**に呼ぶ(前回段=``<var>_stage`` がまだ書き戻されていない)。
    読むだけ=挙動に効かない。逐次ループ宣言: 内受容 3 変数ぶん(体数に比例しない)。
    """
    r = agents.registry
    for c in det.crossings:
        if not c.agent_id.size:
            continue
        ids = c.agent_id
        old = np.asarray(r.field(c.stage_field))[ids].astype(np.int16)
        up = np.asarray(c.new_stage).astype(np.int16) > old
        awake = (np.asarray(r.activity)[ids] != int(Activity.SLEEPING)) & (
            np.asarray(r.transit_state)[ids] == 0
        )
        acc[c.var, 0, 0] += int(np.count_nonzero(up))
        acc[c.var, 1, 0] += int(np.count_nonzero(~up))
        acc[c.var, 0, 1] += int(np.count_nonzero(up & awake))
        acc[c.var, 1, 1] += int(np.count_nonzero(~up & awake))


def _named_closed_lookup(
    resolver: Any, runner: Any, calendar: "SimCalendar | int", tick_seconds: int
) -> Callable[[int], tuple[int, int, int] | None]:
    """段 2c Q25: 体 → ``(POI, 即時閉店の tick, 次の開店の分)`` を引く関数(描画が読む)。

    開店の分=W7 の営業時間過程(``OpeningProcess``)の当日の行列で、失敗の分より後の最初の営業分。
    当日に無ければ翌日の W7 区間の最初の開始分。翌日の曜日の行は暦の口から引く(10a #8:
    失敗の通しの時刻 T の日番号 + 1 の ``table_weekday``。``day_index`` モードでは ``(day_index + 日 + 1) % 7``
    =1 日のランでは今の ``(day_index + 1) % 7`` と同じ)。W7 が無い(合成世界)・区間が無い店は
    ``-1``(時刻を出さない)。逐次ループ宣言: なし(引くのは描画 1 回につき 1 件)。
    ``calendar`` に整数を渡したときは ``SimCalendar.default``(2026-07-13 + その日数)で包む(〔第330・RET〕旧い口 legacy を消した)。
    """
    if not isinstance(calendar, SimCalendar):
        calendar = SimCalendar.default(int(calendar), tick_seconds=int(tick_seconds))
    opening = getattr(runner, "opening", None) if runner is not None else None
    om = getattr(opening, "open_matrix", None)
    pa = getattr(opening, "assets", None)

    def look(agent_id: int) -> tuple[int, int, int] | None:
        got = resolver.named_closed.get(int(agent_id))
        if got is None:
            return None
        poi, t = int(got[0]), int(got[1])
        nxt = -1
        if om is not None and om.size and 0 <= poi < om.shape[0]:
            minute = int(t * int(tick_seconds) // SECONDS_PER_MINUTE) % om.shape[1]
            later = np.flatnonzero(om[poi, minute + 1:])
            if later.size:
                nxt = minute + 1 + int(later[0])
            elif pa is not None and getattr(pa, "plan_poi", None) is not None:
                nxt_wd = calendar.opening_row(calendar.day_of(t) + 1)  # 10a #8: 翌日の行(〔第330〕祝日は PH)
                sel = (np.asarray(pa.plan_poi) == poi) & _opening_rows_of_day(
                    pa.plan_poi, pa.plan_day, int(nxt_wd), getattr(pa, "plan_ph_poi", None))
                if bool(np.any(sel)):
                    nxt = int(np.asarray(pa.plan_start)[sel].min()) % MINUTES_PER_DAY
        return poi, t, nxt

    return look


def _default_mock(
    seed: int | str, vocab_version: str, move_target_p: float = 0.0,
    out_of_cell_target_p: float = 0.0,
) -> Any:
    """``llm`` を注入しないランの既定 mock(``MockLLM``)。**語彙版に語彙を合わせる**。

    ``MockLLM`` はプロンプト本文を読まない(=B0 に 13 語目を載せても出力は変わらない)ので、
    語彙 v2 のランで「食事」を 1 件も出せない。mock は**書式と決定論を通す配管**であって
    振る舞いのモデルではない(``llm.mock`` の expedient 節)から、**提示した語彙から一様に
    引く**という既存の規約をそのまま版に従わせる。既定 ``"v1"`` では
    ``MockLLM(master_seed=seed)`` と**同一**(引数も乱数列も同じ)。
    """
    from shibuya.foundation.vocab.actions import cross_action_words

    if str(vocab_version) == VOCAB_VERSIONS[0]:
        return MockLLM(master_seed=seed)
    if str(vocab_version) == "v3":
        # 二層の段 3: 5 ラベル形(行為=11 語+なし の一様・活動・まで・あたり)=``llm.mock``
        # 段 2b: ``move_target_p`` > 0 で移動の対象にカテゴリ語/見えている名を出す(既定 0=不変)
        # 段 2c: ``out_of_cell_target_p`` > 0 で購入/食事/並ぶの対象に B2 に見える名を出す(既定 0=不変)
        return MockLLM(
            master_seed=seed, vocab=cross_action_words("v3"), form="v3",
            move_target_p=float(move_target_p),
            out_of_cell_target_p=float(out_of_cell_target_p),
        )
    return MockLLM(master_seed=seed, vocab=cross_action_words(vocab_version))


#: **10f(K21 (a))母集団の側の乱数**(用途名 → 何を決めるか)。``run_day(population_seed=…)`` の値から引く。
#: 振り分けの規則(実行役の構成=未リサーチ(expedient)): 体の属性(誰が居るか・体の定数・財布・日課)と、その体が
#: 暮らす舞台の構造(合成小世界の店の配置と在庫=世界資産の代わり)を決める流れ。salt(動きの seed)を変えても動かない。
#: ``world.synthetic`` を環境の側にしない理由: 世界資産(固定のデータ)の代わりの構造で、日ごとに変わる出来事ではない。
#: 環境の側に置くと「天気も変える」salt の比較で地図そのものが変わる(mock の拠点はセルの上に引くので母集団と組)。
POPULATION_RNG_DOMAINS: dict[str, str] = {
    "w16.sample.reserved": "W16 母集団の定員先取り層の抽出(agents.population.sample_population)",
    "w16.sample.stratum": "W16 母集団の統計層の抽出(同上・層ごとの流れ)",
    "wallet.initial": "世帯の初期財布(cli.household_wallets・母集団の種別から)",
    "agent.schedule": "mock 日課(拠点・境界の時刻・mock の初期所持金。W16 の体は拠点と種別を上書き)",
    "body.weight": "体重(engine.energy.draw_bodies・体ごと)",
    "body.eer": "推定エネルギー必要量のばらつき(同上)",
    "energy.meal_default": "〔小さな版上げ・meal_w17〕範囲外の既定の食事時刻の引き(engine.energy.MealStartDistribution.draw・体ごと)",
    "geometry.desired_speed": "希望歩行速度(engine.geometry.desired_speeds・--geometry edge と〔第 5 期 段 1〕--space nav1 のラン)",
    "space.nav1.turn_weight": "〔第 5 期 空間の段 1〕人ごとの曲がる重み 32〜62 m(engine.space.nav1.turn_weights・腕 --turn-weight person のランだけ)",
    "engine.processes.rail": "域外居住の通勤者の抽選と路線(計画実行層の無いランだけ)",
    "world.synthetic": "合成小世界の店の種別と在庫(世界資産が無いときだけ・舞台の構造)",
    "memory.forgetting_rate": "〔第 6 期 6-5〕忘れる速さの人ごとのばらつき 15%(MR8・engine.memory_m1・腕 --memory-model m1 のランだけ)",
    "talk.rate": "〔第 6 期 6-3 T2〕人ごとの話す速さ(モーラの長さ・engine.speech_clock・腕 --talk-clock mora のランだけ)",
    "economy.wage": "〔賃金の小さな版上げ〕体ごとの月の賃金の分位(core.wage_formula・第18表の階級の度数・賃金の腕 occupation のランだけ)",
    "contact.device": "〔第 6 期 6-4 C1〕最初の道具の状態(マナーモード・かばん・イヤホン=engine.contact.device・腕 c1 のランだけ)",
}
#: **10f 第 2 段の直し(S1・ユーザー決定 2026-10-07)環境の側の乱数**。``run_day(environment_seed=…)`` の値から引く。
#: 外から与える舞台の出来事(気象・大きな催し・道路工事)。「天気は同じで動きだけ変える」比較では固定し、
#: 「天気も変える」比較では salt と一緒に変える(``tools/c7/salt_runs.py --environment-mode``)。
ENVIRONMENT_RNG_DOMAINS: dict[str, str] = {
    "engine.processes.environment": "気象の再生実日の層と日(manifest の replay_date・start_sim_datetime・calendar)",
    "world.large_event": "大きな催しの会場の抽選(日ごと)",
    "world.road_works": "道路工事の辺の抽選(日ごと)",
}
#: **10f(K21 (a))動きの側の乱数**(用途名 → 何を決めるか)。``seed`` から引く(salt)。
#: ``world.delivery_inbound`` は動きの側(ユーザー決定 2026-10-07): 配送は本来、店の発注と配達員(エージェントの
#: 行動)で決まるもので、今のエンジンの処理は**つなぎ**(つなぎの台帳に載せる扱い)。
MOTION_RNG_DOMAINS: dict[str, str] = {
    "engine.chooser": "店・行き先の候補の選び手(poi_target・store_choice も同じ流れ)",
    "policy.classical": "古典の方策の抽選",
    # 〔第346 死んだ道の削除〕会話の招待の抽選 conversation.invite は応答率 0.8 の抽選と一緒に消した
    "llm.mock": "mock の応答(行為の抽選)",
    "decision.present": "候補の口の提示の並べ替え(第 1 期 1-8 J0・腕 --decision-port port のランだけ)",
    "llm.mock.move_target": "mock の移動の対象",
    "llm.mock.out_of_cell_target": "mock のセル外の店の対象",
    "perception.attention.p_see": "注視ゲート(看板・親しみの露出)",
    "perception.p_notice": "顕著行為に気づくか",
    "proximity.notice": "知人に気づく抽選(第 2 期 2-2・腕 --proximity distance のランだけ・1 組 1 本の counter の流れ)",
    # 〔第330・RET〕stateful の 2 本(world.salient・world.public_service_dispatch)は切替口と一緒に消した
    "world.salient.counter": "顕著行為の発生(counter)",
    "world.public_service_dispatch.counter": "出動の遅れ(counter)",
    "world.delivery_inbound": "入荷の抽選(つなぎ: 本来は店の発注と配達員の行動)",
    "world.delivery_last_mile": "配達の予約(引くだけ)",
    "talk.jitter": "〔第 6 期 6-3 T2〕発言ごとの話す速さの揺れ(engine.speech_clock・腕 --talk-clock mora のランだけ・計器)",
    "contact.mock": "〔第 6 期 6-4 C1〕連絡の本人の判断の仮のモデルの選び(engine.contact.port・腕 c1 のランだけ)",
    "contact.present": "〔第 6 期 6-4 C1〕連絡の判断の候補の提示の並べ替え(同上)",
    "contact.habit": "〔第 6 期 6-4 C2〕習慣で答えられるときも判断の口へ戻すか(engine.contact.port・腕 c1 と"
                     " SHIBUYA_CONTACT_HABIT=on のランだけ)",
    "calendar2.mock": "〔第 6 期 6-2 カレンダー 2〕予定の本人の判断の仮のモデルの選び(engine.calendar2.port・腕 arm のランだけ)",
    "calendar2.present": "〔第 6 期 6-2 カレンダー 2〕予定の判断の候補の提示の並べ替え(同上)",
    "calendar3.mock": "〔第 6 期 6-2 カレンダー 3〕雇い主と働く人の勤務の判断の仮のモデルの選び(engine.calendar3.port・腕 arm のランだけ)",
    "calendar3.present": "〔第 6 期 6-2 カレンダー 3〕勤務の判断の候補の提示の並べ替え(同上)",
    "duties.mock": "〔第 6 期 6-6 ② 第 1 部〕店の仕事(開閉店・補充・廃棄)の本人の判断の仮のモデルの選び(engine.duties.port・腕 arm のランだけ)",
    "duties.present": "〔第 6 期 6-6 ② 第 1 部〕店の仕事の判断の候補の提示の並べ替え(同上)",
}
#: 動きの側の、``core.rng`` の用途名を持たない塩(``seed`` から作る)。
MOTION_SALTS: dict[str, str] = {
    "run_salt": "blake3(seed‖engine): アービタの同点・適用の順・近接行の同点・歩きの行き先・関係の招待の重み",
    "fleet.call_seed": "xxh64(call_id, seed): 艦隊の呼ごとのデコードの種",
    # 〔第 6 期 6-2〕腕 --calendar 1b だけ。動きの seed(salt)と体の W16 の agent_id から引く決定論の割り振り(乱数の流れを
    # 使わない=core.rng の用途名は無い)。母集団の seed は使わない=母集団と salt の分離は前のまま
    "calendar_1b": "blake3(calendar1b:用途:seed) と agent_id の splitmix: 置き場所・余裕・時計を見る位相"
                   "(engine.calendar_self._key_draw)",
}


def resolve_sub_seed(seed: int | str, sub_seed: int | str | None) -> int | str:
    """10f: 母集団・環境の seed(``None`` なら ``seed`` と同じ値=今と同じ)。

    渡したときだけ ``core.rng`` の master_seed と同じ型と範囲の検査をする(bool・負・空の文字列を止める)。
    """
    if sub_seed is None:
        return seed
    from shibuya.foundation.rng import derive_key

    derive_key(sub_seed, "seed.check")  # 検査だけ(鍵は使わない)
    return sub_seed


def resolve_population_seed(seed: int | str, population_seed: int | str | None) -> int | str:
    """10f(K21 (a)): 母集団の seed(``resolve_sub_seed`` と同じ)。"""
    return resolve_sub_seed(seed, population_seed)


def resolve_environment_seed(seed: int | str, environment_seed: int | str | None) -> int | str:
    """10f 第 2 段の直し(S1): 環境の seed(``resolve_sub_seed`` と同じ)。"""
    return resolve_sub_seed(seed, environment_seed)


def _same_seed(a: int | str, b: int | str) -> bool:
    """2 つの seed が ``core.rng`` で同じ鍵になるか(``1`` と ``"1"`` は別=``i:1`` と ``s:1``)。"""
    return type(a) is type(b) and a == b


def run_salt_for(master_seed: int | str) -> bytes:
    """``blake3(master_seed ‖ 0x1f ‖ "engine")`` の先頭 16 バイト(親の指定)。"""
    text = f"i:{int(master_seed)}" if not isinstance(master_seed, str) else f"s:{master_seed}"
    return _blake3.blake3(f"{text}\x1fengine".encode("utf-8")).digest(length=16)


@dataclass(frozen=True)
class _RunDayLocals:
    """10b: ``run_day`` の局所の状態(状態台帳 O43・O44)を full-hash の持ち主として渡す入れ物。"""

    pending: list
    fleet_deferred: list
    fleet_waiting: set
    replay_inbox: dict


def _resolve_population(
    population: "Population | bool | None",
    world_dir: str | Path | None,
    n_agents: int,
    seed: int | str,
    n_cells: int,
) -> "Population | None":
    """``population`` 引数 → 実体(``None``=資産が無い/切っている)。

    ``False`` は「母集団を使わない」の明示。``None``(既定)は ``world_dir`` に W16 の
    出力があれば読む。既に ``Population`` なら体数だけ合わせる(二層抽出)。
    """
    if population is False:
        return None
    if isinstance(population, Population):
        pop = population
        _check_population_fits(pop, n_cells)
    else:
        if world_dir is None:
            return None
        pop = load_population(world_dir, n=None, seed=seed)
        if pop is None:
            return None
        if not _population_fits(pop, n_cells):
            # ``world_dir`` は知覚資産の置き場として渡されているが、世界そのものは
            # 合成小世界(セル数が違う)。**自動読み込みは黙って見送る**
            # (明示的に population= を渡したときだけ食い違いを例外にする)。
            return None
    if pop.n > n_agents:
        pop = sample_population(pop, n_agents, seed)  # 10e(E4・K19): 層の鍵の並べ方
    return pop


def _population_fits(pop: "Population", n_cells: int) -> bool:
    """母集団のセル索引が世界のセル数に収まるか。"""
    for arr in (pop.home_cell, pop.work_cell, pop.school_cell):
        if arr.size and int(arr.max()) >= int(n_cells):
            return False
    return True


def _check_population_fits(pop: "Population", n_cells: int) -> None:
    if not _population_fits(pop, n_cells):
        raise ValueError(
            f"母集団のセル索引が世界のセル数({n_cells})を超える。世界資産と母集団の版が違う"
        )


def _schedule_with_population(
    schedule, pop: "Population", n_cells: int, *, keep_outside_home: bool = False
):
    """mock 日課の拠点・種別を **W16 母集団**で置き換える(時刻帯は W17 まで mock のまま)。

    体数が母集団より多いときは、足りない分は mock の合成個体のまま残す(縮小ランの保険)。
    ``home_cell`` を持たない体(域外常住)は ``Population.start_cell`` の規約で置く
    (勤務→通学→mock の自宅セル)=W17 が入るまでの繋ぎ・expedient。

    Args:
        keep_outside_home: **D-66 計画実行層のラン**で True。域外常住の ``home_cell`` を
            ``-1`` のまま残し(=自宅=職場の代入をやめ)、``np.clip`` で −1 を潰さない。
            自宅のない体は計画実行層が起動時に ``place_at_external`` で外へ置く。
            既定 False = **帰無腕の挙動そのまま**(1 バイトも変わらない)。
    """
    n = int(schedule.n_agents)
    m = min(n, pop.n)
    home = np.asarray(schedule.home_cell).copy()
    work = np.asarray(schedule.work_cell).copy()
    # C9b G5: 学校セルは W16 が持っている(mock 側に対応する欄は無い)。対象ヒント
    # ``school`` の解決先としてそのまま運ぶ(**-1 のまま**=学校なしはヒントが効かない)。
    school = np.full(n, -1, dtype=np.int32)
    school[:m] = np.asarray(pop.school_cell, dtype=np.int64)[:m].astype(np.int32)
    kind = np.asarray(schedule.kind).copy()
    age = np.zeros(n, dtype=np.uint8)
    sex = np.full(n, -1, dtype=np.int8)
    direction = np.full(n, -1, dtype=np.int32)
    if keep_outside_home:
        ph = np.asarray(pop.home_cell, dtype=np.int64)[:m]
        home[:m] = np.where(ph >= 0, ph, -1)  # 域外常住は −1 のまま(I6 のガードが受ける)
    else:
        start = pop.start_cell(fallback=-1)[:m]
        home[:m] = np.where(start >= 0, start, home[:m])
    pw = pop.work_cell[:m]
    work[:m] = np.where(pw >= 0, pw, work[:m])
    kind[:m] = pop.kind[:m]
    age[:m] = pop.age[:m]
    sex[:m] = pop.sex[:m]
    direction[:m] = pop.direction_node[:m]
    home_out = np.clip(home, 0, n_cells - 1) if not keep_outside_home else np.where(
        home >= 0, np.clip(home, 0, n_cells - 1), -1
    )
    return dataclasses.replace(
        schedule,
        home_cell=home_out.astype(np.int32),
        work_cell=np.clip(work, 0, n_cells - 1).astype(np.int32),
        school_cell=np.where(school >= 0, np.clip(school, 0, n_cells - 1), -1).astype(np.int32),
        kind=kind,
        age=age,
        sex=sex,
        direction_node=direction,
        population_hash=pop.population_hash(),
    )


def _settle_pending_invites(
    conv, agents, tick, agent_ids, codes, named, R, np, by_distance: bool = False, rule: Any = None,
    drop_unreachable: bool = False, keep_activity: bool = False,
) -> set[int]:
    """返事待ちの招待を**Phase C の前に**確定する(層2 中-1・09-09)。

    正典
    - 行動契約書 §1-2 対象スロット: 承諾は「行動: 会話 **対象: 招待者**」。
    - 同 §6「直前の結果」: 承諾を intent のまま Phase C へ流すと、招待者は待ちで
      CONVERSING なので ``resolve._apply_talk`` が ``PARTNER_BUSY`` を書き、被招待の
      B6 に**偽の失敗**が載る(層2 再現: 51 セッション中 45 件)。ここで消費して防ぐ。

    承諾の規則(中-2・**expedient**: 契約書に承諾の対象規則は無い)
      - 返事が **会話** かつ 対象が **招待者 A**(または **名指しなし**)→ **承諾**。
      - 返事が 会話 でも 対象が **第三者 C** → A へは**拒否**。B の行は intent に残し、
        C への新しい招待として通す。
      - それ以外の行動 → 拒否。

    〔第 2 期 2-2 段 11a〕``rule``(腕 ``--proximity distance`` の ``engine.proximity.ProximityRule``)を渡すと、届くかを
    「同じ層・距離 ≤ d、または同じ B5 の単位」で見る(``resolve.talk_within_reach`` の ``rule``)。``None``(既定)は今のまま。

    〔11-03 M16〕``drop_unreachable``(ランは常に真=判断の系が渡す)では、返事が **会話** で対象が招待者
    (か名指しなし)なのに**届かない**ときは断りではなく**不成立**にする(``ConversationManager.drop_pending``=拒否の記憶を
    残さない)。招待側は今と同じく戻す。本人の行は intent に残す(今と同じ=B6 は今のまま)。``False``(この関数の既定=
    直に呼ぶ部品の単体試験の基準の口・〔第346〕ランの切替口 legacy は消した)は版上げの前の挙動(届かない承諾も断りに数え、
    組を 60 刻み記憶する)。

    〔11-03 M10 の続き〕``keep_activity``(ランは常に真)では、末尾の招待側の戻しを CONVERSING の体だけ IDLE にする形
    (``resolve.end_conversation``)にする=返事待ちの間に別の行為を選んだ招待側の活動は変えない。戻す体は会話中(is_busy)
    でない招待側だけ(下の 2 か所の条件)。戻さなかった数は ``ConversationManager.note_revert_kept`` に積む。``False``(この関数
    の既定=旧道)は全員を IDLE に戻す(``resolve.revert_conversation``)。

    Returns:
        **intent から外す**個体(=承諾した被招待。承諾は新しい招待ではない)。
    """
    if conv is None or not conv.pending_invites:
        return set()
    consumed: set[int] = set()
    accepted: list[tuple[int, int]] = []
    reverted: list[int] = []
    # 逐次ループ宣言: この tick に応答した個体のうち返事待ちの数ぶん(≤ 1 tick の呼数)。
    for k in range(int(agent_ids.size)):
        b = int(agent_ids[k])
        if b not in conv.pending_invites:
            continue
        a = conv.pending_inviter_of(b)
        # C9b G7: ``by_distance`` の腕では「同一セル」に実距離 2 m が加わる。
        same_cell = bool(
            a >= 0
            and R.talk_within_reach(agents, np.int64(a), np.int64(b), by_distance=by_distance, rule=rule)
        )
        aimed_at_inviter = int(named[k]) in (a, -1)
        ok = bool(codes[k] == CV.ACT_TALK) and aimed_at_inviter and same_cell
        if drop_unreachable and bool(codes[k] == CV.ACT_TALK) and aimed_at_inviter and not same_cell:
            # 〔11-03 M16〕承諾したが届かない=不成立(断りではない)。招待側は下と同じく戻す
            conv.drop_pending(b, tick, "unreachable")
            if a >= 0 and not conv.is_busy(a):
                reverted.append(a)
            continue
        opened = conv.resolve_pending(b, tick, accepted=ok)
        if opened is not None:
            accepted.append((a, b))
            consumed.add(b)  # 承諾は新しい招待ではない=intent から外す
        elif a >= 0 and not conv.is_busy(a):
            reverted.append(a)
    if accepted:
        R.set_conversing(
            agents,
            np.array([x for x, _ in accepted], dtype=np.int64),
            np.array([y for _, y in accepted], dtype=np.int64),
        )
    if reverted:
        _rv = np.array(sorted(set(reverted)), dtype=np.int64)
        if keep_activity:  # 〔11-03 M10 の続き〕CONVERSING の招待側だけ IDLE に戻す
            # 積むときは会話中でなかったが、同じ呼び出しの後の行で承諾してセッションに入った体は書く直前に除く(検収 低-2)
            _rv = _rv[np.fromiter((not conv.is_busy(int(x)) for x in _rv.tolist()), dtype=bool, count=_rv.size)]
            conv.note_revert_kept("settle", R.end_conversation(agents, _rv))
        else:
            R.revert_conversation(agents, _rv)
    return consumed


def _inviter_of(conv: Any, agent_id: int, condition: int = -1) -> int:
    """**返事待ちの招待**があれば招待者の個体 id、無ければ -1(知覚契約書 §6 起床(ii))。

    起床条件では絞らない(``condition`` は診断用に受けるだけ)。``_settle_pending_invites``
    は**その tick に答えた全員**の中から返事待ちを拾うので、被招待が別の条件
    (一般活動など)で起きた呼も承諾/拒否として消費される。会話ターン起床に限ると
    その分の呼に招待者が載らず、**答えようがないのに拒否と数えられる**(実測: 200体600tick で
    招待文が載った呼は 4 件しかなかった)。

    会話ターン起床には「セッションの話者」と「返事待ちの被招待」の 2 種類が同じ
    ``WakeCondition.CONVERSATION_TURN`` で来る(``conversation.wake_candidates``)が、
    話者には返事待ちが無いので ``pending_inviter_of`` が -1 を返して切り分けになる。
    """
    if conv is None:
        return -1
    return int(conv.pending_inviter_of(int(agent_id)))


def _target_person(target: Any) -> int:
    """``llm.contract.Target`` → 個体 id(``P-nnn`` 以外は ``-1``)。

    行動契約書 §1-2 の「対象: <セルID|物カテゴリ|**個体ID**>」を会話の相手として使う
    (C6・09-09)。パーサは素の整数も PERSON と読むので、そのまま個体 id にする。
    """
    kind = getattr(target, "kind", None)
    if kind is None or int(kind) != int(TargetKind.PERSON):
        return -1
    pid = getattr(target, "person_id", None)
    return -1 if pid is None else int(pid)


def _target_poi(target: Any) -> int:
    """``llm.contract.Target`` → 目印 POI 索引(解決できていなければ ``-1``)。

    C9b G6 a′: ``parse_target(..., landmarks=...)`` を通った応答だけが ``poi_id`` を持つ。
    """
    pid = getattr(target, "poi_id", None)
    return -1 if pid is None else int(pid)


def _pending_extra(res: Any) -> tuple[int, int, Any, Any]:
    """応答 → ``(対象ヒント索引, 目印 POI 索引, 活動, 対象)``。

    C9b G5/G6(腕が立っていなければ ``(0, -1)``)+ **二層の段 2** の活動
    (``engine.activity.payload_of``・語彙 v3 の応答だけ・それ以外は ``None``)+
    **段 2a** の対象(``llm.contract.Target``・購入/食事/並ぶの候補の絞り込みが読む)。
    """
    return (
        CW.target_hint_code(getattr(res, "target_hint", "")),
        _target_poi(getattr(res, "target", None)),
        payload_of(res),
        getattr(res, "target", None),
    )


def _call_ref(res: Any) -> tuple[int, str]:
    """応答 → ``(発射の tick, call_id)``(10b・保留の組の末尾 2 要素)。

    call_id は ``LLMBridge.call``・艦隊の発射と同じ式 ``"{tick}:{agent}:{wake_class}"``(テープの call_id 列と一致)。
    """
    t = int(res.tick)
    return t, f"{t}:{int(res.agent_id)}:{int(res.wake_class)}"


def _split_due(pending: list, tick: int) -> tuple[list, list]:
    """保留の組を「この tick に適用する分」と「残り」に分ける(元の並びを保つ・10b で関数に出しただけ)。"""
    return [p for p in pending if p[0] <= tick], [p for p in pending if p[0] > tick]


def classical_acq_addressable(agents: Any, aid: int, ids: "list[int]", A: np.ndarray, *,
                               by_distance: bool, rule: Any = None) -> np.ndarray:
    """第2波 §2A 項 3-1(検収後): 古典の交際の候補の A から、話しかけられない相手(会話中・就寝中=
    ``resolve._UNADDRESSABLE``)と、このランの設定で会話が届かない相手(``resolve.talk_within_reach`` が偽)を
    −inf にする(``resolve._apply_talk`` が PARTNER_BUSY/PARTNER_GONE で落とす相手を先に除く)。

    逐次ループ宣言(P4): なし(近接行の人数ぶんの配列演算)。
    """
    A = np.asarray(A, dtype=np.float64)
    if A.size == 0:
        return A
    p = np.asarray(ids, dtype=np.int64)
    ok = (p >= 0) & (p < agents.n) & (p != int(aid))
    pc = np.clip(p, 0, max(0, agents.n - 1))
    ok &= ~np.isin(np.asarray(agents.registry.activity)[pc], R._UNADDRESSABLE)
    ok &= R.talk_within_reach(agents, np.full(p.size, int(aid), dtype=np.int64), pc, by_distance=by_distance,
                              rule=rule)  # 第 2 期 2-2: 腕 distance は「届く」(rule=None は今のまま)
    return np.where(ok, A, -np.inf)


def run_day(
    n_agents: int = 5_000,
    seed: int | str = 1,
    world: World | None = None,
    *,
    population_seed: int | str | None = None,
    environment_seed: int | str | None = None,
    tick_seconds: int = DEFAULT_TICK_SECONDS,
    ticks: int = MINUTES_PER_SIM_DAY,
    llm: Any | None = None,
    fleet: "FleetClient | None" = None,
    fleet_wait_s: float = 0.0,
    fleet_debug_dir: str | Path | None = None,
    checkpoint_every: int = 360,
    day_index: int = 0,
    budget: float | None = None,
    l4_scale: float | None = None,
    n_cells: int = 139,
    mode: str = "record",
    tape_path: str | Path | None = None,
    replay: Any | None = None,
    renderer: Any | None = None,
    world_dir: str | Path | None = None,
    conversations: bool = True,
    lane: str = DEFAULT_LANE,
    ledger: "LedgerBundle | None" = None,
    processes: bool = True,
    processes_enabled: "list[str] | tuple[str, ...] | None" = None,
    processes_disabled: "list[str] | tuple[str, ...] | None" = None,
    p_notice_ablation: str | int = "A4",
    p_notice_d50_scale: float = 1.0,
    refractory_scale: Mapping[Any, float] | None = None,
    signage: bool = True,
    signage_p_see: float = SIGNAGE_P_SEE_DEFAULT,
    intent_mode: str = INTENT_MODES[0],
    vocab_version: str = RUN_DEFAULT_VOCAB_VERSION,
    role_words: bool | str = True,
    group_norms: bool | str = True,
    budget_mode: str | BudgetMode = BudgetMode.FIXED_SLOTS,
    salient_rate_per_10k: float | None = None,
    report_precondition: bool = True,
    queue_service: bool = True,
    population: "Population | bool | None" = None,
    occupancy_every: int = 0,
    occupancy_path: "str | Path | None" = None,
    sleep_suppression: bool = True,
    plan_sleep: bool = True,
    plan_executor: bool = True,
    exit_mode: str = "immediate",
    outside_suppression: bool = True,
    derive_rule: str = "v2",
    geometry: str = DEFAULT_GEOMETRY,
    area_source: str = DEFAULT_AREA_SOURCE,
    space: str | None = None,
    seat_area_eatery_m2: float | None = None,
    seat_area_retail_m2: float | None = None,
    census_out: str | Path | None = None,
    activity: bool | str = True,
    eatery: str = "food",
    chooser: str = DEFAULT_CHOOSER,
    move_search_radius: int = MOVE_SEARCH_RADIUS_CELLS,
    mock_move_target_p: float = 0.0,
    intent_max_ticks: int = INTENT_MAX_TICKS,
    mock_out_of_cell_target_p: float = 0.0,
    familiarity: bool | str = False,
    familiarity_k: int = FAMILIARITY_K,
    hunger_model: str = DEFAULT_HUNGER_MODEL,
    energy_rate: str = DEFAULT_ENERGY_RATE,
    meal_sleep_defer: str = DEFAULT_MEAL_SLEEP_DEFER,
    home_meal: str = DEFAULT_HOME_MEAL,
    hunger_words: str = DEFAULT_HUNGER_WORDS,
    policy: str = DEFAULT_POLICY,
    activity_region: str = DEFAULT_ACTIVITY_REGION,
    classical_social: str = DEFAULT_CLASSICAL_SOCIAL,
    meal_gate: str = DEFAULT_MEAL_GATE,
    classical_habit_p: float = HABIT_P,
    classical_tau: float = RANK_TAU,
    p_see_activity: "Mapping[str, float] | str | None" = None,
    memory: bool | str = False,
    memory_n: int = MEMORY_N,
    memory_tau: float = RECALL_TAU,
    store_memory: bool | str = False,
    store_memory_n: int = STORE_MEMORY_N,
    store_sigma: "Mapping[str, float] | str | None" = None,
    store_decay: str = DEFAULT_STORE_DECAY,
    store_wom: bool | str = True,
    store_signage: bool | str = True,
    store_recall_scope: str = "all",
    wom_source: str = DEFAULT_WOM_SOURCE,
    relations: bool | str = False,
    rel_k: int = REL_K,
    rel_tau: float | None = None,
    rel_d: float = REL_D,
    rel_init_density: float = 1.0,
    conv_max_participants: int = 2,
    rel_tenure_weeks: float = REL_TENURE_WEEKS,
    rel_invite: bool | str = True,
    rel_acq_wake: bool | str = True,
    rel_copresent: bool | str = False,
    sim_days: int = 1,
    start_sim_datetime: "datetime | str | None" = None,
    holiday_csv: "str | Path" = DEFAULT_HOLIDAY_CSV,
    school_holidays: Any = (),

    state_out: "str | Path | None" = None,
    stop_at_tick: int | None = None,
    resume_from: "str | Path | None" = None,
    run_id: str = "",
    checkpoint_detail: bool = False,

    weather_perturb: bool = False,
) -> RunResult:
    """1 シミュ日(既定 1,440 tick)の mock ランを回す。

    Args:
        n_agents: 個体数。
        seed: manifest の ``master_seed``。10f(K21 (a))からは**動きの seed**(salt)。``population_seed`` を
            渡さないときは母集団の側にも同じ値を使う(既定の結果は今と同じ)。
        population_seed: **10f(K21 (a))母集団の seed**。``None``(既定)= ``seed`` と同じ値。母集団の側の乱数
            (W16 の抽出 ``w16.sample.*``・mock 日課 ``agent.schedule``・体の定数 ``body.*``・希望歩行速度
            ``geometry.desired_speed``・域外居住 ``engine.processes.rail``・合成世界 ``world.synthetic``)はこの値から
            引く。気象・大きな催し・道路工事は ``environment_seed`` から引く。ほかの乱数(選び手・mock の応答・知覚・
            会話・顕著行為や入荷などの世界の出来事・``run_salt``・出勤の抽選など)は ``seed`` から引く。用途名ごとの表は
            ``POPULATION_RNG_DOMAINS``。salt の比較では母集団を固定して ``seed`` だけを変える。
        environment_seed: **10f 第 2 段の直し(S1)環境の seed**。``None``(既定)= ``seed`` と同じ値。気象の再生実日
            (``engine.processes.environment``)・大きな催し(``world.large_event``)・道路工事(``world.road_works``)
            はこの値から引く(``ENVIRONMENT_RNG_DOMAINS``)。
        world: 世界(None なら ``World.synthetic(n_cells, population_seed)``)。
        tick_seconds: 1 tick の秒数。
        ticks: tick 数。
        llm: ``LLMClient``(None なら ``MockLLM(seed)``)。
        fleet: 実 vLLM 艦隊(``llm.fleet.FleetClient``)。**渡すと LLM 経路が非同期になる**:
            ④ で 1 tick 分をまとめて発射(非ブロッキング)し、④′ で届いた分を拾う。
            繰り延べ(タイムアウト・キュー満杯・接続エラー枯渇)は**次 tick の起床候補へ
            再投入**する(不応期は免除=``resolve.clear_refractory``)。``None`` なら従来の
            同期 1 呼経路(``llm``=mock/tape)で、**挙動は 1 バイトも変わらない**。
        fleet_wait_s: ④′(艦隊の受け取り)で未応答が残っているとき**最大この秒数だけ待つ**。既定 0.0=
            純非ブロッキング。**本番の運用は 120**(障壁 120 s=c7 の本番ラン。1 tick に発射した呼が
            次の tick の受け取りで全部届くように待つ)。0 のままだと応答がラン終端にまとめて届き
            δ_think の契約(``t_apply``=起床+δ_perc+δ_think)が観測できない(スモークやテストのように
            エンジンが LLM より桁違いに速いランでも同じ)。受け取りの位置は ``response_delay`` を参照。
        fleet_debug_dir: 書式の原因分析用 jsonl の置き場(``None``=off が既定)。初回パースが
            落ちた呼だけ {プロンプト・初回の生応答・再生成の生応答・実効/厳密の判定・理由} を
            1 行 1 呼で落とす。**テープ形式は変えない**(テープは最終応答 1 行のまま)。
        checkpoint_every: checkpoint 間隔[tick]。
        day_index: 曜日(0=月曜)。
        budget: 1 tick の呼数上限(None なら ``l4_scale`` から ``l4_budget`` で作る)。
        l4_scale: 呼数の倍率(PENDING D-99 (a)・腕 AB8-L4-SCALE)。``budget`` を渡さないランは
            ``l4_budget(n_agents, l4_scale)``(``l4_scale>0`` なら ``call_budget_per_tick(n_agents)×倍率``・
            ``0`` なら ``n_agents``=無制限)を上限にする(``cli.run`` と同じ式)。
            **〔Q13 (a′)〕渡さない(``None``)ときは ``resolve_l4_scale``**=予算を渡したランは 1.0(manifest に載せるだけ)・
            渡さないランは 0=無制限(``RUN_DEFAULT_L4_SCALE``=``cli.CLI_DEFAULT_L4_SCALE``・D-99 (a′)・D-110)。
            ``1.0`` で旧挙動(L4 按分)。``cli.run`` と同じ決め方。L4 は監査線=
            manifest の ``llm_calls_total``/``llm_calls_per_agent_day``/``l4_line``/``l4_exceeded``。
        n_cells: 合成世界を作るときのセル数。
        mode: ``"record"``(``llm`` を呼ぶ)/ ``"replay"``(テープ完全一致・テープ外は計数)。
        tape_path: 録画テープの出力先(None なら記録しない)。
        replay: ``mode="replay"`` のときのテープ(``Replay`` かパス)。
        renderer: プロンプト生成。**None なら本物の ``perception.renderer.Renderer``**
            (C3 結線)。``"stub"`` で ``StubRenderer``(安い決定論テスト用)。
        world_dir: 世界資産ディレクトリ(``PerceptionAssets.load`` の入口。None または
            資産が無ければ ``PerceptionAssets.synthetic`` へ落ちる)。
        conversations: 会話プロトコル(行動契約書 §3)を回すか。
        lane: δ_think のレーン(認知設計書 §1)。
        ledger: 金/物の台帳(``engine.ledger_api.LedgerBundle``・economy が実装を注入する)。
            ``None`` なら C2 と同じ直接更新の経路。世帯の現金は**個体 SoA の ``money``
            そのもの**を採用するので、run は ``AgentState`` を作った直後に
            ``attach_household_cash`` を呼ぶ(台帳の世帯数は ``n_agents`` と一致が必要)。
        census_out: 日次センサス/月次 MER の**出力先ディレクトリ**(境界・経済設計書 §2.4)。
            ``None``(既定)なら**何も書かない**=manifest・checkpoint・出力ファイルは
            1 バイトも動かない。渡すと日の締めのあとに ``LedgerBundle.write_census``
            (economy 側が注入する書き手)を 1 回呼び、書いたパスを
            ``RunResult.census_paths`` に置く。台帳を渡していないランでは何も起きない。
        processes: 世界過程(C4 第1陣)を回すか(既定 True)。資産が無い合成世界では
            混雑場だけが動き、他の過程は「休む」。
        processes_enabled / processes_disabled: 過程 id か感度試験 id(``AB-*``)で
            過程単位に切る(ablation)。
        budget_mode: 知覚契約書 §3.2 の**義務 ablation ①**「チャネル固定枠 vs 同一総トークンの
            単一ランキング」の腕。``"fixed"``(既定=現行の描画・1 バイトも変わらない)/
            ``"ranking"``(チャネル別の上限表を使わず群予算だけを守る)。
            ``renderer`` を明示注入したランでは**このフラグは効かない**(注入側が持つ)。
        p_notice_ablation: 顕著行為の到達 ``p_notice`` の ablation(知覚契約書 §3.1 の
            ``A0``-``A4``。既定 ``A4``=完成形)。``processes_enabled`` に
            ``AB-PNOTICE-A2`` のように書いても効く。**``--ablate AB-PNOTICE-A0`` は
            ``salient`` 過程ごと止まる**(過程トグルと id を共有するため)ので、A0-A4 の
            腕を選ぶときは必ずこの引数を使う。
        p_notice_d50_scale: 知覚契約書 §8 第1陣 **② の腕**「p_notice の d50 を 0.5×/2×」。
            §3.1 の d50(既定 40 m・事象クラス別の表も同じ倍率)に掛ける正の倍率。
            既定 1.0=現行の抽選で**1 ビットも変わらない**。打ち切り 80 m は動かさない
            (2.0× は d50=打ち切りと同値になる=報告に明記する)。
        refractory_scale: 知覚契約書 §8 第1陣 **③ の腕**「近接入替の不応期 15 分 ±50%」。
            ``{起床条件: 倍率}``(鍵は ``WakeCondition``・列番号・条件名)。§6 不応期表を
            ランごとに振る(``engine.resolve.refractory_ticks``)。既定 ``None``=表どおり。
        signage: 知覚契約書 §8 第1陣 **⑥ の腕**「広告ゼロ」。``False`` で看板・広告面
            (B2.signage)を全セルで空にする(W14 凍結文も合成文も載せない)。既定 True。
            ``renderer`` を明示注入したランでは**このフラグは効かない**(注入側が持つ)。
        signage_p_see: **看板の注視ゲート**(知覚契約書 §4 段1 の視認確率 p_see・
            D-59 (b) ユーザー決定 2026-09-17・腕 ``AB6b-AD-NOTICE``)。在圏セルの
            看板行を観測へ入れるかを**体×看板×tick の決定論的ベルヌーイ**で決める
            (``core.rng`` の Philox・ドメイン ``perception.attention.p_see``・
            カウンタ ``(tick, agent_id, poi_id)``=テープから再現できる)。
            既定 1.0=常に載せる=**1 バイトも変わらない**(抽選も引かない)。
            0.0 は ⑥「広告ゼロ」と同じ描画になる(ただし ⑥ は ``signage=False`` が正典)。
            0.0〜1.0 の外は ``ValueError``。``renderer`` を明示注入したランでは
            **効かない**(注入側が持つ)。
        intent_mode: **AB7 自由意図の腕**(仕様書 §2)。``"vocab"``(既定)は
            現行どおり B0 に 24 語のホワイトリストを見せる。``"open"`` は ``行動:`` の 1 行だけを
            「いま自分がしたいことを10字以内の動詞句で」に差し替える(理由・対象・ひと言・
            2 行形・JSON 禁止は同文)。``"hint"``(AB7b)は同じ 1 行を「語彙から選ぶのが基本・
            当てはまる語が無いときだけ 10 字以内の動詞句」にする中間の腕。接地はどの腕でも
            エンジン側(§7 段0 辞書写像 → 段1 記録+待機)。
        role_words: **D-113 ④(第269)** B0 の末尾に役割語 12 語の 1 行(「自分の役割に権限が
            あるときだけ成立」)を足す(既定 True=行動契約書 §2.2「語彙自体は全員に見せる」)。
            ``False`` は第268 以前の B0(prompt_hash が変わるので、それ以前に録ったテープの
            再生では ``False`` を渡す)。mock の checkpoint は B0 を読まないので不変。
            既定では**1 バイトも変わらない**(テンプレ本体・``template_sha256`` も不変)。
            ``INTENT_MODES`` 以外は ``ValueError``。
        group_norms: **第309(Q150)** 群・規範の計器(D-107 (a)・``engine.norm_meter``=読むだけ)を回すか。
            ``True``/``"on"``(既定=第308 のまま)/ ``False``/``"off"`` で計器の 3 つの口を通さない(manifest
            ``group_norms`` は ``{"enabled": False}``)。計器は状態・乱数・テープに触れないので**どちらでも final は同じ**。
        vocab_version: **行動語彙の版**(D-71 §3 F・2026-09-17 ユーザー決定)。
            〔Q13〕既定は ``"v3"``(``RUN_DEFAULT_VOCAB_VERSION``=CLI の既定)。``"v1"`` は 24 語(横断 12 + 役割 12)。
            ``"v2"`` は横断語「食事」(飲食店オブジェクトの affordance・コード 24)を足し、
            ① B0 の出力規約が 13 語提示になる ② 段0 辞書が v3 になる
            (``食べる``/``飲む`` → ``食事``)③ ``resolve`` に「食事」の分岐が増える。
            **``llm`` を注入しないランでは mock の語彙もこの版に従う**(``MockLLM`` は
            プロンプトを読まないので、ここを合わせないと mock では「食事」が 1 件も出ない)。
            ``renderer`` を明示注入したランでは B0 側だけ注入側が持つ。
            ``VOCAB_VERSIONS`` 以外は ``ValueError``。
        population: W16 母集団(``agents.population.Population``)。``None``(既定)は
            **``world_dir`` に ``w16_population.parquet`` があれば自動で読む**
            (``n_agents`` 体へ二層抽出)。``False`` で明示的に切る(合成個体のまま)。
            資産が無ければ静かに合成個体へ落ちる。
        salient_rate_per_10k: 〔第347 止めた切替口の削除〕「倒れる」の発生率[件/10,000体/日]を上げる試験の口は**消した**
            (率の規則の旧道=消した切替口 ``--rate-rules legacy`` でだけ効いた)。引数は設定の指紋と 1-0 の引数の数を
            変えないため残し、``None`` 以外は ``ValueError``(旧値の再現は安定版のタグ
            ``stable-v2-before-switch-removal-347``)。倒れる率は部品の口(``WorldProcessRunner(salient_rate_per_10k=)``・
            ``SalientProcess(rate_per_10k_per_day=)``=旧道 ``rate_rules="legacy"`` でだけ効く)で渡す。
        report_precondition: **D-113 ②(第267)** 通報の前提「当該事象を知覚済み」(直近 5 tick に
            自分のセルの B4 に顕著行為の行が出た)を検査する(既定 True)。``False`` は従来どおり
            通報が必ず成功する挙動(=帰無腕・第266 以前の checkpoint ``ba01bd0b`` を再現)。
        queue_service: **D-113 ③(第268)** 満席で並んだ体を、席が空いた分だけ並んだ順に席へ
            入れて購入/食事を完了させる(既定 True)。``False`` は第267 以前の挙動(誰も捌かず
            15 tick で ``INTERRUPTED``)。既定の mock 5,000 では列が立たないので checkpoint 不変。
        sleep_suppression: **D-56 就寝抑止**(既定 True=ユーザー決定 (a))。``activity ==
            Activity.SLEEPING`` の個体の起床候補を、計画境界・顕著行為・会話ターン以外は
            アービタに入れない。``False`` は **D-56 前の挙動**(=ablation の帰無腕)。
            エンジンは tick 0 で全員を ``SLEEPING`` に置く(``resolve.initialize``=世界内
            00:00 の種。**週次表があるランは D-62 (b) が 0:00 の活動から立て直す**)ので、
            **深夜だけを回す短いラン**は既定のままだと呼が 0 になる。
            LLM 配管そのものを見るテスト(艦隊・テープ・パーサ)は ``False`` で回す。
        plan_sleep: **D-62 就寝は計画の実行**(既定 True=ユーザー決定 (a)+(b))。
            (a) 計画境界のうち**就寝境界**(``WakeCondition.PLAN_SLEEPING``)はエンジンが
            実行する——``activity=SLEEPING``(就寝地に居なければ歩かせて着いたら寝る)+
            **その境界では LLM を呼ばない**(候補にしない)。非就寝の計画境界は逆に
            ``SLEEPING`` の体を起こしてから呼ぶ。(b) 週次表(W17)があるランは tick 0 の
            ``activity`` を**0:00 時点の活動**から立てる(``resolve.set_initial_activity``)。
            ``False`` は **D-62 前の挙動**(=帰無腕。就寝境界も LLM に判断させ、tick 0 は
            全員 ``SLEEPING``)。週次表を持たない合成世界/mock 日課でも (a) は効く
            (mock 日課の第 5 境界=就寝)。
        plan_executor: **D-66 計画実行層**(``engine.presence.PlanExecutor``・既定 True)。
            W17 週次表を在圏ブロックに畳み、到着・退出・就寝・起床を**エンジンが実行する**。
            有効になるのは「W16 母集団 + W17 週次表があるラン」だけ(合成世界・
            ``--no-population`` では静かに休む=既存の下限対照は無傷)。
            ``False`` = **帰無腕**(rail の乱数 12% + D-61 帰りの便 + D-62 の run.py 発火=
            現行挙動。checkpoint も 1 バイト変わらない)。
        exit_mode: 退出の実行形(設計書 §10-3)。既定 ``"immediate"``(即時 ``rail_depart``)・
            **9a(D-115 ①)** ``"walk_to_platform"``=その体の路線のホームへ歩いて受容関数を通して乗る
            (上限 ``intent_max_ticks``・超えたら即時)。``"board_intent"`` は予約(``NotImplementedError``)。
        outside_suppression: **D-66 域外抑止**(既定 True)。``transit_state != 0``
            (域外滞在・乗車中)の体の起床候補をアービタに入れない——舞台に居ない体は
            B0-B6 の描画欄が全て空で、プロンプトが「どこにも居ない」になるため。
            D-56 の就寝抑止と同型だが**例外を作らない**(計画境界・顕著行為・会話ターンも落ちる)。
            ``False`` = **帰無腕**(``--no-outside-suppression``)。**計画実行層が立つラン
            でだけ効く**(``--no-plan-executor`` の帰無腕は現行挙動のまま=checkpoint 不変)。
        geometry: **C9 位置幾何の腕**(G1/G2・2026-09-17 ユーザー決定)。
            ``"node"``(既定)= 現行の 1 tick=1 ノード(実資産で ≒2.3 km/h)。
            **checkpoint も manifest 既存欄も 1 バイト動かない**。
            ``"edge"`` = 体が辺上の連続位置(``edge_id`` / ``edge_s`` / 向き=
            ``path_next_node``・+8 B/体)を持ち、1 tick に
            「希望速度 ``Uniform(1.00,1.60)`` m/s × Kladek 減速 × 60 s」の距離だけ進む。
            ``xy`` は両端ノードの線形補間・セルは近い方の端点・密度段は人/m² の
            Fruin LOS 段。``GEOMETRY_MODES`` 以外は ``ValueError``。
        area_source: **C9c-1 歩行可能面積の出所**(G8 (b)・D-84 (c)・2026-09-17)。
            ``"legacy"``(既定)= 現行の「W10 街路点数 × 6.25 m²・床 1,500 m²」
            (**expedient**・6.25 は 2.5 m 格子の目の面積)。**checkpoint も manifest 既存欄も
            1 バイト動かない**。``"plateau"`` = ``c9c_walkable_area.parquet``(PLATEAU tran の
            歩道部の面 + OSM 線 × 道路構造令の既定幅員・``tools/build_geo/walkable_area.py``)
            を読み、**密度の分母を 1 本だけ差し替える**(``PerceptionAssets.walkable_area_m2``
            = B4 の LOS 段・``ChangeDetector`` の起床条件 (i)・``EdgeGeometry`` の Kladek 減速が
            **同じ値**を見る)。読み込みは起動時 1 回で tick ループに新しい逐次ループを作らない。
        seat_area_eatery_m2 / seat_area_retail_m2: **1 人あたり床面積[m²]の感度腕**
            (C9c-1・R-8 ③)。``None``(既定)= ``processes.crowd.SEAT_AREA_M2``
            (飲食 2.0 / 物販その他 4.0)のまま=**1 バイトも変わらない**。法定の帯は
            ``world.assets.SEAT_AREA_M2_FIRE_CODE``(消防法施行規則 1 条の 3・飲食 **3.0** /
            物販 **4.0**)と ``SEAT_AREA_M2_BUILDING_NOTICE``(建告1441・飲食 1.43 / 売場 2.0)。
            ``eatery`` は ``food``/``nightlife``、``retail`` は**表に無い全カテゴリ**に効く。
        activity: **行為と活動の二層の活動層**(段 2・D-116・既定 True=``--activity on``)。
            立つのは ``vocab_version="v3"`` のときだけ(v1/v2 では活動欄が来ない=**実質無効**で
            checkpoint も 1 バイト動かない)。立つと ① ``activity_until``/``activity_kind`` の
            2 欄(+5 B/体)② 満了入口(``WakeCondition.ACTIVITY_EXPIRY``)③ 活動中は場所の変化
            (CELL_BLOCK)で起こさない ④「移動 対象: あたり」の近傍歩行 ⑤ 同セルの B4b に
            活動の 1 行 ⑥ 休んでいる体の疲労回復(10 tick ごとに −1)⑦ 活動の文を checkpoint に
            混ぜる。``False``/``"off"`` は抑止も満了も無効=現行の挙動。
        eatery: **飲食店の切替口**(段 1b・D-96 nightlife (b)・``World.eatery_mask``)。
            ``"food"``(既定)=現行の ``cat`` の価格帯「飲食」(実資産 823 件)=**checkpoint は
            1 バイトも動かない**。``"place_food"``=W17 の場所語「飲食店」と同じ集合(``food`` ∨
            ``nightlife`` のうち subcat が club/karaoke/sauna/net_cafe でないもの・実資産 1,042 件)。
            価格(``poi_price``)は動かさない。``EATERY_MODES`` 以外は ``ValueError``。
        chooser: **選び手**(段 2a・D-114 (a)・``engine.chooser``)。購入/食事/並ぶの対象を
            「現在セルの営業中・意図に合う POI の候補」→ 選び手の分布 → 抽選
            (``core.rng.stream(seed, "engine.chooser", tick, agent_id)``)で決める。既定
            ``"nearest"``=可視(W8 の視点数)の降順 → POI 索引(憲法⑥の宣言つき暫定)。
            それまでの「現在セルの最小 id」から**既定 checkpoint が動く**(版の台帳
            ``docs/bench/analysis/intent-chooser-2026-09-28/``)。
        move_search_radius: **段 2b**(行き先を対象欄から・D-112 ②)のカテゴリ語の近傍探索で
            見る近いセルの数(現在セル・見えている POI の次に ``cell_dist`` の昇順で R 個・宣言・
            既定 5)。0 なら近傍探索をしない。
        mock_move_target_p: 既定 mock(語彙 v3)の移動の対象にカテゴリ語か B2 に見えている名を
            出す確率(段 2b の経路を mock で通す腕・既定 0=golden 不変)。
        intent_max_ticks: **段 2c(意図の保持・D-112 ①・D-114 案 A)** の上限[tick]。購入/食事/
            並ぶ/会話/就寝の対象が現在セルに無く解決できるとき、行為を意図(SoA 4 欄・既定で確保)に
            保存して目的地つき移動を始め、着いたら LLM を呼ばずに実行する。歩いてこの tick を
            超えたら ``TOO_FAR``(宣言 60・expedient・感度腕 30/120)。意図の層は**活動層が立ち
            (語彙 v3・``activity=True``)** のランだけ働く
            (v1/v2・``--activity off`` は欄を確保するだけ=挙動は段 2b のまま)。
        mock_out_of_cell_target_p: 既定 mock(語彙 v3)の購入/食事/並ぶの対象に B2 の「見えるもの」
            の名(括弧内の店名があればそれ)を出す確率(段 2c の経路を mock で通す腕・既定 0)。
        familiarity: **4 段目(記憶の先行部品=M13 訪問+M17 露出)**。``True``/``"on"`` で体×K 行の
            親しみの表(``AgentState(familiarity_columns=True)``・16 B/行)を確保し、訪問(購入/食事の
            成立)・看板の露出(B2 に看板行が載った)・場所(セルに入った回)を書く。**本段では誰も
            読まない**。既定 ``False``=表を確保しない=**既定 checkpoint 不変**。
        familiarity_k: 体あたりの行数(既定 ``FAMILIARITY_K``=64・宣言・感度 32/128)。
        hunger_model: **5 段目 5a(D-118 K1〜K9)**。``"energy"`` で体のエネルギー収支
            (``AgentState(energy_columns=True)``・+16 B/体・``engine.energy``)=体重と EER を抽選し、
            毎 tick 活動の METs で消費・食事/軽食/飲料で摂取・``hunger`` は語の段の写し・B5 は語・
            範囲外の食事は W17 の食事行か既定の時刻。〔Q13〕既定は ``energy``(``world.body.energy.
            DEFAULT_HUNGER_MODEL``=``cli.CLI_DEFAULT_HUNGER_MODEL``・K5 (a))。``"v1"`` は旧規則
            (+1/30 分・購入/食事で −4)=ランの口からは止める(試験の中だけの口 ``world.body.energy._HUNGER_V1_FOR_TESTS``・
            旧 checkpoint の値は安定版のタグ ``stable-v2-before-library-defaults-q13``)。
        energy_rate: 消費の式(``"eer"``=K1 (c)・既定 / ``"bmr"``=K1 (a) の感度腕)。``hunger_model=
            "energy"`` のときだけ効く。
        meal_sleep_defer: **第2波 §2B 項 1(Q34 (b))** ``"off"``(**既定**=旧)/ ``"on"``=範囲外の既定の食事時刻に
            W17 で就寝中の体は、起床の時刻(窓の中なら)へ遅らせて食べる(``engine.energy.OutOfAreaMeals``)。
            ``hunger_model="energy"`` のときだけ効く。
        home_meal: **第2波 §2B 項 2(Q35 (a))** ``"off"``(**既定**=旧)/ ``"plan"``=W17 の自宅の食事行(自宅が
            範囲内の体)を、行の開始に自宅に居て起きていれば「予定の実行」として食べさせる(金と物は動かさない・
            照合の分布と店の集計から外す・``engine.energy.HomeMeals``)。``hunger_model="energy"`` のときだけ効く。
        hunger_words: **第2波 §2B 項 3(Q31 (b))** B5 の空腹の語。``"hungry"``(**既定**=旧=空腹以上だけ描く)/
            ``"all"``=満腹・ふつうも描く(``energy_columns`` のランだけ効く)。
        policy: **5 段目 5b(D-119 L5 (a))**。``"classical"`` で LLM(mock)を呼ばず、起床ごとに
            食事の門+ActivityChooser(社会生活基本調査の事前分布)から 5 ラベルの応答文を作る
            (``engine.classical.ClassicalPolicy``・語彙 v3 だけ)。既定 ``"mock"``=凍結の mock
            (**既定 checkpoint 不変**)。``llm`` の注入・再生・艦隊とは併用できない。
        activity_region: 事前分布の地域(``"kanto"``=関東大都市圏・既定 / ``"national"``=全国)。
        classical_social: **第2波 §2A 項 3-1(Q42 (b))** 方策 classical の交際・付き合い(符号 18)の相手。
            ``"acquaintance"``(既定)=B5 近接行の知人(生きている関係辺の相手)のうち A が最大の人・居なければ
            「なし・待つ」(関係 off のランでは会話を始めない)/ ``"near_first"``=旧(近接行の最初の人=見知らぬ人・
            関係 on は C10 8b の重みつき抽選)。``policy="classical"`` のときだけ効く。
        meal_gate: **第2波 §2A 項 4(Q48 (a))** 方策 classical の食事の門の確率の読み方。``"per_wake"``(**既定**=旧・
            起床ごと)/ ``"per_hour"``=1 時間あたりと読み、前回の門の後に範囲内で起きていた各 tick の語の段で
            ハザードを積算して換算(**第2波 §2B の規則**・体ごとの H 4 B/体・``engine.classical``)。既定の切り替えは食事の束の版上げで確認する(指示書 §8-2)。
        classical_habit_p / classical_tau: ``chooser="classical"`` の習慣の確率 p_h(宣言 0.5)と
            満足化の揺らぎ τ(宣言 1.0)。
        p_see_activity: 〔第 1 期 1-2・決定 10-12 §1-6「係数で持たない」〕5 段目 5c(D-117)の看板の注視 p_see に
            掛ける活動の種別の乗数は**消した**(既定のランで効く道が無かった=byte-check 19 構成で結果不変)。引数は
            設定の指紋(``_call_args``)と 1-0 の引数の数を変えないため残し、``None`` 以外は ``ValueError``。
            manifest の欄 ``p_see_activity`` は残して値は null。
        memory: **6 段目 6a(記憶 第 1 段の記録)**。``True``/``"on"`` で体 × N 行の記憶の表
            (``AgentState(memory_columns=True)``・実 25 B/行・宣言 32 B/行)を確保し、行動の成否・会話・
            気づき・強い看板(初見)を書く(``engine.memory``)。読み手は 6b の想起(下)。既定 ``False``=
            表を確保しない=**既定 checkpoint 不変**。
        memory_n: 体あたりの行数(既定 ``MEMORY_N``=128・宣言・感度 64/256)。
            **6b(想起)**: on のランは、各呼の描画で q(起床の級・セル・直前の結果・相手・対象)に ID で
            合う行を score 順に k 件(会話 3・他 2)想起し、B5 の最後に「記憶」の 1 行(≤60 tok)を載せる
            (テンプレ v1.2・テープ版 3 の ``recalled_rows``)。off は描画バイトが 1 バイトも変わらない。
        memory_tau: 想起の閾値 τ(A ≥ τ の行だけ想起・既定 ``RECALL_TAU``)。
        store_memory: **D-120 7a(店の評価の記憶)**。``True``/``"on"`` で体 × M 行の店の評価の表
            (``AgentState(store_memory_columns=True)``・実 23 B/行・宣言 24 B/行)を確保し、記憶の
            エピソード(購入/食事/並ぶの成否・看板の初見)から店の行を書く(``engine.store_memory``)。
            **``memory`` が on のランでだけ**使える(書き手がエピソードの書き手に乗る)。本段では誰も
            読まない。既定 ``False``=表を確保しない=**既定 checkpoint 不変**。
        store_memory_n: 体あたりの店の行数(既定 ``STORE_MEMORY_N``=32・宣言・感度 16/64)。
        store_sigma: 出どころ別の σ(辞書か JSON・既定 自分 1/伝聞 2/看板 4/ネット 2・感度腕)。
        store_decay: 減衰の形(``actr`` 既定・``ga``/``citysim`` は感度腕の口)。
        store_wom / store_signage: **D-120 7c(N8 の腕)**。口コミ(7b の聞き手への転写)と看板(N2 (iii))の
            書き手を使うか(既定 どちらも on・``"on"``/``"off"`` か bool)。店の記憶 on のランだけ効く。
        store_recall_scope: 7c: B5 の想起で店の行を候補にする入口(``all`` 既定・``conversation``=会話だけ=感度腕)。
        wom_source: **第2波 §2A 項 1(Q57 の確認)** 口コミの抽出の源。``"utterance"``(既定)=発話の欄(ひと言)だけ
            (いまの語彙 v3 にはひと言欄が無い=抽出 0)/ ``"reason-target"``=旧(v3 で理由欄+対象欄=内心が聞き手に
            漏れる欠陥・旧 golden の再現用)。店の記憶 on のランだけ効く。manifest ``wom.source``。
        relations: **C10 8a(関係辺)**。``True``/``"on"`` で体 × k 辺の関係の表(``AgentState(relation_columns=
            True)``・16 B/辺)を確保し、W16+W17 の機械的初期化と、記憶のエピソード(会話・手伝い)から辺を書く
            (``engine.relations``)。B5 近接行の「知人」の印に結線する(v1.4)。**``memory`` が on のランでだけ**。
            既定 ``False``=表を確保しない=**既定 checkpoint 不変**。
        rel_k / rel_tau / rel_d / rel_init_density: 辺の数(既定 15・感度 5/50)・閾値 τ_rel(既定 None=全母集団の再逆算 v2 −2.322・感度
            ±0.5)・減衰 d(既定 0.5・感度 0.25/0.75)・初期網の密度の腕(0.5/1.0/2.0)。
        conv_max_participants: **C10 8a(D-93 (d))の 3 人会話の口**。3 なら会話中の相手に話しかけた体が
            そのセッションに加わる(``talk_partner``=名指しした相手=主相手・参加者はセッション表)。既定 2=不変。
        rel_tenure_weeks: C10 8b(第299 Q89/Q90): 初期辺の在職期間 T_uv の上限[週](既定 13・感度 26)。
        rel_invite / rel_acq_wake / rel_copresent: **C10 8b**(``relations`` が on のランだけ効く)。
            ``rel_invite``(既定 on)=名指しの無い会話の相手を関係辺の重み(内側 5 人 40%・次の 10 人 20%・残り
            40%・居る層で再正規化)+seed つき乱択で引く・2 m 内の知人を第一候補(偶然)・classical 方策の相手も
            同じ重み。``rel_acq_wake``(既定 on)=知人出現の起床(``WakeCondition.ACQUAINTANCE``・同一相手 60 分)。
            ``rel_copresent``(既定 off=第299 Q91)=同席の書き手(同セル・2 m 内・連続 5 分で 1 本・相手ごと
            1 日 1 本・表に居る相手だけ)。起点の診断行(招待/偶然/知人出現)は関係 on のランでいつも数える。
            想起優先の候補合成(N6)は選び手 ``classical`` のランだけ(``engine.store_choice``)。
        sim_days: **複数日の通しラン**(10a の口・10d で世界資産・台帳・艦隊にも広げた)。既定 1。2 以上では
            ``ticks`` を 1 日の tick 数にして、同じプロセスで T = 0〜``sim_days × 1 日の tick 数``−1 を続けて回す。
            各日の終わりに日次の締め(``runner.end_of_day``・台帳の締め・日次センサス)を 1 回走らせ、締めの後の
            2 つのハッシュを日ごとに ``RunResult.daily`` に記録する。次の日の頭の初期化(``initialize``・初期の
            活動・域外の配置・空腹の初期値・初期の財布・店舗の参入資本・帳簿の作り直し)は**走らせない**(A11)。
            日の頭で張り直すのは、鉄道の時刻表(T の座標で末尾に足す)・計画実行層の在圏ブロックとイベント
            (出勤率は日番号つきの鍵で引き直す)・計画境界の表(W17 は K9 のつなぎ=月曜の行)・天気の実日。
            営業時間(W7)・世界過程の日ごとの乱数の表・食事の予定は 0 日目の表を繰り返す(宣言・10d README)。
            再生(replay)とは一緒に使えない。
        start_sim_datetime: **10a(A1-1)の開始日の欄**(``datetime``・``date``・``"YYYY-MM-DD"``)。``None``
            (既定)は ``DEFAULT_WORLD_START``(2026-07-13・月)+ ``day_index`` 日。渡すと T=0 の世界内日時(プロンプトの
            日付)と暦の日付になる。曜日・土休・祝日は日付と内閣府の祝日から(祝日は土休・曜日 7 日の表では日曜の行・W7 は
            PH の行)。曜日・土休・祝日を引く 18 か所は暦の口(``engine.calendar.SimCalendar``)を通す。〔第330・RET〕10e
            より前の曜日の決め方 ``day_index`` と切替口 ``calendar_weekday`` は消した。
        holiday_csv: 祝日 CSV の場所(既定 ``data/calendar/syukujitsu.csv``)。読めなければ開始日の検査で止める。
            読んだ md5 を manifest の ``calendar.holiday_csv_md5`` に書く。
        school_holidays: 学校の長期休みの区間の一覧(``"YYYY-MM-DD:YYYY-MM-DD,…"`` か組の列)。開始日の検査で
            当たれば止める。既定は空(表の中身は K7 の判断待ち)。
        (乱数: 10c・10e の counter=顕著行為の発生を ``(seed, 名前, T)``・出動の遅れを ``(seed, 名前, T, セル, k)`` から毎回
        作る・K19 の鍵の並べ方。〔第330・RET〕10e より前の ``stateful`` と切替口 ``rng_scheme`` は消した。manifest の
        ``rng_scheme`` は ``counter`` の記録)
        state_out: **10d の状態の書き出し先**(ディレクトリ)。渡すと各日の締めの後(複数日のランの途中の日)と、
            ``stop_at_tick`` で止めたとき、ランの最後(``finished: true``)に、状態のまとまりを 1 ファイルずつ
            書く(``engine.resume``・名前は ``state-T<次に回す T>.npz``=10f の npz+json。10d の ``.pkl`` は 10e で読み口を消した)。``None``(既定)=書かない。
        stop_at_tick: **10d の止める時刻**(通しの時刻 T・その tick の手前で止める)。日の境目(1 日の tick 数の
            倍数)なら直前の日の締めの後、日の途中(試験用・A10)なら締めずにそこで状態を書いて止める。
            ``state_out`` が要る。止めたランは ``finished: false``。
        resume_from: **10d の再開**(状態のファイル)。日の頭の初期化(``initialize``・初期の活動・域外の配置・
            空腹の初期値・初期の財布・関係の初期の辺)を走らせず、保存した状態を読んで続ける(A11)。設定の指紋が
            親と違う・親が ``finished: true``・状態台帳の版が違う ならば止める。台帳を渡すときは初期の入れ直しを
            していない新しい台帳(``cli.build_ledger_bundle(endow=False)``)。``sim_days`` は親と同じ通しの日数。
        run_id: manifest のラン ID(空なら設定の指紋・始めの T・親のラン ID から作る)。
        checkpoint_detail: checkpoint ごとに列ごと・外の状態の行ごとの digest も控える(食い違いの場所を探す道具
            ``docs/bench/analysis/wallbounce-1003/10d/first_diff.py`` 用・既定 off=費用 0)。
        (天気と暦の規則: 世界の日付は暦・天気は再生日の行・日の出と日の入りと太陽高度と影は暦の日付=ユーザーの答え 1-3・
        ``engine.processes.environment``。〔第330・RET〕10e より前の ``legacy`` と切替口 ``weather_scheme`` は消した)
        weather_perturb: **10e(B6)天気を揺らす**(アンサンブル・既定 ``False``)。``True`` では暦の日付が窓の中でも
            実際の天気を使わず、同じ季節 × 平日/土休の層から天候型を日数の割合で引く(鍵は環境の seed)。アンサンブルは
            これを付けて ``environment_seed`` を変えて回す。
            「環境の seed を動きの seed と別の値にしたら揺らす」にしなかった理由: salt の比較(10f)は環境の seed を
            固定して動きの seed だけを変えるので、salt ごとに天気が揺れて共通の乱数(CRN)が崩れる。

    Returns:
        ``RunResult``。
    """
    _call_args = dict(locals())  # 10d: 設定の指紋(先頭で引数だけを写す)
    # 〔Q13 (a′)〕渡さなかった倍率(None)を決めた値で写しに置く(設定の指紋も決めた値=予算を渡したランは前のまま 1.0)
    _call_args["l4_scale"] = resolve_l4_scale(l4_scale, budget)
    # 1-0 段 F: 組み立て・tick のループ・ランの終わりは engine.systems(状態の箱+系+進行役)。結果は HEAD と同じ。
    from shibuya.runtime.systems.conductor import conduct

    return conduct(_call_args)
