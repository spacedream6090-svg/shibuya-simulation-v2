"""被招待の提示(知覚契約書 §6 起床(ii))を B6 の**既存スロット**で出す。

C6 の会話結線(サブ O)で「被招待がプロンプト上で**誰に誘われたか**を知らされていない」
=承諾(行動契約書 §1-2「承諾は 行動: 会話 **対象: 招待者**」)がほぼ起きない、が判明した。
本テストは修正を固定する。

見るもの
(a) 被招待の描画に**招待者の人ID**が出る/(b) 招待なしの描画は**1 バイトも変わらない**
(golden 不変・テンプレ SHA 161fe181 不変)/(c) §2.4 ⑧(B0-B4b のバイト一致)と B5 は
被招待でも動かない(B6 は個体ブロック)/(d) 予算(B6 ≤80・個体群 ≤300)/(e) 決定論/
(f) 文面が**パーサで招待者に戻る**(承諾の対象規則と地続き)/(g) 両 budget_mode で成立/
(h) **端から端まで**: プロンプトを読む LLM は承諾でき(実レンダラ)、読めない構成
(``renderer="stub"``)では承諾が 0 になる=情報経路そのものの効果。
"""

from __future__ import annotations

import re

import numpy as np
import pytest

from shibuya.agents.state import AgentKind, AgentState, ResultCode
from shibuya.engine.run import _inviter_of, run_day
from shibuya.llm import LLMResponse, format_two_line, parse_two_line
from shibuya.perception import templates as T
from shibuya.perception.renderer import INVITE_REASON, Renderer, person_word
from shibuya.world.state import World

SHARED_BLOCKS = ("B0", "B1", "B2", "B3", "B4", "B4b")
#: プロンプトから招待者を読む正規表現(端から端までの LLM が使う)。
INVITE_RE = re.compile(r"P-(\d+)があなたに話しかけました")


def build(n: int = 24, n_cells: int = 9, seed: int = 1, mode: str = "fixed"):
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n)
    g = np.random.default_rng(seed)
    with a.writable():
        a.cell[:] = 0
        a.xy[:] = g.uniform(0.0, 50.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 4_000
        a.hunger[:] = 5
        a.activity[:] = 0
        a.last_result[:] = int(ResultCode.OK)
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=7, budget_mode=mode)
    r.prepare_tick(600)
    return r


# ---------------------------------------------------------------- (a)(b)
def test_the_invitee_is_told_who_spoke_to_them():
    r = build()
    out = r.render(0, tick=600, wake_reason=0, inviter=13)
    wake = [ln for ln in out.text.splitlines() if ln.startswith("[B6 起床]")][0]
    assert person_word(13) in wake  # P-13
    assert "会話" in wake  # 承諾に要る行動語
    assert wake == "[B6 起床] " + INVITE_REASON.format(person="P-13")


def test_no_invite_renders_exactly_as_before():
    """招待が無ければ(None/負値)**バイト不変**=既存 golden は動かない。"""
    r = build()
    base = r.render(0, tick=600, wake_reason=0)
    assert r.render(0, tick=600, wake_reason=0, inviter=None).prompt_hash == base.prompt_hash
    assert r.render(0, tick=600, wake_reason=0, inviter=-1).prompt_hash == base.prompt_hash
    wake = [ln for ln in base.text.splitlines() if ln.startswith("[B6 起床]")][0]
    assert wake == "[B6 起床] " + T.WAKE_REASON_TEXT[0]


def test_template_sha256_is_untouched():
    """テンプレ本体(``TEMPLATES``/``WAKE_REASON_TEXT``)に行を足していない。"""
    assert T.template_sha256().startswith("161fe181")
    assert "{reason}" in T.TEMPLATES["B6.wake"]
    assert INVITE_REASON not in T.TEMPLATES.values()
    assert INVITE_REASON not in T.WAKE_REASON_TEXT


# ---------------------------------------------------------------- (c)
@pytest.mark.parametrize("mode", ["fixed", "ranking"])
def test_rule8_and_b5_do_not_move_for_the_invitee(mode):
    """B6 は**個体ブロック**なので、被招待でも B0-B4b と B5 は 1 バイトも動かない。"""
    r = build(mode=mode)
    plain = r.render(0, tick=600, wake_reason=0)
    invited = r.render(0, tick=600, wake_reason=0, inviter=5)
    for b in SHARED_BLOCKS:
        assert plain.blocks[b] == invited.blocks[b], b
    assert plain.blocks["B5"] == invited.blocks["B5"]
    assert plain.blocks["B6"] != invited.blocks["B6"]
    assert plain.prefix_key == invited.prefix_key  # prefix キャッシュも壊れない
    # 同セルの別個体(招待なし)との ⑧ 検査も通る
    other = r.render(1, tick=600, wake_reason=0)
    assert invited.shared_static_bytes() == other.shared_static_bytes()


