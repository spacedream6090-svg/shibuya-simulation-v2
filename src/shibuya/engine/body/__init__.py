"""engine.body — 本人の体と System 1 の層(第 3 期 3-5・③ 群=意図しない体と System 1 の反応)。

正: 決定 10-12 §1-5(55 件の 3 群の ③=ロンバード効果・空腹と疲れ・体感温度・急に倒れる・混雑の中の歩き方と避け方・
大きな音に注意が向く=本人の体と System 1 としてコードに残す。研究で「意図しない」と裏付けがあり選択を決めないものに
限る)・D の論点 3(体の生理と急変=本人の体・倒れる率は出典を探す)・§4-2 TM5(体の変化は次に段階の境目を越える時刻を
予約する・全員を毎回見る版と一致することが受入)・計画 10-12 の 3-5 の行。

| モジュール | 中身 |
|---|---|
| :mod:`engine.body.rules` | 規則の値と純関数(3-5 より前の ``resolve.advance_body``・``processes/environment.py``・``processes/salient.py``・``resolve.initialize`` と同じ値)と出典の表 ``BODY_RULES`` |
| :mod:`engine.body.model` | 持ち主 ``BodyModel``(書く口は ``step``・``initial`` だけ)と manifest の ``body`` |
| :mod:`engine.body.schedule` | TM5 の予約の口(腕 ``--body-schedule {sweep,reserve}``・既定 sweep) |
| :mod:`engine.body.system1` | 器だけの 3 件(ロンバード効果・混雑の中の歩き方と避け方・大きな音に注意が向く=値は空) |

SoA への書き込みは今までどおり ``engine.resolve`` だけ(体の層は書く値を返す)。
"""

from shibuya.engine.body.model import BodyModel
from shibuya.engine.body.schedule import ARM_RESERVE, ARM_SWEEP, ARMS, DEFAULT_ARM, arm, set_arm

__all__ = ["BodyModel", "ARM_SWEEP", "ARM_RESERVE", "ARMS", "DEFAULT_ARM", "arm", "set_arm"]
