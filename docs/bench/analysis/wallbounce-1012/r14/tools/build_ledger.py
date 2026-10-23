"""1-4: つなぎの台帳 ``docs/design/bridging-ledger.json`` の最初の中身を作る作業用の道具(1 回だけ・記録 r14/README.md)。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/r14/tools/build_ledger.py [--check]``

- コードの宣言(``shibuya.engine.bridging.scan`` の 4 形)を全部 1 行ずつ載せる(id は build の段の宣言なら
  ``W<n>#<i>``=C8 の感度の台帳 D-44 の行の番号と同じ・第 4 形の見出しは ``HD-<モジュール>-<何個目>``・それ以外は
  ``BR-...``)。第 4 形は見出し単位で 1 行(親の判断 第334)で、台帳の末尾に置く(前の 172 行の並びを変えない)。
- 文書で宣言したつなぎ(計画 §1 の 3 の 9 件・#88 の 3 件・西武の 1 部屋・不応期 11 種と起床条件のクラス・W16 の弱点 3 件)
  を足す。
- 外す段(``remove_at``)は、計画と決定に書いてあるものは ``plan``、実装役が当てたものは ``inferred``(仮採用)。
- 段の宣言の文が f 文字列や式のときは、``data/world/v2/build_manifest.json`` に書かれた値(構築したときの文)を
  ``what`` に使う(無ければ式の文字列)。照合の鍵(``declared_in``)はコードの式から作るので data に依らない。
- ``--check``: 書かずに、今のファイルと同じ中身になるかだけを見る(差があれば 1 で終わる)。

この台帳は以後、手で直す(この道具を回し直すと手の直しが消える)。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "src"))

from shibuya.agents.state import REFRACTORY_MINUTES, WakeCondition  # noqa: E402
from shibuya.engine.bridging import ledger as L  # noqa: E402
from shibuya.engine.bridging import scan as S  # noqa: E402

SINCE = "2026-10-14"
OUT = ROOT / L.LEDGER_RELPATH
D1012 = "docs/design/v2-wallbounce-decisions-2026-10-12.md"
PLAN = "docs/design/v2-implementation-plan-2026-10-12.md"
R10E = "docs/bench/analysis/wallbounce-1012/10e/README.md"
C8 = "docs/bench/c8/sensitivity_v1.md"

#: build のファイル → 段の名(C8 の D-44 の行の番号の頭)。
FILE_STAGE = {
    "build/geo/w1_walk_graph.py": "W1", "build/geo/w2_cells.py": "W2", "build/geo/w3_distances.py": "W3",
    "build/geo/w4_heights.py": "W4", "build/geo/w5_entrances.py": "W5", "build/geo/w6_poi_org.py": "W6",
    "build/field/w7_planspec.py": "W7", "build/vis/w8_visibility.py": "W8", "build/vis/w9_shadow.py": "W9",
    "build/field/w10_noise.py": "W10", "build/geo/w11_station_exits.py": "W11",
    "build/field/w12_external_nodes.py": "W12", "build/field/w13_weather.py": "W13",
    "build/lang/w14_signage.py": "W14", "build/lang/w15_cell_static.py": "W15", "build/pop/w16_population.py": "W16",
    "build/sched/trial.py": "W17", "build/sched/w17_schedule.py": "W17v1", "build/audit/w18_coverage.py": "W18",
    "build/audit/w19_freeze.py": "W19", "build/audit/w20_acceptance_pack.py": "W20",
}

#: 段 → (外す段, 根拠, 理由)。項ごとの例外は ITEM_STAGE。
STAGE_REMOVE = {
    "W1": ("5-1", "inferred", "空間の段 1 で PLATEAU の三角形と上下の接続口から歩行の面(ナビメッシュ)を作り直す"),
    "W2": ("5-3", "inferred", "空間の段 3 でセルを廃止する"),
    "W3": ("5-1", "inferred", "空間の段 1 でナビメッシュの上の移動に替える(セル間距離の表を使わない)"),
    "W4": ("5-2", "inferred", "空間の段 2 の階の割り当てと建物の中の構造(SR14・LOD4)"),
    "W5": ("5-2", "inferred", "空間の段 2 の入口(3-7)"),
    "W6": ("5-2", "inferred", "空間の段 2 の場所の表と区画"),
    "W7": ("4-2", "inferred", "4-2 権利台帳と規則の表の中身(営業の規制・機械が守らせる/人が取り締まるの分け)"),
    "W8": ("5-3", "inferred", "空間の段 3 の気づく確率(SR7=視線の通り道を全員の位置から直接確かめる)"),
    "W9": ("7", "inferred", "置き換える段が計画に無い=主張の前に感度試験で駆動しないことを示す"),
    "W10": ("5-6", "inferred", "空間の段 6(車)で騒音を車の流れから出す(10-06 SR8・騒音は車の段で 2023 既定)"),
    "W11": ("5-1", "inferred", "空間の段 1 の上下の接続口(駅の構内=SR17 の骨組み)"),
    "W12": ("4-1", "inferred", "4-1 段 1 人数の枠(来街の時間帯と目的の構成は PT の構築側=§10-2)"),
    "W13": ("7", "inferred", "置き換える段が計画に無い=主張の前に感度試験で駆動しないことを示す"),
    "W14": ("7", "inferred", "看板の文は現実のデータで置き換えていく(10-12 §1-5 の 6)=段の番号は計画に無い"),
    "W15": ("5-3", "inferred", "空間の段 3 のセルの廃止と知覚の個人化(セルの定型文をやめる)"),
    "W16": ("4-1", "plan", "4-1 段 10 で W16 を合成人口に差し替える(計画 第 4 期)"),
    "W17": ("6-2", "inferred", "6-2 カレンダー 1b で W17 の出入り・就寝のつなぎを外す(計画 6-2)=W17 を読まなくなる"),
    "W17v1": ("6-2", "inferred", "6-2 カレンダー 1b で W17 を読まなくなる(v1 の構築の宣言)"),
    "W18": ("7", "inferred", "監査の報告(置き換える段が計画に無い)"),
    "W19": ("7", "inferred", "凍結の記録(置き換える段が計画に無い)"),
    "W20": ("7", "inferred", "受入パックの見せ方(置き換える段が計画に無い)"),
}
ITEM_STAGE = {
    "W6#1": ("4-1", "inferred", "4-1 段 4 組織と関係(PS5・開始時点の組織データ)"),
    "W6#2": ("5-3", "inferred", "空間の段 3 のセルの廃止"),
    "W6#3": ("5-0", "inferred", "空間の段 0 のデータ(OpenPOI の分類)"),
    "W9#5": ("2-3", "inferred", "2-3 複数日の mock で暦の日付ごとの影が要る。#88(10e 締め-4 の 6)の「影は SHADOW_DATES の 6 日だけ」"),
    "W10#8": ("5-3", "inferred", "空間の段 3 の音の伝わり方(SR8)"),
    "W12#4": ("2-3b", "plan", "2-3b 鉄道の実ダイヤ(W12 の等間隔の推定を実ダイヤに置き換える)"),
    "W12#5": ("2-3b", "plan", "2-3b 鉄道の実ダイヤ"),
    "W12#6": ("2-3b", "plan", "2-3b 鉄道の実ダイヤ"),
    "W12#7": ("2-3b", "plan", "2-3b 鉄道の実ダイヤ"),
    "W12#8": ("2-3b", "plan", "2-3b 鉄道の実ダイヤ"),
    "W17#2": ("3-1", "plan", "K9: カレンダー化の第 1 段(3-1)で解消するまでのつなぎ(10-12 §4-1 K9)"),
}

#: build の段でないコードの宣言(道筋 → (id, 外す段, 根拠, 理由, conf))。docstring と表は道筋と中身の頭で引く。
OTHER_CODE = [
    ("src/shibuya/engine/processes/environment.py", "天気の層が空のとき", "BR-WEATHER-STRATUM-WIDEN", "7", "inferred",
     "#88(10e 締め-4 の 5)の「層を広げる順」。置き換える段が計画に無い=感度試験で駆動しないことを示す"),
    ("src/shibuya/engine/processes/environment.py", "暦の日付の影", "BR-SHADOW-NEAREST-DAY", "2-3", "inferred",
     "#88(10e 締め-4 の 4)の「影の近い日」。2-3 複数日の mock で暦の日付ごとの影を作れば使わない"),
    ("src/shibuya/build/field/street_grid.py", "expedient:", "BR-DOC-STREET-GRID", "5-6", "inferred",
     "W10 と同じ街路格子(W10#9)。空間の段 6(車)で騒音を車の流れから出す"),
    ("src/shibuya/core/rng.py", "expedient:", "BR-DOC-RNG-KEY-FORMAT", "7", "inferred",
     "鍵の材料の形式の自前規約。置き換える段が計画に無い(TM7 (d) の鍵の材料は T0 で準備だけ)"),
    ("src/shibuya/economy/ledger.py", "expedient:", "BR-DOC-RESIDENT-CASH-ACCOUNT", "2-1", "inferred",
     "2-1 経済 EC(最初の資産は統計から=EC2・科目の整理)"),
    ("src/shibuya/manifest/schema.py", "expedient:", "BR-DOC-DECODING-FIELDS", "7", "inferred",
     "decoding の下位欄の構成の暫定形。置き換える段が計画に無い"),
    ("src/shibuya/engine/run_kind.py", "expedient:", "BR-RUN-KIND-CLI-ARMS", "3-3", "plan",
     "3-3 反実仮想の器(申込書とランの種類の記録)で決め直す(計画 3-3)"),
]


#: 第 4 形(見出し)の外す段(ファイル → (外す段, 理由)・(ファイル, 何個目) で上書き)。どれも inferred(仮採用)。
#: 当てられないものは 7(主張の前に感度試験で駆動しないことを示す)。
HEAD_NONE = "置き換える段が計画に無い(表し方・見積り・自前規約)=主張の前に感度試験で駆動しないことを示す"
HEAD_STAGE: dict = {
    "agents/schedule.py": ("3-1", "3-1 カレンダー 1a(約束をペルソナと実データから作る=mock の粗い日課をやめる)"),
    "agents/state.py": ("7", HEAD_NONE),
    "build/field/road_names.py": ("5-6", "W10 の道路名の突合(W10 と同じ=空間の段 6 の車の騒音)"),
    "build/field/w10_noise.py": ("5-6", "空間の段 6(車)で騒音を車の流れから出す"),
    "build/field/w13_weather.py": ("7", HEAD_NONE),
    "build/field/w7_planspec.py": ("4-2", "4-2 権利台帳と規則の表の中身(営業の規制)"),
    "build/lang/common.py": ("7", "W14・W15 の生成の共通の設定。" + HEAD_NONE),
    "build/lang/w14_signage.py": ("7", "看板の文は現実のデータで置き換えていく(10-12 §1-5 の 6)=段の番号は計画に無い"),
    "build/lang/w15_cell_static.py": ("5-3", "空間の段 3 のセルの廃止と知覚の個人化(セルの定型文をやめる)"),
    "build/sched/pool_facts.py": ("6-2", "W17 の構築(6-2 カレンダー 1b で W17 を読まなくなる)"),
    "build/sched/trial.py": ("6-2", "W17 の構築(6-2 カレンダー 1b で W17 を読まなくなる)"),
    "build/sched/vocab.py": ("6-2", "W17 の語彙(6-2 カレンダー 1b で W17 を読まなくなる)"),
    "build/vis/w8_visibility.py": ("5-3", "空間の段 3 の気づく確率(SR7)"),
    "core/growth.py": ("7", HEAD_NONE),
    "core/soa.py": ("7", HEAD_NONE),
    "core/types.py": ("7", HEAD_NONE),
    "economy/anchors.py": ("2-1", "2-1 経済 EC(最初の資産は統計から=EC2)"),
    "economy/census.py": ("2-1", "2-1 経済 EC"),
    "economy/checks.py": ("2-1", "2-1 経済 EC(保存則の検算)"),
    "economy/entry_capital.py": ("2-1", "2-1 経済 EC(店の資本は現実の写し=EC6)"),
    "economy/goods.py": ("2-1", "2-1 経済 EC"),
    "economy/ledger.py": ("2-1", "2-1 経済 EC"),
    "economy/pricing.py": ("2-1", "2-1 経済 EC"),
    "engine/activity.py": ("6-1", "6-1 判断モデル(活動の種別の割り当てを判断の口へ)"),
    "engine/arbiter.py": ("T3", "T3 驚き駆動(起床のクラス・昇格の待ちを外す=回答 10-13b §4-2 の 2)"),
    "engine/change_detect.py": ("7", HEAD_NONE),
    "engine/classical.py": ("7", "古典モデルは物差しとして残す(R-83 結論 5)。" + HEAD_NONE),
    "engine/commit.py": ("7", HEAD_NONE),
    "engine/conversation.py": ("5-3", "空間の段 3(会話の距離 2 m の決め打ちを外す)"),
    "engine/energy.py": ("7", "体の System 1(10-12 §1-5 ③群=コードに残す)。" + HEAD_NONE),
    "engine/familiarity.py": ("6-5", "6-5 記憶 M1〜M5(親しみの表を記憶の器に寄せる)"),
    "engine/geometry.py": ("5-1", "空間の段 1 のナビメッシュの上の移動"),
    "engine/growth_decl.py": ("7", HEAD_NONE),
    "engine/intent.py": ("6-6", "6-6 ①(意図の打ち切りは人の選択=判断モデルへ・10-12 §1-5 ①群)"),
    "engine/ledger_api.py": ("1-9", "1-9 お金の基本操作(帳簿の口を「移す」に)"),
    "engine/llm_bridge.py": ("7", HEAD_NONE),
    "engine/poi_target.py": ("5-3", "空間の段 3 の地名帳(SR5=解決の手順)"),
    "engine/presence.py": ("6-2", "6-2 カレンダー 1b(出入りを本人へ・E4 と W17 のつなぎを外す)"),
    "engine/processes/civic.py": ("6-6", "6-6 ②(出動・ホテル・報道は働く人のエージェントへ・10-12 §1-5 ②群)"),
    "engine/processes/crowd.py": ("5-2", "空間の段 2 の容量と席(SR3)"),
    "engine/processes/environment.py": ("7", HEAD_NONE),
    "engine/processes/goods_flow.py": ("6-6", "6-6 ②(補充・納品・廃棄・清掃は働く人のエージェントへ)"),
    "engine/processes/logistics.py": ("6-6", "6-6 ②(宅配・バス・道路工事は働く人のエージェントへ)"),
    "engine/processes/opening.py": ("1-5", "1-5 権利台帳の器(staff_of_poi の丸振りを台帳からの読みに)"),
    "engine/processes/rail.py": ("2-3b", "2-3b 鉄道の実ダイヤ(停車と折返し)"),
    "engine/processes/salient.py": ("7", "倒れる率は出典を探す(10-12 §1-5 D-3)。" + HEAD_NONE),
    "engine/processes/traffic.py": ("5-6", "空間の段 6(車)"),
    "engine/resolve.py": ("5-1", "空間の段 1(1 刻み=1 ノードの移動をナビメッシュの移動に)"),
    ("engine/resolve.py", 2): ("T3", "T3 驚き駆動(不応期の倍率の丸め=不応期を外す)"),
    ("engine/resolve.py", 3): ("6-2", "6-2 カレンダー 1b(D-62 就寝の計画の実行)"),
    ("engine/resolve.py", 4): ("T3", "T3 驚き駆動(不応期の戻し方=不応期を外す)"),
    "engine/run.py": ("6-7", "6-7 熟考の形(考えた時間の換算=B8 の後)"),
    "engine/scheduler.py": ("3-2", "3-2 時計 T1(計算のまとめ・事象の待ち行列の流用)"),
    "llm/__init__.py": ("7", HEAD_NONE),
    "llm/contract.py": ("6-1", "6-1 判断モデル(今の「文 → 2 行形 → パーサ → 語彙」は第 6 期で消す=計画 1-8)"),
    "llm/fleet.py": ("7", HEAD_NONE),
    "llm/parser.py": ("6-1", "6-1 判断モデル(パーサは第 6 期で消す=計画 1-8)"),
    "llm/undefined.py": ("6-1", "6-1 判断モデル(段 0 の辞書は第 6 期で消す=計画 1-8)"),
    "perception/attention.py": ("5-3", "空間の段 3 の気づく確率(SR7)"),
    "perception/channels.py": ("7", HEAD_NONE),
    "perception/hashes.py": ("7", HEAD_NONE),
    "perception/normalize.py": ("7", HEAD_NONE),
    "perception/p_notice.py": ("5-3", "空間の段 3 の気づく確率(SR7)"),
    "perception/renderer.py": ("5-3", "空間の段 3 のセルの廃止と知覚の個人化"),
    "perception/state.py": ("7", HEAD_NONE),
    "perception/templates.py": ("4-1", "4-1 段 9 見せ方(属性を言葉で・PS7)"),
    "world/assets.py": ("5-1", "空間の段 1(合成世界の格子の移動)"),
    "world/graph.py": ("5-1", "空間の段 1(1 刻み=1 ノードの移動をナビメッシュの移動に)"),
    "world/processes/actual_log.py": ("7", HEAD_NONE),
    "world/processes/constitution.py": ("7", HEAD_NONE),
    "world/processes/records.py": ("4-2", "4-2 規則の表の中身(PlanSpec の軸)"),
    "world/processes/registry.py": ("7", HEAD_NONE),
    "world/processes/relations.py": ("7", HEAD_NONE),
    "world/state.py": ("5-3", "空間の段 3(密度の段階の語=知覚の個人化)"),
}
#: 見出しが同じファイルの第 2 形(StageResult.expedients)の要旨の写しのもの(二重の宣言=台帳の件数も二重)。
HEAD_DUP = {
    rel: "同じファイルの StageResult.expedients の要旨(項は第 2 形の行と重なる)"
    for rel in ("build/field/w10_noise.py", "build/field/w13_weather.py", "build/field/w7_planspec.py",
                "build/lang/w14_signage.py", "build/lang/w15_cell_static.py", "build/sched/trial.py",
                "build/vis/w8_visibility.py")
}


def doc_rows() -> list[dict]:
    rows = [
        dict(id="BR-W17-IO-SLEEP", remove_at="6-2", remove_basis="plan",
             what="W17 の週次表から、エンジンが到着・退出・就寝・起床を実行する(計画実行層 D-66)",
             why="存在の連続性(10-12 §1-3 の 1)=出入りは境界を歩くか乗り物で越え、寝るのは本人が決める。外す時期は"
                 "カレンダーの段(CA9: 出入りは段 1b・就寝は疲労の後)。計画 6-2 で E4 と一緒に外す",
             declared_in=f"{D1012} §1-3 の 1", code_at=["src/shibuya/engine/presence.py"]),
        dict(id="BR-E4-EXIT-VANISH", remove_at="6-2", remove_basis="plan",
             what="計画実行層の E4: 退出の途中で別の行動を選ぶと、その場で範囲外へ消す(退出は即時 rail_depart)",
             why="体は消えず急に現れない(10-12 §1-3 の 1)。計画 6-2(1b 出入りを本人へ)で外す",
             declared_in=f"{D1012} §1-3 の 1", code_at=["src/shibuya/engine/presence.py"]),
        dict(id="BR-ATTENDANCE-LOTTERY", remove_at="6-6", remove_basis="plan",
             what="出勤率のくじ(attendance_rate・既定 1.0=全員来る・日番号つきの鍵で欠席を引く)",
             why="人の選択(出勤)をエンジンが決めている(10-12 §1-5 ①群)。判断モデルができるまでのつなぎ(10-12 §4-1 CA5)。"
                 "計画 6-6 ①(人の選択を判断モデルへ)",
             declared_in=f"{D1012} §4-1 CA5", code_at=["src/shibuya/engine/presence.py"]),
        dict(id="BR-K9-MONDAY", remove_at="3-1", remove_basis="plan",
             what="W17 v2 は月曜の行しか無く、火〜金も月曜の予定を使う(K9)",
             why="カレンダー化の第 1 段で解消するまでのつなぎ。この期間の複数日の結果は曜日の比較に使わない(10-12 §4-1 K9)",
             declared_in=f"{D1012} §4-1 K9", code_at=["src/shibuya/engine/presence.py"]),
        dict(id="BR-SIGNAGE-FICTION", remove_at="7", remove_basis="inferred",
             what="看板の文は W14 で LLM が書いた作り物(「作り物」の印を付けて残す)",
             why="範囲の中の情報はエージェントの行動から、範囲の外は実データを境界の入力にする。看板の文は現実のデータに"
                 "置き換わるまでのつなぎ(10-12 §4-4 CT0・§1-5 の 6)。看板に頼る結果には「看板は推定」と明記する。"
                 "置き換える段の番号は計画に無い",
             declared_in=f"{D1012} §4-4 CT0", code_at=["src/shibuya/build/lang/w14_signage.py"]),
        dict(id="BR-DELIVERY-INBOUND", remove_at="6-6", remove_basis="plan",
             what="店の入荷(世界過程 delivery_inbound)はエンジンの抽選(乱数の用途 world.delivery_inbound)",
             why="配送は本来、店の発注と配達員の行動で決まる(ユーザー決定 2026-10-07・run.py の MOTION_RNG_DOMAINS の注)。"
                 "10-12 §1-5 ②群「納品」=計画 6-6 ②(人の仕事を働く人のエージェントへ)",
             declared_in=f"{PLAN} §1 の 3",
             code_at=["src/shibuya/engine/processes/goods_flow.py", "src/shibuya/engine/run.py"]),
        dict(id="BR-THINK-TIME-TABLE", remove_at="6-7", remove_basis="plan",
             what="考えた時間の表(レーン → δ_think 秒: L0 0・L1 2.6・L2 82・L3 300・L4 0.2=LANE_SECONDS)",
             why="考えた時間は本人の出力から決める(10-12 §4-2 TM2・リサーチ B8)。それまでは今の表でつなぎ、腕で振る。"
                 "計画 6-7(考えた量がシム内の時間)",
             declared_in=f"{D1012} §4-2 TM2", code_at=["src/shibuya/engine/llm_bridge.py"]),
        dict(id="BR-THINK-ALPHA", remove_at="6-7", remove_basis="plan",
             what="考えた量からシム内の時間への仮の換算(α_think 0.04 秒/トークン・線形=ALPHA_THINK_SECONDS_PER_TOKEN)",
             why="換算は B8 の後。それまで仮の換算を宣言する(10-12 §4-7 熟考の形・計画 6-7)",
             declared_in=f"{D1012} §4-7 熟考の形", code_at=["src/shibuya/engine/llm_bridge.py"]),
        dict(id="BR-RENT-BLANK", remove_at="4-2", remove_basis="inferred",
             what="店の賃借の家賃は空欄(家賃の科目はあるが、払う行為が無い)",
             why="権利台帳の最初の中身=店の賃借は区画にいること(家賃は空欄・宣言)(10-12 §4-5 CP4・計画 1-5)。"
                 "家賃の額は 4-2(権利台帳と規則の表の中身=賃貸借)で入れる",
             declared_in=f"{D1012} §4-5 CP4", code_at=["src/shibuya/economy/accounts.py"]),
        dict(id="BR-W18-X", remove_at="7", remove_basis="inferred",
             what="W18 の被覆の表の過剰の指標 X: 天候・気温の行のカタログの現実の数 n_real が 35 日のまま"
                  "(n_sim 35 → 365 で X 0.004056 → 0.184787)",
             why="凍結カタログの改訂は 10e の外(10e 記録 §B5)。報告だけのゲート。置き換える段の番号は計画に無い",
             declared_in=f"{R10E} 締め-4 の 1", code_at=["src/shibuya/build/audit/w18_coverage.py"]),
        dict(id="BR-W12-HOLIDAY-GT-WEEKDAY", remove_at="2-3b", remove_basis="plan",
             what="等間隔の推定のダイヤで 1 日の本数が土休 > 平日(5 線とも・10e §B3 の表)",
             why="実データの時刻表で直す(回答 10-12b §2)。実データの無いまま残る線だけ同時に直す(計画 2-3b)",
             declared_in=f"{R10E} 締め-4 の 2", code_at=["src/shibuya/build/field/w12_external_nodes.py"]),
        dict(id="BR-W11-SHINSEN-EXIT", remove_at="2-3b", remove_basis="plan",
             what="W11 の神泉の出口(井の頭線の渋谷の到着の元=範囲の端の駅)",
             why="終点の到着は手前の駅(神泉)の渋谷方面の発車から作る(回答 10-12b §2-1〜3)。計画 2-3b(終点の到着)",
             declared_in=f"{R10E} 締め-4 の 3", code_at=["src/shibuya/build/geo/w11_station_exits.py"]),
        dict(id="BR-SEIBU-ONE-ROOM", remove_at="7", remove_basis="inferred",
             what="西武渋谷店は床の広さと入口だけの 1 部屋(閉店した A館・B館を含め平面図が入手できない・MR14)",
             why="既知の弱点として記録する(回答 10-13 の 5)。世界の時点 2026-07-13 では営業中=建物と店は存在させる。"
                 "西武の規約に「営利の準備」の禁止がある。作るのは空間の段 2、外す段(図が入る段)は計画に無い",
             declared_in="docs/design/v2-answers-2026-10-13.md の 5", code_at=[]),
        dict(id="BR-W16-REPLICATED-108142", remove_at="4-1", remove_basis="plan",
             what="W16 は複製で足した人を含む(実測 108,142 人=R-109)",
             why="人口の作り直しが済むまでの今の W16 の弱点(計画 第 4 期の注・回答 2-0)。4-1 段 10 で差し替える",
             declared_in=f"{PLAN} 第 4 期の注", code_at=["src/shibuya/build/pop/w16_population.py"]),
        dict(id="BR-W16-VISITOR-COUNT-BASIS", remove_at="4-1", remove_basis="plan",
             what="W16 の来街者の数の根拠が弱い(通勤+通学 249,157 は現実の 1.3〜1.6 倍=R-109)",
             why="人口の作り直しが済むまでの今の W16 の弱点(計画 第 4 期の注)。4-1 段 1(人数の枠)と段 10",
             declared_in=f"{PLAN} 第 4 期の注", code_at=["src/shibuya/build/pop/w16_population.py"]),
        dict(id="BR-W16-NO-TRANSFER-ONLY", remove_at="4-1", remove_basis="plan",
             what="駅で乗り換えるだけの人が 0(乗り換えか直通 140〜158 万回/日と JR の通過 917,279 人/日は 1 体も無い=R-109)",
             why="人口の作り直しが済むまでの今の W16 の弱点(計画 第 4 期の注)。4-1 段 1(乗り換えだけの人)と段 10",
             declared_in=f"{PLAN} 第 4 期の注", code_at=["src/shibuya/build/pop/w16_population.py"]),
    ]
    # 不応期 11 種(agents.state.REFRACTORY_MINUTES の注の mechanism/expedient を conf に写す)
    notes = {
        "CONVERSATION_TURN": ("会話ターン", "mechanism", "床なし"),
        "PLAN_SLEEPING": ("計画境界: 睡眠中", "mechanism", "起床まで≥360 分を 360 で表す"),
        "PLAN_WORKING": ("計画境界: 就業/就学中", "expedient", "GATSim の就業値"),
        "PLAN_GENERAL": ("計画境界: 一般活動", "expedient", ""),
        "PLAN_TRANSIT": ("計画境界: 移動・待機中", "expedient", ""),
        "INTEROCEPTION": ("内受容閾値", "expedient", "ヒステリシスで置換を試す"),
        "ACQUAINTANCE": ("知人出現", "expedient", "同一相手 60 分は C2 未実装"),
        "PROXIMITY_SWAP": ("近接入替", "expedient", "最大の暴発源"),
        "BEING_WATCHED": ("被注視", "expedient", ""),
        "OVERHEARD": ("傍受", "expedient", "同一話者 30 分は C2 未実装"),
        "CELL_BLOCK": ("セル動的ブロック変化", "expedient", ""),
    }
    for wc in list(WakeCondition)[: len(REFRACTORY_MINUTES)]:
        label, conf, note = notes[wc.name]
        rows.append(dict(
            id=f"BR-REFRACTORY-{wc.name.replace('_', '-')}", remove_at="T3", remove_basis="plan", conf=conf,
            what=f"不応期「{label}」{REFRACTORY_MINUTES[int(wc)]} 分(起床条件 {wc.name}・知覚契約書 §6 の表"
                 + (f"・{note}" if note else "") + ")",
            why="「いつ考えるか」(起床の検出と再呼び出しの間隔)をエンジンが強制している。驚き駆動で判断モデルへ移す"
                "(回答 10-13b §4-1)。T3 で外す(回答 10-13b §4-2 の 2・カレンダー 1b と同じ版上げ)",
            declared_in="docs/design/v2-answers-2026-10-13b.md §4-2 の 2", code_at=["src/shibuya/agents/state.py"]))
    rows.append(dict(
        id="BR-WAKE-CONDITION-CLASS", remove_at="T3", remove_basis="plan",
        what="起床条件のクラス(WakeCondition 12 種 → 繰り延べアービタの 4 クラス=WAKE_CONDITION_CLASS)",
        why="近接入替・被注視・傍受・知人出現は起床の条件でなく知覚の事実として扱う(回答 10-13b §4-2 の 1)。"
            "起床条件のクラスは T3 で外す(同 §4-2 の 2)",
        declared_in="docs/design/v2-answers-2026-10-13b.md §4-2 の 2",
        code_at=["src/shibuya/agents/state.py", "src/shibuya/engine/arbiter.py"]))
    for r in rows:
        r.setdefault("conf", "expedient")
        r.setdefault("since", SINCE)
        r.setdefault("status", "active")
    return rows


def built_texts() -> dict[str, list[str]]:
    """build_manifest に書かれた段ごとの宣言の文(構築したときの値)。無ければ空。"""
    p = ROOT / "data" / "world" / "v2" / "build_manifest.json"
    if not p.exists():
        return {}
    doc = json.loads(p.read_text(encoding="utf-8"))
    return {s["stage"]: list(s.get("expedients", [])) for s in doc["stages"]}


def heading_rows() -> list[dict]:
    """第 4 形(docstring の ``expedient(…)`` の見出し)を見出し単位で 1 行ずつ(親の判断 第334)。台帳の末尾に置く。"""
    rows: list[dict] = []
    heading_n: dict[str, int] = {}
    for d in S.scan_package():
        if d.form != S.FORM_HEADING:
            continue
        rel = d.path.removeprefix("src/shibuya/")
        heading_n[rel] = heading_n.get(rel, 0) + 1
        k = heading_n[rel]
        remove_at, reason = HEAD_STAGE.get((rel, k), HEAD_STAGE.get(rel, ("7", HEAD_NONE)))
        mod = rel.removesuffix(".py").replace("/", ".")
        what = f"{d.path} の docstring の見出し「{d.text}」の下の項 {d.items} 個" + (
            "(項の形でなく段落の文)" if d.items == 0 else "")
        dup = f"・{HEAD_DUP[rel]}" if rel in HEAD_DUP else ""
        why = (f"コードの宣言(第 4 形=docstring の expedient(…) の見出し・このファイルの {k} 個目・見出し単位で 1 行="
               f"親の判断 第334{dup})。外す段: {reason}")
        # 検収 L5: id はファイル+見出しの文の sha8(=declared_in の鍵)。見出しを足しても後ろの id がずれない
        key = d.declared_in.rsplit(":", 1)[-1]
        rows.append(dict(id=f"HD-{mod}-{key}", what=what, why=why, remove_at=remove_at, declared_in=d.declared_in,
                         conf="expedient", since=SINCE, status="active", remove_basis="inferred"))
    return rows


#: 第 5 形(世界過程と PlanSpec の宣言)と第 6 形(フォールバック台帳)の外す段。返済期限(``repayment_due``)が
#: エージェントへの置き換えを書くものは 6-6 ②(人の仕事を働く人のエージェントへ)=``declared``。データの取得を待つ
#: ものは話題で段を当てる=``inferred``(当てられないものは 7)。
PROCESS_STAGE = {
    "shelf_stock_restock": ("2-1", "2-1 経済 EC(SKU 粒度・補充の閾値とロットの較正)"),
    "delivery_inbound": ("6-6", "6-6 ②(納品は働く人のエージェントへ=BR-DELIVERY-INBOUND と同じ段)"),
    "waste_collection": ("6-6", "6-6 ②(収集は働く人のエージェントへ)"),
    "indoor_occupancy": ("5-2", "空間の段 2 の容量と席(SR3)"),
    "delivery_last_mile": ("6-6", "6-6 ②(宅配は働く人のエージェントへ)"),
    "bus_taxi_operation": ("6-6", "6-6 ②(鉄道とバスの運行は働く人のエージェントへ)"),
    "public_service_dispatch": ("6-6", "6-6 ②(出動は働く人のエージェントへ)"),
    "street_cleaning": ("6-6", "6-6 ②(清掃は働く人のエージェントへ)"),
    "infra_daily_load": ("7", HEAD_NONE),
    "road_works_occupancy": ("6-6", "6-6 ②(道路工事は働く人のエージェントへ)"),
    "press_official_release": ("6-6", "6-6 ②(報道は働く人のエージェントへ)"),
    "large_event": ("6-6", "6-6 ②(催しは働く人のエージェントへ)"),
    "plan.opening_hours": ("4-2", "4-2 規則の表の中身(営業時間=W7 と同じ段)"),
    "plan.road_works": ("6-6", "6-6 ②(道路工事は働く人のエージェントへ)"),
}


def _stage_from_repayment(ident: str, repayment_due: str) -> tuple[str, str, str]:
    """(外す段, 根拠, 理由)。"""
    if "エージェント" in repayment_due:
        return "6-6", "declared", f"返済期限「{repayment_due}」=6-6 ②(人の仕事を働く人のエージェントへ)"
    stage, reason = PROCESS_STAGE.get(ident, ("7", HEAD_NONE))
    return stage, "inferred", f"返済期限「{repayment_due}」はデータの取得待ち=話題で当てた: {reason}"


def process_rows() -> list[dict]:
    """第 5 形(``mechanism=False`` と ``repayment_due=`` の世界過程と PlanSpec の宣言)=1 つの宣言で 1 行(検収 M1)。"""
    from shibuya.world.processes import first_batch as FB

    reg = FB.build_registry()
    decl = {p.id: p for p in reg.processes}
    decl.update({s.id: s for s in reg.plan_specs})
    rows: list[dict] = []
    for d in S.scan_package():
        if d.form != S.FORM_PROCESS:
            continue
        x = decl[d.text]
        kind = "PlanSpec" if d.text.startswith("plan.") else "世界過程"
        sens = getattr(x, "sensitivity_test_id", "") or "-"
        ex = getattr(getattr(x, "executor", None), "value", "-")
        stage, basis, reason = _stage_from_repayment(d.text, str(x.repayment_due))
        rows.append(dict(
            id=f"PR-{d.text}", what=f"{kind} {d.text}(mechanism=False・executor={ex}・感度 {sens}・返済期限「{x.repayment_due}」)",
            why=f"コードの宣言(第 5 形=世界過程と PlanSpec の mechanism=False+repayment_due の宣言・CLAUDE.md §4 の"
                f" mechanism|expedient のタグ・検収 M1)。外す段: {reason}",
            remove_at=stage, declared_in=d.declared_in, conf="expedient", since=SINCE, status="active",
            remove_basis=basis))
    return rows


def fallback_rows() -> list[dict]:
    """第 6 形(conf 宣言つきフォールバック台帳 ``WorldRegistry.fallback_ledger()`` の行)=1 行で 1 行(検収 M1)。"""
    from shibuya.world.processes import first_batch as FB

    by_key = {f"{r.subject_id}|{r.plan_spec_id}": r for r in FB.build_registry().fallback_ledger()}
    rows: list[dict] = []
    for d in S.scan_package():
        if d.form != S.FORM_FALLBACK:
            continue
        r = by_key[d.text]
        stage, basis, reason = _stage_from_repayment(r.subject_id, str(r.repayment_due))
        plan = r.plan_spec_id or "(PlanSpec なし=過程そのものの代替)"
        rows.append(dict(
            id=f"FB-{r.subject_id}",
            what=(f"フォールバック台帳の行 {r.subject_id} → {plan}(executor=engine_rule・conf {r.conf}・被覆「{r.coverage}」"
                  f"・返済期限「{r.repayment_due}」)"),
            why=(f"コードの宣言(第 6 形=CLAUDE.md §3「エンジン規則でつなぐ(conf 宣言つき・カバー率を台帳へ)」の台帳"
                 f"=WorldRegistry.fallback_ledger() の行・検収 M1。同じ過程の第 5 形の行 PR-{r.subject_id} と重なる)。"
                 f"外す段: {reason}"),
            remove_at=stage, declared_in=d.declared_in, conf="expedient", since=SINCE, status="active",
            remove_basis=basis))
    return rows


def extra_doc_rows() -> list[dict]:
    """検収 M1 (c)(コードが「繋ぎ」と明記した 3 か所=文書の行)と L7(規則の表に結ぶ直書きの係数)。"""
    review = "docs/bench/analysis/wallbounce-1012/r14/review.md"
    rows = [
        dict(id="BR-START-CELL-OUTSIDE-HOME", remove_at="6-2", remove_basis="inferred",
             what="自宅セルの無い体(域外常住の通勤・通学・来街・職務)のランの初期セルを 勤務→通学→fallback の順に置く"
                  "(Population.start_cell)",
             why="コードの docstring が「W17(週次スケジュール)が入るまでの繋ぎ(expedient)」と明記(検収 M1 (c))。"
                 "体の出入りを本人へ渡す 6-2(カレンダー 1b)で外す",
             declared_in=f"{review} M1(繋ぎと明記した 3 か所)", code_at=["src/shibuya/agents/population.py"]),
        dict(id="BR-MOCK-SCHEDULE-POPULATION", remove_at="6-2", remove_basis="inferred",
             what="mock 日課の拠点・種別を W16 母集団で置き換え、時刻帯は W17 まで mock のまま(域外常住の体は "
                  "start_cell の規約で置く)",
             why="コードの docstring が「W17 が入るまでの繋ぎ・expedient」と明記(engine/run.py の "
                 "_schedule_with_population・検収 M1 (c))。6-2(カレンダー 1b)で外す",
             declared_in=f"{review} M1(繋ぎと明記した 3 か所)", code_at=["src/shibuya/engine/run.py"]),
        dict(id="BR-MOCK-ACTION-ANCHOR", remove_at="6-1", remove_basis="inferred",
             what="mock の語彙 v3 の出力の行為の分布の錨(渡された語彙の一様)",
             why="コードの docstring が「行為の分布の錨は D-119 の古典モデルが来るまでの繋ぎ(expedient)」と明記"
                 "(llm/mock.py・検収 M1 (c))。古典モデルと判断モデル(6-1)が来たら mock は配管だけにする",
             declared_in=f"{review} M1(繋ぎと明記した 3 か所)", code_at=["src/shibuya/llm/mock.py"]),
        dict(id="BR-MIN-WAGE-HOURLY-1226", remove_at="4-2", remove_basis="plan", rule_id="minimum_wage.tokyo",
             what="economy/anchors.py の MIN_WAGE_HOURLY = 1_226(東京都の最低賃金の直書き=世界の時点の値)",
             why="口の約束 1-4 の約束 (1)「既存の直書きの係数は 4-2 まで残す=つなぎとして台帳へ」。規則の表の "
                 "minimum_wage.tokyo(1,280 円・2026-10-01〜)に結ぶ。1,226 円の版は R-106 で △=4-2 で表に足して読み替える"
                 "(検収 L7)",
             declared_in="docs/design/v2-foundation-contracts-2026-10-13.md 1-4 約束 (1)",
             code_at=["src/shibuya/economy/anchors.py"]),
    ]
    for r in rows:
        r.setdefault("conf", "expedient")
        r.setdefault("since", SINCE)
        r.setdefault("status", "active")
    return rows


def code_rows() -> list[dict]:
    decls = [d for d in S.scan_package() if d.form in (S.FORM_CONF, S.FORM_EXPEDIENTS, S.FORM_DOCSTRING)]
    built = built_texts()
    per_stage: dict[str, int] = {}
    rows: list[dict] = []
    for d in decls:
        rel = d.path.removeprefix("src/shibuya/")
        stage = FILE_STAGE.get(rel) if d.form == S.FORM_EXPEDIENTS else None
        if stage is not None:
            per_stage[stage] = per_stage.get(stage, 0) + 1
            i = per_stage[stage]
            rid = f"{stage}#{i}"
            remove_at, basis, reason = ITEM_STAGE.get(rid, STAGE_REMOVE[stage])
            texts = built.get(stage, []) if stage != "W17v1" else []
            what = texts[i - 1] if i - 1 < len(texts) and d.text != texts[i - 1] and not _is_literal(d) else d.text
            if stage == "W17v1":
                ref = "W17 v1 の構築(今の資産の W17 は v2=sched/trial.py)。C8 の D-44 の行は無い"
            else:
                ref = f"C8 の感度の台帳 {C8} の D-44 の行 {rid}"
            why = f"構築の段 {stage} が宣言した近似(StageResult.expedients の {i} 番目・{ref})。外す段: {reason}"
            rows.append(dict(id=rid, what=what, why=why, remove_at=remove_at, declared_in=d.declared_in,
                             conf="expedient", since=SINCE, status="active", remove_basis=basis))
            continue
        hit = [o for o in OTHER_CODE if o[0] == d.path and d.text.startswith(o[1])]
        if len(hit) != 1:
            raise SystemExit(f"台帳の行を決められない宣言: {d.path}:{d.line} {d.text[:60]!r}")
        _, _, rid, remove_at, basis, reason = hit[0]
        rows.append(dict(id=rid, what=d.text, why=f"コードの宣言({d.form})。外す段: {reason}", remove_at=remove_at,
                         declared_in=d.declared_in, conf="expedient", since=SINCE, status="active",
                         remove_basis=basis))
    return rows


def _is_literal(d: S.Declaration) -> bool:
    return not (d.text.startswith(("f'", 'f"')) or " if " in d.text)


def main(argv: list[str]) -> int:
    rows = [L.Bridge.from_dict(r).as_dict()  # 欄の順をそろえる(前に載せた行の並びは変えず、足した行は末尾)
            for r in code_rows() + doc_rows() + heading_rows() + process_rows() + fallback_rows() + extra_doc_rows()]
    doc = {
        "schema": L.SCHEMA,
        "note": "つなぎの台帳(第 1 期 1-4・CA8・計器の最初・計画 10-12 §1 の 3)。1 行=Bridge(src/shibuya/engine/bridging/"
                "ledger.py)。declared_in が src/...#<形>:<鍵> の行はコードの expedient の宣言(scan.py の 6 形=conf・"
                "expedients・docstring の expedient: の段落・docstring の expedient(…) の見出し(見出し単位)・世界過程と "
                "PlanSpec の mechanism=False+repayment_due の宣言・フォールバック台帳の行)と 1 対 1(試験 "
                "tests/engine/bridging/test_bridging_ledger.py)。docs/... の行は文書で宣言したつなぎ。remove_at は"
                "計画の段の番号(5-N=空間の段 N・T3=時計の段・7=第 7 期=外す段が計画に無く主張の前に感度試験で示す)。"
                "remove_basis: plan=計画・決定に段が書いてある / declared=コードの返済期限から読み替えた / inferred="
                "実装役が当てた(仮採用)。bridges_count(active の行の数)は宣言の行の数で、一意のつなぎの数ではない"
                "(同じ近似を 2 か所以上で宣言した行がある=記録 r14/README.md §3-3)。最初の中身は "
                "docs/bench/analysis/wallbounce-1012/r14/tools/build_ledger.py で作った(以後は手で直す)。",
        "bridges": rows,
    }
    led = L.BridgeLedger([L.Bridge.from_dict(r) for r in rows])  # 欄の検査
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    if "--check" in argv:
        same = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("same" if same else "differs")
        return 0 if same else 1
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"{len(led)} 行(active {led.count()})・外す段 {led.by_remove_at()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
