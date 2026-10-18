"""engine.contact.calls — 電話の会話(第 6 期 6-4 C1・決定 10-12 §4-4 CT1「TM3 の会話の仕組みがそのまま使える」・§4-2 TM1・TM3)。

正: CT1(電話を入れるのは TM3 の会話の仕組みがそのまま使えるため)・TM1(電話は窓の境目で届け、出るかは本人)・TM3(発言は
モーラ数・まとめの中は時刻順・上限は安全装置だけで当たったら記録・会話の LLM の入力には聞こえた範囲の相手の発言が入る)・
発注「通話=対面の会話と同じ器・場所が違うだけ。出る/出ない・切るは本人。通話中は心の向き=通話」。

- :class:`CallManager`: ``engine.conversation.ConversationManager`` をそのまま使う子クラス(足すのは状態台帳の腕の名だけ)。
  セッション(``Session``)・1 人 1 会話(話し中)・話す番の交替・番の数の上限(``max_turns``=安全装置)・沈黙のソフト終了・
  寿命・締め → 終わり・``close_now``(切る=本人)は対面の会話と同じコード。違うのは場所(``cell=-1``=同じセルの門を見ない=
  網でつながる)と、招待の答えがいつも本人の判断(``answered=True``=出ると答えたときだけ開く・出ないは開かない=エンジンの
  応答確率 0.8 は引かない)。拒否の記憶(同じ対の招待の門)は出ないで書かない(かけ直すのは本人=門で止めない)。
  持ち主の道筋 ``contact.calls``(状態台帳の腕の行 ``CT1K``・``CT1KM``)。
- :class:`CallSpeechPort`: ``engine.speech.port.SpeechPort`` の子クラス(足すのは腕の名と口の名だけ)。通話の番の発話を
  ``Utterance``(届け先=相手・道具=通話・モーラ数)で 1 回だけ出来事の記録に書き(``行為:発話``・via=通話)、相手の次の番の
  入力(聞こえた相手の発言=``take_heard``)に積む。持ち主の道筋 ``contact.speech``(状態台帳の腕の行 ``CT1S``・``CT1SM``)。

逐次ループ宣言: なし(親のクラスの宣言のまま=活動中のセッションの数ぶん)。
"""

from __future__ import annotations

from typing import Final

from shibuya.engine.contact.arm import LEDGER_ARM
from shibuya.engine.conversation import ConversationManager
from shibuya.engine.speech.port import SpeechPort

__all__ = ["CallManager", "CallSpeechPort", "VIA_CALL"]

#: 通話の道具の語(1-3 の ``Event.via``=CT9)。
VIA_CALL: Final[str] = "通話"


class CallManager(ConversationManager):
    """電話の会話(対面の会話の仕組みそのまま・場所が違うだけ)。"""

    LEDGER_ARM: Final[str] = LEDGER_ARM

    def __init__(self, master_seed: int | str) -> None:
        super().__init__(master_seed, max_participants=2)


class CallSpeechPort(SpeechPort):
    """通話の発話の口(発話の口そのまま・道具=通話)。"""

    name: str = "call"
    LEDGER_ARM: str = LEDGER_ARM