# ---------------------------------------------------------------- (d)
@pytest.mark.parametrize("mode", ["fixed", "ranking"])
def test_budgets_hold_with_the_invite_line(mode):
    """B6 はブロック予算 80 内・個体群は 300 内(混雑+長い id+失敗理由の最悪ケース)。"""
    n = 60
    w = World.synthetic(n_cells=9, seed=3)
    a = AgentState(n)
    g = np.random.default_rng(5)
    with a.writable():
        a.cell[:] = 0
        a.xy[:] = g.uniform(0.0, 60.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 1_234_567
        a.hunger[:] = 10
        a.fatigue[:] = 10
        a.thermal[:] = 10
        a.last_result[:] = int(ResultCode.MONEY_SHORT)
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=7, budget_mode=mode, acquaintances={0: list(range(1, n))})
    r.prepare_tick(600)
    out = r.render(0, tick=600, wake_reason=0, inviter=999_999)
    assert out.tokens_est["B6"] <= T.BLOCK_TOKEN_BUDGET["B6"], out.tokens_est["B6"]
    assert out.within_group_budgets(), dict(out.group_tokens)


# ---------------------------------------------------------------- (e)(f)
def test_deterministic_and_parses_back_to_the_inviter():
    """同入力→同バイト。文面の「対象: P-<id>」は**パーサで招待者 id に戻る**。"""
    r1, r2 = build(), build()
    x = r1.render(3, tick=600, wake_reason=0, inviter=17)
    y = r2.render(3, tick=600, wake_reason=0, inviter=17)
    assert x.prompt_hash == y.prompt_hash and x.text == y.text
    said = parse_two_line("理由: 誘われたから\n行動: 会話 対象: P-17 ひと言: はい")
    assert said.action == "会話" and int(said.target.person_id) == 17
    assert person_word(17) in x.text


def test_inviter_wins_over_the_wake_reason_word():
    """被招待は起床理由そのもの=``wake_reason`` の語ではなく招待文が出る。"""
    r = build()
    out = r.render(0, tick=600, wake_reason="なにか用事があるため。", inviter=2)
    assert "なにか用事があるため。" not in out.text
    assert person_word(2) in out.text


# ---------------------------------------------------------------- 結線(engine 側の 1 関数)
class _FakeConv:
    def __init__(self, pending: dict[int, int]) -> None:
        self.pending = dict(pending)

    def pending_inviter_of(self, invitee: int) -> int:
        return int(self.pending.get(int(invitee), -1))


def test_only_the_pending_invitee_gets_an_inviter():
    """返事待ちの被招待だけが招待者を持つ。**起床条件では絞らない**。

    ``_settle_pending_invites`` はその tick に答えた全員から返事待ちを拾うので、
    会話ターン以外で起きた呼も承諾/拒否として消費される。条件で絞ると、その呼には
    招待文が載らないまま「拒否」と数えられる。
    """
    from shibuya.agents.state import WakeCondition

    conv = _FakeConv({7: 3})
    turn = int(WakeCondition.CONVERSATION_TURN)
    assert _inviter_of(conv, 7, turn) == 3  # 返事待ち
    assert _inviter_of(conv, 8, turn) == -1  # 同じ条件で起きた話者(返事待ちなし)
    assert _inviter_of(conv, 7, turn + 1) == 3  # 別の条件で起きても招待は事実
    assert _inviter_of(None, 7, turn) == -1  # 会話を回していないラン


