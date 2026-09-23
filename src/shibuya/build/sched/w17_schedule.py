"""W17 スケジュール生成(§1 W17・D-W17・決定台帳「母集団合成」⑦)。

入力: W16 ``w16_population.parquet``(種別・目的・年齢・性別・自宅/勤務/通学セル・方面・
      ``pool_layer``/``pool_index``)+ ペルソナプール(職業・シフト・来訪頻度・就寝)+
      W7 ``w7_plan_spec.parquet``(営業時間)+ W6 ``w6_poi.parquet``(業種)+
      W12 ``w12_generation_weights.parquet``(**時間帯カーブの代替**)。
出力: ``w17_prompts.jsonl``(段階が書く)→ [外で fleet_gen] → ``w17_responses*.jsonl``
      → ``w17_schedule.parquet``(agent_id・day・seq・start_min・end_min・activity_code・
      place_kind・target_cell)+ ``w17_gates.json``。

ゲート(§1 W17 行)
- **呼数=体数**(``n_prompts == n_agents``・repeat 1)。
- **修正率 < 20%**(段2 の強制修正で触った活動の割合・答申 Q4-2)。
- **PT 時間帯カーブとの JSD**(値の合格線は仕様書に無い=**報告のみ**+「raking で下がった」を
  機械検査する)。

**時間帯カーブの出所(expedient・昇格条件つき)**
    D-W17 は「PT 目的別時間帯カーブで raking」と書くが、§3 取得レーンのとおり
    **PT の時間帯別表は未取得**(表 d-1 は目的×手段×OD だけで時刻の次元を持たない)。
    そこで W12 の ``hour`` 重み(= 第12回大都市交通センサス time_dist_12・**2015 年**の
    目的別時刻分布を 2018/2021 総量へ移植したもの)を較正カーブに使う。
    **昇格条件 = PT 時間帯別表(e-Stat 同データセット内の別表)の取得**。

D-W14 の再確認: この表は**来街を抽選する装置ではない**。生成入力・較正としてのみ使い、
「渋谷に来るか」は各体の週次表(T0)→ T1 差分 → T2 の判断で決まる(U10 案A)。
"""

from __future__ import annotations

import array
import glob as _glob
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterable, Iterator, Sequence

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from shibuya.core.hashing import blake3_u64

from ..geo import common as C
from ..pop.w16_population import (
    KIND_COMMUTER,
    KIND_CREW,
    KIND_DISPATCHER,
    KIND_FOREIGN_VISITOR,
    KIND_NAMES,
    KIND_REGULAR_VISITOR,
    KIND_RESIDENT,
    KIND_STUDENT,
    KIND_VISITOR,
    KIND_WORKER,
    PURPOSE_NAMES,
)
from . import pool_facts as PF
from . import vocab as V

STAGE = "W17"
STAGE_VERSION = "1.2.0"  # 1.1.0 = 第1回パイロット後の改版 / 1.2.0 = 第2回後=日見出し形+構造化出力 regex(§4 登録簿)

# ---------------------------------------------------------------- 復号パラメータ(D-W17)
#: D-W17 (i)「モデル=T1(8B INT8)全件」。served-model-name は fleet_gen が解決するので記録用。
MODEL_HINT: Final[str] = "Qwen3-8B-INT8"
#: 温度(D-W17 (i)「温度 0.7」)。W14/W15(温度 0)と違い**多様性が目的**。
TEMPERATURE: Final[float] = 0.7
#: 生成回数。D-W17 に「2 回生成でバイト一致」の要求は無い(温度 0.7 なので成立しない)。
REPEAT: Final[int] = 1
#: 思考トークン(認知設計書 §1「T1 は思考 0」・U19)。
THINKING: Final[bool] = False
#: 生成上限[tok]。**第2回パイロット(344体・v2)で 318/344 が 560 で切れた**
#: (1 行 ≈19 tok・モデルは 1 日 12 行を書く)。v3 は ①**日見出し形**で行から曜日欄を外し
#: ②**構造化出力(regex)**で 1 日 4-5 行・7 日を機械的に強制する。
#: 35 行 × ≈15 tok + 見出し 7 行 ≈ 546 → 上限 600。
MAX_TOKENS: Final[int] = 600
#: 出力トークンの目標(ゲートは平均で見る。実測は fleet_gen の ``completion_tokens``)。
#: v3 の算術: 活動行 28-35 × ≈15 tok + 見出し 7 × ≈3 tok = **≈441-546**。
TOKEN_TARGET_MEAN: Final[int] = 550
#: 1 日あたりの活動行数(構造化出力 regex が**機械的に強制**する)。
LINES_PER_DAY_MIN: Final[int] = 4
LINES_PER_DAY_MAX: Final[int] = 5
#: 入力トークンの目標(共有 prefix を含む・報告のみ)。
PROMPT_TOKEN_TARGET: Final[int] = 700

#: seed = ``blake3(SEED_TAG ‖ agent_id) mod SEED_MOD``(D-W17 (i)「seed=hash(agent)」)。
#: 2^53−1 に丸めるのは JSON の数値として厳密に往復させるため(倍精度の整数範囲)。
SEED_TAG: Final[bytes] = b"shibuya.build.sched/W17/v1"
SEED_MOD: Final[int] = (1 << 53) - 1

# ---------------------------------------------------------------- ゲート閾値
#: 段2 修正率の上限(§1 W17 行「修正率<20%」)。
GATE_MODIFIED_RATE: Final[float] = 0.20
#: 応答が読めた体の割合の下限(自前・これを割ったら艦隊側の失敗を疑う)。
GATE_RESPONSE_RATE: Final[float] = 0.99
#: raking が動かせる活動の割合の**固定**上限(自前・**ablation/フォールバック用**)。
#: 本番は下の ``ADAPTIVE_MODIFIED_TARGET`` からの適応予算を使う。
RAKE_MAX_FRAC: Final[float] = 0.12
#: **適応予算の目標**: 修復ぶんを差し引いて、総修正率がこの値を超えないところまで raking する。
#: 出所= 設計ゲート(§1 W17「修正率<20%」)からの逆算で、1 ポイントの余裕を取った自前の値。
#: 本番第1回(390,067 体)は 修復だけで 9.2% だったため固定 12% だと 21.2% でゲートを割った。
ADAPTIVE_MODIFIED_TARGET: Final[float] = 0.19
#: 移動後に確保する最小の活動長[分](自前)。
MIN_ACT_MINUTES: Final[int] = 10
#: 1 日あたりの活動数の上限(自前・暴走出力の打ち切り)。
MAX_ACTS_PER_DAY: Final[int] = 8
#: 1 日あたりの活動数の下限(自前・**第1回パイロットで 23/300 が「就寝だけ」を書いた**
#: ことへの対処。これを割った日は骸格から隙間に補って計上する)。
MIN_ACTS_PER_DAY: Final[int] = 4
#: 就寝が 1 日にこれ未満なら骸格の就寝を足す[分](自前)。
MIN_SLEEP_MINUTES: Final[int] = 240
#: 営業していないとみなす開店率(自前・この時間帯に始まる店内活動は動かす)。
OPEN_SHARE_MIN: Final[float] = 0.05

#: 入力ファイル(``ctx.out`` にある前段の出力)。
INPUT_FILES: Final[tuple[str, ...]] = (
    "w16_population.parquet",
    "w7_plan_spec.parquet",
    "w6_poi.parquet",
    "w12_generation_weights.parquet",
)
#: プールの位置(``ctx.data`` 起点)。
POOL_DIR: Final[tuple[str, ...]] = ("persona_pool_v2",)

#: 出力ファイル名。
PROMPTS_NAME: Final[str] = "w17_prompts.jsonl"
RESPONSES_GLOB: Final[str] = "w17_responses*.jsonl"
SCHEDULE_NAME: Final[str] = "w17_schedule.parquet"
GATES_NAME: Final[str] = "w17_gates.json"

#: 未解決のセル(場所種別だけが決まっていて、セルはエンジンが経路・選好から決める)。
CELL_UNRESOLVED: Final[int] = -1


