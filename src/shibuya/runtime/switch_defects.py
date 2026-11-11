"""engine.defect_fixes_1103 — 棚卸し B で見つけた欠陥 4 件の直しの宣言・計器・見出し(指示書 11-03 §3・小さな版上げ 1 回分)。

決定(11-03/§3): 「検証で見つけた欠陥の修正」(CLAUDE.md §2-6=試験つき・事後報告)。棚卸し B
(``docs/reference/behavior-audit-B-resolve-world-2026-11-02.md``)の M10・M11・M28・M16 を親が HEAD で読み、4 件とも誤りと
確かめた。M10・M16 は既定の結果を動かすので、4 件を 1 つの小さな版上げ(旧道の切替口つき)に束ねる(回答 10-13b §0-6)。

| 名 | 直した所 | 前(旧道) | 後(既定) |
|---|---|---|---|
| ``M10`` | ``engine/systems/talk.py``(会話の終わり・``_revert`` に積まれた招待側=対象の決まらない会話の失敗・招待が流れた・期限切れの返事待ち)・``run._settle_pending_invites`` の末尾(返事の解決の招待側の戻し)・``resolve.end_conversation`` | 会話の終わりと招待側の戻しで、対象の体を全員 ``IDLE`` に戻す(今の活動を見ない)。``_revert`` は CONVERSING の確かめより前に「対象の決まらない会話」(resolve が失敗させた体=活動は変わっていない)からも呼ばれるので、寝ている・歩いている・在店の体まで IDLE にしていた | 活動が ``CONVERSING`` の体だけ ``IDLE`` に戻す。ほかの活動は変えない(対象のある会話の失敗は旧道でも戻していない=それと揃う)。相手の欄 ``talk_partner`` は全員 −1。戻す対象は積むときと書く直前の 2 回、会話中(is_busy)の体を除く |
| ``M11`` | ``resolve._apply_move``・``_apply_board``・``_serve_poi_queue`` | 列の印 ``queue_poi`` は移動・乗車で消えない(席が空けば離れた所で購入・食事が成立する) | 移動で歩き出した体・乗車でホームへ歩き出した体は列を離れる(失敗は書かない)。列を捌く前に「店のセルに居る」を確かめ、居なければ列から外す。**列を離れない歩き出しが残る**(``resolve.begin_planned_sleep``・``begin_walk_to``・``engine/calendar2/layer.py`` の歩き出し・乗車でホームに居た体=``on_plat``): 安全網は給仕の前の居場所の確かめ ``n_queue_dropped_away``(既定のランで 0 件) |
| ``M28`` | ``resolve._serve_poi_queue`` | 列から席へ入る前の支払いの確かめが現金だけ | 新しい行の購入と同じ ``_payable``(現金か口座) |
| ``M16`` | ``run._settle_pending_invites``・``ConversationManager.drop_pending`` | 返事が「会話」で招待者宛て(か名指しなし)でも、届かなければ「断った」(拒否の記憶 60 刻み) | 届かないときは「不成立」(拒否の記憶を残さない)。招待側は今と同じく戻す・本人の B6 は今のまま |

ランは常に ``on``=上の 4 件を直した状態。腕の名と 4 件の計器は manifest の ``defect_fixes_1103``(``mode`` は ``on`` に固定)と、
状態のファイルの見出しの ``defect_fixes_1103``(``{"mode": "on"}``=見出しに無い状態のファイルは legacy=版上げの前のラン=
再開できない)に出る。

〔第346 旧道の切替口の削除〕版上げの前の値の再現の切替口 ``--defect-fixes-1103 legacy``(環境変数
``SHIBUYA_DEFECT_FIXES_1103``・``set_arm``)は消した: 環境変数を与えると読み込みで止まる・CLI の旗は引数の誤り・系の旧道の
分かれ(``systems/talk.py`` の全員を IDLE に戻す道)も消した。旧値の再現は安定版のタグ ``stable-v2-before-switch-removal-346``
(つなぎの台帳 ``DOC-fix4-defect-legacy-switch`` は removed)。部品の関数の既定(``resolve.apply(defect_fixes=False)``・
``run._settle_pending_invites(drop_unreachable=False, keep_activity=False)``・``ConversationManager(count_unreachable=False)``)
と ``manifest_fields("legacy")`` は部品の単体試験の基準の口として残す(ランの口からは選べない)。

計器(manifest の ``defect_fixes_1103.counts``・legacy のランでは全部 0=旧道は数えない):
``n_conversation_end_kept_activity``(会話の終わりで戻さなかった体の数・活動の名ごと=M10)・``n_invite_revert_kept_activity``
(招待側の戻しで戻さなかった体の数・原因ごと × 活動の名ごと=M10 の続き。原因 ``conversation.REVERT_CAUSES``=``no_target``
対象の決まらない会話の失敗・``invite_failed`` 招待が流れた・``expired`` 期限切れ・``settle`` 返事の解決。既定のラン
=5,000 体・seed 1・w6_v3_default の引数で no_target 2,130(うち IDLE 1,488)・settle 31・ほかは 0=戻さなかった体のほとんどは
対象の決まらない会話の失敗)・``n_queue_left_by_move``・
``n_queue_left_by_board``・``n_queue_dropped_away``(M11・最後の 1 本は本来 0 のはず)・``n_queue_payable_not_cash``
(列の確かめで、現金だけなら外れたが口座で払えたので残った数=M28)・``n_pending_unreachable``(届かない返事を不成立にした数=M16)。

仕分けへ残したもの(本モジュールの外・README §8): 会話の番で別の行為を選んだ体をセッションから外す配線(``conv.step`` に
``in_conversation`` を渡す=本人の判断の口の設計に関わる)。

時間の方針(11-02r §2-2): 本モジュールは時刻を持たない(腕の名だけ)。

逐次ループ宣言(P4): なし(組み立てで 1 回読む・ランの終わりに 1 回まとめる)。
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from shibuya.engine import removed_switches as _RSW

__all__ = [
    "MODE_ON", "MODE_LEGACY", "MODES", "DEFAULT_MODE", "SCHEMA", "FIXES", "FIX_DECLARATIONS", "COUNT_KEYS",
    "ENV_REMOVED", "resolve", "is_on", "is_legacy", "empty_counts", "manifest_fields", "header_fields",
    "check_resume",
]

MODE_ON: Final[str] = "on"
MODE_LEGACY: Final[str] = "legacy"
MODES: Final[tuple[str, ...]] = (MODE_ON, MODE_LEGACY)
#: ランの腕(11-03 §3・〔第346〕これだけ)。``legacy`` は部品の口と見出しに無い状態のファイルの読みだけ。
DEFAULT_MODE: Final[str] = MODE_ON
#: manifest の ``defect_fixes_1103`` の値の形の版(欄の意味を変えたら上げる)。
SCHEMA: Final[str] = "shibuya.defect_fixes_1103/1"

#: 直した欠陥の名(棚卸し B の番号・manifest の並びの順)。
FIXES: Final[tuple[str, ...]] = ("M10", "M11", "M28", "M16")

#: 欠陥ごとの宣言(直した所・前・後)。manifest の ``defect_fixes_1103.fixes``。
FIX_DECLARATIONS: Final[Mapping[str, Mapping[str, str]]] = {
    "M10": {"where": "engine/systems/talk.py(会話の終わり・_revert に積まれた招待側=対象の決まらない会話の失敗・招待が"
                     "流れた・期限切れ)・run._settle_pending_invites の末尾・resolve.end_conversation",
            "legacy": "会話の終わりと招待側の戻しで、対象の体を全員 IDLE に戻す(対象の決まらない会話を選んで失敗した体="
                      "寝ている・歩いている・在店の体も)",
            "on": "CONVERSING の体だけ IDLE に戻す(ほかの活動は変えない=対象のある失敗と揃う)・talk_partner は全員 -1・"
                  "書く直前に会話中の体を除く"},
    "M11": {"where": "resolve._apply_move・_apply_board・_serve_poi_queue",
            "legacy": "列の印 queue_poi は移動・乗車で消えない",
            "on": "移動・乗車で歩き出した体は列を離れる(失敗は書かない)・店のセルに居ない体は列から外す(列を離れない"
                  "歩き出し=計画の就寝・begin_walk_to・カレンダー 2 の歩き出し・ホームに居た乗車の体は、この確かめが安全網)"},
    "M28": {"where": "resolve._serve_poi_queue",
            "legacy": "列から席へ入る前の支払いの確かめが現金だけ",
            "on": "新しい行の購入と同じ _payable(現金か口座)"},
    "M16": {"where": "run._settle_pending_invites・ConversationManager.drop_pending",
            "legacy": "届かない「会話」の返事を断りに数える(拒否の記憶 60 刻み)",
            "on": "届かない返事は不成立(拒否の記憶を残さない)・招待側は戻す・本人の B6 は今のまま"},
}

#: 計器の鍵(manifest の ``defect_fixes_1103.counts`` の並び)。
COUNT_KEYS: Final[tuple[str, ...]] = (
    "n_conversation_end_kept_activity", "n_invite_revert_kept_activity", "n_queue_left_by_move", "n_queue_left_by_board", "n_queue_dropped_away",
    "n_queue_payable_not_cash", "n_pending_unreachable",
)

#: 〔第346〕消した切替口の環境変数(与えると止まる=黙って無視しない)。
ENV_REMOVED: Final[str] = "SHIBUYA_DEFECT_FIXES_1103"
_RSW.stop_if_set(ENV_REMOVED)  # 一覧と止める文は engine.removed_switches(ランの入口=組み立ての最初でも止める)


def resolve(mode: str | None) -> str:
    """引数の腕(``None``=ランの腕 ``on``)を名に直す(名の誤りは止める)。"""
    m = DEFAULT_MODE if mode is None else str(mode)
    if m not in MODES:
        raise ValueError(f"defect_fixes_1103 は {MODES} のどれか(いま {m!r})")
    return m


def is_on(mode: str | None = None) -> bool:
    """``mode``(省略=ランの腕 on)が直した道か。"""
    return resolve(mode) == MODE_ON


def is_legacy(mode: str | None = None) -> bool:
    """``mode``(省略=ランの腕 on)が旧道(版上げの前の挙動=部品の口だけ)か。"""
    return resolve(mode) == MODE_LEGACY


def empty_counts() -> dict[str, Any]:
    """計器の空の形(活動の名ごとの dict 2 本と整数 5 本)。"""
    return {"n_conversation_end_kept_activity": {}, "n_invite_revert_kept_activity": {}, "n_queue_left_by_move": 0, "n_queue_left_by_board": 0,
            "n_queue_dropped_away": 0, "n_queue_payable_not_cash": 0, "n_pending_unreachable": 0}


def _counts(leave_counts: Mapping[str, Any] | None, conv: Any) -> dict[str, Any]:
    """ランの積算から計器を集める(会話の 3 本は会話マネージャ・列の 4 本は ``leave_counts``)。"""
    c = empty_counts()
    lc = leave_counts if isinstance(leave_counts, Mapping) else {}
    for k in ("n_queue_left_by_move", "n_queue_left_by_board", "n_queue_dropped_away", "n_queue_payable_not_cash"):
        c[k] = int(lc.get(k, 0))
    if conv is not None:
        c.update(conv.defect_fix_counters())
    return c


def manifest_fields(mode: str, leave_counts: Mapping[str, Any] | None = None, conv: Any = None) -> dict[str, Any]:
    """manifest の ``defect_fixes_1103``(設定=形の版・腕・4 件の宣言・直した印/観測=計器)。"""
    on = is_on(mode)
    return {
        "schema": SCHEMA,
        "mode": resolve(mode),
        "fixes": {k: dict(v) for k, v in FIX_DECLARATIONS.items()},
        "fixed": {f"fix_{k}": int(on) for k in FIXES},
        "counts": _counts(leave_counts, conv),
    }


def header_fields(mode: str = DEFAULT_MODE) -> dict[str, Any] | None:
    """状態のファイルの見出しの ``defect_fixes_1103``(ランは常に ``{"mode": "on"}``・on の外の名は None)。"""
    return {"mode": MODE_ON} if str(mode) == MODE_ON else None


def check_resume(saved: Any) -> None:
    """再開のときに、保存したランの見出しの ``defect_fixes_1103``(無ければ legacy=版上げの前のラン)が on かを確かめる(違えば止める)。"""
    s = saved if isinstance(saved, Mapping) else {}
    s_mode = str(s.get("mode", MODE_LEGACY))
    if s_mode != DEFAULT_MODE:
        raise ValueError(f"再開の欠陥の直し(11-03)の腕が親と違う(親 {s_mode}・今 {DEFAULT_MODE})=旧値の切替口 "
                         "--defect-fixes-1103 legacy は消した(安定版のタグ stable-v2-before-switch-removal-346 で回す)")
