"""manifest.schema: U8 run manifest の型(13節)と機械化される規則。

正典: docs/design/v2-run-manifest-concurrency.md §1.2(スキーマ表・13節)/§1.4(T1-T9)。
規約: docs/design/v2-implementation-plan.md §2(ハッシュ=blake3・RNG欄=``numpy-philox4x64``)・§3(層契約)。

13節 = 同定 / 事前登録 / コード / 設定 / 乱数 / データ資産 / holdout封印 /
LLM艦隊 / 並行意味論 / 予算 / ハードウェア / 出力 / 系譜。

機械化される規則(``RunManifest`` の model_validator・すべて日本語メッセージで ValueError):

(a) ``code.dirty=true`` は mode=calibration/holdout に使えない(設計書§1.2 コード行)。
(b) mode≠holdout で ``holdout_seal.layers[*].opened=true`` があれば起動拒否(同 holdout封印行)。
(c) mode=calibration/holdout は ``llm_fleet.prefix_caching_hash_algo="sha256_cbor"`` かつ
    ``llm_fleet.env["VLLM_BATCH_INVARIANT"]="1"``(同 LLM艦隊行・B14実測)。
(d) ハードウェア節・出力節に IPv4 アドレスと ``http`` 始まりの文字列を書かない
    (同 ハードウェア行「サーバー名・IPは書かない」/出力行「s3_uri は接続情報を書かない」)。
(e) mode=calibration/holdout は ``output.diagnostics.columns`` に診断行4列+保存則2検算を要求(T9)。

**expedient(未リサーチの命名)**: 本モジュールの ``DIAG_COLUMNS``(繰り延べ/昇格/縮退/抑止)と
``CONSERVATION_CHECKS``(取引残差/在庫残差)の**キー名そのもの**は設計書に文字列として
書かれていない。日本語の項目名から親が付けた暫定名であり、**C4(世界過程第1陣+経済)の
診断行・月次センサス実装時に確定**する。ここで固定しているのは「4列+2検算が存在すること」
という T9 の規則であって、命名ではない。
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Iterator, Literal

from pydantic import BaseModel, ConfigDict, model_validator

__all__ = [
    "CONSERVATION_CHECKS",
    "DIAG_COLUMNS",
    "Arbiter",
    "Code",
    "Concurrency",
    "Contracts",
    "DataAsset",
    "Decoding",
    "DecodingTier",
    "Diagnostics",
    "DocRef",
    "Engine",
    "FidelityProfile",
    "Hardware",
    "HoldoutLayer",
    "HoldoutSeal",
    "Identity",
    "Lineage",
    "LlmApply",
    "LlmFleet",
    "Mode",
    "Output",
    "Preregistration",
    "PromptContract",
    "Replica",
    "Rng",
    "Routing",
    "RunManifest",
    "Scheduler",
    "Settings",
    "SourceRef",
    "Budget",
]

# --- T9: 診断行4列+保存則2検算(キー名は expedient・C4で確定) ---------------
DIAG_COLUMNS: tuple[str, ...] = ("deferred", "promoted", "degraded", "suppressed")
CONSERVATION_CHECKS: tuple[str, ...] = (
    "conservation_transfer_residual",
    "conservation_stock_residual",
)

# 検証ラン(mode=calibration/holdout)で必須の艦隊設定(設計書§1.2 LLM艦隊行)
REQUIRED_PREFIX_HASH_ALGO = "sha256_cbor"
BATCH_INVARIANT_ENV = "VLLM_BATCH_INVARIANT"
BATCH_INVARIANT_REQUIRED = "1"
MARLIN_ATOMIC_ADD_ENV = "VLLM_MARLIN_USE_ATOMIC_ADD"
MARLIN_ATOMIC_ADD_REQUIRED = "0"  # 設計書 §1.2 LLM艦隊行(太字)・加算順序の非決定を防ぐ
REQUIRED_PHASES: tuple[str, ...] = ("read_intent", "arbitrate", "commit")  # 設計書 §2.2 二相コミット

# 規則(d): IPv4 の8bit境界を見る(``1.2.3.4`` 形の版番号も弾く=安全側・expedient)
_IPV4_RE = re.compile(
    r"(?<![\w.])(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?![\w.])"
)


class _Frozen(BaseModel):
    """本書の全モデル共通: 未知欄を拒否し、生成後は不変。"""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Mode(str, Enum):
    """実行モード(設計書§1.2 同定行・modeで勘定分離=L3)。"""

    SMOKE = "smoke"
    CALIBRATION = "calibration"
    HOLDOUT = "holdout"
    ABLATION = "ablation"
    PRODUCTION = "production"


#: 較正・holdout = 「検証ラン」勘定。(a)(c)(e) が効く集合。
VERIFICATION_MODES: frozenset[Mode] = frozenset({Mode.CALIBRATION, Mode.HOLDOUT})


# --- 1. 同定 -----------------------------------------------------------------
class Identity(_Frozen):
    """同定。``run_id`` は manifest 正規化本文の自己ハッシュ(§1.1)。

    ``run_id`` は正規化本文から除外して計算するため、生成前は ``None`` を許す
    (``canonical.with_run_id`` が埋める)。
    """

    schema_version: str
    run_id: str | None = None
    label: str
    mode: Mode
    created_utc: datetime
    tz: str


# --- 2. 事前登録 -------------------------------------------------------------
class Preregistration(_Frozen):
    """事前登録。封印後の変更は新 run_id(HARKing防止)。"""

    hypothesis: str
    metrics: list[str]
    thresholds: dict[str, float]
    ablation_id: str | None = None
    sealed_at: datetime


# --- 3. コード ---------------------------------------------------------------
class DocRef(_Frozen):
    """文書参照(ODD・契約書)。manifest は本文でなくハッシュで参照する(§1.1)。"""

    path: str
    blake3: str


class Contracts(_Frozen):
    """契約書2本(知覚・行動)。"""

    perception: DocRef
    action: DocRef


class Code(_Frozen):
    """コード。``dirty=true`` は較正・holdout に使えない(CI拒否・規則(a))。"""

    repo: str
    commit: str
    describe: str
    dirty: bool
    odd_doc: DocRef
    contracts: Contracts


# --- 4. 設定 -----------------------------------------------------------------
class FidelityProfile(_Frozen):
    """忠実度プロファイル。比較ランは同一プロファイル必須。"""

    name: str
    blake3: str


class Settings(_Frozen):
    """設定。``normalized_blake3`` = 正規化済み設定本文のハッシュ。"""

    fidelity_profile: FidelityProfile
    normalized_blake3: str
    tick_seconds: int
    n_agents: int
    sim_days: int
    start_sim_datetime: datetime


# --- 5. 乱数 -----------------------------------------------------------------
class Rng(_Frozen):
    """乱数。個体/LLMシードは導出(別欄に持たない)=§2.5。"""

    master_seed: int
    scheme: Literal["numpy-philox4x64"]
    domain_table_version: str


# --- 6. データ資産 -----------------------------------------------------------
class DataAsset(_Frozen):
    """データ資産1件。ライセンス台帳行と1対1(``license_row``)。"""

    id: str
    version: str
    blake3: str
    bytes: int
    records: int
    license_row: str


# --- 7. holdout封印 ----------------------------------------------------------
class HoldoutLayer(_Frozen):
    """封印層1枚。``opened`` は mode≠holdout では false でなければならない(規則(b))。"""

    name: str
    member_hash: str
    sealed_utc: datetime
    opened: bool = False


class HoldoutSeal(_Frozen):
    """holdout封印。``seal_scheme`` = D(直接) / S(署名) / P(公開コミットメント)。"""

    seal_scheme: Literal["D", "S", "P"]
    layers: list[HoldoutLayer]


# --- 8. LLM艦隊 --------------------------------------------------------------
class Engine(_Frozen):
    """推論エンジンの版(vLLM 系)。"""

    name: str
    version: str
    torch: str
    cuda_driver: str
    attention_backend: str


class Replica(_Frozen):
    """レプリカ1台(1 vLLM サーバプロセス)。"""

    tier: str
    model: str
    revision: str
    quant: str
    weights_blake3: str
    tp: int
    dp: int
    gpus: list[int]
    max_num_seqs: int
    max_model_len: int
    gpu_memory_utilization: float
    in_flight_cap: int


class Routing(_Frozen):
    """ルーティング。``cell_affinity`` は BN-4 で不採用=既定 false。"""

    rule: str
    cell_affinity: bool


class DecodingTier(_Frozen):
    """1階層分のデコード設定。

    expedient: 設計書§1.2 は ``decoding{T1,T2}`` としか書いておらず、下位欄
    (temperature/top_p/max_tokens/seed)の構成は親が置いた暫定形。
    """

    temperature: float
    top_p: float
    max_tokens: int
    seed: int | None = None


class Decoding(_Frozen):
    """デコード設定(T1=行動選択・T2=発話/静的言語化)。

    欄名 ``T1``/``T2`` は設計書の欄名をそのまま採る(snake_case にしない)。
    """

    T1: DecodingTier
    T2: DecodingTier


class PromptContract(_Frozen):
    """プロンプト契約(M11: 静的≤750・セル依存≤250・個体≤300)。"""

    version: str
    static_tok: int
    cell_tok: int
    individual_tok: int


class LlmFleet(_Frozen):
    """LLM艦隊。既定 sha256(pickle) は版をまたいで非再現(vLLM公式)。"""

    engine: Engine
    env: dict[str, str]
    replicas: list[Replica]
    routing: Routing
    decoding: Decoding
    prompt_contract: PromptContract
    prefix_caching_hash_algo: str
    cache_salt: str


# --- 9. 並行意味論 -----------------------------------------------------------
class Scheduler(_Frozen):
    """スケジューラの版(§2の規則の版)。"""

    name: str
    version: str


class LlmApply(_Frozen):
    """LLM応答の適用(§2.4)。``overdue``=締切超過・``missing``=未着の扱い。"""

    policy: str
    order: str
    overdue: str
    missing: str


class Arbiter(_Frozen):
    """繰り延べアービタ(知覚契約書§6)。"""

    rule: str
    promotion_T_max_min: float
    degrade_enabled: bool


class Concurrency(_Frozen):
    """並行意味論(U9)。二相コミット reserve→arbitrate→commit。"""

    scheduler: Scheduler
    phases: list[str]
    priority_key: str
    tiebreak_key: str
    class_rank: dict[str, int]
    llm_apply: LlmApply
    retry_rounds: int
    arbiter: Arbiter

    @model_validator(mode="after")
    def _phases_fixed(self) -> "Concurrency":
        """二相コミットの段は設計書 §2.2 の固定列(read_intent→arbitrate→commit)。"""
        if list(self.phases) != list(REQUIRED_PHASES):
            raise ValueError(
                f"並行意味論 phases は {list(REQUIRED_PHASES)!r} で固定です(実際: {list(self.phases)!r})。"
                "設計書 §2.2 二相コミット。"
            )
        return self


# --- 10. 予算 ----------------------------------------------------------------
class SourceRef(_Frozen):
    """予算書の参照(パス+コミット+ハッシュ)。"""

    path: str
    commit: str
    blake3: str


class Budget(_Frozen):
    """予算。``effective`` はラン時点のスナップショット(W1/L4/L6/M8/M11/P6…)。"""

    source: SourceRef
    effective: dict[str, str | float | int]


# --- 11. ハードウェア --------------------------------------------------------
class Hardware(_Frozen):
    """ハードウェア。**サーバー名・IPは書かない**(規則(d))。"""

    profile: str
    gpus: list[str]
    cpu: str
    ram_gb: float
    os: str


# --- 12. 出力 ----------------------------------------------------------------
class Diagnostics(_Frozen):
    """診断行の列。T9=4列+保存則2検算(規則(e))。"""

    columns: list[str]


class Output(_Frozen):
    """出力。接続情報(URL・IP)は書かない(規則(d))。"""

    journal: str
    checkpoints: str
    llm_tape: str
    diagnostics: Diagnostics


# --- 13. 系譜 ----------------------------------------------------------------
class Lineage(_Frozen):
    """系譜。``parent_run`` = resume 元の run_id。"""

    parent_run: str | None = None


# --- 走査ヘルパ(規則(d)) ---------------------------------------------------
def _iter_strings(obj: Any) -> Iterator[str]:
    """dict/list を再帰的に辿り、キーと値の文字列を全て返す。"""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                yield key
            yield from _iter_strings(value)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            yield from _iter_strings(value)


def _find_forbidden_endpoint(section_name: str, dumped: Any) -> str | None:
    """IPv4 か http 始まりの文字列を見つけたら日本語の理由文を返す。"""
    for text in _iter_strings(dumped):
        if _IPV4_RE.search(text):
            return f"{section_name}節に IPv4 アドレスらしき文字列があります: {text!r}"
        if text.casefold().startswith("http"):
            return f"{section_name}節に URL(http 始まり)があります: {text!r}"
    return None


# --- 上位: run manifest ------------------------------------------------------
class RunManifest(_Frozen):
    """U8 run manifest(13節)。``identity.run_id`` は正規化本文の自己ハッシュ。"""

    identity: Identity
    preregistration: Preregistration
    code: Code
    settings: Settings
    rng: Rng
    data_assets: list[DataAsset]
    holdout_seal: HoldoutSeal
    llm_fleet: LlmFleet
    concurrency: Concurrency
    budget: Budget
    hardware: Hardware
    output: Output
    lineage: Lineage

    # --- 規則(a) ---
    @model_validator(mode="after")
    def _rule_a_dirty_not_allowed_in_verification(self) -> "RunManifest":
        if self.code.dirty and self.identity.mode in VERIFICATION_MODES:
            raise ValueError(
                "規則(a)違反: code.dirty=true は mode="
                f"{self.identity.mode.value} (較正・holdout) に使えません。"
                "作業ツリーをコミットしてから再実行してください"
                "(設計書 v2-run-manifest-concurrency.md §1.2 コード行)。"
            )
        return self

    # --- 規則(b) ---
    @model_validator(mode="after")
    def _rule_b_opened_layer_only_in_holdout(self) -> "RunManifest":
        if self.identity.mode is not Mode.HOLDOUT:
            opened = [layer.name for layer in self.holdout_seal.layers if layer.opened]
            if opened:
                raise ValueError(
                    "規則(b)違反: mode="
                    f"{self.identity.mode.value} (≠holdout) で opened=true の封印層が"
                    f"あります: {opened}。起動を拒否します"
                    "(設計書 §1.2 holdout封印行)。"
                )
        return self

    # --- 規則(c) ---
    @model_validator(mode="after")
    def _rule_c_batch_invariant_for_verification(self) -> "RunManifest":
        if self.identity.mode not in VERIFICATION_MODES:
            return self
        mode_name = self.identity.mode.value
        algo = self.llm_fleet.prefix_caching_hash_algo
        if algo != REQUIRED_PREFIX_HASH_ALGO:
            raise ValueError(
                f"規則(c)違反: mode={mode_name} (検証ラン) は "
                f"llm_fleet.prefix_caching_hash_algo={REQUIRED_PREFIX_HASH_ALGO!r} が必須です"
                f"(実際: {algo!r})。既定の sha256(pickle) は版をまたいで非再現"
                "(設計書 §1.2 LLM艦隊行)。"
            )
        env_value = self.llm_fleet.env.get(BATCH_INVARIANT_ENV)
        if env_value != BATCH_INVARIANT_REQUIRED:
            raise ValueError(
                f"規則(c)違反: mode={mode_name} (検証ラン) は "
                f"llm_fleet.env[{BATCH_INVARIANT_ENV!r}]={BATCH_INVARIANT_REQUIRED!r} が必須です"
                f"(実際: {env_value!r})。バッチ不変性なしでは T6 が成立しません"
                "(B14実測・設計書 §1.3)。"
            )
        marlin = self.llm_fleet.env.get(MARLIN_ATOMIC_ADD_ENV)
        if marlin != MARLIN_ATOMIC_ADD_REQUIRED:
            raise ValueError(
                f"規則(c)違反: mode={mode_name} (検証ラン) は "
                f"llm_fleet.env[{MARLIN_ATOMIC_ADD_ENV!r}]={MARLIN_ATOMIC_ADD_REQUIRED!r} が必須です"
                f"(実際: {marlin!r})。atomic add は加算順序が非決定(設計書 §1.2 LLM艦隊行)。"
            )
        return self

    # --- 規則(d) ---
    @model_validator(mode="after")
    def _rule_d_no_endpoints(self) -> "RunManifest":
        for section_name, section in (
            ("ハードウェア", self.hardware),
            ("出力", self.output),
        ):
            reason = _find_forbidden_endpoint(
                section_name, section.model_dump(mode="json")
            )
            if reason is not None:
                raise ValueError(
                    f"規則(d)違反: {reason}。サーバー名・IP・接続情報は manifest に書きません"
                    "(設計書 §1.2 ハードウェア行/出力行)。"
                )
        return self

    # --- 規則(e) ---
    @model_validator(mode="after")
    def _rule_e_diagnostics_columns(self) -> "RunManifest":
        if self.identity.mode not in VERIFICATION_MODES:
            return self
        present = set(self.output.diagnostics.columns)
        missing_diag = [c for c in DIAG_COLUMNS if c not in present]
        missing_cons = [c for c in CONSERVATION_CHECKS if c not in present]
        if missing_diag or missing_cons:
            raise ValueError(
                "規則(e)違反(T9): mode="
                f"{self.identity.mode.value} (較正・holdout) には診断行4列"
                f"{list(DIAG_COLUMNS)} と保存則2検算{list(CONSERVATION_CHECKS)} が必要です。"
                f"欠落: 診断行={missing_diag} 検算={missing_cons}"
                "(設計書 §1.2 出力行・§1.4 T9)。"
            )
        return self