def estimate_tokens(text: str) -> int:
    """粗いトークン数見積り(``perception.channels.estimate_tokens`` と**同一規約の二重定義**)。

    層契約により build から perception を import しない(W14/W15 の例外は「凍結バイト=描画
    バイト」を守るためで、W17 の出力は知覚ブロックの文面ではないので例外を作らない)。
    """
    return max(1, len(text) // 2)


def agent_seed(agent_id: int) -> int:
    """``seed = blake3(SEED_TAG ‖ ":" ‖ agent_id) mod (2^53−1)``(D-W17 「seed=hash(agent)」)。

    Example:
        >>> agent_seed(0) == agent_seed(0)
        True
        >>> agent_seed(0) != agent_seed(1)
        True
    """
    return blake3_u64(SEED_TAG + b":" + str(int(agent_id)).encode("ascii")) % SEED_MOD


# ================================================================= プロンプト(fleet_gen 形式)
@dataclass(frozen=True)
class SchedPrompt:
    """1 呼ぶんのプロンプト(``tools/gen/fleet_gen.py`` の入力行)。

    ``build.lang.common.Prompt`` と**同形だが別実装**: あちらは温度 0・seed 固定・repeat 2 を
    クラス定数で焼いており、W17(温度 0.7・seed=hash(agent)・repeat 1)を表現できない。
    また ``build.lang.common`` を import すると perception まで引き込む(層契約の例外)。
    """

    id: str
    system: str
    user: str
    seed: int
    max_tokens: int = MAX_TOKENS
    #: vLLM の構造化出力(``structured_outputs: {"regex": …}``)。``fleet_gen`` が
    #: この欄を見て送る。**体ごとに違う**(事実に無い場所語を文法で排除するため)。
    regex: str = ""

    def to_json(self) -> dict[str, Any]:
        out = {
            "id": self.id,
            "system": self.system,
            "user": self.user,
            "max_tokens": int(self.max_tokens),
            "temperature": TEMPERATURE,
            "seed": int(self.seed),
            "repeat": REPEAT,
            "thinking": THINKING,
        }
        if self.regex:
            out["regex"] = self.regex
        return out


def prompt_bytes(prompts: Iterable[SchedPrompt]) -> Iterator[bytes]:
    """プロンプト列 → jsonl の行バイト(決定論・LF 固定・キー整列)。"""
    for p in prompts:
        yield C.canonical_json_bytes(p.to_json()) + b"\n"


def prompts_sha256(prompts: Sequence[SchedPrompt]) -> str:
    """プロンプト列の版ハッシュ(文面を変えたら値が変わる=改版の検出器)。"""
    return C.sha256_bytes(b"".join(prompt_bytes(prompts)))


# ================================================================= 種別別テンプレ(凍結)
#: 全種別で共有する system の頭(**vLLM の prefix キャッシュが効くよう先頭に置く**)。
SYSTEM_COMMON: Final[str] = "\n".join(
    (
        "あなたは生活時間調査の記録係です。与えられた事実から、その人の1週間(7日)の"
        "活動表を作ります。",
        "書式は2種類の行だけ:",
        "・曜日の見出し行 = d0 d1 d2 d3 d4 d5 d6 のどれか1つだけを書いた行"
        "(d0=月曜 d1=火曜 d2=水曜 d3=木曜 d4=金曜 d5=土曜 d6=日曜)。",
        "・活動行 = 「<開始HHMM>-<終了HHMM> <活動語> <場所語>」の3列を半角空白1つで区切る。",
        "例:",
        "d0",
        "0000-0700 就寝 自宅",
        "0700-0800 支度 自宅",
        "0800-0900 移動 職場",
        "0900-1800 勤務 職場",
        "1800-1900 食事 飲食店",
        "d1",
        "(以下 d6 まで同じ形で続ける)",
        "活動語は次の12語だけを使う: " + " ".join(V.ACTIVITY_WORDS),
        "場所語は次の12語だけを使う: " + " ".join(V.PLACE_WORDS),
        "規則:",
        f"1. d0 から d6 まで 7 日ぶんの見出し行を必ず書く。各日の活動行は"
        f"{LINES_PER_DAY_MIN}行から{LINES_PER_DAY_MAX}行。",
        "2. 時刻は4桁(0700)。1日は0000から2400。日をまたぐ就寝は "
        "「2300-0700 就寝 自宅」のように1行で書く(2行に分けない)。",
        "3. 各日に 就寝 と 支度 と 食事 と 移動(または 乗車)を必ず入れる。同じ活動を"
        "続けて2行書かない。書かない時間は自宅で過ごすものとして扱うので、在宅の時間を"
        "細切れに書かない。",
        "4. 与えられた勤務・通学・来訪の時間帯と曜日に従う。曜日ごとに少し違う日にする。",
        "5. 同じ日の活動行は時刻の昇順に並べ、時間帯を重ねない。",
        "6. 表以外は何も書かない。前置き・説明・記号・箇条書き・空行を書かない。"
        "行末に空白を置かない。",
    )
)

#: 種別ごとの 1 行(``SYSTEM_COMMON`` の後ろに足す)。索引=``AgentKind``。
SYSTEM_KIND_LINE: Final[tuple[str, ...]] = (
    # 0 通勤者
    "この人は渋谷の外に住み、渋谷の職場へ通う。通勤は 乗車 駅 と 移動 職場 で書き、"
    "帰りは 移動 駅 と 乗車 域外 で書く。自宅での就寝は 就寝 自宅 で書いてよい。"
    "休みの日も見出し行と活動行を書く(自宅と域外で過ごす)。",
    # 1 来街者
    "この人は渋谷に住んでも働いてもいない。渋谷へ来るのは来訪日だけで、その日は "
    "乗車 駅 で来て 乗車 域外 で帰る。**来訪日でない曜日は見出し行だけを書き、"
    "活動行を1行も書かない**。",
    # 2 従業者
    "この人は渋谷に住み、渋谷の職場へ通う。通勤は徒歩か短い移動で 移動 職場 と書く。",
    # 3 居住者
    "この人は渋谷に住んでいる。職場や学校が渋谷の外にあるときは、往復を 乗車 駅 と "
    "移動 域外 で書く。渋谷の外で働いていない人は街の中で1日を過ごす。",
    # 4 指令
    "この人は交代制の指令勤務に就く。勤務は指定の時間帯と曜日に置き、"
    "勤務のない日は自宅で過ごす。",
    # 5 通学者
    "この人は渋谷の外に住み、渋谷の学校へ通う。通学は 乗車 駅 と 移動 学校 で書き、"
    "帰りは 移動 駅 と 乗車 域外 で書く。",
    # 6 定期来街者
    "この人は渋谷に住んでも働いてもいないが、決まった曜日に渋谷へ来る。来訪日は "
    "乗車 駅 で来て 乗車 域外 で帰る。**来訪日でない曜日は見出し行だけを書き、"
    "活動行を1行も書かない**。",
    # 7 訪日来街者
    "この人は日本の外から渋谷を訪れる旅行者。渋谷にいるのは来訪日だけで、"
    "その日は 乗車 駅 で来て 乗車 域外 で帰る。**来訪日でない曜日は見出し行だけを書き、"
    "活動行を1行も書かない**。",
    # 8 乗務員
    "この人は鉄道・駅務・警備などの職務に就き、交代制で働く。勤務は指定の時間帯と曜日に"
    "置き、勤務のない日は休む。",
)
assert len(SYSTEM_KIND_LINE) == len(KIND_NAMES)


def system_prompt(kind: int) -> str:
    """種別 → 凍結 system プロンプト(``SYSTEM_COMMON`` + 種別 1 行)。"""
    return SYSTEM_COMMON + "\n" + SYSTEM_KIND_LINE[int(kind)]


def system_sha256() -> dict[str, str]:
    """種別別テンプレの凍結 SHA(D-W17 (ii)「プロンプト=種別別テンプレ凍結(SHA)」)。"""
    return {
        KIND_NAMES[k]: C.sha256_bytes(system_prompt(k).encode("utf-8"))
        for k in range(len(KIND_NAMES))
    }


# ================================================================= 個体の事実(SoA)
#: 種別ごとの既定の勤務/通学時間帯(expedient・プールに実値が無いときの埋め)。
DEFAULT_WORK_WINDOW: Final[dict[int, tuple[int, int]]] = {
    KIND_COMMUTER: (540, 1080),  # 9:00-18:00
    KIND_WORKER: (540, 1080),
    KIND_RESIDENT: (540, 1080),
    KIND_STUDENT: (510, 960),  # 8:30-16:00
    KIND_CREW: (360, 840),  # 早番 6:00-14:00(交代は seed で回す)
    KIND_DISPATCHER: (480, 1200),  # 8:00-20:00(12h 2 交代)
}
#: 学校段階 → 在校時間帯(expedient・公的な標準時程表は取得していない)。
SCHOOL_WINDOW: Final[dict[str, tuple[int, int]]] = {
    "保育所": (480, 1080),
    "幼稚園": (540, 840),
    "小学校": (510, 930),
    "中学校": (510, 990),
    "高校": (500, 1020),
    "大学": (540, 1080),
    "専門学校": (540, 1020),
    "学校": (510, 960),
}
#: 年齢 → 学校段階(``school_stage`` が空のとき・expedient)。
AGE_TO_STAGE: Final[tuple[tuple[int, str], ...]] = (
    (3, "保育所"), (6, "幼稚園"), (12, "小学校"), (15, "中学校"),
)
#: 学齢の上限(これ未満は必ず通学として facts に書く。第1回パイロットの
#: 「勤務・通学: なし」209/300 への対処)。
SCHOOL_AGE_MAX: Final[int] = 15
#: 職業名が**通学**を意味する語 → 学校段階(expedient)。
SCHOOL_OCCUPATIONS: Final[dict[str, str]] = {
    "未就学児": "保育所", "小学生": "小学校", "中学生": "中学校", "小中学生": "中学校",
    "高校生": "高校", "大学生": "大学", "専門学生": "専門学校", "学生": "学校",
}
#: 職業名が**無職**を意味する語(expedient・プールの `occupations` から拾った)。
NON_WORKING_OCCUPATIONS: Final[frozenset[str]] = frozenset(
    {"", "主婦・主夫", "年金生活者", "無職・求職", "無職", "路上生活者"}
)
#: この年齢以上で職業が ``NON_WORKING_OCCUPATIONS`` なら、勤務席があっても無職とみなす
#: (パイロット id=18「68歳 女 年金生活者」に 09:00-18:00 の勤務が付いていた=expedient)。
RETIREMENT_AGE: Final[int] = 65
#: 交代制の勤務開始(expedient・早番/中番/遅番)。
CREW_SHIFT_STARTS: Final[tuple[int, ...]] = (360, 840, 1320)
#: 指令の勤務開始(expedient・12h 2 交代)。
DISPATCH_SHIFT_STARTS: Final[tuple[int, ...]] = (480, 1200)
#: 職業名にこれを含むと夜勤扱い(expedient)。
NIGHT_MARKERS: Final[tuple[str, ...]] = ("夜間", "深夜")
#: 夜勤の時間帯(expedient)。``close`` は 1440 を超える(翌日へ跨ぐ)。
NIGHT_WINDOW: Final[tuple[int, int]] = (1_320, 1_800)  # 22:00-翌6:00
#: 既定の就寝時刻と睡眠長(expedient・プールに値が無いとき)。
DEFAULT_BEDTIME: Final[int] = 1_380  # 23:00
DEFAULT_SLEEP: Final[int] = 420

#: 来街種別(在圏が「来訪日だけ」の種別)。
VISITOR_KINDS: Final[tuple[int, ...]] = (
    KIND_VISITOR, KIND_REGULAR_VISITOR, KIND_FOREIGN_VISITOR,
)


@dataclass(frozen=True)
class AgentFacts:
    """W17 の生成・修復が使う個体の事実(行順=``w16_population`` の行順)。"""

    n: int
    agent_id: np.ndarray
    kind: np.ndarray
    purpose: np.ndarray
    age: np.ndarray
    sex: np.ndarray
    home_cell: np.ndarray
    work_cell: np.ndarray
    school_cell: np.ndarray
    direction_node: np.ndarray
    seed: np.ndarray
    work_open: np.ndarray
    work_close: np.ndarray
    work_days: np.ndarray
    duty_activity: np.ndarray  # ACT_WORK / ACT_SCHOOL / -1
    duty_outside: np.ndarray  # 勤務先/通学先が舞台の外(域外)か
    duty_stage: list[str]  # 通学の学校段階(勤務は "")
    visit_days: np.ndarray
    bed_min: np.ndarray
    sleep_min: np.ndarray
    pool: PF.PoolFacts = field(repr=False, default=None)  # type: ignore[assignment]

    def is_visitor(self) -> np.ndarray:
        return np.isin(self.kind, np.asarray(VISITOR_KINDS, dtype=self.kind.dtype))


def _weekday_from_seed(seed: int, n: int = 5) -> int:
    return int((seed >> 7) % n)


def _pick_days(seed: int, k: int) -> int:
    """seed から相異なる k 曜日を選ぶ(決定論・expedient)。"""
    mask = 0
    s = int(seed)
    picked = 0
    for _ in range(32):  # 逐次: 定数回
        if picked >= k:
            break
        d = (s >> (3 * picked + 5)) % 7
        if not (mask >> d) & 1:
            mask |= 1 << d
            picked += 1
        s = (s * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
    return mask


def build_facts(world_dir: Path, data_dir: Path) -> AgentFacts:
    """W16 母集団+プール素材 → ``AgentFacts``(決定論)。

    Note:
        逐次ループ宣言(P4): 体数ぶんのループ 1 本(勤務窓・来訪日の決定)。構築時 1 回。
    """
    world_dir = Path(world_dir)
    cols = C.read_parquet_columns(
        world_dir / "w16_population.parquet",
        ["agent_id", "kind", "purpose", "age", "sex", "home_cell", "work_cell",
         "school_cell", "direction_node", "pool_layer", "pool_index"],
    )
    n = len(cols["agent_id"])
    agent_id = np.asarray(cols["agent_id"], dtype=np.int64)
    kind = np.asarray(cols["kind"], dtype=np.int8)
    purpose = np.asarray(cols["purpose"], dtype=np.int8)
    work_cell = np.asarray(cols["work_cell"], dtype=np.int32)
    school_cell = np.asarray(cols["school_cell"], dtype=np.int32)
    home_cell_arr = np.asarray(cols["home_cell"], dtype=np.int32)
    pool = PF.read_facts(
        Path(data_dir).joinpath(*POOL_DIR), cols["pool_layer"], cols["pool_index"]
    )

    seed = np.fromiter((agent_seed(int(a)) for a in agent_id), dtype=np.int64, count=n)
    work_open = np.full(n, -1, dtype=np.int16)
    work_close = np.full(n, -1, dtype=np.int16)
    work_days = np.zeros(n, dtype=np.uint8)
    duty_activity = np.full(n, -1, dtype=np.int8)
    duty_outside = np.zeros(n, dtype=bool)
    duty_stage: list[str] = [""] * n
    visit_days = np.zeros(n, dtype=np.uint8)
    occupation = pool.col("occupation")
    school_stage = pool.col("school_stage")
    cadence = pool.col("visit_cadence")
    age = np.asarray(cols["age"], dtype=np.uint8)

    for i in range(n):  # 逐次ループ宣言(P4): 体数ぶん・構築時 1 回
        k = int(kind[i])
        s = int(seed[i])
        if k in VISITOR_KINDS:
            if k == KIND_REGULAR_VISITOR:
                visit_days[i] = (
                    PF.WEEKDAY_MASK if cadence[i] == "school_day" else _pick_days(s, 2)
                )
            elif int(purpose[i]) == 2:  # 業務来街=平日
                visit_days[i] = 1 << _weekday_from_seed(s, 5)
            else:
                visit_days[i] = 1 << (s % 7)
            continue
        # --- 通学(学齢・学校セル・学生の職業名のいずれか)。**域外通学もここで書く** ---
        stage = school_stage[i] or SCHOOL_OCCUPATIONS.get(occupation[i], "")
        if not stage and int(age[i]) < SCHOOL_AGE_MAX:
            stage = next(s2 for lim, s2 in AGE_TO_STAGE if int(age[i]) < lim)
        if school_cell[i] >= 0 or stage:
            if not stage:
                stage = "学校"
            lo, hi = SCHOOL_WINDOW.get(stage, DEFAULT_WORK_WINDOW[KIND_STUDENT])
            work_open[i], work_close[i] = lo, hi
            work_days[i] = PF.WEEKDAY_MASK
            duty_activity[i] = V.ACT_SCHOOL
            duty_stage[i] = stage
            # 通学先が域外なのは**域外常住の体だけ**。舞台に住む子の通学先が空なのは
            # 「W16 の学校 POI に保育所/幼稚園が無い」からであって域外通学ではない
            # (勤務は逆: 席の無い住民は W16 の定義どおり域外通勤)。
            duty_outside[i] = school_cell[i] < 0 and home_cell_arr[i] < 0
            continue
        # --- 無職(職業名が無職を意味する。65 歳以上は勤務席があっても無職)---
        if occupation[i] in NON_WORKING_OCCUPATIONS and (
            work_cell[i] < 0 or int(age[i]) >= RETIREMENT_AGE
        ):
            continue
        # --- 勤務。**勤務席が無い住民は「域外勤務」として必ず書く**(パイロットで
        #     「勤務・通学: なし」の体が 7 日とも就寝だけを書いた)---
        duty_activity[i] = V.ACT_WORK
        duty_outside[i] = work_cell[i] < 0
        if k == KIND_CREW:
            start = CREW_SHIFT_STARTS[s % len(CREW_SHIFT_STARTS)]
            hours = int(pool.duty_hours[i]) if pool.duty_hours[i] > 0 else 8
            work_open[i], work_close[i] = start, start + hours * 60
            days = int(pool.duty_days[i]) or PF.ALL_DAYS_MASK
            work_days[i] = days & ~_pick_days(s >> 11, 2)  # 交代2=週2日の休み
        elif k == KIND_DISPATCHER:
            start = DISPATCH_SHIFT_STARTS[s % len(DISPATCH_SHIFT_STARTS)]
            work_open[i], work_close[i] = start, start + 720
            work_days[i] = PF.ALL_DAYS_MASK & ~_pick_days(s >> 11, 3)
        elif any(m in occupation[i] for m in NIGHT_MARKERS):
            work_open[i], work_close[i] = NIGHT_WINDOW
            work_days[i] = int(pool.work_days[i]) or PF.WEEKDAY_MASK
        else:
            lo = int(pool.shift_open[i])
            hi = int(pool.shift_close[i])
            if lo < 0 or hi <= lo:
                lo, hi = DEFAULT_WORK_WINDOW.get(k, (540, 1080))
            work_open[i], work_close[i] = lo, hi
            work_days[i] = int(pool.work_days[i]) or PF.WEEKDAY_MASK

    bed = np.where(pool.bedtime_min >= 0, pool.bedtime_min, DEFAULT_BEDTIME).astype(np.int16)
    sleep = np.where(pool.sleep_min > 0, pool.sleep_min, DEFAULT_SLEEP).astype(np.int16)
    return AgentFacts(
        n=n,
        agent_id=agent_id,
        kind=kind,
        purpose=purpose,
        age=age,
        sex=np.asarray(cols["sex"], dtype=np.int8),
        home_cell=home_cell_arr,
        work_cell=work_cell,
        school_cell=school_cell,
        direction_node=np.asarray(cols["direction_node"], dtype=np.int32),
        seed=seed,
        work_open=work_open,
        work_close=work_close,
        work_days=work_days,
        duty_activity=duty_activity,
        duty_outside=duty_outside,
        duty_stage=duty_stage,
        visit_days=visit_days,
        bed_min=bed,
        sleep_min=sleep,
        pool=pool,
    )


# ================================================================= user プロンプト
_SEX_WORDS: Final[tuple[str, ...]] = ("男", "女")
#: 勤務も通学も来訪も無い体(=無職)の 1 行。**この行が出るのは無職だけ**。
NO_DUTY_LINE: Final[str] = "勤務・通学: なし(無職・渋谷の街の中で過ごす。域外へは出ない)"
#: user プロンプトで「予定」を表す行の頭(テストがこの 4 つのどれかを必ず要求する)。
DUTY_LINE_PREFIXES: Final[tuple[str, ...]] = ("勤務: ", "通学: ", "来訪日: ", NO_DUTY_LINE)


def _days_word(mask: int) -> str:
    if mask == 0:
        return "なし"
    if mask == PF.ALL_DAYS_MASK:
        return "毎日"
    if mask == PF.WEEKDAY_MASK:
        return "月火水木金"
    return "".join(V.DAY_WORDS[d][0] for d in range(7) if (mask >> d) & 1)


def _hm(minute: int) -> str:
    m = int(minute) % 1440
    return f"{m // 60:02d}{m % 60:02d}"


def user_prompt(f: AgentFacts, i: int) -> str:
    """個体 ``i`` の user プロンプト(決定論・**セル ID は載せない**=答申 Q4-2)。"""
    p = f.pool
    sex = _SEX_WORDS[int(f.sex[i])] if 0 <= int(f.sex[i]) < 2 else "不明"
    # 職業名が空なのは素材の無い体(指令 24 体)だけ。「無職」と書くと事実が歪むので
    # 役割 → 配置 → 種別名の順で埋める。
    occ = (
        p.col("occupation")[i] or p.col("role")[i] or p.col("post")[i]
        or KIND_NAMES[int(f.kind[i])]
    )
    lines = [f"{int(f.age[i])}歳 {sex} {occ}"]

    if int(f.home_cell[i]) >= 0:
        lines.append("自宅: 渋谷")
    else:
        line = p.col("residence_line")[i]
        lines.append("自宅: 域外" + (f"({line})" if line else ""))

    # **勤務・通学・来訪のどれか 1 行を必ず入れる**(第1回パイロットで
    # 「勤務・通学: なし」だった 209/300 のうち 23 体が 7 日とも就寝だけを書いた)。
    # 「なし」が出るのは**無職の体だけ**= ``tests`` が機械検査する。
    duty = int(f.duty_activity[i])
    where = "渋谷の外(域外)" if bool(f.duty_outside[i]) else "渋谷"
    if duty == V.ACT_WORK:
        lines.append(
            f"勤務: {where} {_days_word(int(f.work_days[i]))} "
            f"{_hm(int(f.work_open[i]))}-{_hm(int(f.work_close[i]))}"
            + ("(夜勤)" if int(f.work_close[i]) > 1440 else "")
        )
    elif duty == V.ACT_SCHOOL:
        stage = f.duty_stage[i] or p.col("school_stage")[i] or "学校"
        lines.append(
            f"通学: {stage} {where} {_days_word(int(f.work_days[i]))} "
            f"{_hm(int(f.work_open[i]))}-{_hm(int(f.work_close[i]))}"
        )
    elif int(f.visit_days[i]):
        purpose = p.col("visit_purpose")[i] or PURPOSE_NAMES[int(f.purpose[i])]
        lines.append(f"来訪日: {_days_word(int(f.visit_days[i]))} 目的: {purpose}")
    else:
        lines.append(NO_DUTY_LINE)

    if int(f.visit_days[i]) and duty >= 0:  # 職務も来訪もある体(現状は出ない)
        purpose = p.col("visit_purpose")[i] or PURPOSE_NAMES[int(f.purpose[i])]
        lines.append(f"来訪日: {_days_word(int(f.visit_days[i]))} 目的: {purpose}")
    lines.append(f"就寝: {_hm(int(f.bed_min[i]))}ごろ 睡眠{int(f.sleep_min[i])}分")
    lines.append("7日の活動表を書く。")
    return "\n".join(lines)


# ---------------------------------------------------------------- 構造化出力(regex)
def place_set(f: AgentFacts, i: int) -> tuple[str, ...]:
    """その体が**書いてよい場所語**(事実にない場所を regex で排除する)。

    第2回パイロットで**無職の住民が全活動を「域外」で書いた**ため、固有名詞検査の代わりに
    「事実にない場所語は文法で出せない」を構造で強制する(D-W18 の捏造検査と同じ発想)。

    規則(自前・登録簿へ)
      - ``域外``: 域外常住(``home_cell < 0``)・域外へ通う(``duty_outside``)・来街種別
        のいずれかのときだけ入れる。**区内で完結する体(無職の住民・区内勤務/通学の住民)
        からは外す**。
      - ``職場``: 勤務席がある(``work_cell >= 0``)ときだけ。無いときは代わりに ``域外``。
      - ``学校``: 通学先セルがある(``school_cell >= 0``)ときだけ。
      - 残り 9 語(自宅・駅・飲食店・物販店・公園・娯楽施設・宿泊施設・医療施設・路上)は
        常に許す。``自宅``は域外常住でも「自宅=舞台の外の家」として書けてよい
        (``target_cell`` は ``home_cell`` = −1 のまま未解決になる)。
    """
    outside = (
        int(f.home_cell[i]) < 0 or bool(f.duty_outside[i]) or int(f.visit_days[i]) != 0
    )
    drop = set()
    if not outside:
        drop.add(V.PLACE_WORDS[V.PLACE_OUTSIDE])
    if int(f.work_cell[i]) < 0:
        drop.add(V.PLACE_WORDS[V.PLACE_WORK])
    if int(f.school_cell[i]) < 0:
        drop.add(V.PLACE_WORDS[V.PLACE_SCHOOL])
    return tuple(w for w in V.PLACE_WORDS if w not in drop)


def prompt_regex(f: AgentFacts, i: int) -> str:
    """vLLM の構造化出力(``structured_outputs.regex``)に渡す正規表現。

    形: ``d0(?:\\n<行>){4,5}\\nd1(?:\\n<行>){4,5}…\\nd6(?:\\n<行>){4,5}\\n?``。
    ``<行>`` = ``HHMM-HHMM <活動語> <場所語>``。活動語は 12 語の選択、場所語は
    ``place_set`` の選択。**来街種別の来訪日でない曜日は活動行 0 行**(見出しだけ)。

    これで「形式違反」「行末空白」「語彙外」「事実にない場所」「1 日の行数超過」「日の欠落」が
    **生成の段階で起こらなくなる**(第2回パイロットで 318/344 が上限で切れ、無職の住民が
    全活動を域外で書いた問題への対処)。パーサ側の検査は互換のためそのまま残す。
    """
    acts = "|".join(V.ACTIVITY_WORDS)
    places = "|".join(place_set(f, i))
    line = f"{V.TIME_PATTERN}-{V.TIME_PATTERN} (?:{acts}) (?:{places})"
    visit = int(f.visit_days[i])
    parts: list[str] = []
    for d in range(V.N_DAYS):
        if visit and not ((visit >> d) & 1):  # 来訪日でない日は見出しだけ
            parts.append(f"d{d}")
        else:
            parts.append(f"d{d}(?:\\n{line}){{{LINES_PER_DAY_MIN},{LINES_PER_DAY_MAX}}}")
    return "\\n".join(parts) + "\\n?"


def regex_summary(facts: AgentFacts) -> dict[str, Any]:
    """構造化出力 regex の版(ヘッダ ``notes``・登録簿用)。

    体ごとに regex が違う(場所語の集合と来訪日で変わる)ので、**種別ごとの代表 1 本**の
    SHA と、母集団全体で相異なる regex の本数を記録する。代表は「その種別で最初に現れる体」
    = 決定論。
    """
    by_kind: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for i in range(facts.n):  # 逐次: 体数ぶん(構築時 1 回)
        rx = prompt_regex(facts, i)
        seen.add(rx)
        name = KIND_NAMES[int(facts.kind[i])]
        if name not in by_kind:
            by_kind[name] = {
                "sha256": C.sha256_bytes(rx.encode("utf-8")),
                "chars": len(rx),
                "places": list(place_set(facts, i)),
            }
    return {
        "engine": "vLLM structured_outputs.regex",
        "n_distinct": len(seen),
        "by_kind": dict(sorted(by_kind.items())),
    }


def prompt_of(facts: AgentFacts, i: int) -> SchedPrompt:
    """行 ``i`` の 1 呼ぶんのプロンプト(決定論)。"""
    return SchedPrompt(
        id=str(int(facts.agent_id[i])),
        system=system_prompt(int(facts.kind[i])),
        user=user_prompt(facts, i),
        seed=int(facts.seed[i]),
        regex=prompt_regex(facts, i),
    )


def iter_prompts(
    facts: AgentFacts, *, shard: int = 0, n_shards: int = 1
) -> Iterator[SchedPrompt]:
    """``AgentFacts`` → プロンプト列(行順=母集団の行順・シャードは行の剰余で切る)。

    Note:
        逐次ループ宣言(P4): 体数ぶんのループ 1 本。構築時 1 回(I1 の外)。
    """
    if n_shards < 1 or not (0 <= shard < n_shards):
        raise ValueError("shard は 0..n_shards-1")
    for i in range(facts.n):
        if n_shards > 1 and (i % n_shards) != shard:
            continue
        yield prompt_of(facts, i)


def build_prompts(
    world_dir: str | Path,
    data_dir: str | Path,
    *,
    shard: int = 0,
    n_shards: int = 1,
    facts: AgentFacts | None = None,
) -> list[SchedPrompt]:
    """W16+プール → プロンプトの list(テスト・小規模用。実データは ``write_prompts``)。"""
    f = facts if facts is not None else build_facts(Path(world_dir), Path(data_dir))
    return list(iter_prompts(f, shard=shard, n_shards=n_shards))


def shard_name(shard: int, n_shards: int) -> str:
    """シャードのファイル名(``n_shards==1`` は素の ``w17_prompts.jsonl``)。"""
    if n_shards <= 1:
        return PROMPTS_NAME
    return f"w17_prompts.{shard}of{n_shards}.jsonl"


def write_prompts(
    out_dir: Path,
    facts: AgentFacts,
    *,
    shard: int = 0,
    n_shards: int = 1,
    rows: np.ndarray | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """プロンプト jsonl を**ストリーミングで**書く(39 万行をメモリに載せない)。

    Args:
        rows: 書く行(母集団の行索引)。``None`` でシャード規則に従い全件。
        name: 出力ファイル名。``None`` で ``shard_name(shard, n_shards)``。
    """
    path = Path(out_dir) / (name or shard_name(shard, n_shards))
    n_rows = 0
    tok_sum = 0
    tok_max = 0
    gen = (
        iter_prompts(facts, shard=shard, n_shards=n_shards)
        if rows is None
        else (prompt_of(facts, int(r)) for r in rows)
    )
    with open(path, "wb") as fh:
        for p in gen:
            fh.write(C.canonical_json_bytes(p.to_json()) + b"\n")
            n_rows += 1
            t = estimate_tokens(p.system) + estimate_tokens(p.user)
            tok_sum += t
            tok_max = max(tok_max, t)
    return {
        "path": path.name,
        "sha256": C.sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": n_rows,
        "prompt_tokens_mean": round(tok_sum / n_rows, 2) if n_rows else 0.0,
        "prompt_tokens_max": tok_max,
    }


# ---------------------------------------------------------------- パイロット標本
#: パイロット標本のファイル名(本番の ``w17_responses*.jsonl`` と**当たらない**名前)。
PILOT_PROMPTS_NAME: Final[str] = "w17_pilot_prompts.jsonl"
PILOT_RESPONSES_NAME: Final[str] = "w17_pilot_responses.jsonl"


def pilot_rows(facts: AgentFacts, per_kind: int) -> np.ndarray:
    """**種別ごとに ``per_kind`` 体**を決定論で抜いた行索引(昇順)。

    先頭から取ると W16 の並び(コホート単位の塊)に偏るので、``_mix64(agent_id)`` の
    小さい順に取る=**seed 固定・母集団全体に散る**標本。種別の在庫が ``per_kind`` に
    満たないときはある分だけ取る。

    Note:
        第1回パイロット(先頭 300 体= 全員住民)で種別横断の検査ができなかったことへの対処。
    """
    if per_kind <= 0:
        raise ValueError("per_kind は 1 以上")
    key = _mix64(facts.agent_id.astype(np.uint64))
    picked: list[np.ndarray] = []
    for k in range(len(KIND_NAMES)):  # 逐次: 種別数(9)
        rows = np.flatnonzero(facts.kind == k)
        if rows.size == 0:
            continue
        order = np.argsort(key[rows], kind="stable")
        picked.append(rows[order[: min(per_kind, rows.size)]])
    return np.sort(np.concatenate(picked)) if picked else np.zeros(0, dtype=np.int64)


def write_pilot_prompts(out_dir: Path, facts: AgentFacts, per_kind: int) -> dict[str, Any]:
    """種別ごとに ``per_kind`` 体のパイロット用プロンプト jsonl を書く。"""
    rows = pilot_rows(facts, per_kind)
    rec = write_prompts(out_dir, facts, rows=rows, name=PILOT_PROMPTS_NAME)
    counts: dict[str, int] = {}
    for k in np.asarray(facts.kind)[rows].tolist():
        counts[KIND_NAMES[int(k)]] = counts.get(KIND_NAMES[int(k)], 0) + 1
    rec["per_kind"] = per_kind
    rec["kinds"] = dict(sorted(counts.items()))
    return rec


# ================================================================= 較正カーブ・営業時間
def hour_curves(world_dir: Path) -> dict[str, np.ndarray]:
    """W12 の hour 重み → PT 目的別の 24 時間カーブ(和 1)。**expedient**(冒頭 docstring)。"""
    cols = C.read_parquet_columns(
        Path(world_dir) / "w12_generation_weights.parquet", ["purpose", "hour", "weight"]
    )
    out: dict[str, np.ndarray] = {}
    for p, h, w in zip(cols["purpose"], cols["hour"], cols["weight"]):
        vec = out.setdefault(str(p), np.zeros(24, dtype=np.float64))
        vec[int(h) % 24] += float(w)
    for p, vec in out.items():
        s = vec.sum()
        if s > 0:
            out[p] = vec / s
    return out


#: 活動語コード → PT 目的(raking の対象。載っていない活動は raking しない)。
ACTIVITY_TO_PT_PURPOSE: Final[dict[int, str]] = {
    V.ACT_WORK: "自宅－勤務",
    V.ACT_SCHOOL: "自宅－通学",
    V.ACT_MEAL: "私事",
    V.ACT_SHOP: "私事",
    V.ACT_LEISURE: "私事",
    V.ACT_SOCIAL: "私事",
    V.ACT_ERRAND: "自宅－私事",
}

#: POI の cat/subcat → 場所種別(営業エンベロープの集計キー)。
CAT_TO_PLACE: Final[dict[str, int]] = {
    "food": V.PLACE_FOOD,
    "nightlife": V.PLACE_FOOD,
    "shop": V.PLACE_SHOP,
    "service": V.PLACE_SHOP,
    "office": V.PLACE_WORK,
    "hotel": V.PLACE_HOTEL,
    "school": V.PLACE_SCHOOL,
    "education": V.PLACE_SCHOOL,
    "leisure": V.PLACE_LEISURE,
    "hall": V.PLACE_LEISURE,
    "attraction": V.PLACE_LEISURE,
    "cinema": V.PLACE_LEISURE,
}
SUBCAT_TO_PLACE: Final[dict[str, int]] = {
    # **公園**(W6 subcat 改訂 2026-09-17): 改訂前は公園 POI が cat=leisure のまま
    # PLACE_LEISURE(娯楽施設)に潰れ、場所語 12 語のうち「公園」へ写る POI が 0 件だった
    # (語彙の孤児・答申 v2-hobby-preference-research.md §5-3 (4))。subcat=park を
    # PLACE_PARK に写すのがこの改訂の本体。PLACE_PARK は ENVELOPE_PLACES に無いので
    # 営業エンベロープは掛からない(公園に開店時刻は無い)。
    "park": V.PLACE_PARK,
    "convenience": V.PLACE_SHOP,
    "love_hotel": V.PLACE_HOTEL,
    "hospital": V.PLACE_CLINIC,
    "karaoke": V.PLACE_LEISURE,
    "club": V.PLACE_LEISURE,
    "pachinko": V.PLACE_LEISURE,
    "arcade": V.PLACE_LEISURE,
    "sauna": V.PLACE_LEISURE,
    "net_cafe": V.PLACE_LEISURE,
    "childcare": V.PLACE_SCHOOL,
}
#: 営業エンベロープを掛ける場所種別(店内の活動だけ・自宅/駅/路上/公園は掛けない)。
ENVELOPE_PLACES: Final[tuple[int, ...]] = (
    V.PLACE_FOOD, V.PLACE_SHOP, V.PLACE_LEISURE, V.PLACE_HOTEL, V.PLACE_CLINIC,
)


def open_share(world_dir: Path) -> np.ndarray:
    """W7+W6 → ``(場所種別, 曜日, 時)`` の開店率(その時間帯に開いている POI の割合)。

    D-W17 の「PlanSpec 内へ丸め」の店側の実装(答申 Q4-2 段2(d)「閉店中の飲食ブロックを削る」)。
    **expedient**: 「開いている店が 5% 未満の時間帯は営業していないとみなす」という閾値は自前。
    """
    poi = C.read_parquet_columns(
        Path(world_dir) / "w6_poi.parquet", ["poi_id", "cat", "subcat"]
    )
    plan = C.read_parquet_columns(
        Path(world_dir) / "w7_plan_spec.parquet", ["poi_id", "content"]
    )
    content_of = {str(p): str(c) for p, c in zip(plan["poi_id"], plan["content"])}
    counts = np.zeros((len(V.PLACE_WORDS), 7, 24), dtype=np.float64)
    totals = np.zeros(len(V.PLACE_WORDS), dtype=np.float64)
    for pid, cat, subcat in zip(poi["poi_id"], poi["cat"], poi["subcat"]):
        place = SUBCAT_TO_PLACE.get(str(subcat), CAT_TO_PLACE.get(str(cat), -1))
        if place < 0:
            continue
        totals[place] += 1.0
        try:
            days = json.loads(content_of.get(str(pid), "[]"))
        except (TypeError, ValueError):
            continue
        if len(days) != 7:
            continue
        for d, intervals in enumerate(days):
            for a, b in intervals:
                lo, hi = int(a) // 60, min(24, (int(b) + 59) // 60)
                if hi > lo:
                    counts[place, d, lo:hi] += 1.0
    share = np.zeros_like(counts)
    nz = totals > 0
    share[nz] = counts[nz] / totals[nz, None, None]
    return share


# ================================================================= 骸格スケジュール
def skeleton_day(f: AgentFacts, i: int, d: int) -> list[V.Act]:
    """骸格スケジュールの **1 日ぶん**(全て expedient)。

    使い道は 2 つ: ①応答が全滅した体の埋め(``skeleton``)②**1 日の活動が
    ``MIN_ACTS_PER_DAY`` に満たない日の穴埋め**(``_fill_day``・第1回パイロットで
    「就寝だけ」の日が多発したことへの対処)。

    Note:
        「実データに寄せる意図はない」——``agents.schedule`` の mock 日課と同じ位置づけで、
        **この体は LLM 生成が失敗した**ことをゲート(骸格率・underfill 件数)で見えるように
        するための埋め。
    """
    s = int(f.seed[i])
    jit = (s >> 17) % 41 - 20  # ±20 分(決定論)
    bed = int(f.bed_min[i])
    sleep = int(f.sleep_min[i])
    wake = (bed + sleep) % 1440
    duty = int(f.duty_activity[i])
    acts: list[V.Act] = []
    home_in = int(f.home_cell[i]) >= 0

    if int(f.visit_days[i]):  # 来街者: 来訪日だけ入退場
        if not (int(f.visit_days[i]) >> d) & 1:
            return []
        t0 = 600 + jit
        acts.append(V.Act(d, t0, t0 + 30, V.ACT_RIDE, V.PLACE_STATION))
        acts.append(V.Act(d, t0 + 30, t0 + 120, V.ACT_SHOP, V.PLACE_SHOP))
        acts.append(V.Act(d, t0 + 120, t0 + 180, V.ACT_MEAL, V.PLACE_FOOD))
        acts.append(V.Act(d, t0 + 180, t0 + 240, V.ACT_LEISURE, V.PLACE_LEISURE))
        acts.append(V.Act(d, t0 + 240, t0 + 270, V.ACT_RIDE, V.PLACE_OUTSIDE))
        return [a for a in acts if a.end > a.start]
    working = duty >= 0 and (int(f.work_days[i]) >> d) & 1
    if wake > 0:
        acts.append(V.Act(d, 0, wake, V.ACT_SLEEP, V.PLACE_HOME))
    if working:
        lo = max(wake + 30, min(int(f.work_open[i]), 1380))
        hi = min(int(f.work_close[i]), 1440)
        if hi <= lo:
            hi = min(1440, lo + 240)
        place = V.PLACE_SCHOOL if duty == V.ACT_SCHOOL else V.PLACE_WORK
        acts.append(V.Act(d, wake, min(lo, wake + 45), V.ACT_PREP, V.PLACE_HOME))
        acts.append(V.Act(d, min(lo, wake + 45), lo, V.ACT_MOVE, V.PLACE_STATION))
        acts.append(V.Act(d, lo, hi, duty, place))
        back = min(1440, hi + 45)
        acts.append(V.Act(d, hi, back, V.ACT_MOVE, V.PLACE_HOME if home_in
                          else V.PLACE_OUTSIDE))
        if back < 1440:
            acts.append(V.Act(d, back, 1440, V.ACT_REST, V.PLACE_HOME))
    else:
        acts.append(V.Act(d, wake, min(1440, wake + 60), V.ACT_PREP, V.PLACE_HOME))
        mid = min(1400, wake + 240)
        acts.append(V.Act(d, min(1440, wake + 60), mid, V.ACT_REST, V.PLACE_HOME))
        acts.append(V.Act(d, mid, min(1440, mid + 60), V.ACT_MEAL, V.PLACE_FOOD))
        if mid + 60 < 1440:
            acts.append(V.Act(d, min(1440, mid + 60), 1440, V.ACT_REST, V.PLACE_HOME))
    return [a for a in acts if a.end > a.start]


def skeleton(f: AgentFacts, i: int) -> list[V.Act]:
    """骸格スケジュールの 7 日ぶん(``skeleton_day`` を曜日ごとに)。"""
    out: list[V.Act] = []
    for d in range(V.N_DAYS):  # 逐次: 7 回
        out.extend(skeleton_day(f, i, d))
    return out


# ================================================================= 整合修復(段2)
@dataclass
class RepairCounters:
    """修復規則ごとの適用件数(ゲート json へ)。"""

    counts: dict[str, int] = field(default_factory=dict)

    def bump(self, rule: str, n: int = 1) -> None:
        if n:
            self.counts[rule] = self.counts.get(rule, 0) + n


def _fill_day(
    acts: list[V.Act], flags: list[bool], f: AgentFacts, i: int, day: int, ctr: RepairCounters
) -> tuple[list[V.Act], list[bool]]:
    """1 日の活動が ``MIN_ACTS_PER_DAY`` に満たないとき、骸格から**隙間に入る分だけ**足す。

    第1回パイロット(300 体)で **23/300 が 7 日とも「就寝」だけ**を書いたことへの対処
    (規則 3「書かない時間は自宅」が就寝だけの退化を許してしまった)。LLM が書いた活動は
    残し、空いている時間帯に骸格の活動を差し込む。足した活動は**全て修正として計上**する。
    """
    if len(acts) >= MIN_ACTS_PER_DAY:
        return acts, flags
    out, fl = list(acts), list(flags)
    added = 0
    for c in skeleton_day(f, i, day):  # 逐次: 骸格の 1 日ぶん(最大 6)
        if len(out) >= MIN_ACTS_PER_DAY:
            break
        pos = 0
        while pos < len(out) and out[pos].start < c.start:
            pos += 1
        lo = out[pos - 1].end if pos > 0 else 0
        hi = out[pos].start if pos < len(out) else V.MINUTES_PER_DAY
        s, e = max(c.start, lo), min(c.end, hi)
        if e - s < MIN_ACT_MINUTES:
            continue
        out.insert(pos, V.Act(day, s, e, c.activity, c.place))
        fl.insert(pos, True)
        added += 1
    if added:
        ctr.bump("day_underfilled", added)
    return out, fl


def repair_day(
    acts: list[V.Act], f: AgentFacts, i: int, day: int, share: np.ndarray, ctr: RepairCounters
) -> tuple[list[V.Act], list[bool], int]:
    """1 日ぶんの活動を整合させる。返り値=(修復後, 行ごとの修正フラグ, 捨てた件数)。

    規則(この順・全て自前=登録簿へ)
      1. 範囲外(0-1440 の外)を切り、長さ 0 以下を捨てる。
      2. 開始時刻の昇順に並べ、重なりを後続の開始をずらして解く(長さ 0 になったら捨てる)。
      3. 1 日 ``MAX_ACTS_PER_DAY`` 件を超えたら短い活動から捨てる。
      4. 勤務/通学は本人の勤務窓へ丸める。勤務日でない日の勤務/通学は休憩(自宅)へ落とす。
      5. 店内の活動(飲食店・物販店・娯楽施設・宿泊施設・医療施設)は、開店率が
         ``OPEN_SHARE_MIN`` 未満の時間帯に始まっていたら同じ日の最寄りの開店時間帯へ動かす。
      6. 来街者は来訪日だけを残し(来訪日でない日は空)、入場と退場を必ず持たせる。
      7. 自宅が街にある体は 1 日 ``MIN_SLEEP_MINUTES`` 以上の就寝を持つ(足りなければ足す)。
      8. 1 日の活動が ``MIN_ACTS_PER_DAY`` に満たない日は骸格から隙間に補う(``_fill_day``)。

    「修正フラグ」= その活動が LLM の書いたものから動いた/足されたこと。捨てた件数と
    合わせて段2 修正率(答申 Q4-2)の分子になる。
    """
    dropped = 0
    out: list[V.Act] = []
    flags: list[bool] = []
    for a in acts:  # 1. 範囲
        s = max(0, min(V.MINUTES_PER_DAY, a.start))
        e = max(0, min(V.MINUTES_PER_DAY, a.end))
        if e - s < 1:
            ctr.bump("out_of_range")
            dropped += 1
            continue
        moved = (s, e) != (a.start, a.end)
        if moved:
            ctr.bump("clamped")
        out.append(V.Act(day, s, e, a.activity, a.place))
        flags.append(moved)

    idx = sorted(range(len(out)), key=lambda j: (out[j].start, out[j].end))
    fixed: list[V.Act] = []
    ff: list[bool] = []
    for j in idx:  # 2. 重なり
        a, fl = out[j], flags[j]
        if fixed and a.start < fixed[-1].end:
            s = fixed[-1].end
            if a.end - s < 1:
                ctr.bump("overlap_dropped")
                dropped += 1
                continue
            ctr.bump("overlap_shifted")
            a, fl = V.Act(day, s, a.end, a.activity, a.place), True
        fixed.append(a)
        ff.append(fl)

    if len(fixed) > MAX_ACTS_PER_DAY:  # 3. 上限
        keep = sorted(
            sorted(range(len(fixed)), key=lambda j: -(fixed[j].end - fixed[j].start))[
                :MAX_ACTS_PER_DAY
            ]
        )
        ctr.bump("too_many", len(fixed) - len(keep))
        dropped += len(fixed) - len(keep)
        fixed = [fixed[j] for j in keep]
        ff = [ff[j] for j in keep]

    if int(f.visit_days[i]):  # 6. 来街者
        if not (int(f.visit_days[i]) >> day) & 1:
            if fixed:
                ctr.bump("visitor_non_visit_day", len(fixed))
                dropped += len(fixed)
            return [], [], dropped
        keep = [
            j for j, a in enumerate(fixed)
            if a.activity != V.ACT_SLEEP or a.place == V.PLACE_HOTEL
        ]
        dropped += len(fixed) - len(keep)
        fixed = [fixed[j] for j in keep]
        ff = [ff[j] for j in keep]
        fixed, ff = _fill_day(fixed, ff, f, i, day, ctr)  # 来訪日が薄すぎる分を補う
        if not fixed:
            return [], [], dropped
        if fixed[0].activity != V.ACT_RIDE:
            s = max(0, fixed[0].start - 30)
            if s < fixed[0].start:
                fixed.insert(0, V.Act(day, s, fixed[0].start, V.ACT_RIDE, V.PLACE_STATION))
                ff.insert(0, True)
                ctr.bump("visitor_entry_added")
        if fixed[-1].place != V.PLACE_OUTSIDE:
            e = min(V.MINUTES_PER_DAY, fixed[-1].end + 30)
            if e > fixed[-1].end:
                fixed.append(V.Act(day, fixed[-1].end, e, V.ACT_RIDE, V.PLACE_OUTSIDE))
                ff.append(True)
                ctr.bump("visitor_exit_added")
        return fixed, ff, dropped

    work_day = (int(f.work_days[i]) >> day) & 1
    lo, hi = int(f.work_open[i]), min(V.MINUTES_PER_DAY, int(f.work_close[i]))
    result: list[V.Act] = []
    rf: list[bool] = []
    for a, fl in zip(fixed, ff):
        if a.activity in (V.ACT_WORK, V.ACT_SCHOOL):  # 4. 勤務窓
            if not work_day or lo < 0:
                ctr.bump("duty_off_day")
                result.append(V.Act(day, a.start, a.end, V.ACT_REST, V.PLACE_HOME))
                rf.append(True)
                continue
            s, e = max(a.start, lo), min(a.end, hi)
            if e - s < MIN_ACT_MINUTES:
                s, e = lo, max(lo + MIN_ACT_MINUTES, min(hi, lo + (a.end - a.start)))
            if (s, e) != (a.start, a.end):
                ctr.bump("duty_clamped")
                fl = True
            result.append(V.Act(day, s, e, a.activity, a.place))
            rf.append(fl)
            continue
        if a.place in ENVELOPE_PLACES:  # 5. 営業エンベロープ
            h = a.start // 60
            if share[a.place, day].sum() > 0 and share[a.place, day, h] < OPEN_SHARE_MIN:
                openh = np.flatnonzero(share[a.place, day] >= OPEN_SHARE_MIN)
                if openh.size == 0:
                    ctr.bump("closed_dropped")
                    dropped += 1
                    continue
                nh = int(openh[np.argmin(np.abs(openh - h))])
                dur = a.end - a.start
                s = min(V.MINUTES_PER_DAY - MIN_ACT_MINUTES, nh * 60 + a.start % 60)
                result.append(
                    V.Act(day, s, min(V.MINUTES_PER_DAY, s + dur), a.activity, a.place)
                )
                rf.append(True)
                ctr.bump("closed_moved")
                continue
        result.append(a)
        rf.append(fl)

    idx = sorted(range(len(result)), key=lambda j: (result[j].start, result[j].end))
    merged: list[V.Act] = []
    mf: list[bool] = []
    for j in idx:  # 4/5 で作った重なりを解き直す
        a, fl = result[j], rf[j]
        if merged and a.start < merged[-1].end:
            s = merged[-1].end
            if a.end - s < 1:
                dropped += 1
                continue
            a, fl = V.Act(day, s, a.end, a.activity, a.place), True
        merged.append(a)
        mf.append(fl)

    merged, mf = _fill_day(merged, mf, f, i, day, ctr)  # 8. 薄すぎる日を骸格で補う

    if int(f.home_cell[i]) >= 0:  # 7. 就寝
        slept = sum(a.end - a.start for a in merged if a.activity == V.ACT_SLEEP)
        if slept < MIN_SLEEP_MINUTES:
            first = merged[0].start if merged else V.MINUTES_PER_DAY
            if first >= MIN_ACT_MINUTES:
                merged.insert(0, V.Act(day, 0, first, V.ACT_SLEEP, V.PLACE_HOME))
                mf.insert(0, True)
                ctr.bump("sleep_added")
    return merged, mf, dropped


def repair(
    acts: list[V.Act], f: AgentFacts, i: int, share: np.ndarray, ctr: RepairCounters
) -> tuple[list[V.Act], list[bool], int]:
    """7 日ぶんの修復(``repair_day`` を曜日ごとに)。"""
    by_day: list[list[V.Act]] = [[] for _ in range(V.N_DAYS)]
    for a in acts:
        if 0 <= a.day < V.N_DAYS:
            by_day[a.day].append(a)
    out: list[V.Act] = []
    flags: list[bool] = []
    dropped = 0
    for d in range(V.N_DAYS):
        got, fl, dr = repair_day(by_day[d], f, i, d, share, ctr)
        out.extend(got)
        flags.extend(fl)
        dropped += dr
    return out, flags, dropped


# ================================================================= raking(段2 較正)
def jensen_shannon(p: np.ndarray, q: np.ndarray) -> float:
    """Jensen-Shannon divergence(底 2・0..1)。両方 0 の成分は 0 として扱う。"""
    p = np.asarray(p, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)
    ps, qs = p.sum(), q.sum()
    if ps <= 0 or qs <= 0:
        return 0.0
    p, q = p / ps, q / qs
    m = 0.5 * (p + q)

    def _kl(a: np.ndarray) -> float:
        ok = a > 0
        return float(np.sum(a[ok] * np.log2(a[ok] / m[ok])))

    return max(0.0, 0.5 * _kl(p) + 0.5 * _kl(q))


def _mix64(x: np.ndarray) -> np.ndarray:
    """splitmix64 の最終混合(決定論・ベクトル化)。

    raking の並べ替えキーに使う。目的は **ID 順のバイアスを断つこと**だけなので暗号強度は
    要らない(``core.hashing.blake3_u64`` を 1,600 万行に掛けると数秒かかるので採らない)= expedient。
    """
    x = np.asarray(x, dtype=np.uint64).copy()
    with np.errstate(over="ignore"):
        x ^= x >> np.uint64(33)
        x *= np.uint64(0xFF51AFD7ED558CCD)
        x ^= x >> np.uint64(33)
        x *= np.uint64(0xC4CEB9FE1A85EC53)
        x ^= x >> np.uint64(33)
    return x


def _largest_remainder(weights: np.ndarray, total: int) -> np.ndarray:
    """最大剰余法(``build.pop.fitting`` と同規約・24 要素なので自前で持つ)。"""
    w = np.asarray(weights, dtype=np.float64)
    s = w.sum()
    if s <= 0 or total <= 0:
        return np.zeros(w.size, dtype=np.int64)
    exact = w * (total / s)
    base = np.floor(exact).astype(np.int64)
    rest = int(total - base.sum())
    if rest > 0:
        order = np.lexsort((np.arange(w.size), -(exact - base)))
        base[order[:rest]] += 1
    return base


@dataclass
class RakeReport:
    """raking の前後(ゲート json へ)。"""

    jsd_before: dict[str, float] = field(default_factory=dict)
    jsd_after: dict[str, float] = field(default_factory=dict)
    n_moved: int = 0
    n_candidates: int = 0
    rolled_back: bool = False
    budget_rows: int = 0

    @property
    def max_before(self) -> float:
        return max(self.jsd_before.values(), default=0.0)

    @property
    def max_after(self) -> float:
        return max(self.jsd_after.values(), default=0.0)


#: 1 日ぶんの平行移動で確保する最小の活動長[分](先頭/末尾の切り詰め後)。
_BIG: Final[int] = 1 << 30


def _groups(
    agent_row: np.ndarray, day: np.ndarray, start: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """(体, 曜日)ごとの並び。返り値=``(order, gid, g0, g1)``。ループなし。

    - ``order``: ``(体, 曜日, 開始)`` 昇順の行索引。
    - ``gid``: **並べ替え後の位置** → 群番号。
    - ``g0``/``g1``: 群番号 → 並べ替え後の開始位置・終了位置(排他)。
    """
    n = int(start.size)
    order = np.lexsort((start, day, agent_row)).astype(np.int32)
    if n == 0:
        e = np.zeros(0, dtype=np.int32)
        return order, e, e, e
    gkey = agent_row[order].astype(np.int64) * V.N_DAYS + day[order]
    new = np.ones(n, dtype=bool)
    new[1:] = gkey[1:] != gkey[:-1]
    del gkey
    gid = (np.cumsum(new) - 1).astype(np.int32)
    g0 = np.flatnonzero(new).astype(np.int32)
    g1 = np.append(g0[1:], np.int32(n))
    return order, gid, g0, g1


def _hour_hist(start: np.ndarray, rows: np.ndarray) -> np.ndarray:
    return np.bincount((start[rows] // 60).astype(np.int64), minlength=24).astype(np.int64)


def rake(
    agent_row: np.ndarray,
    day: np.ndarray,
    start: np.ndarray,
    end: np.ndarray,
    activity: np.ndarray,
    modified: np.ndarray,
    curves: dict[str, np.ndarray],
    *,
    max_frac: float = RAKE_MAX_FRAC,
    budget_rows: int | None = None,
) -> RakeReport:
    """目的別の**開始時刻分布**を時間帯カーブへ寄せる(配列は in-place で書き換える)。

    規則(自前・全て expedient)
      - 対象は**平日(d0-d4)**の ``ACTIVITY_TO_PT_PURPOSE`` に載る活動。PT の調査日が
        火〜木の平日 1 日(F1)なので休日は較正の対象外。
      - 過剰な時と不足の時をどちらも時刻昇順に並べて突き合わせる(1 次元の最適輸送=
        移動量の総和が最小)。移す量は 1 時間単位・分の端数は保つ。
      - 動かし方は「**その体のその日を丸ごと平行移動する**」。先頭の活動の開始は 0 に、
        末尾の活動の終了は 1440 に切り詰める(就寝が伸縮を吸収する)。これで
        **重なりも並びの入れ替えも起こらない**(修復をやり直す必要がない)。
        隙間の中だけで動かす案は、LLM が隙間なく書いた日には何もできない=不採用。
      - 1 つの (体, 曜日) は**全目的を通して 1 回まで**動かす。
      - 動かせる総量は**行数**で ``budget_rows``(与えられなければ ``max_frac`` × 全活動数)。
        本番は ``ingest`` が **修復ぶんを差し引いた適応予算**を渡す
        (``ADAPTIVE_MODIFIED_TARGET`` − 修復による修正率)。予算 0 なら raking しない。
      - 平行移動は PlanSpec 窓(段2 規則4)を最大 1-2 時間はみ出しうる。窓の値自体が
        プールの既定値(09:00-18:00 一律)= expedient なので、**較正カーブを優先する**。
      - 全目的の JSD の最大値が下がらなかったら**丸ごと巻き戻す**(較正が悪化した
        ままの表を凍結しない)。

    Note:
        逐次ループ宣言(P4): **目的数 × 24 時間**ぶんのループだけ(活動数に比例しない)。
    """
    rep = RakeReport()
    n = int(start.size)
    if n == 0:
        return rep

    order, gid, g0, g1 = _groups(agent_row, day, start)
    pos = np.empty(n, dtype=np.int32)
    pos[order] = np.arange(n, dtype=np.int32)
    group_of = gid[pos]
    del pos
    n_groups = int(g0.size)
    gsize = (g1 - g0).astype(np.int32)
    weekday = day <= 4
    rows_of: dict[str, np.ndarray] = {}
    want_of: dict[str, np.ndarray] = {}
    for act_code, pt in sorted(ACTIVITY_TO_PT_PURPOSE.items()):
        target = curves.get(pt)
        if target is None:
            continue
        rows = np.flatnonzero((activity == act_code) & weekday)
        if rows.size == 0:
            continue
        rows_of[pt] = rows if pt not in rows_of else np.union1d(rows_of[pt], rows)
    for pt, rows in rows_of.items():
        want_of[pt] = _largest_remainder(curves[pt], int(rows.size))
        rep.jsd_before[pt] = jensen_shannon(_hour_hist(start, rows), want_of[pt])
        rep.n_candidates += int(rows.size)
    if not rows_of:
        return rep

    saved_start, saved_end = start.copy(), end.copy()
    shifted = np.zeros(n_groups, dtype=bool)
    budget = int(max_frac * n) if budget_rows is None else max(0, int(budget_rows))
    rep.budget_rows = budget
    if budget <= 0:  # 修復だけでゲートの枠を使い切った=raking しない
        for pt, rows in rows_of.items():
            rep.jsd_after[pt] = rep.jsd_before[pt]
        return rep
    budget_rows = budget
    # 予算は**目的の候補数に比例**して割る(先に回った目的が使い切らないように)。
    total_cand = sum(int(r.size) for r in rows_of.values()) or 1
    quota = {pt: int(budget_rows * r.size / total_cand) for pt, r in rows_of.items()}

    def _apply(groups: np.ndarray, delta: np.ndarray) -> None:
        """群ごとの平行移動を一括適用(先頭/末尾だけ切り詰める)。ループなし。"""
        gd = np.zeros(n_groups, dtype=np.int32)
        gd[groups] = delta
        d = gd[gid]
        s = start[order] + d
        e = end[order] + d
        s[g0] = np.maximum(s[g0], 0)
        e[g1 - 1] = np.minimum(e[g1 - 1], V.MINUTES_PER_DAY)
        start[order] = s
        end[order] = e
        modified[order[d != 0]] = True

    for pt, rows in rows_of.items():  # 逐次: 目的数ぶん(挿入順=決定論)
        allow = min(budget_rows, quota[pt])
        if allow <= 0:
            continue
        hours = (start[rows] // 60).astype(np.int64)
        obs = np.bincount(hours, minlength=24).astype(np.int64)
        want = want_of[pt]

        picks: list[np.ndarray] = []
        for h in range(24):  # 逐次: 24 時間ぶん
            k = int(obs[h] - want[h])
            if k <= 0:
                continue
            cand = rows[hours == h]
            ckey = _mix64(  # 並べ替えキーは候補行ぶんだけ作る(全行ぶん持たない)
                agent_row[cand].astype(np.uint64) * np.uint64(10007)
                + start[cand].astype(np.uint64)
            )
            picks.append(cand[np.argsort(ckey, kind="stable")[::-1]][:k])
        if not picks:
            continue
        src = np.concatenate(picks)
        dst = np.repeat(np.arange(24, dtype=np.int64), np.maximum(want - obs, 0))
        m = min(src.size, dst.size)
        if m == 0:
            continue
        src, dst = src[:m], dst[:m]
        delta = ((dst - start[src] // 60) * 60).astype(np.int32)

        g = group_of[src]
        keep = (~shifted[g]) & (delta != 0)
        src, delta, g = src[keep], delta[keep], g[keep]
        if g.size == 0:
            continue
        _, first = np.unique(g, return_index=True)  # 1 群 1 回
        first = np.sort(first)
        src, delta, g = src[first], delta[first], g[first]

        sz = gsize[g]
        fe = end[order[g0[g]]]  # 先頭の活動の終了
        ls = start[order[g1[g] - 1]]  # 末尾の活動の開始
        ss = np.where(sz > 1, start[order[np.minimum(g0[g] + 1, n - 1)]], _BIG).astype(np.int64)
        pe = np.where(sz > 1, end[order[np.maximum(g1[g] - 2, 0)]], -_BIG).astype(np.int64)
        d64 = delta.astype(np.int64)
        ok = np.where(
            d64 < 0,
            (fe + d64 >= MIN_ACT_MINUTES) & (ss + d64 >= 0),
            (ls + d64 <= V.MINUTES_PER_DAY - MIN_ACT_MINUTES)
            & (pe + d64 <= V.MINUTES_PER_DAY),
        )
        if not ok.any():
            continue
        g, delta, sz = g[ok], delta[ok], sz[ok]
        take = np.cumsum(sz.astype(np.int64)) <= allow
        g, delta = g[take], delta[take]
        if g.size == 0:
            continue
        budget_rows -= int(gsize[g].sum())
        shifted[g] = True
        rep.n_moved += int(gsize[g].sum())
        _apply(g, delta)

    for pt, rows in rows_of.items():
        rep.jsd_after[pt] = jensen_shannon(_hour_hist(start, rows), want_of[pt])
    if rep.max_after > rep.max_before + 1e-12:  # 悪化したら巻き戻す
        start[:] = saved_start
        end[:] = saved_end
        rep.jsd_after = dict(rep.jsd_before)
        rep.n_moved = 0
        rep.rolled_back = True
    return rep


# ================================================================= 応答の取り込み
_ID_RE: Final[re.Pattern[str]] = re.compile(r'"id"\s*:\s*"([^"]{1,32})"')


def response_files(world_dir: Path, pattern: str = RESPONSES_GLOB) -> list[Path]:
    """応答 jsonl(名前順=決定論)。"""
    return sorted(Path(p) for p in _glob.glob(str(Path(world_dir) / pattern)))


@dataclass
class IngestReport:
    """取り込みの集計(``w17_gates.json`` の中身)。"""

    n_agents: int
    n_response_rows: int = 0
    n_with_response: int = 0
    n_skeleton: int = 0
    n_parsed_acts: int = 0
    n_considered: int = 0
    n_activities: int = 0
    n_modified: int = 0
    n_repair_modified: int = 0
    n_dropped: int = 0
    parse_bad: dict[str, int] = field(default_factory=dict)
    repair: RepairCounters = field(default_factory=RepairCounters)
    rake: RakeReport = field(default_factory=RakeReport)
    completion_tokens: list[int] = field(default_factory=list)
    responses: list[dict[str, Any]] = field(default_factory=list)

    @property
    def response_rate(self) -> float:
        return self.n_with_response / self.n_agents if self.n_agents else 0.0

    @property
    def skeleton_rate(self) -> float:
        return self.n_skeleton / self.n_agents if self.n_agents else 0.0

    @property
    def parse_fail_rate(self) -> float:
        """捨てた行 / (捨てた行 + 採用した活動)。``fix_*``(同義語で直した)は数えない。"""
        bad = sum(v for k, v in self.parse_bad.items() if k in V.FAILURE_REASONS)
        return bad / max(1, bad + self.n_parsed_acts)

    @property
    def modified_rate(self) -> float:
        """段2 修正率(答申 Q4-2「LLM 出力のうち修正されたブロックの割合」)。

        分子= 修正フラグの立った活動 + 捨てた活動。分母= 検討したブロック(パースできた
        活動 + 骸格で埋めた活動)。骸格の体は **LLM 出力が 1 件も使えなかった**ので全件が
        修正として数えられる(= 応答が無いままの段階はゲートに落ちる)。
        """
        return self.n_modified / max(1, self.n_considered)

    def token_stats(self) -> dict[str, float]:
        if not self.completion_tokens:
            return {"n": 0, "mean": 0.0, "p50": 0.0, "p90": 0.0, "max": 0.0}
        a = np.asarray(self.completion_tokens, dtype=np.float64)
        return {
            "n": int(a.size),
            "mean": round(float(a.mean()), 2),
            "p50": round(float(np.percentile(a, 50)), 1),
            "p90": round(float(np.percentile(a, 90)), 1),
            "max": round(float(a.max()), 1),
        }

    def to_json(self) -> dict[str, Any]:
        return {
            "n_agents": self.n_agents,
            "n_response_rows": self.n_response_rows,
            "n_with_response": self.n_with_response,
            "response_rate": round(self.response_rate, 6),
            "n_skeleton_fallback": self.n_skeleton,
            "skeleton_rate": round(self.skeleton_rate, 6),
            "n_parsed_activities": self.n_parsed_acts,
            "n_considered": self.n_considered,
            "n_activities": self.n_activities,
            "activities_per_agent": round(self.n_activities / max(1, self.n_agents), 3),
            "n_modified": self.n_modified,
            "n_repair_modified": self.n_repair_modified,
            "repair_modified_rate": round(
                self.n_repair_modified / max(1, self.n_considered), 6
            ),
            "n_dropped": self.n_dropped,
            "modified_rate": round(self.modified_rate, 6),
            "parse_fail_rate": round(self.parse_fail_rate, 6),
            "parse_reasons": dict(sorted(self.parse_bad.items())),
            "repair_rules": dict(sorted(self.repair.counts.items())),
            "raking": {
                "jsd_before": {k: round(v, 6) for k, v in sorted(self.rake.jsd_before.items())},
                "jsd_after": {k: round(v, 6) for k, v in sorted(self.rake.jsd_after.items())},
                "jsd_max_before": round(self.rake.max_before, 6),
                "jsd_max_after": round(self.rake.max_after, 6),
                "n_moved": self.rake.n_moved,
                "n_candidates": self.rake.n_candidates,
                "rolled_back": self.rake.rolled_back,
                "budget_rows": self.rake.budget_rows,
            },
            "completion_tokens": self.token_stats(),
            "responses": self.responses,
        }


def _last_rows(paths: Sequence[Path], id_to_row: dict[str, int], n: int) -> tuple[np.ndarray, np.ndarray, int]:
    """1 巡目: 各 id の**最後の行**の位置(ファイル番号・行番号)を拾う(全文は読まない)。

    fleet_gen は追記型で resume すると同じ ``(id, rep)`` が二度書かれるので、W14/W15 と同じ
    「最後の行を採る」規約にする。id の抽出は正規表現(``json.loads`` を 2 度しない)。
    """
    file_of = np.full(n, -1, dtype=np.int16)
    line_of = np.full(n, -1, dtype=np.int64)
    total = 0
    for fi, path in enumerate(paths):
        with open(path, "r", encoding="utf-8") as fh:
            for li, line in enumerate(fh):
                if not line.strip():
                    continue
                total += 1
                m = _ID_RE.search(line[:200])
                if m is None:
                    continue
                row = id_to_row.get(m.group(1))
                if row is not None:
                    file_of[row] = fi
                    line_of[row] = li
    return file_of, line_of, total


def _iter_texts(
    paths: Sequence[Path], file_of: np.ndarray, line_of: np.ndarray
) -> Iterator[tuple[int, str, int]]:
    """2 巡目: 採用する行だけを ``json.loads`` して ``(row, text, completion_tokens)`` を返す。"""
    for fi, path in enumerate(paths):
        wanted: dict[int, int] = {}
        rows = np.flatnonzero(file_of == fi)
        for r in rows:
            wanted[int(line_of[r])] = int(r)
        if not wanted:
            continue
        with open(path, "r", encoding="utf-8") as fh:
            for li, line in enumerate(fh):
                row = wanted.get(li)
                if row is None:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                yield row, str(d.get("text", "") or ""), int(d.get("completion_tokens", 0) or 0)


def ingest(
    world_dir: str | Path,
    data_dir: str | Path,
    *,
    facts: AgentFacts | None = None,
    responses: Sequence[Path] | None = None,
    share: np.ndarray | None = None,
    curves: dict[str, np.ndarray] | None = None,
    rake_budget_rows: int | None = None,
    chunk: int = 1 << 20,
) -> tuple[IngestReport, dict[str, np.ndarray]]:
    """応答を**ストリーミングで**読み、行パーサ → 整合修復 → raking を通して SoA を作る。

    ``rake_budget_rows`` を与えると raking の行数予算を固定する(``None``=**適応**:
    ``ADAPTIVE_MODIFIED_TARGET × n_considered − 修復ぶんの修正``)。適応予算は集計値だけから
    決まるので決定論。

    Returns:
        ``(IngestReport, 列辞書)``。列= ``agent_id``/``day``/``seq``/``start_min``/
        ``end_min``/``activity_code``/``place_kind``/``target_cell``。

    Note:
        逐次ループ宣言(P4): 体数ぶんのループ 1 本(応答のパースと修復)。構築時 1 回。
        メモリは ``array.array``(12 B/活動)で持つ=39 万体 × 約 40 活動で約 200 MB。
    """
    world_dir, data_dir = Path(world_dir), Path(data_dir)
    f = facts if facts is not None else build_facts(world_dir, data_dir)
    sh = share if share is not None else open_share(world_dir)
    cv = curves if curves is not None else hour_curves(world_dir)
    paths = list(responses) if responses is not None else response_files(world_dir)

    rep = IngestReport(n_agents=f.n)
    rep.responses = [
        {"path": p.name, "sha256": C.sha256_file(p), "bytes": p.stat().st_size} for p in paths
    ]
    id_to_row = {str(int(a)): i for i, a in enumerate(f.agent_id)}
    file_of, line_of, rep.n_response_rows = _last_rows(paths, id_to_row, f.n)

    b_agent = array.array("i")
    b_day = array.array("b")
    b_start = array.array("h")
    b_end = array.array("h")
    b_act = array.array("b")
    b_place = array.array("b")
    b_mod = array.array("b")
    for buf, want in ((b_agent, 4), (b_day, 1), (b_start, 2), (b_end, 2)):
        if buf.itemsize != want:  # pragma: no cover - 主要プラットフォームでは成立
            raise RuntimeError(f"array.array の要素幅が想定と違う: {buf.typecode}")

    def _emit(row: int, acts: list[V.Act], flags: list[bool]) -> None:
        b_agent.extend([row] * len(acts))
        b_day.extend([a.day for a in acts])
        b_start.extend([a.start for a in acts])
        b_end.extend([min(a.end, V.MINUTES_PER_DAY) for a in acts])
        b_act.extend([a.activity for a in acts])
        b_place.extend([a.place for a in acts])
        b_mod.extend([1 if x else 0 for x in flags])

    def _emit_skeleton(row: int) -> None:
        rep.n_skeleton += 1
        acts, _, _ = repair(skeleton(f, row), f, row, sh, RepairCounters())
        rep.n_considered += len(acts)  # 骸格は「LLM 出力が使えなかった」= 全件が修正
        _emit(row, acts, [True] * len(acts))

    used = np.zeros(f.n, dtype=bool)
    # 1) 応答のある体(**応答ファイルの順**に流す=テキストを辞書に溜めない)
    for row, text, ctok in _iter_texts(paths, file_of, line_of):  # 逐次(P4): 体数ぶん
        rep.n_with_response += 1
        if ctok > 0:
            rep.completion_tokens.append(ctok)
        parsed, bad = V.parse_text(text)
        for k, v in bad.items():
            rep.parse_bad[k] = rep.parse_bad.get(k, 0) + v
        rep.n_parsed_acts += len(parsed)
        acts: list[V.Act] = []
        flags: list[bool] = []
        if parsed:
            acts, flags, dropped = repair(parsed, f, row, sh, rep.repair)
            rep.n_dropped += dropped
        if not acts:
            _emit_skeleton(row)
        else:
            rep.n_considered += len(parsed)
            _emit(row, acts, flags)
        used[row] = True
    # 2) 応答が無かった体
    for row in np.flatnonzero(~used):  # 逐次(P4): 欠落体数ぶん
        _emit_skeleton(int(row))

    # **dtype は最小幅で持つ**(RSS 目標 ≤2 GB。int64 に広げると 1,600 万行で +0.5 GB)。
    agent_row = np.frombuffer(b_agent, dtype=np.int32).copy()
    day = np.frombuffer(b_day, dtype=np.int8).astype(np.int32)
    start = np.frombuffer(b_start, dtype=np.int16).astype(np.int32)
    end = np.frombuffer(b_end, dtype=np.int16).astype(np.int32)
    activity = np.frombuffer(b_act, dtype=np.int8).copy()
    place = np.frombuffer(b_place, dtype=np.int8).copy()
    modified = np.frombuffer(b_mod, dtype=np.int8).astype(bool)
    del b_agent, b_day, b_start, b_end, b_act, b_place, b_mod

    # --- raking の予算は**修復ぶんを差し引いた適応値**(§1 W17「修正率<20%」の内枠) ---
    # この時点の ``modified`` は修復が立てたフラグだけ。raking はここから
    # ``ADAPTIVE_MODIFIED_TARGET`` に届くまでしか動かさない。集計値だけで決まるので決定論。
    rep.n_repair_modified = int(modified.sum()) + rep.n_dropped
    room = ADAPTIVE_MODIFIED_TARGET * rep.n_considered - rep.n_repair_modified
    budget = int(max(0.0, room)) if rake_budget_rows is None else int(rake_budget_rows)
    rep.rake = rake(agent_row, day, start, end, activity, modified, cv, budget_rows=budget)
    rep.n_activities = int(agent_row.size)
    rep.n_modified = int(modified.sum()) + rep.n_dropped

    order = np.lexsort((start, day, agent_row)).astype(np.int32)
    agent_row, day, start, end = agent_row[order], day[order], start[order], end[order]
    activity, place = activity[order], place[order]
    del order
    seq = _sequence_within_group(agent_row, day)
    return rep, {
        "agent_id": f.agent_id[agent_row].astype(np.int32),
        "day": day.astype(np.int8),
        "seq": seq.astype(np.int16),
        "start_min": start.astype(np.int16),
        "end_min": end.astype(np.int16),
        "activity_code": activity.astype(np.int8),
        "place_kind": place.astype(np.int8),
        "target_cell": _target_cells(f, agent_row, place).astype(np.int32),
    }


def _sequence_within_group(agent_row: np.ndarray, day: np.ndarray) -> np.ndarray:
    """(体, 曜日)ごとの 0 起点連番(ソート済み前提・ループなし)。"""
    n = int(agent_row.size)
    if n == 0:
        return np.zeros(0, dtype=np.int32)
    new = np.ones(n, dtype=bool)
    new[1:] = (agent_row[1:] != agent_row[:-1]) | (day[1:] != day[:-1])
    idx = np.arange(n, dtype=np.int32)
    return idx - np.maximum.accumulate(np.where(new, idx, np.int32(0)))


def _target_cells(f: AgentFacts, agent_row: np.ndarray, place: np.ndarray) -> np.ndarray:
    """場所種別 → セル。**自宅/職場/学校だけ**を解決し、残りは ``-1``。

    D-W13(出口は目的地への経路の結果)と世界過程設計書 行1(目的地の選好は LLM)により、
    店・駅・公園のセル選択は**ランの側の決定**。W17 はここまでを凍結する。
    """
    out = np.full(agent_row.size, CELL_UNRESOLVED, dtype=np.int32)
    for pk, col in (
        (V.PLACE_HOME, f.home_cell),
        (V.PLACE_WORK, f.work_cell),
        (V.PLACE_SCHOOL, f.school_cell),
    ):
        m = place == pk
        if m.any():
            out[m] = col[agent_row[m]]
    return out


# ================================================================= 出力
_SCHEMA: Final[pa.Schema] = pa.schema(
    [
        ("agent_id", pa.int32()),
        ("day", pa.int8()),
        ("seq", pa.int16()),
        ("start_min", pa.int16()),
        ("end_min", pa.int16()),
        ("activity_code", pa.int8()),
        ("place_kind", pa.int8()),
        ("target_cell", pa.int32()),
    ]
)
#: parquet の行グループ(ストリーミング書き出しの粒度)。
ROW_GROUP: Final[int] = 1 << 20


def write_schedule(out_dir: Path, columns: dict[str, np.ndarray]) -> dict[str, Any]:
    """SoA → ``w17_schedule.parquet``(行グループ単位で書く=全体を 1 テーブルに積まない)。"""
    path = Path(out_dir) / SCHEDULE_NAME
    n = int(columns["agent_id"].size)
    with pq.ParquetWriter(path, _SCHEMA, compression="zstd", compression_level=3,
                          version="2.6", write_statistics=False) as w:
        for lo in range(0, max(n, 1), ROW_GROUP):
            hi = min(n, lo + ROW_GROUP)
            if lo >= hi and n:
                break
            w.write_table(
                pa.table(
                    {
                        name: pa.array(
                            columns[name][lo:hi], type=_SCHEMA.field(name).type
                        )
                        for name in _SCHEMA.names
                    },
                    schema=_SCHEMA,
                )
            )
            if n == 0:
                break
    return {
        "path": path.name,
        "sha256": C.sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": n,
    }


# ================================================================= 段階本体
def run(ctx: C.Ctx, *, shard: int = 0, n_shards: int = 1) -> C.StageResult:
    """W17: プロンプトを書き、応答があれば取り込んで週次表を凍結する(純関数)。"""
    out = ctx.out
    facts = build_facts(out, ctx.data)
    prompt_rec = write_prompts(out, facts, shard=shard, n_shards=n_shards)

    inputs = [out / f for f in INPUT_FILES]
    inputs += PF.layer_files(ctx.data.joinpath(*POOL_DIR), "L1")
    for name in PF.LAYERS[1:]:
        inputs += PF.layer_files(ctx.data.joinpath(*POOL_DIR), name)
    outputs: list[dict[str, Any]] = [prompt_rec]

    gates: list[C.Gate] = [
        C.Gate("n_agents", facts.n),
        C.Gate("n_calls_equals_n_agents", prompt_rec["rows"] * REPEAT,
               facts.n if n_shards <= 1 else None,
               passed=(n_shards > 1) or (prompt_rec["rows"] * REPEAT == facts.n)),
        C.Gate("prompts_sha256", prompt_rec["sha256"]),
        C.Gate("prompt_tokens_mean", prompt_rec["prompt_tokens_mean"],
               f"<= {PROMPT_TOKEN_TARGET}",
               passed=prompt_rec["prompt_tokens_mean"] <= PROMPT_TOKEN_TARGET),
        C.Gate("max_tokens", MAX_TOKENS, MAX_TOKENS),
        C.Gate("temperature", TEMPERATURE, TEMPERATURE),
    ]
    notes: dict[str, Any] = {
        "structured_output": regex_summary(facts),
        "llm": {
            "model_hint": MODEL_HINT,
            "temperature": TEMPERATURE,
            "seed": "blake3(SEED_TAG:agent_id) mod (2^53-1)",
            "repeat": REPEAT,
            "thinking": THINKING,
            "n_calls": prompt_rec["rows"] * REPEAT,
        },
        "system_sha256": system_sha256(),
        "token_estimator": "UTF-8 文字数 ÷ 2(perception.channels.estimate_tokens と同規約)",
        "hour_curve_source": (
            "W12 の hour 重み(time_dist_12・2015)= PT 時間帯別表が未取得のための代替"
            "(expedient・昇格条件=PT 時間帯別表の取得)"
        ),
        "shard": {"index": shard, "n": n_shards},
    }

    resp = response_files(out)
    catalog: list[str] = []
    if resp:
        report, columns = ingest(out, ctx.data, facts=facts)
        outputs.append(write_schedule(out, columns))
        outputs.append(C.write_json(out, GATES_NAME, report.to_json(), rows=report.n_activities))
        inputs += resp
        notes["ingest"] = report.to_json()
        gates += [
            C.Gate("responses_present", True, True),
            C.Gate("response_rate", round(report.response_rate, 6),
                   f">= {GATE_RESPONSE_RATE}", passed=report.response_rate >= GATE_RESPONSE_RATE),
            C.Gate("modified_rate", round(report.modified_rate, 6),
                   f"< {GATE_MODIFIED_RATE}", passed=report.modified_rate < GATE_MODIFIED_RATE),
            C.Gate("jsd_max_after", round(report.rake.max_after, 6)),  # 合格線は仕様書に無い
            C.Gate("raking_lowers_jsd", round(report.rake.max_after, 6),
                   f"<= {round(report.rake.max_before, 6)}",
                   passed=report.rake.max_after <= report.rake.max_before + 1e-12),
            C.Gate("parse_fail_rate", round(report.parse_fail_rate, 6)),
            C.Gate("completion_tokens_mean", report.token_stats()["mean"],
                   f"<= {TOKEN_TARGET_MEAN}",
                   passed=report.token_stats()["mean"] <= TOKEN_TARGET_MEAN),
        ]
        if report.n_activities > 0:
            catalog = ["週次活動スケジュール表"]
    else:
        gates.append(C.Gate("responses_present", False, None, passed=True))
        notes["responses_missing"] = (
            f"{RESPONSES_GLOB} が無い。tools/gen/fleet_gen.py で生成してから再実行すると"
            "凍結する(段階は落とさない)。"
        )

    return C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash(inputs),
        param_hash=C.param_hash(
            {
                "system_sha256": system_sha256(),
                "activity_words": list(V.ACTIVITY_WORDS),
                "place_words": list(V.PLACE_WORDS),
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "repeat": REPEAT,
                "seed_tag": SEED_TAG.decode("ascii"),
                "seed_mod": SEED_MOD,
                "gate_modified_rate": GATE_MODIFIED_RATE,
                "min_acts_per_day": MIN_ACTS_PER_DAY,
                "lines_per_day": [LINES_PER_DAY_MIN, LINES_PER_DAY_MAX],
                "regex_by_kind": {k: v["sha256"] for k, v in
                                  regex_summary(facts)["by_kind"].items()},
                "activity_synonyms": V.ACTIVITY_SYNONYMS,
                "place_synonyms": V.PLACE_SYNONYMS,
                "rake_max_frac": RAKE_MAX_FRAC,
                "adaptive_modified_target": ADAPTIVE_MODIFIED_TARGET,
                "open_share_min": OPEN_SHARE_MIN,
                "max_acts_per_day": MAX_ACTS_PER_DAY,
                "min_sleep_minutes": MIN_SLEEP_MINUTES,
                "school_window": {k: list(v) for k, v in SCHOOL_WINDOW.items()},
                "crew_shift_starts": list(CREW_SHIFT_STARTS),
                "night_window": list(NIGHT_WINDOW),
                "sleep_step_minutes": PF.SLEEP_STEP_MINUTES,
            }
        ),
        params={
            "n_agents": facts.n,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "repeat": REPEAT,
            "prompts_sha256": prompt_rec["sha256"],
            "shard": f"{shard}/{n_shards}",
        },
        outputs=outputs,
        gates=gates,
        catalog_classes=catalog,
        expedients=[
            "活動語 12・場所語 12 の語彙表と行書式(4 列 HHMM)は自前=先行研究なし",
            "活動語 → 行動契約書 §2.1 の 12 語への写像表",
            "時間帯カーブ= W12 の hour 重み(time_dist_12・2015)。PT 時間帯別表が未取得の代替"
            "(昇格条件=PT 時間帯別表の取得)",
            "seed=blake3(タグ:agent_id) mod 2^53−1(D-W17「seed=hash(agent)」の実装形)",
            f"max_tokens={MAX_TOKENS}(I1 の 590 tok/体 + 余裕)・出力平均目標 "
            f"{TOKEN_TARGET_MEAN} tok",
            "種別別 system テンプレ(共通部+種別1行)は自前・版は system_sha256",
            "勤務窓の既定表・学校段階別の在校時間・交代制の勤務開始・夜勤判定(職業名の"
            "「夜間」「深夜」)",
            "来訪日の決め方(一度きり来街=seed から 1 日・定期来街=cadence または seed から 2 日)",
            "sleep_steps の単位= 1 step 10 分",
            "整合修復の 8 規則と閾値(1 日 8 件上限・就寝 240 分・開店率 5%・最小活動 10 分・4 行未満の日は骸格で補う)",
            "raking の規則(平日のみ・その体のその日を丸ごと平行移動・1 群 1 回・行数 12% 予算・悪化時は巻き戻し)",
            "ゲート raking_lowers_jsd は rake() が悪化時に巻き戻すため構造上 FAIL しない pin(同語反復)=実測は jsd_max_after(報告値)",
            "target_cell は自宅/職場/学校のみ解決(店・駅・公園はランの決定=D-W13/行1)",
            "骸格スケジュール(応答全滅の埋め・実データに寄せる意図はない)",
        ],
        notes=notes,
    )
