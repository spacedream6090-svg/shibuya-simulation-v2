"""engine.experiment.gate — 実験が世界に入る口(第 1 期 1-3・CP12)。**この 1 関数 ``admit`` だけ**。

決定 10-12 §4-5 CP12 (a): 原因の種類に「実験の条件」を足して 3 種類に限り、実験が世界に入る口をコードで 1 か所にし、
ほかの場所から「実験の条件」を書けないことを試験で強制する。

- 実行時: 原因の型 ``Experiment`` の ``__init__`` が呼び手のフレームを見て、この ``admit`` の中でなければ
  ``PermissionError``(``engine.events.log._only_from_gate``)。書きの検査の切替口(``SHIBUYA_WRITE_GUARD=off``)でも
  外さない(理由は同じ関数の docstring)。
- 静的: ``tests/engine/events/test_e_cause_three_kinds.py`` が ``src/shibuya`` の全ファイルを AST で見て、この置き場と
  型の定義の置き場(``engine/events/log.py``)の外で型の名を参照する形(呼び出し・import・別名・``getattr``・
  ``vars``・``__dict__``・文字列の名)を落とす。
- 実験で世界に入れるのは「決定」だけ(CLAUDE.md §3・CP6)。準備・告知・実行は世界の中の人が行う。この口は
  決定を原因の印つきの出来事として 1 行書くだけで、世界の状態は書かない(書くのは後の段の申込書の仕組み=CP5-4)。
  1-3 では src に呼び手は無い(口と試験だけ)。
- 〔第 3 期 3-3〕呼び手は申込書の効かせる口 ``engine.experiment.apply.apply`` だけ(試験 ``tests/engine/experiment`` が AST で
  確かめる)。告知の「届いた情報」の行のために ``via``(CT9 の道具)と ``received_ns``(届いた時刻)の欄を足した(既定は 1-3 と
  同じ=``無し``・``None``)。

先例: AI Town ``abstractGame.ts`` の外からの入力の 1 本の表(MIT)。「実験の口を 1 か所に強制」する先例は
コードに無い(R-113 §13=自前の構成・未リサーチ(expedient))。

逐次ループ宣言: なし。
"""

from __future__ import annotations

from typing import Any

from shibuya.engine.events import vocab as _V
from shibuya.engine.events.log import Event, EventId, EventLog
from shibuya.engine.events.log import Experiment as _Experiment

__all__ = ["admit", "ADMIT_CODE"]


def admit(log: EventLog, cond_id: str, *, what: str, who: int | str, whom: int | str | None = None,
          where: tuple[str, int] | None = None, how_much: int | None = None,
          origin: str | None = None, via: str = _V.VIA_NONE, received_ns: int | None = None) -> EventId | None:
    """実験の条件 ``cond_id`` を原因とする出来事を記録の時計の時刻で 1 行書き、id を返す(CP12 の唯一の口)。

    ``what`` は語彙表の語(表の外は ``ValueError``)。記録しないとき(切替口)は ``None``(原因の型は作る=口の検査は通す)。
    〔3-3〕``via``・``received_ns`` は告知の「届いた情報」の行の欄(既定は 1-3 と同じ)。
    """
    cause = _Experiment(cond_id)
    return log.append(Event(t_ns=log.now_ns, who=who, what=what, whom=whom, where=where, how_much=how_much,
                            origin=origin, via=via, received_ns=received_ns, cause=cause))


#: 原因の型 ``Experiment`` を作ってよい唯一のコード(実行時の検査が呼び手のフレームのコードと比べる)。
ADMIT_CODE: Any = admit.__code__