# ---------------------------------------------------------------- (h) 端から端まで
class _InviteReadingLLM:
    """**プロンプトを読む** LLM(``MockLLM`` は読まない)。

    - B6 に招待文があれば **招待者を名指して承諾**する。
    - 無ければ ``(agent_id + 1)`` を誘う(招待を出す側)。``+1`` は対合ではないので、
      **招待文を読めない限り承諾は起きない**(被招待 B は A ではなく B+1 を名指す)。
    """

    def __init__(self, n_agents: int) -> None:
        self.n_agents = int(n_agents)
        self.n_prompts_with_invite = 0
        self.n_calls = 0

    def complete(self, request):
        self.n_calls += 1
        m = INVITE_RE.search(request.prompt)
        if m is not None:
            self.n_prompts_with_invite += 1
            text = format_two_line("誘われたから", "会話", f"P-{m.group(1)}", "はい")
        else:
            partner = (int(request.agent_id) + 1) % self.n_agents
            text = format_two_line("知人を見かけたから", "会話", f"P-{partner}", "こんにちは")
        return LLMResponse(text=text, source="scripted")


def _conv_run(renderer, llm, n_agents: int = 200):
    """会話が開く窓(朝を含む 600 tick)+呼数上限を外したラン。

    ``budget`` を外すのは L4 按分(200 体では 1.4 呼/tick)だと**返事待ちがほぼ期限切れ**に
    なり、情報経路の効果が呼の枯渇に埋もれるため(実測: 既定予算では招待 262 中 248 が期限切れ)。
    """
    return run_day(
        n_agents=n_agents, seed=1, world=World.synthetic(n_cells=2, seed=1), ticks=600,
        llm=llm, renderer=renderer, processes=False, population=False, world_dir=None,
        checkpoint_every=600, budget=n_agents,
    )


def test_end_to_end_only_the_real_renderer_lets_the_invitee_accept(capsys):
    """情報経路そのものの効果: 招待文が届く構成でだけ承諾が立つ。

    同じ LLM・同じ世界・同じ seed で、**描画だけ**を実レンダラ / ``"stub"`` に替える。
    LLM は「招待文が読めたら招待者を名指して承諾・読めなければ (id+1) を誘う」。
    ``+1`` は対合ではないので、**招待文を読めない限り承諾は起きない**。
    """
    n = 200
    real_llm, stub_llm = _InviteReadingLLM(n), _InviteReadingLLM(n)
    real = _conv_run(None, real_llm, n).conversation_counters
    stub = _conv_run("stub", stub_llm, n).conversation_counters
    with capsys.disabled():
        print()
        print(
            f"[被招待の提示] 実レンダラ: 招待 {int(real['conv_invites'])} → 承諾 "
            f"{int(real['conv_accepted'])} / 拒否 {int(real['conv_declined'])}"
            f"(招待文が載った呼 {real_llm.n_prompts_with_invite})  vs  stub: 招待 "
            f"{int(stub['conv_invites'])} → 承諾 {int(stub['conv_accepted'])} / 拒否 "
            f"{int(stub['conv_declined'])}(招待文 {stub_llm.n_prompts_with_invite})"
        )
    assert stub_llm.n_prompts_with_invite == 0
    # 招待文を読めない側でも**偶然**ペアが立つことがある: 名指した相手が同一セルに
    # 居ないと ``commit.pair_partners`` が同席者への差し替えを行う(``conv_fallback_same_batch``)
    # ので、同じセルで 2 人が同時に「会話」を選ぶと相互指名になる。D-62(就寝は計画の実行)で
    # 起きている体が増え、この窓で 358 招待中 **2 件(0.6%)**出るようになった(D-62 前は 147
    # 招待中 0 件)。**招待文を読んだ承諾ではない**ので、率で判定する。
    # 層2(第137)の指摘で率でなく**絶対値**でも縛る: 差し替えで立つのは高々 2 セッション。
    assert stub["conv_accepted"] <= 2, stub
    assert stub["conv_accepted"] <= 0.01 * stub["conv_invites"], stub
    assert real_llm.n_prompts_with_invite > 0
    assert real["conv_accepted"] > 0 and real["sessions_opened"] > 0, real
    assert real["conv_accepted"] > 10 * (stub["conv_accepted"] + 1), (real, stub)
    # 承諾が立つと発話ブロック(1呼1発話)も回り始める。stub 側に残るのは上の
    # 「同席者への差し替え」で立った 2 セッションぶんだけ(実測 12 / 実レンダラ 1,572)。
    assert real["utterance_blocks"] > 0
    # 差し替えで立ったセッションぶんの発話しか無いこと(1 セッションあたり高々 8 ブロック・
    # 実測 2 セッションで 12)。実レンダラ側の 5% という相対枠は緩すぎる(層2 第137)。
    assert stub["utterance_blocks"] <= 8 * max(1, int(stub["conv_accepted"])), (real, stub)
