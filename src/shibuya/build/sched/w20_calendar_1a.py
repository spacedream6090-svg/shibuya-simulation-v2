"""build.sched.w20_calendar_1a — 構築側の段 W20(暦 1a・勤務と授業の約束の週の表・第 3 期 3-1)。

正典
    決定 ``docs/design/v2-wallbounce-decisions-2026-10-12.md`` §4-1 CA1(約束はペルソナと実データから直接作る・W17 から
    写さない・決まっていない予定は空欄・勤務の時刻は始業と終業の統計が見つかるまで社会生活基本調査 第 31/36 表からの
    逆算でつなぐ=「入力の写しになる」・曜日は産業別と雇用形態別の統計・休むかどうかは本人・正規は毎週固定で非正規と
    シフトは週ごと・勤務場所は職業で種類を分ける・学校の時程と休業日は取得の許可の後・duty_role は v1 の在庫=経済
    センサスの従業上の地位で引き直す)・CA2 (a)(影の段)・CA9(1a はペルソナの作り直しを待たない)。計画
    ``docs/design/v2-implementation-plan-2026-10-12.md`` の 3-1 と第 4 期の注(人口に依る部分は**属性から作る関数**の形)。
    答申 R-99(``docs/research/v2-r99-work-schedule-public-statistics.md``)。

段の名
    既存の段 ``W20`` は検収パック(``build/audit/w20_acceptance_pack.py``)の名なので、本段の id は ``W20cal``(暦 1a)、
    ヘッダは ``calendar_1a.header.json``(``W*.header.json`` の glob=W18〜W20 の数の読みに当たらない名)。
    ``build.run`` の ``ALL_STAGES`` には入れない(``c9c_walkable_area`` と同じ脇の段)。資産は
    ``data/world/v2_stage_3-1/`` に組み、本体の ``data/world/v2`` への活性化は版上げ 3 回目(親が決める)。

属性から作る関数(人口が変わっても作り直しにならない形)
    1. :func:`attributes_from_world` — W16 の体の表+ペルソナの素材(``persona_pool_v2``)→ :class:`Attributes`。
       4-1(ペルソナの作り直し)では、ここだけを新しい人口の読み口に差し替える。
    2. :func:`draw_employment_status` — 従業上の地位(経済センサス 第6-2表=渋谷区 × 産業中分類)を引き直す(A3)。
       新しい人口が地位を持てば、この段を飛ばしてその値を渡す。
    3. :func:`calendar_from_attributes` — 属性と地位 → 週の表(体 × 週 × 曜日 × 欄)。
    4. :func:`annual_check` — 第19表との年間の整合の計器(診断)。

材料(表ごとの区分=パターン台帳 §10・親の判断 2026-10-15)
    ========================================  ==============  ==========================================
    表                                        区分            使いみち
    ========================================  ==============  ==========================================
    社会生活基本調査 第31/36表(平均時刻編)  構築側          出勤・帰宅の時刻(既存の錨 commute_time_dist_r3.json)
    社会生活基本調査 第74-6表(東京都)       構築側          従業上の地位・勤務形態 × 曜日の仕事の率=曜日の予定の率
    社会生活基本調査 第74-9表(東京都)       構築側          職業 × 曜日=duty_role の体だけ職業/総数の比
    就業構造基本調査 2022 第19表(特別区部)  構築側(別調査)  年間就業日数=年間の整合の計器(診断・合否なし)
    経済センサス 2021 第6-2表(渋谷区)        構築側(別調査)  産業中分類 × 従業上の地位 6 区分=duty_role の地位の引き直し
    社会生活基本調査 第14表・第15-1〜3表      検証側          **開かない**(:data:`R99_VALIDATION_FILES`)
    社会生活基本調査 第68-3表                  検証側          **開かない**
    ========================================  ==============  ==========================================

    検証側のファイルは守り(:class:`R99Guard`)が開く前に落とす(名で縛る+監査フック)。``research_cache/r99`` の下で
    開いてよいのは :data:`R99_BUILD_FILES` の 4 本だけ。

表の欄(``w20_calendar_1a.parquet``・行=体 × 週 × 曜日・``agent_id``・``week``・``weekday`` の昇順)
    ``commit``(0 なし=空欄・1 勤務・2 授業)・``start_min``/``end_min``(約束の始まりと終わり[分]・空欄 −1・終わりは
    1 日の分を超えうる=翌日)・``depart_min``/``return_min``(出勤=家を出る・帰宅=家に着く[分]・空欄 −1)・``lead_min``
    (片道の通勤時間[分]・空欄 −1)・``place_kind``(:data:`PLACE_WORDS`)・``target_cell``・``certainty``(0 空欄・
    1 確定・2 仮=1a は使わない)・``recurrence``(0 なし・1 毎週固定・2 週ごとの抽選・3 規則)・``placement``(置き場所=
    CA3・1a は空欄 0)・``origin_conv``(元の会話=CA3・1a は無い −1)・``status``(:data:`STATUS_WORDS`)・``emp_row``
    (第 31/36 表の行=:data:`EMP_ROWS`)・``status_source``(地位の出どころ=:data:`STATUS_SOURCE_WORDS`)・``occ``
    (第 74-9 表の職業=:data:`OCC_ROWS`・duty_role の体だけ・−1=無し)。
    休む日の行は ``commit=0``(休むかどうかは本人の判断=表には予定だけ)。

属性の出どころ(親の判断 2026-10-15・第 4 期 段 0 の答申 R-116 §5 からの接続)
    1. W16 に職業の列が無い=第74-9表(職業 × 曜日)は直接は引けない。曜日の仕事の率は**第74-6表(従業上の地位・勤務
       形態 × 曜日・東京都)を第一に**使う。職業が分かるのは duty_role の体だけ(:data:`DUTY_ROLE_SPEC`=役割 → 職業の
       当てはめ)で、その体だけ第74-9表の職業/総数の比を掛ける。産業 → 職業の写像は使わない。勤務場所の種類も duty_role の
       表だけで決め、W16 の事業所の体は建物(第 4 期 段 3 で職業の列が入ったら差し替え=外す段 4-1)。
    2. 公務(産業大分類 S)は ``industry_key`` の 15 語に無い=新しい語を足さず**空欄**(警察官・消防士・救急隊員・指令・
       議員の産業の欄・ペルソナの ``PA``)。
    3. 従業上の地位は W16 に無い=ペルソナの ``employment``(正規・非正規・役員・自営業主・家族従業者・非就業の 6 値・
       国勢調査由来)から作り、第6-2表の 6 区分への写像(正規=無期・非正規=有期・役員=有給役員・自営業主=個人業主・
       家族従業者=無給の家族)を宣言する(第 4 期 段 3 で置き換え=外す段 4-1)。W16 が席を当てたのにペルソナの
       ``employment`` が「非就業」の体(種別 2 の 1,230 体)は**勤務の約束を空欄**にする(席は W16 のまま・数を
       ``seat_nonworking`` に出す=つなぎの台帳 DOC-ca31-w16-seat-but-nonworking・親の判断 第336 (3))。ペルソナの無い
       指令(公務)は正規の行(数える)。
    4. duty_role(v1 の在庫)の体だけ、経済センサス 第6-2表(渋谷区・中分類)の従業上の地位で引き直す(発注文どおり・
       第 4 期 段 4 で置き換え)。
    5. W16 の席(種別 0・2)があってペルソナが学校段階(高校など)か学校のセルを持つ体は、**席を優先して勤務の約束**にし、
       授業は空欄にする(数を ``seat_and_school`` に出す=つなぎの台帳 DOC-ca31-w16-seat-and-school・親の判断 第337 中 1)。
    6. **週 1 日の休み**: 労働基準法 9 条の労働者に当たる雇われる側(無期・有期・臨時。ペルソナの無い指令=正規の行も含む)の
       体は、その週に 7 日とも勤務を引いたら 1 日を休みにする。根拠は規則の表の行 ``labor.weekly_rest_day``(労働基準法
       第 35 条 1 項「毎週少くとも一回の休日」・``docs/design/rules-table.json``・対象の地位は行の ``applies_to_status``)。
       休みの曜日は、その曜日の働かない率(1 − 第74-6表の率)に比例して体・週の鍵で引く(当てはめ=つなぎの台帳 W20cal#9・
       親の判断 第337 (2))。自営業主・家族従業者と有給役員(9 条の労働者に当たらない=親の判断 第337 (1))は対象の外=週 7 日を
       制約しない。35 条 2 項(4 週 4 日の変形休日制)は入れない。

expedient(本モジュール分・つなぎの台帳へ。未リサーチ=実装役の当てはめ)
    - 始業と終業は第 31/36 表の逆算=**入力の写し**(実企業の始業・終業のデータが無い=R-99 A1 の空欄)。出勤と帰宅は
      同じ一様変数で引く(早く出る人は早く帰る=順位の相関 1)。始業=出勤+片道の通勤時間・終業=帰宅−片道の通勤時間・
      勤務の長さを [4 時間, 12 時間] に切る(W17 v2 の下見と同じ値)。切った体の帰宅は終業+片道の通勤時間に作り直す
      (終業 ≤ 帰宅)。土日も平日の表で引く(第 31/36 表は平日の行)。
    - 片道の通勤時間はペルソナの ``arrival_lead_min``(v1 の在庫・意味は未確認)・無ければ 30 分。
    - 曜日の予定の率=第74-6表(東京都)の地位・勤務形態の行の「仕事」の行動者率(平日/土/日)そのもの(親の判断 第336
      (1)=実現値=休んだ後の率なので予定の率の下限・予定はこれを下回らない)。duty_role の体だけ第74-9表の職業/総数の比を
      掛ける(独立の掛け算・上限 1)。曜日ごとに独立に引く(週の日数の分布の形は確かめていない=平均だけ)。対象の地位で 7 日とも
      勤務を引いた週は、働かない率に比例して 1 日を休みにする(休みの曜日の選び方は当てはめ・週 1 日の休みそのものは規則の
      表の行=上の「属性の出どころ」の 6・休みを入れた分だけ実現の率は第74-6表の率を少し下回る=記録 ca31 §4-1)。週の日数=
      5×平日の率+土の率+日の率。第19表(特別区部)の年間就業日数(階級の中央の値・300 日以上は 320)は**年間の整合の
      計器**(予定の日数 × 365/7 と並べる・その比=稼働率の読み・診断・合否なし)。
    - 従業上の地位=ペルソナの ``employment`` の 6 値 → 第6-2表の 6 区分への写像(上の 3)→ 第 31/36 表の行: 無期=正規・
      有期=非正規(第31表の全国の人数比で 5 つに按分)・臨時=アルバイト・有給役員=会社などの役員・個人業主=業主(人数比
      28:72)・無給の家族=家族従業者。ペルソナの無い体(指令)は正規の行(数える)。
    - duty_role → 職業・産業・中分類・場所・交替制の表 :data:`DUTY_ROLE_SPEC`(職業分類と産業分類の当てはめ)。duty_role の
      体だけ第6-2表で地位を引き直す。交替制(シフト)は週ごとの抽選。夜勤の型(2 交替・3 交替)は空欄(R-99 §空欄 4)=
      時刻は第 31/36 表のまま。W16 の事業所の体の勤務場所は建物(職業の列が無い)。
    - 公務は産業の鍵の 15 語に無い=産業の欄は空欄(新しい語を足さない)・第19表は産業の総数の行。
    - 学校: 授業の時間帯は空欄(公式の時程の取得は許可の後)・通学の曜日は月〜金(規則)。保育所は授業でない=空欄。
    - 週は ``N_WEEKS`` 週(既定 1=2026-07-13 の週)。祝日を含むランは第 3 段まで回さない(CA1)ので 1 週で足りる。

逐次ループ宣言(P4)
    構築時 1 回: プールの行数ぶん(必要な行だけ ``json.loads``)・xlsx の行数ぶん(4 本・ストリームで読む)・第 31/36 表の
    行の名ぶん(10)・曜日 × 週(7 × ``N_WEEKS``)・属性の文字列の欄の読み替え(``attributes_from_columns``=体の数ぶん)。
    抽選と時刻と曜日は配列で引く(体の数に比例するのは属性の読み替えの 1 本だけ)。
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Final, Iterator, Mapping, Sequence

import numpy as np
import pyarrow as pa

from shibuya.core.rng import k19_counter_array, philox_array, unit_float
from shibuya.core.time_consts import MINUTES_PER_DAY

from ..geo import common as C
from ..pop.w16_population import (
    KIND_COMMUTER,
    KIND_DISPATCHER,
    KIND_RESIDENT,
    KIND_STUDENT,
    KIND_WORKER,
)
from . import pool_facts as PF
from . import trial as TR

__all__ = [
    "STAGE",
    "STAGE_VERSION",
    "HEADER_NAME",
    "OUTPUT_NAME",
    "MATERIALS_NAME",
    "R99_BUILD_FILES",
    "R99_VALIDATION_FILES",
    "INPUT_FAMILIES",
    "INPUT_FILES",
    "R99Guard",
    "ValidationTableError",
    "Attributes",
    "Employment",
    "Materials",
    "attributes_from_world",
    "draw_employment_status",
    "calendar_from_attributes",
    "build_materials",
    "load_materials",
    "run",
    "main",
]

STAGE: Final[str] = "W20cal"
STAGE_VERSION: Final[str] = "1.0.0"
HEADER_NAME: Final[str] = "calendar_1a.header.json"
OUTPUT_NAME: Final[str] = "w20_calendar_1a.parquet"
MATERIALS_NAME: Final[str] = "w20_calendar_1a_materials.json"
SCHEMA: Final[str] = "shibuya.build.sched/w20_calendar_1a/1"
#: 抽選の鍵(``core.rng.philox_array`` の master seed=文字列)。体・週・曜日はカウンタの側(10c の counter の鍵)。
SEED_KEY: Final[str] = "shibuya.build.sched/W20cal/v1"
#: 週 0 の月曜(``engine.calendar.DEFAULT_WORLD_START`` と同じ日=試験が突き合わせる)。
WEEK0_MONDAY: Final[str] = "2026-07-13"
#: 表に持つ週の数(既定 1・祝日を含むランは第 3 段まで回さない=CA1)。
N_WEEKS: Final[int] = 1
N_DAYS: Final[int] = 7
#: 1 年の日数(年間就業日数 → 週の日数)。
DAYS_PER_YEAR: Final[int] = 365
#: 曜日 → 曜日の型(0 平日・1 土・2 日)。
DAY_TYPE_OF_WEEKDAY: Final[tuple[int, ...]] = (0, 0, 0, 0, 0, 1, 2)
DAY_TYPE_COUNT: Final[tuple[int, int, int]] = (5, 1, 1)

# ----------------------------------------------------------------------------- 入力
R99_DIR: Final[tuple[str, ...]] = ("research_cache", "r99")
#: 構築側に使ってよい 4 本(親の判断 2026-10-15)。
R99_BUILD_FILES: Final[dict[str, str]] = {
    "74-9": "ssb2021_seikatsu_t74-9_occupation_pref.xlsx",
    "74-6": "ssb2021_seikatsu_t74-6_workstyle_pref.xlsx",
    "19": "shugyo2022_pref_t19_industry_days.xlsx",
    "6-2": "ecensus2021_t6-2_industry_status_muni.xlsx",
}
#: 検証側(開かない)。第14表・第15-1〜3表(時間帯別の行動者率)・第68-3表(行動の種類別・全体)。
R99_VALIDATION_FILES: Final[tuple[str, ...]] = (
    "ssb2021_jikantai_t14_occupation.xlsx",
    "ssb2021_jikantai_t15-1_emp_weekday.xlsx",
    "ssb2021_jikantai_t15-2_emp_sat.xlsx",
    "ssb2021_jikantai_t15-3_emp_sun.xlsx",
    "ssb2021_seikatsu_t68-3_activity_pref.xlsx",
)
#: 表の出典(MANIFEST.md の statInfId)。
R99_SOURCES: Final[dict[str, dict[str, str]]] = {
    "74-9": {"survey": "令和3年社会生活基本調査 生活時間編", "statInfId": "000032224240",
             "title": "第74-9表 曜日,男女,職業,行動の種類別行動者率(有業者)-全国,都道府県"},
    "74-6": {"survey": "令和3年社会生活基本調査 生活時間編", "statInfId": "000032224237",
             "title": "第74-6表 曜日,男女,従業上の地位,勤務形態,行動の種類別行動者率(有業者)-全国,都道府県"},
    "19": {"survey": "令和4年就業構造基本調査 地域結果", "statInfId": "000040077594",
           "title": "第19表 男女、従業上の地位・雇用形態・起業の有無、産業(3 部門)、年間就業日数・就業の規則性・"
                    "週間就業時間別人口(有業者)"},
    "6-2": {"survey": "令和3年経済センサス-活動調査", "statInfId": "000040067881",
            "title": "第6-2表 産業(中分類)、従業上の地位(6区分)、男女別従業者数(民営事業所)-全国、都道府県、市区町村"},
}
#: 産業の鍵 → 経済センサスの大分類・中分類(W16 の入力=町丁目別の表の ``_meta.sim_mapping``)。
CENSUS_MAP_FILE: Final[tuple[str, ...]] = ("realworld", "census_r3", "station_area_industry.json")
#: 本段の data 根の入力(W19 の資産表に載る)。第 31/36 表の錨は data 根の外(``docs/bench/anchors``)。
INPUT_FILES: Final[tuple[tuple[str, ...], ...]] = (
    *(R99_DIR + (name,) for name in R99_BUILD_FILES.values()),
    CENSUS_MAP_FILE,
)
#: 層の元(W19 の ``BUILD_INPUT_FAMILIES``)。元の語は「提供元/データセット」。
INPUT_FAMILIES: Final[dict[str, tuple[str, ...]]] = {
    "estat/ssb2021_seikatsu_tokyo": tuple("/".join(R99_DIR + (R99_BUILD_FILES[k],)) for k in ("74-9", "74-6")),
    "estat/shugyo2022_regional": ("/".join(R99_DIR + (R99_BUILD_FILES["19"],)),),
    "estat/ecensus2021_muni": ("/".join(R99_DIR + (R99_BUILD_FILES["6-2"],)),),
}

# ----------------------------------------------------------------------------- 符号
COMMIT_NONE, COMMIT_WORK, COMMIT_SCHOOL = 0, 1, 2
COMMIT_WORDS: Final[tuple[str, ...]] = ("なし", "勤務", "授業")
PLACE_NONE, PLACE_BUILDING, PLACE_STATION, PLACE_AREA, PLACE_VEHICLE, PLACE_SCHOOL, PLACE_OUTSIDE, PLACE_HOME = range(8)
#: 勤務場所の種類(CA1「建物・駅・担当区域・乗り物」+学校・域外・自宅)。
PLACE_WORDS: Final[tuple[str, ...]] = ("なし", "建物", "駅", "担当区域", "乗り物", "学校", "域外", "自宅")
RECUR_NONE, RECUR_FIXED, RECUR_WEEKLY, RECUR_RULE = range(4)
RECUR_WORDS: Final[tuple[str, ...]] = ("なし", "毎週固定", "週ごとの抽選", "規則")
CERT_BLANK, CERT_FIXED, CERT_TENTATIVE = range(3)
CERT_WORDS: Final[tuple[str, ...]] = ("空欄", "確定", "仮")
PLACEMENT_BLANK: Final[int] = 0
ORIGIN_NONE: Final[int] = -1
BLANK: Final[int] = -1
#: 従業上の地位(経済センサス 6 区分+区分の外 2 つ)。
ST_NONE, ST_SOLE, ST_FAMILY, ST_OFFICER, ST_INDEF, ST_FIXED_TERM, ST_TEMP = range(7)
STATUS_WORDS: Final[tuple[str, ...]] = (
    "なし", "個人業主", "無給の家族従業者", "有給役員", "無期雇用者", "有期雇用者", "臨時雇用者",
)
#: 地位の出どころ(0 なし・1 ペルソナの employment の写像・2 第6-2表の引き直し(duty_role)・3 ペルソナが無い(指令)=正規)。
SRC_NONE, SRC_EMPLOYMENT, SRC_CENSUS, SRC_MISSING = range(4)
STATUS_SOURCE_WORDS: Final[tuple[str, ...]] = ("なし", "ペルソナの employment", "第6-2表の引き直し", "ペルソナ無し=正規")
#: ペルソナの ``employment``(国勢調査の 6 値)→ 第6-2表の 6 区分(親の判断 2026-10-15 の 3・expedient)。
EMPLOYMENT_TO_STATUS: Final[dict[str, int]] = {
    "正規": ST_INDEF, "非正規": ST_FIXED_TERM, "役員": ST_OFFICER, "自営業主": ST_SOLE, "家族従業者": ST_FAMILY,
}
#: 第 6-2 表の地位の列(行の数の並び=抽出した値の並び)。
CENSUS_STATUS_COLS: Final[tuple[tuple[int, int], ...]] = (
    (ST_SOLE, 8), (ST_FAMILY, 11), (ST_OFFICER, 14), (ST_INDEF, 20), (ST_FIXED_TERM, 23), (ST_TEMP, 26),
)
#: 第 31/36 表の行(錨 commute_time_dist_r3.json の行の名)。
EMP_ROWS: Final[tuple[str, ...]] = (
    "正規の職員・従業員", "パート", "アルバイト", "契約社員", "嘱託", "派遣社員", "会社などの役員",
    "雇人のある業主", "雇人のない業主", "家族従業者",
)
_ROW_IDX: Final[dict[str, int]] = {n: i for i, n in enumerate(EMP_ROWS)}
#: 毎週固定でない(週ごとの抽選)行=非正規(臨時を含む)。
WEEKLY_ROWS: Final[frozenset[str]] = frozenset({"パート", "アルバイト", "契約社員", "嘱託", "派遣社員"})
#: 第74-9表の職業の行(大分類 10+農林漁業)。−1=総数の行。
OCC_ROWS: Final[tuple[str, ...]] = (
    "管理的職業従事者", "専門的・技術的職業従事者", "事務従事者", "販売従事者", "サービス職業従事者",
    "保安職業従事者", "生産工程従事者", "輸送・機械運転従事者", "建設・採掘従事者", "運搬・清掃・包装等従事者",
    "農林漁業従事者",
)
_OCC_IDX: Final[dict[str, int]] = {n: i for i, n in enumerate(OCC_ROWS)}
#: 第 31/36 表の行 → 第19表の雇用形態の行。
EMP_ROW_TO_19: Final[dict[str, str]] = {
    "正規の職員・従業員": "321_正規の職員・従業員", "パート": "3221_うちパート", "アルバイト": "3222_うちアルバイト",
    "派遣社員": "3223_うち労働者派遣事業所の派遣社員", "契約社員": "3224_うち契約社員", "嘱託": "322_非正規の職員・従業員",
    "会社などの役員": "31_会社などの役員", "雇人のある業主": "1_自営業主", "雇人のない業主": "1_自営業主",
    "家族従業者": "2_家族従業者",
}
#: 第 31/36 表の行 → 第74-6表の(従業上の地位, 勤務形態)の行と、比の分母の行。
EMP_ROW_TO_746: Final[dict[str, tuple[str, str]]] = {
    "正規の職員・従業員": ("1_うち雇用されている人|1_フルタイム", "1_うち雇用されている人|0_総数"),
    "会社などの役員": ("1_うち雇用されている人|1_フルタイム", "1_うち雇用されている人|0_総数"),
    "契約社員": ("1_うち雇用されている人|1_フルタイム", "1_うち雇用されている人|0_総数"),
    "嘱託": ("1_うち雇用されている人|1_フルタイム", "1_うち雇用されている人|0_総数"),
    "派遣社員": ("1_うち雇用されている人|1_フルタイム", "1_うち雇用されている人|0_総数"),
    "パート": ("1_うち雇用されている人|2_短時間勤務", "1_うち雇用されている人|0_総数"),
    "アルバイト": ("1_うち雇用されている人|2_短時間勤務", "1_うち雇用されている人|0_総数"),
    "雇人のある業主": ("2_うち自営業主|0_総数", "0_総数|0_総数"),
    "雇人のない業主": ("2_うち自営業主|0_総数", "0_総数|0_総数"),
    "家族従業者": ("2_うち自営業主|0_総数", "0_総数|0_総数"),
}
#: 第19表の年間就業日数の階級(列の名の頭の番号 → 階級の中央の値[日]・expedient)。
DAY_CLASSES: Final[tuple[tuple[str, int], ...]] = (
    ("11_", 25), ("12_", 75), ("13_", 125), ("14_", 175), ("2_", 225), ("3_", 275), ("4_", 320),
)
#: 産業の鍵 → 第19表の産業 3 部門(第 2 次=建設・製造)。
SECTOR2_KEYS: Final[frozenset[str]] = frozenset({"CN", "MF"})
SECTOR_19: Final[dict[str, str]] = {"total": "0_総数", "2": "2_第２次産業", "3": "3_第３次産業"}
#: 第 74 表の曜日の行。
DAY_ROWS_74: Final[tuple[str, str, str]] = ("2_平日", "3_土曜日", "4_日曜日")
#: 公務(産業大分類 S)は産業の鍵の 15 語に無い=空欄にするペルソナの鍵(親の判断 2026-10-15 の 2)。
POOL_PUBLIC_KEYS: Final[frozenset[str]] = frozenset({"PA"})

#: duty_role(v1 の在庫)→ (職業, 産業の鍵, 経済センサスの中分類, 場所, 交替制, 勤務の約束がある)。expedient。
DUTY_ROLE_SPEC: Final[dict[str, tuple[str, str, tuple[str, ...], int, bool, bool]]] = {
    "駅員": ("輸送・機械運転従事者", "TR", ("42",), PLACE_STATION, True, True),
    "車掌": ("輸送・機械運転従事者", "TR", ("42",), PLACE_VEHICLE, True, True),
    "電車運転士": ("輸送・機械運転従事者", "TR", ("42",), PLACE_VEHICLE, True, True),
    "バス運転士": ("輸送・機械運転従事者", "TR", ("43",), PLACE_VEHICLE, True, True),
    "タクシー運転手": ("輸送・機械運転従事者", "TR", ("43",), PLACE_VEHICLE, True, True),
    "納品ドライバー": ("輸送・機械運転従事者", "TR", ("44",), PLACE_VEHICLE, False, True),
    "警察官": ("保安職業従事者", "", (), PLACE_AREA, True, True),
    "消防士": ("保安職業従事者", "", (), PLACE_BUILDING, True, True),
    "救急隊員": ("保安職業従事者", "", (), PLACE_VEHICLE, True, True),
    "指令": ("保安職業従事者", "", (), PLACE_BUILDING, True, True),
    "議員": ("管理的職業従事者", "", (), PLACE_BUILDING, False, True),
    "清掃作業員": ("運搬・清掃・包装等従事者", "SV", ("88",), PLACE_AREA, False, True),
    "夜間清掃員": ("運搬・清掃・包装等従事者", "SV", ("92",), PLACE_BUILDING, False, True),
    "ティッシュ配り": ("サービス職業従事者", "PS", ("73",), PLACE_AREA, False, True),
    "募金スタッフ": ("サービス職業従事者", "SV", ("93",), PLACE_AREA, False, True),
    "キッチンカー営業者": ("サービス職業従事者", "FB", ("77",), PLACE_VEHICLE, False, True),
    "路上支援員": ("専門的・技術的職業従事者", "MW", ("85",), PLACE_AREA, False, True),
    # 勤め先の約束が無い(自分で決める・決まっていない予定=空欄)
    "ストリートミュージシャン": ("", "", (), PLACE_NONE, False, False),
    "路上占い師": ("", "", (), PLACE_NONE, False, False),
    "配信者": ("", "", (), PLACE_NONE, False, False),
    "街頭演説者": ("", "", (), PLACE_NONE, False, False),
    "路上生活者": ("", "", (), PLACE_NONE, False, False),
}
#: 規則の表(リポの根からの道筋)と、週 1 日の休みの行の id(労働基準法 第 35 条・親の判断 第337 中 2)。
RULES_TABLE_RELPATH: Final[str] = "docs/design/rules-table.json"
WEEKLY_REST_RULE_ID: Final[str] = "labor.weekly_rest_day"
#: 週 1 日の休みの対象=労働基準法 9 条の労働者に当たる雇われる側の地位(規則の表の行の ``applies_to_status`` と同じ=試験が
#: 突き合わせる・構築は表の行の値を使う)。自営業主・無給の家族と、有給役員(9 条の労働者に当たらない=親の判断 第337)は
#: 対象の外=週 7 日を制約しない。
REST_STATUSES: Final[frozenset[int]] = frozenset({ST_INDEF, ST_FIXED_TERM, ST_TEMP})
#: 授業がある学校段階(学校教育法の学校。保育所は授業でない=空欄)。
TEACHING_STAGES: Final[frozenset[str]] = frozenset(
    {"幼稚園", "小学校", "中学校", "高校", "高等学校", "中等教育学校", "高専", "大学", "大学院", "短大", "専門学校",
     "学校", "特別支援学校"}
)
#: 学齢(義務教育)の範囲[歳](学校段階の欄が空の住民の子)。
COMPULSORY_AGE: Final[tuple[int, int]] = (6, 15)
#: 片道の通勤時間が無いときの値[分](W17 v2 の下見と同じ)。
LEAD_DEFAULT_MIN: Final[int] = TR.LEAD_DEFAULT_MIN
WORK_LEN_MIN: Final[int] = TR.WORK_LEN_MIN_MIN
WORK_LEN_MAX: Final[int] = TR.WORK_LEN_MAX_MIN
WP_NONE, WP_AREA, WP_OUTSIDE, WP_HOME = range(4)


# ============================================================================= 守り(検証側を開かない)
class ValidationTableError(PermissionError):
    """検証側の表(第14・15・68-3表)か、``research_cache/r99`` の許可の外のファイルを開こうとした(開く前に落とす)。"""


def _norm(p: Any) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(p))).replace("\\", "/")


class R99Guard:
    """``research_cache/r99`` の読み口の守り(名で縛る+監査フック)。

    - :meth:`check`: 開く前に名を照らす。検証側の名 → :class:`ValidationTableError`・``r99`` の下で 4 本の外 → 同じ。
    - :meth:`active`: 守りの間、Python の ``open`` が検証側の名(どの道筋でも)か ``r99`` の下の許可の外を開こうとしたら落とす
      (``sys.addaudithook``・入れたら外せないのでフックは ``_ACTIVE`` が空なら何もしない)。
    - :attr:`opened`: 守りの間に開いた ``r99`` の下のファイルの名(記録・試験が読む)。
    """

    _ACTIVE: list["R99Guard"] = []
    _HOOKED: bool = False

    def __init__(self, allowed: Sequence[str] = tuple(R99_BUILD_FILES.values()),
                 denied: Sequence[str] = R99_VALIDATION_FILES) -> None:
        self.allowed = frozenset(str(x).lower() for x in allowed)
        self.denied = frozenset(str(x).lower() for x in denied)
        self.opened: list[str] = []

    def check(self, path: Any) -> str:
        raw = os.fspath(path).replace("\\", "/")
        name = raw.rsplit("/", 1)[-1].lower()
        if name in self.denied:
            raise ValidationTableError(f"検証側の表は開かない: {name}")
        low = raw.lower()
        if "research_cache/r99/" in low or "research_cache/r99/" in _norm(path).lower():
            if name not in self.allowed and name != "manifest.md":
                raise ValidationTableError(f"research_cache/r99 の下で許可の外のファイルは開かない: {name}")
            if name not in self.opened:
                self.opened.append(name)
        return name

    @contextlib.contextmanager
    def active(self) -> Iterator["R99Guard"]:
        if not R99Guard._HOOKED:
            sys.addaudithook(_r99_hook)
            R99Guard._HOOKED = True
        R99Guard._ACTIVE.append(self)
        try:
            yield self
        finally:
            R99Guard._ACTIVE.remove(self)


def _r99_hook(event: str, args: tuple[Any, ...]) -> None:
    if event != "open" or not R99Guard._ACTIVE:
        return
    path = args[0] if args else None
    if not isinstance(path, (str, bytes, os.PathLike)):
        return
    if isinstance(path, bytes):
        try:
            path = path.decode(sys.getfilesystemencoding())
        except UnicodeDecodeError:  # pragma: no cover
            return
    if str(path).endswith((".py", ".pyc", ".pyd", ".dll")):
        return
    R99Guard._ACTIVE[-1].check(path)


# ============================================================================= xlsx(標準ライブラリだけ・ストリーム)
_XL_NS: Final[str] = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_COL_RE: Final[re.Pattern[str]] = re.compile(r"([A-Z]+)")


def iter_xlsx_rows(path: Path, guard: R99Guard) -> Iterator[list[str]]:
    """xlsx(1 シート目)の行を順に返す(``ET.iterparse``=大きな表でも行ごとに捨てる)。開く前に守りで照らす。

    ``trial._read_xlsx_rows`` と同じ読み(共有文字列・数値・inlineStr)。第6-2表は展開して約 283 MB あるので
    ``fromstring`` で全部を持たない。逐次ループ宣言: 表の行数ぶん(構築時 1 回)。
    """
    guard.check(path)
    with zipfile.ZipFile(path) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(_XL_NS + "si"):
                shared.append("".join(t.text or "" for t in si.iter(_XL_NS + "t")))
        with z.open("xl/worksheets/sheet1.xml") as fh:
            for _ev, el in ET.iterparse(fh, events=("end",)):
                if el.tag != _XL_NS + "row":
                    continue
                cells: dict[int, str] = {}
                for c in el.findall(_XL_NS + "c"):
                    m = _COL_RE.match(c.get("r") or "")
                    if m is None:
                        continue
                    idx = 0
                    for ch in m.group(1):
                        idx = idx * 26 + (ord(ch) - 64)
                    idx -= 1
                    t = c.get("t")
                    v = c.find(_XL_NS + "v")
                    if t == "s":
                        cells[idx] = shared[int(v.text)] if v is not None and v.text else ""
                    elif t == "inlineStr":
                        node = c.find(_XL_NS + "is")
                        cells[idx] = "".join(x.text or "" for x in node.iter(_XL_NS + "t")) if node is not None else ""
                    else:
                        cells[idx] = (v.text or "") if v is not None else ""
                el.clear()
                n = max(cells) + 1 if cells else 0
                yield [cells.get(i, "") for i in range(n)]


def _num(x: Any) -> float | None:
    s = str(x).strip()
    if s in ("", "-", "…", "x", "X", "***", "−"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _col(row: Sequence[str], i: int) -> str:
    return str(row[i]) if i < len(row) else ""


# ============================================================================= 材料の抽出(構築時 1 回)
def extract_74_9(path: Path, guard: R99Guard) -> dict[str, Any]:
    """第74-9表 → 東京都・男女総数・職業 × 曜日(平日/土/日)の「仕事」の行動者率(0〜1)と推定人口・サンプル。"""
    out: dict[str, dict[str, Any]] = {}
    for i, r in enumerate(iter_xlsx_rows(path, guard)):
        if i < 9 or len(r) < 10:
            continue
        day, area, sex, occ = _col(r, 0), _col(r, 1), _col(r, 2), _col(r, 3)
        if area != "13_東京都" or sex != "0_総数" or day not in DAY_ROWS_74:
            continue
        name = occ.split("_", 1)[1] if "_" in occ else occ
        name = name[2:] if name.startswith("うち") else name
        rate = _num(_col(r, 9))
        out.setdefault(name, {})[day] = {"rate": None if rate is None else round(rate / 100.0, 6),
                                         "pop_k": _num(_col(r, 4)), "sample": _num(_col(r, 28))}
    return {"area": "13_東京都", "sex": "0_総数", "activity": "05_仕事", "rows": out}


def extract_74_6(path: Path, guard: R99Guard) -> dict[str, Any]:
    """第74-6表 → 東京都・男女総数・(従業上の地位|勤務形態)× 曜日の「仕事」の行動者率(0〜1)。"""
    out: dict[str, dict[str, Any]] = {}
    for i, r in enumerate(iter_xlsx_rows(path, guard)):
        if i < 9 or len(r) < 11:
            continue
        day, area, sex = _col(r, 0), _col(r, 1), _col(r, 2)
        if area != "13_東京都" or sex != "0_総数" or day not in DAY_ROWS_74:
            continue
        key = f"{_col(r, 3)}|{_col(r, 4)}"
        rate = _num(_col(r, 10))
        out.setdefault(key, {})[day] = {"rate": None if rate is None else round(rate / 100.0, 6),
                                        "pop_k": _num(_col(r, 5)), "sample": _num(_col(r, 29))}
    return {"area": "13_東京都", "sex": "0_総数", "activity": "05_仕事", "rows": out}


def extract_19(path: Path, guard: R99Guard) -> dict[str, Any]:
    """第19表 → 特別区部・男女総数・(雇用形態, 産業 3 部門)の年間就業日数の階級の人数と平均の日数(階級の中央の値)。"""
    head: list[str] = []
    cols: list[tuple[int, str, int]] = []
    out: dict[str, Any] = {}
    for i, r in enumerate(iter_xlsx_rows(path, guard)):
        if i == 6:
            head = list(r)
            for code, mid in DAY_CLASSES:
                j = next((k for k, x in enumerate(head) if k >= 8 and str(x).startswith(code)), None)
                if j is None:
                    raise ValueError(f"第19表の列 {code} が無い")
                cols.append((j, str(head[j]), mid))
            continue
        if i < 9 or len(r) < 98:
            continue
        area, sex, emp, ind = _col(r, 1), _col(r, 3), _col(r, 5), _col(r, 7)
        if area != "131_特別区部" or sex != "0_総数":
            continue
        counts = {lab: (_num(_col(r, j)) or 0.0) for j, lab, _m in cols}
        tot = sum(counts.values())
        mean = (sum((_num(_col(r, j)) or 0.0) * m for j, _lab, m in cols) / tot) if tot > 0 else None
        out[f"{emp}|{ind}"] = {"counts": counts, "classes_total": tot, "all_total": _num(_col(r, 8)),
                               "mean_days": None if mean is None else round(mean, 4)}
    return {"area": "131_特別区部", "sex": "0_総数", "midpoints": {lab: m for _j, lab, m in cols}, "rows": out}


def extract_6_2(path: Path, guard: R99Guard) -> dict[str, Any]:
    """第6-2表 → 渋谷区(13113)の産業(全体・大分類・中分類)× 従業上の地位 6 区分の従業者数(男女計)。"""
    total: dict[str, Any] = {}
    majors: dict[str, Any] = {}
    middles: dict[str, Any] = {}
    for i, r in enumerate(iter_xlsx_rows(path, guard)):
        if i < 9 or len(r) < 27 or not _col(r, 1).startswith("13113"):
            continue
        level, major, label = _col(r, 2), _col(r, 3), _col(r, 4)
        rec = {"label": label, "total": _num(_col(r, 5)) or 0.0,
               "status": {STATUS_WORDS[st]: (_num(_col(r, j)) or 0.0) for st, j in CENSUS_STATUS_COLS}}
        if level == "1" and major == "AR":
            total = rec
        elif level == "2":
            majors[major] = rec
        elif level == "4":
            middles[label.split("_", 1)[0]] = {**rec, "major": major}
    return {"area": "13113_渋谷区", "unit": "人(男女計・民営)", "total": total, "majors": majors, "middles": middles}


def _md5(path: Path) -> str:
    import hashlib

    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_materials(data_root: Path, *, anchor_path: Path | None = None, guard: R99Guard | None = None
                    ) -> dict[str, Any]:
    """構築側の 4 本の xlsx・第 31/36 表の錨・産業の写像から材料の表(JSON にできる辞書)を作る。

    検証側の表は開かない(守りの下で読む)。逐次ループ宣言: 表の行数ぶん(4 本・構築時 1 回)。
    """
    g = guard or R99Guard()
    root = Path(data_root).joinpath(*R99_DIR)
    ap = Path(anchor_path) if anchor_path is not None else TR.anchor_path()
    tables: dict[str, Any] = {}
    with g.active():
        for key, fn in (("74-9", extract_74_9), ("74-6", extract_74_6), ("19", extract_19), ("6-2", extract_6_2)):
            p = root / R99_BUILD_FILES[key]
            body = fn(p, g)
            tables[key] = {"side": "構築側", "file": "/".join(R99_DIR + (R99_BUILD_FILES[key],)), "md5": _md5(p),
                           **R99_SOURCES[key], **body}
    cmap_p = Path(data_root).joinpath(*CENSUS_MAP_FILE)
    cmap = json.loads(cmap_p.read_text(encoding="utf-8"))
    return {
        "schema": "shibuya.build.sched/w20_materials/1",
        "stage": STAGE,
        "stage_version": STAGE_VERSION,
        "tables": tables,
        "commute_31_36": {"side": "構築側", "file": "docs/bench/anchors/" + ap.name, "md5": _md5(ap),
                          "note": "第 31/36 表(出勤・帰宅の構成比・全国・平日)=既存の錨。始業・終業の逆算のつなぎ(入力の写し)"},
        "industry_map": {"file": "/".join(CENSUS_MAP_FILE), "md5": _md5(cmap_p),
                         "sim_mapping": cmap["_meta"]["sim_mapping"]},
        "validation_side_not_opened": list(R99_VALIDATION_FILES),
        "r99_opened": sorted(g.opened),
    }


# ============================================================================= 材料の読み口
@dataclass(frozen=True)
class Materials:
    """材料の表(:func:`build_materials` の辞書)を引く口。試験は作り物の辞書でも作れる。"""

    doc: Mapping[str, Any]

    @property
    def t749(self) -> Mapping[str, Any]:
        return self.doc["tables"]["74-9"]["rows"]

    @property
    def t746(self) -> Mapping[str, Any]:
        return self.doc["tables"]["74-6"]["rows"]

    @property
    def t19(self) -> Mapping[str, Any]:
        return self.doc["tables"]["19"]["rows"]

    @property
    def t62(self) -> Mapping[str, Any]:
        return self.doc["tables"]["6-2"]

    @property
    def sim_mapping(self) -> Mapping[str, Any]:
        return self.doc["industry_map"]["sim_mapping"]

    def rate74(self, table: Mapping[str, Any], key: str) -> np.ndarray:
        """曜日の型(平日/土/日)の仕事の率(無ければ ``nan``)。"""
        row = table.get(key) or {}
        return np.asarray([float((row.get(d) or {}).get("rate") or np.nan) for d in DAY_ROWS_74], dtype=np.float64)

    def status_counts(self, key: str, middles: Sequence[str] = ()) -> np.ndarray | None:
        """産業の鍵(または中分類の並び)→ 渋谷区の地位 6 区分の人数(``CENSUS_STATUS_COLS`` の順)。無ければ None。"""
        t = self.t62
        recs: list[Mapping[str, Any]] = []
        if middles:
            recs = [t["middles"][m] for m in middles if m in t["middles"]]
        elif key == "*":
            recs = [t["total"]] if t.get("total") else []
        else:
            spec = self.sim_mapping.get(key)
            if spec is None:
                return None
            mids = [str(x) for x in (spec.get("middles") or [])]
            if mids:
                recs = [t["middles"][m] for m in mids if m in t["middles"]]
            else:
                recs = [t["majors"][m] for m in (spec.get("majors") or []) if m in t["majors"]]
        if not recs:
            return None
        v = np.zeros(len(CENSUS_STATUS_COLS), dtype=np.float64)
        for r in recs:
            v += np.asarray([float(r["status"][STATUS_WORDS[st]]) for st, _j in CENSUS_STATUS_COLS])
        return v if v.sum() > 0 else None

    def mean_days(self, emp_row: str, sector: str) -> float | None:
        """第19表(特別区部)の雇用形態 × 産業 3 部門の平均の年間就業日数(無ければ産業の総数の行)。"""
        st = EMP_ROW_TO_19[emp_row]
        for ind in (SECTOR_19.get(sector, SECTOR_19["total"]), SECTOR_19["total"]):
            r = self.t19.get(f"{st}|{ind}")
            if r and r.get("mean_days"):
                return float(r["mean_days"])
        return None


def load_materials(path: Path) -> Materials:
    return Materials(json.loads(Path(path).read_text(encoding="utf-8")))


# ============================================================================= 属性(体の表)
@dataclass(frozen=True)
class Attributes:
    """体ごとの属性(行順=W16 の行順)。:func:`calendar_from_attributes` の入力。

    Attributes:
        agent_id / kind / age: W16。
        industry: 産業の鍵(W16 の事業所・住民はペルソナ・duty_role は :data:`DUTY_ROLE_SPEC`・``公務``・空)。
        duty_role: W16 の duty_role(空=無し)。
        occupation: 第74-9表の職業の名(duty_role の体だけ=:data:`DUTY_ROLE_SPEC`・W16 に職業の列が無い=ほかは空)。
        employment_pool: ペルソナの ``employment``(国勢調査の 6 値・従業上の地位の元=親の判断 2026-10-15 の 3)。
        employed: 勤務の約束を持つか。
        workplace: ``WP_*``(舞台の中・舞台の外・自宅・なし)。
        school: 授業の約束を持つか(学校のセル・授業のある学校段階・学齢)。
        work_cell / school_cell / home_cell: W16 のセル(−1=無し)。
        lead_min: 片道の通勤時間[分](ペルソナの ``arrival_lead_min``・無ければ −1)。
        census_middles: 地位を引く中分類(duty_role だけ・空=産業の鍵から)。
        place_hint: duty_role の場所(``PLACE_*``・0=職業から決める)。
        shift: 交替制(週ごとの抽選)。
        seat_nonworking: W16 の席(種別 0・2)があるのにペルソナの ``employment`` が「非就業」の体(勤務の約束は空欄・
            親の判断 第336 (3))。
        seat_and_school: W16 の席(種別 0・2)があってペルソナが学校段階か学校のセルを持つ体(席を優先=勤務・授業は空欄・
            親の判断 第337 中 1)。
    """

    agent_id: np.ndarray
    kind: np.ndarray
    age: np.ndarray
    industry: list[str]
    duty_role: list[str]
    occupation: list[str]
    employment_pool: list[str]
    employed: np.ndarray
    workplace: np.ndarray
    school: np.ndarray
    work_cell: np.ndarray
    school_cell: np.ndarray
    home_cell: np.ndarray
    lead_min: np.ndarray
    census_middles: list[tuple[str, ...]]
    place_hint: np.ndarray
    shift: np.ndarray
    seat_nonworking: np.ndarray | None = None
    seat_and_school: np.ndarray | None = None

    @property
    def n(self) -> int:
        return int(np.asarray(self.agent_id).size)


#: ペルソナから読む欄(``pool_facts`` の読み方と同じ行順=``pool_index``)。
POOL_FIELDS: Final[tuple[str, ...]] = (
    "employment", "industry_key", "workplace_scope", "school_stage", "arrival_lead_min",
)


def read_pool_fields(pool_root: Path, pool_layer: np.ndarray, pool_index: np.ndarray,
                     fields: Sequence[str] = POOL_FIELDS) -> dict[str, list[Any]]:
    """``(pool_layer, pool_index)`` の並びに対応するペルソナの欄(``pool_facts.read_facts`` と同じ読み方・必要な行だけ)。

    逐次ループ宣言(P4): プールの行数ぶん(必要な行だけ ``json.loads``・構築時 1 回)。
    """
    layer = np.asarray(pool_layer, dtype=np.int64)
    index = np.asarray(pool_index, dtype=np.int64)
    n = int(layer.size)
    out: dict[str, list[Any]] = {f: [None] * n for f in fields}
    for lno, name in enumerate(PF.LAYERS, start=1):
        want = np.flatnonzero((layer == lno) & (index >= 0))
        if want.size == 0:
            continue
        want = want[np.argsort(index[want], kind="stable")]
        wanted = index[want]
        cursor = 0
        row_no = 0
        for path in PF.layer_files(Path(pool_root), name):
            if cursor >= wanted.size:
                break
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    if cursor < wanted.size and row_no == wanted[cursor]:
                        d = json.loads(line)
                        while cursor < wanted.size and wanted[cursor] == row_no:
                            for f in fields:
                                out[f][int(want[cursor])] = d.get(f)
                            cursor += 1
                    row_no += 1
                    if cursor >= wanted.size:
                        break
    return out


def attributes_from_world(world_dir: Path, data_root: Path) -> Attributes:
    """W16 の体の表(``<world_dir>/w16_population.parquet``)+ペルソナ → :class:`Attributes`(**ここだけが人口に依る**)。"""
    cols = C.read_parquet_columns(
        Path(world_dir) / "w16_population.parquet",
        ["agent_id", "kind", "age", "home_cell", "work_cell", "school_cell", "industry_key", "duty_role",
         "pool_layer", "pool_index"],
    )
    pool = read_pool_fields(Path(data_root).joinpath(*PF_POOL_DIR), np.asarray(cols["pool_layer"]),
                            np.asarray(cols["pool_index"]))
    return attributes_from_columns(cols, pool)


#: ペルソナの置き場(data 根からの相対・``w16_population.POOL_DIR`` と同じ)。
PF_POOL_DIR: Final[tuple[str, ...]] = ("persona_pool_v2",)


def _s(x: Any) -> str:
    return "" if x is None else str(x)


def attributes_from_columns(cols: Mapping[str, Sequence[Any]], pool: Mapping[str, Sequence[Any]]) -> Attributes:
    """列の辞書(W16 と同じ名)+ペルソナの欄 → :class:`Attributes`。逐次ループ宣言: 体の数ぶん(文字列の欄の読み替え)。"""
    agent_id = np.asarray(cols["agent_id"], dtype=np.int64)
    n = int(agent_id.size)
    kind = np.asarray(cols["kind"], dtype=np.int64)
    age = np.asarray(cols["age"], dtype=np.int64)
    work_cell = np.asarray(cols["work_cell"], dtype=np.int64)
    school_cell = np.asarray(cols["school_cell"], dtype=np.int64)
    home_cell = np.asarray(cols["home_cell"], dtype=np.int64)
    w16_ind = [_s(x) for x in cols["industry_key"]]
    duty = [_s(x) for x in cols["duty_role"]]
    p_emp = [_s(x) for x in pool.get("employment", [None] * n)]
    p_ind = [_s(x) for x in pool.get("industry_key", [None] * n)]
    p_scope = [_s(x) for x in pool.get("workplace_scope", [None] * n)]
    p_stage = [_s(x) for x in pool.get("school_stage", [None] * n)]
    p_lead = pool.get("arrival_lead_min", [None] * n)
    industry: list[str] = [""] * n
    occupation: list[str] = [""] * n
    middles: list[tuple[str, ...]] = [()] * n
    employed = np.zeros(n, dtype=bool)
    workplace = np.zeros(n, dtype=np.int8)
    school = np.zeros(n, dtype=bool)
    place_hint = np.zeros(n, dtype=np.int8)
    shift = np.zeros(n, dtype=bool)
    seat_nonworking = np.zeros(n, dtype=bool)
    seat_and_school = np.zeros(n, dtype=bool)
    lead = np.full(n, BLANK, dtype=np.int64)
    for i in range(n):  # 逐次ループ宣言: 体の数ぶん(構築時 1 回・文字列の欄)
        k = int(kind[i])
        lv = p_lead[i]
        if isinstance(lv, (int, float)) and not isinstance(lv, bool) and lv > 0:
            lead[i] = min(int(lv), MINUTES_PER_DAY - 1)
        stage = p_stage[i]
        is_school = (school_cell[i] >= 0) or (stage in TEACHING_STAGES) or (
            k == KIND_RESIDENT and not stage and COMPULSORY_AGE[0] <= int(age[i]) < COMPULSORY_AGE[1])
        if k == KIND_STUDENT:
            is_school = True
        if k in (KIND_COMMUTER, KIND_WORKER):  # 席(W16 の明示の事実)が先=授業は空欄(親の判断 第337 中 1)
            seat_and_school[i] = bool(is_school)
            if p_emp[i] == "非就業":  # 席はあるがペルソナは非就業=約束は空欄(席は W16 のまま・数える)
                seat_nonworking[i] = True
                continue
            employed[i] = True
            workplace[i] = WP_AREA
            industry[i] = w16_ind[i]
            continue
        if is_school:
            school[i] = True
            continue
        role = duty[i]
        if role in DUTY_ROLE_SPEC:
            occ, ind, mids, place, sh, job = DUTY_ROLE_SPEC[role]
            if job:
                employed[i] = True
                occupation[i], industry[i], middles[i] = occ, ind, mids
                place_hint[i], shift[i] = place, sh
                workplace[i] = WP_AREA
            continue
        if k == KIND_DISPATCHER:  # 指令(duty_role が無い版の W16 でも)
            occ, ind, mids, place, sh, _job = DUTY_ROLE_SPEC["指令"]
            employed[i], workplace[i] = True, WP_AREA
            occupation[i], industry[i], middles[i], place_hint[i], shift[i] = occ, ind, mids, place, sh
            continue
        if k == KIND_RESIDENT and p_emp[i] and p_emp[i] != "非就業":
            employed[i] = True
            ind = p_ind[i]
            industry[i] = "" if ind in POOL_PUBLIC_KEYS else ind
            if work_cell[i] >= 0 or p_scope[i] == "in_area":
                workplace[i] = WP_AREA
            elif p_scope[i] == "at_home":
                workplace[i] = WP_HOME
            else:
                workplace[i] = WP_OUTSIDE
    return Attributes(
        agent_id=agent_id, kind=kind, age=age, industry=industry, duty_role=duty, occupation=occupation,
        employment_pool=p_emp, employed=employed, workplace=workplace, school=school, work_cell=work_cell,
        school_cell=school_cell, home_cell=home_cell, lead_min=lead, census_middles=middles, place_hint=place_hint,
        shift=shift, seat_nonworking=seat_nonworking, seat_and_school=seat_and_school,
    )


# ============================================================================= 抽選(10c の counter の鍵)
def draw_u(domain: str, agent_id: np.ndarray, week: Any = 0, weekday: Any = 0) -> np.ndarray:
    """``[0, 1)`` の一様変数(体・週・曜日がカウンタ・鍵は :data:`SEED_KEY` と用途の名)。決定的・体の数に依らない。"""
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return np.empty(0, dtype=np.float64)
    a = np.maximum(a, 0)
    w = np.broadcast_to(np.asarray(week, dtype=np.int64), a.shape)
    d = np.broadcast_to(np.asarray(weekday, dtype=np.int64), a.shape)
    raw = philox_array(SEED_KEY, f"w20.{domain}", k19_counter_array(a, w, d))
    return unit_float(raw[:, 0])


def _pick(weights: Mapping[str, float], u: np.ndarray) -> np.ndarray:
    """重みの辞書(名 → 重み)と一様変数 → 名の番号(``EMP_ROWS`` の番号)。逆関数法(名の数ぶん)。"""
    names = [k for k, v in weights.items() if float(v) > 0]
    w = np.asarray([float(weights[k]) for k in names], dtype=np.float64)
    cdf = np.cumsum(w / w.sum())
    j = np.minimum(np.searchsorted(cdf, u, side="right"), len(names) - 1)
    lut = np.asarray([_ROW_IDX[k] for k in names], dtype=np.int64)
    return lut[j]


# ============================================================================= 地位の引き直し(A3)
@dataclass(frozen=True)
class Employment:
    """従業上の地位(``ST_*``)・第 31/36 表の行(``EMP_ROWS`` の番号・−1=無し)・地位の出どころ(``SRC_*``)と数。"""

    status: np.ndarray
    emp_row: np.ndarray
    source: np.ndarray | None = None
    counters: dict[str, int] = field(default_factory=dict)


#: 地位(第6-2表の 6 区分)→ 第 31/36 表の行(按分の 2 つ=非正規・業主は ``employment_mix`` の重みで引く)。
STATUS_TO_ROW: Final[dict[int, str]] = {
    ST_INDEF: "正規の職員・従業員", ST_TEMP: "アルバイト", ST_OFFICER: "会社などの役員", ST_FAMILY: "家族従業者",
}
STATUS_TO_MIX: Final[dict[int, str]] = {ST_FIXED_TERM: "非正規", ST_SOLE: "自営業主"}


def draw_employment_status(attrs: Attributes, materials: Materials, anchor: Mapping[str, Any]) -> Employment:
    """勤務の約束を持つ体の従業上の地位(第6-2表の 6 区分)と第 31/36 表の行を決める(親の判断 2026-10-15 の 3・4)。

    - duty_role の体(:data:`DUTY_ROLE_SPEC` に中分類のある体): 経済センサス 第6-2表(渋谷区・中分類)の 6 区分の人数比で
      引き直す(v1 の在庫の引き直し=発注文どおり)。
    - ほかの体(W16 の事業所・住民・公務の duty_role): ペルソナの ``employment`` の 6 値を :data:`EMPLOYMENT_TO_STATUS`
      で 6 区分に写す。ペルソナの無い体(指令)は無期=正規の行(数える)。席があってもペルソナが非就業の体は勤務の約束を
      持たない(:class:`Attributes` の ``seat_nonworking``=ここには来ない)。
    逐次ループ宣言: 中分類の組の数ぶん(高々 10)。
    """
    n = attrs.n
    status = np.full(n, ST_NONE, dtype=np.int64)
    source = np.full(n, SRC_NONE, dtype=np.int64)
    row = np.full(n, BLANK, dtype=np.int64)
    mix = anchor.get("employment_mix", {})
    u_st = draw_u("status", attrs.agent_id)
    u_row = draw_u("emprow", attrs.agent_id)
    emp = np.asarray(attrs.employed, dtype=bool)
    mids = np.asarray(["|".join(m) for m in attrs.census_middles], dtype=object)
    pe = np.asarray(attrs.employment_pool, dtype=object)
    # ---- duty_role の体: 第6-2表(渋谷区・中分類)で引き直す ----
    cen = emp & (mids != "")
    for mid in sorted({str(x) for x in mids[cen]}):  # 逐次: 中分類の組の数
        sel = cen & (mids == mid)
        counts = materials.status_counts("", tuple(x for x in mid.split("|") if x))
        if counts is None:
            counts = materials.status_counts("*")
        cdf = np.cumsum(counts / counts.sum())
        j = np.minimum(np.searchsorted(cdf, u_st[sel], side="right"), len(CENSUS_STATUS_COLS) - 1)
        status[sel] = np.asarray([st for st, _c in CENSUS_STATUS_COLS], dtype=np.int64)[j]
        source[sel] = SRC_CENSUS
    # ---- ほかの体: ペルソナの employment の写像 ----
    rest = emp & ~cen
    for word, st in EMPLOYMENT_TO_STATUS.items():  # 逐次: 6 値
        m = rest & (pe == word)
        status[m] = st
        source[m] = SRC_EMPLOYMENT
    missing = rest & (source == SRC_NONE)
    status[missing] = ST_INDEF
    source[missing] = SRC_MISSING
    # ---- 地位 → 第 31/36 表の行 ----
    for st, name in STATUS_TO_ROW.items():
        row[status == st] = _ROW_IDX[name]
    for st, key in STATUS_TO_MIX.items():
        m = status == st
        row[m] = _pick(mix.get(key, {}), u_row[m])
    ctr = {"from_employment": int((source == SRC_EMPLOYMENT).sum()), "census_redraw_duty_role": int((source == SRC_CENSUS).sum()),
           "employment_missing": int(missing.sum())}
    return Employment(status=status, emp_row=row, source=source, counters=ctr)


# ============================================================================= 週の日数と曜日の形
def _day_weights(materials: Materials, occ: str, emp_row: str) -> np.ndarray:
    """曜日の型(平日/土/日)の重み=第74-6表の地位・勤務形態の行(第一)。職業の分かる体(duty_role)だけ第74-9表の
    職業/総数の比を掛ける(独立の掛け算・expedient)。W16 に職業の列が無い=産業 → 職業の写像は使わない。"""
    style, _denom = EMP_ROW_TO_746[emp_row]
    w = materials.rate74(materials.t746, style)
    if np.isnan(w).any():
        w = materials.rate74(materials.t746, "0_総数|0_総数")
    if occ in _OCC_IDX:
        a = materials.rate74(materials.t749, occ)
        b = materials.rate74(materials.t749, "総数")
        ok = (b > 0) & ~np.isnan(a) & ~np.isnan(b)
        w = w * np.where(ok, a / np.where(b > 0, b, 1.0), 1.0)
    return np.nan_to_num(w, nan=0.0)


def annual_check(days_per_week: np.ndarray, emp_row: np.ndarray, sector: np.ndarray, materials: Materials,
                 work: np.ndarray) -> dict[str, Any]:
    """年間の整合の計器(親の判断 第336 (1)・診断=合否にしない): 予定の週の日数 × 365/7 と、第19表(特別区部)の年間就業日数
    (実現値=休暇を含む)を第 31/36 表の行ごとに並べ、その比(第19表 ÷ 予定=稼働率の読み)を出す。

    逐次ループ宣言: 行の数(10)× 産業 3 部門。
    """
    out: dict[str, Any] = {}
    D = np.asarray(days_per_week, dtype=np.float64)
    for r_i in np.unique(emp_row[work]):  # 逐次: 行の数
        rname = EMP_ROWS[int(r_i)]
        m = work & (emp_row == r_i)
        t19 = np.zeros(int(m.sum()), dtype=np.float64)
        sec_m = sector[m]
        for sec in ("2", "3", "total"):  # 逐次: 3 部門
            md = materials.mean_days(rname, sec)
            t19[sec_m == sec] = np.nan if md is None else md
        plan_year = float(D[m].mean()) * DAYS_PER_YEAR / N_DAYS
        t19_mean = float(np.nanmean(t19)) if np.isfinite(t19).any() else None
        out[rname] = {"bodies": int(m.sum()), "plan_days_per_week": round(float(D[m].mean()), 4),
                      "plan_days_per_year": round(plan_year, 1),
                      "t19_days_per_year": None if t19_mean is None else round(t19_mean, 1),
                      "t19_over_plan": None if t19_mean is None else round(t19_mean / plan_year, 4)}
    return out


def load_weekly_rest_rule(path: Path | None = None) -> dict[str, Any]:
    """規則の表から週 1 日の休みの行(:data:`WEEKLY_REST_RULE_ID`)を読む(JSON を直に読む=build は engine を import しない)。

    Raises:
        KeyError: 行が無い。
    """
    p = Path(path) if path is not None else Path(__file__).resolve().parents[4] / RULES_TABLE_RELPATH
    doc = json.loads(p.read_text(encoding="utf-8"))
    rows = [r for r in doc.get("rules", []) if r.get("id") == WEEKLY_REST_RULE_ID]
    if not rows:
        raise KeyError(f"規則の表に {WEEKLY_REST_RULE_ID} の行が無い")
    r = sorted(rows, key=lambda x: str(x.get("asof", "")))[-1]
    return {"id": r["id"], "asof": r["asof"], "params": dict(r.get("params", {})),
            "source": [{k: v for k, v in x.items() if k in ("law", "law_id", "article")} for x in r.get("source", [])]}


def rest_statuses_of(rule: Mapping[str, Any]) -> frozenset[int]:
    """規則の表の行の ``applies_to_status``(地位の語)→ 地位の符号(行に無ければ :data:`REST_STATUSES`)。

    Raises:
        ValueError: :data:`STATUS_WORDS` に無い語。
    """
    words = rule.get("params", {}).get("applies_to_status")
    if words is None:
        return REST_STATUSES
    bad = [w for w in words if w not in STATUS_WORDS]
    if bad:
        raise ValueError(f"規則の表の applies_to_status に地位の語でないものがある: {bad}")
    return frozenset(STATUS_WORDS.index(w) for w in words)


def rest_day_of(p_type: np.ndarray) -> np.ndarray:
    """体ごとの、曜日の予定の率が最も低い曜日(同じなら後の曜日=日曜)。:func:`rest_day_draw` の受け皿(働かない率が全部 0)。"""
    r7 = np.asarray(p_type, dtype=np.float64)[:, list(DAY_TYPE_OF_WEEKDAY)]
    return (N_DAYS - 1) - np.argmin(r7[:, ::-1], axis=1)


def rest_day_draw(p_type: np.ndarray, u: np.ndarray) -> np.ndarray:
    """休みの曜日を、その曜日の「働かない率」(1 − 予定の率)に比例して 1 日引く(``u``=体・週の鍵の一様変数・決定的)。

    〔親の判断 第337 (2)〕日曜に固定すると日曜の実現の率だけが第74-6表を大きく下回る=働かない率で分ける。どの曜日も
    働かない率が 0(7 日とも率 1)の体は :func:`rest_day_of`。
    """
    w = 1.0 - np.clip(np.asarray(p_type, dtype=np.float64)[:, list(DAY_TYPE_OF_WEEKDAY)], 0.0, 1.0)
    tot = w.sum(axis=1)
    cw = np.cumsum(w, axis=1) / np.where(tot > 0, tot, 1.0)[:, None]
    d = (np.asarray(u, dtype=np.float64)[:, None] >= cw).sum(axis=1)
    last_pos = (N_DAYS - 1) - np.argmax((w > 0)[:, ::-1], axis=1)  # 働かない率が正の最後の曜日(丸めの受け皿)
    d = np.minimum(d, last_pos)
    return np.where(tot > 0, d, rest_day_of(p_type)).astype(np.int64)


# ============================================================================= 時刻(第 31/36 表の逆算)
def inverse_sample_array(bt: TR.BinTable, u: np.ndarray) -> np.ndarray:
    """``trial.inverse_sample`` の配列の版(同じ式・試験が値の一致を見る)。"""
    uu = np.asarray(u, dtype=np.float64)
    j = np.minimum(np.searchsorted(bt.cdf, uu, side="right"), int(bt.cdf.size) - 1)
    lo = np.where(j > 0, bt.cdf[np.maximum(j - 1, 0)], 0.0)
    p = bt.cdf[j] - lo
    frac = np.where(p > 1e-15, (uu - lo) / np.where(p > 1e-15, p, 1.0), 0.0)
    frac = np.clip(frac, 0.0, 1.0 - 1e-12)
    return (bt.start[j] + np.floor(frac * bt.width[j])).astype(np.int64)


# ============================================================================= 属性から作る関数
def calendar_from_attributes(attrs: Attributes, employment: Employment, materials: Materials,
                             anchor: Mapping[str, Any], *, n_weeks: int = N_WEEKS,
                             rest_rule: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """属性と従業上の地位 → 週の表(体 × 週 × 曜日の列の辞書)と数(``counters``)。決定的・体の数に依らない。

    勤務: 曜日ごとに「その曜日に勤務の予定があるか」を第74-6表の地位・勤務形態の曜日の率(duty_role の体だけ第74-9表の
    比・上限 1)で引く(毎週固定=鍵は体と曜日・週ごと=鍵は体と週と曜日)。時刻は第 31/36 表の行の逆関数法(出勤と帰宅を同じ一様変数で・毎週固定は体ごとに 1 回・
    週ごとは体と週と曜日)。授業: 月〜金(規則)・時刻は空欄。それ以外は空欄。週 1 日の休み(``rest_rule``=規則の表の行・
    省略=表から読む)は対象の地位(行の ``applies_to_status``)の体の 7 日とも勤務の週に、働かない率に比例して 1 日を休みにする。

    逐次ループ宣言: 第 31/36 表の行の数(10)× 週 × 曜日(7)・職業 × 行の組の数(高々 110)。体はベクトル。
    """
    n = attrs.n
    W = int(n_weeks)
    rows_n = n * W * N_DAYS
    aid = np.asarray(attrs.agent_id, dtype=np.int64)
    ctr: dict[str, int] = {"lead_default": 0, "work_len_clipped": 0, "weekly_rest_inserted": 0,
                           "seat_nonworking": int(np.count_nonzero(attrs.seat_nonworking))
                           if attrs.seat_nonworking is not None else 0,
                           "seat_and_school": int(np.count_nonzero(attrs.seat_and_school))
                           if attrs.seat_and_school is not None else 0,
                           # 席を優先して勤務の約束にした体(席と学校の両方のうち、ペルソナが非就業でない体)
                           "seat_and_school_work": int(np.count_nonzero(np.asarray(attrs.seat_and_school)
                                                                        & np.asarray(attrs.employed)))
                           if attrs.seat_and_school is not None else 0}
    rule = dict(rest_rule) if rest_rule is not None else load_weekly_rest_rule()
    min_rest = int(rule.get("params", {}).get("min_rest_days_per_week", 1))
    # ---- 体ごとの量(週・曜日に依らない)----
    emp_row = np.asarray(employment.emp_row, dtype=np.int64)
    work = np.asarray(attrs.employed, dtype=bool) & (emp_row >= 0)
    school = np.asarray(attrs.school, dtype=bool)
    weekly = work & (np.isin(emp_row, [_ROW_IDX[r] for r in WEEKLY_ROWS]) | np.asarray(attrs.shift, dtype=bool)
                     | (np.asarray(employment.status) == ST_TEMP))
    src = (np.asarray(employment.source, dtype=np.int64) if employment.source is not None
           else np.where(np.asarray(employment.status) > 0, SRC_EMPLOYMENT, SRC_NONE))
    occ_names = np.asarray(attrs.occupation, dtype=object)
    occ_idx = np.asarray([_OCC_IDX.get(str(o), -1) for o in attrs.occupation], dtype=np.int64)
    ind = np.asarray(attrs.industry, dtype=object)
    sector = np.where(np.isin(ind, list(SECTOR2_KEYS)), "2", np.where(ind == "", "total", "3"))
    # 曜日の型(平日/土/日)の予定の率=第74-6表(地位・勤務形態)× duty_role だけ第74-9表の比(職業 × 行の組ごとに 1 回)。
    # 実現値(休んだ後)なので予定の率の下限=これをそのまま予定の率にする(親の判断 第336 (1))。週の日数はその和。
    p_type = np.zeros((n, 3), dtype=np.float64)
    for r_i in np.unique(emp_row[work]):  # 逐次: 行の数
        rname = EMP_ROWS[int(r_i)]
        for occ in sorted({str(o) for o in occ_names[work & (emp_row == r_i)]}):  # 逐次: 職業の数
            m = work & (emp_row == r_i) & (occ_names == occ)
            p_type[m] = np.clip(_day_weights(materials, occ, rname), 0.0, 1.0)
    D = (p_type * np.asarray(DAY_TYPE_COUNT, dtype=np.float64)).sum(axis=1)
    lead = np.asarray(attrs.lead_min, dtype=np.int64).copy()
    need_lead = work & (lead <= 0) & (np.asarray(attrs.workplace) != WP_HOME)
    ctr["lead_default"] = int(need_lead.sum())
    lead[need_lead] = LEAD_DEFAULT_MIN
    lead[work & (np.asarray(attrs.workplace) == WP_HOME)] = 0
    # 場所
    place = np.zeros(n, dtype=np.int64)
    hint = np.asarray(attrs.place_hint, dtype=np.int64)
    wp = np.asarray(attrs.workplace, dtype=np.int64)
    place[work] = np.where(hint[work] > 0, hint[work], PLACE_BUILDING)  # W16 に職業の列が無い=duty_role の表だけ
    place[work & (wp == WP_OUTSIDE)] = PLACE_OUTSIDE
    place[work & (wp == WP_HOME)] = PLACE_HOME
    wc, sc, hc = (np.asarray(x, dtype=np.int64) for x in (attrs.work_cell, attrs.school_cell, attrs.home_cell))
    cell = np.full(n, BLANK, dtype=np.int64)
    cell[work & (wp == WP_AREA)] = wc[work & (wp == WP_AREA)]
    cell[work & (wp == WP_HOME)] = hc[work & (wp == WP_HOME)]
    # 学校のセルが無い体: 舞台に住む子は学校(セル不明=W16 の学校の点に無い)・舞台の外に住む体は域外(W17 と同じ読み)
    place[school] = np.where((sc[school] >= 0) | (hc[school] >= 0), PLACE_SCHOOL, PLACE_OUTSIDE)
    cell[school] = sc[school]
    # ---- 表(体 × 週 × 曜日)----
    shape = (n, W, N_DAYS)
    commit = np.zeros(shape, dtype=np.int8)
    start = np.full(shape, BLANK, dtype=np.int64)
    end = np.full(shape, BLANK, dtype=np.int64)
    dep = np.full(shape, BLANK, dtype=np.int64)
    ret = np.full(shape, BLANK, dtype=np.int64)
    lead_t = np.full(shape, BLANK, dtype=np.int64)
    recur = np.zeros(shape, dtype=np.int8)
    tables = {nm: (TR._bin_table(anchor["depart"], nm), TR._bin_table(anchor["return"], nm)) for nm in EMP_ROWS}
    fixed = work & ~weekly
    rest_target = work & np.isin(np.asarray(employment.status), list(rest_statuses_of(rule)))
    for wk in range(W):  # 逐次: 週の数
        on_week = np.zeros((n, N_DAYS), dtype=bool)
        for d in range(N_DAYS):  # 逐次: 曜日(7)
            u_day = np.where(weekly, draw_u("day", aid, wk, d), draw_u("day", aid, 0, d))
            on_week[:, d] = work & (u_day < p_type[:, DAY_TYPE_OF_WEEKDAY[d]])
        # 週 1 日の休み(労働基準法 第 35 条 1 項=規則の表の行): 対象の地位で 7 日とも勤務なら、働かない率に比例して 1 日を
        # 休みに(鍵=体と週・毎週固定の体は週 0=毎週同じ休み)。2 項(4 週 4 日の変形休日制)は入れない(expedient)
        if min_rest >= 1:
            full = rest_target & (on_week.sum(axis=1) > N_DAYS - min_rest)
            if full.any():
                fi = np.flatnonzero(full)
                u_rest = np.where(weekly[fi], draw_u("rest", aid[fi], wk, 0), draw_u("rest", aid[fi], 0, 0))
                on_week[fi, rest_day_draw(p_type[fi], u_rest)] = False
            if wk == 0:
                ctr["weekly_rest_inserted"] = int(full.sum())
        for d in range(N_DAYS):  # 逐次: 曜日(7)
            t = DAY_TYPE_OF_WEEKDAY[d]
            on = on_week[:, d]
            u_time = np.where(weekly, draw_u("time", aid, wk, d), draw_u("time", aid, 0, 0))
            for r_i in np.unique(emp_row[on]):  # 逐次: 行の数
                m = on & (emp_row == r_i)
                bt_dep, bt_ret = tables[EMP_ROWS[int(r_i)]]
                dep[m, wk, d] = inverse_sample_array(bt_dep, u_time[m])
                ret[m, wk, d] = inverse_sample_array(bt_ret, u_time[m])
            lo = dep[:, wk, d] + lead
            hi = ret[:, wk, d] - lead
            short = on & (hi - lo < WORK_LEN_MIN)
            long_ = on & (hi - lo > WORK_LEN_MAX)
            hi = np.where(short, lo + WORK_LEN_MIN, np.where(long_, lo + WORK_LEN_MAX, hi))
            clipped = short | long_
            ret[clipped, wk, d] = hi[clipped] + lead[clipped]  # 切った体の帰宅=終業+片道の通勤時間(終業 ≤ 帰宅)
            if wk == 0:
                ctr["work_len_clipped"] += int(clipped.sum())
            start[on, wk, d] = lo[on]
            end[on, wk, d] = hi[on]
            lead_t[on, wk, d] = lead[on]
            commit[on, wk, d] = COMMIT_WORK
            recur[on & fixed, wk, d] = RECUR_FIXED
            recur[on & weekly, wk, d] = RECUR_WEEKLY
            if t == 0:  # 授業=月〜金(規則)・時刻は空欄
                commit[school, wk, d] = COMMIT_SCHOOL
                recur[school, wk, d] = RECUR_RULE
                lead_t[school & (lead > 0), wk, d] = lead[school & (lead > 0)]
            dep[~on, wk, d] = BLANK
            ret[~on, wk, d] = BLANK
    has = commit > 0
    place_t = np.where(has, place[:, None, None], PLACE_NONE)
    cell_t = np.where(has, cell[:, None, None], BLANK)
    cols = {
        "agent_id": np.repeat(aid, W * N_DAYS).astype(np.int32),
        "week": np.tile(np.repeat(np.arange(W, dtype=np.int8), N_DAYS), n),
        "weekday": np.tile(np.arange(N_DAYS, dtype=np.int8), n * W),
        "commit": commit.reshape(rows_n),
        "start_min": start.reshape(rows_n).astype(np.int16),
        "end_min": end.reshape(rows_n).astype(np.int16),
        "depart_min": dep.reshape(rows_n).astype(np.int16),
        "return_min": ret.reshape(rows_n).astype(np.int16),
        "lead_min": lead_t.reshape(rows_n).astype(np.int16),
        "place_kind": place_t.reshape(rows_n).astype(np.int8),
        "target_cell": cell_t.reshape(rows_n).astype(np.int32),
        "certainty": np.where(has, CERT_FIXED, CERT_BLANK).reshape(rows_n).astype(np.int8),
        "recurrence": recur.reshape(rows_n),
        "placement": np.full(rows_n, PLACEMENT_BLANK, dtype=np.int8),
        "origin_conv": np.full(rows_n, ORIGIN_NONE, dtype=np.int32),
        "status": np.repeat(np.asarray(employment.status, dtype=np.int8), W * N_DAYS),
        "emp_row": np.repeat(emp_row.astype(np.int8), W * N_DAYS),
        "status_source": np.repeat(src.astype(np.int8), W * N_DAYS),
        "occ": np.repeat(occ_idx.astype(np.int8), W * N_DAYS),
    }
    ctr.update({"bodies": n, "rows": rows_n, "work_bodies": int(work.sum()), "school_bodies": int(school.sum()),
                "weekly_bodies": int(weekly.sum()), "fixed_bodies": int(fixed.sum())})
    return {"columns": cols, "counters": ctr, "days_per_week": D, "p_type": p_type,
            "annual_check": annual_check(D, emp_row, sector, materials, work)}


TABLE_SCHEMA: Final[pa.Schema] = pa.schema([
    ("agent_id", pa.int32()), ("week", pa.int8()), ("weekday", pa.int8()), ("commit", pa.int8()),
    ("start_min", pa.int16()), ("end_min", pa.int16()), ("depart_min", pa.int16()), ("return_min", pa.int16()),
    ("lead_min", pa.int16()), ("place_kind", pa.int8()), ("target_cell", pa.int32()), ("certainty", pa.int8()),
    ("recurrence", pa.int8()), ("placement", pa.int8()), ("origin_conv", pa.int32()), ("status", pa.int8()),
    ("emp_row", pa.int8()), ("status_source", pa.int8()), ("occ", pa.int8()),
])


# ============================================================================= 統計(記録と計器の元)
def hist15(minutes: np.ndarray) -> list[int]:
    """分 → 15 分の枠(96)の数(1 日の分を超える値は翌日の同じ枠に畳む)。"""
    m = np.asarray(minutes, dtype=np.int64)
    m = m[m >= 0]
    slots = MINUTES_PER_DAY // 15
    return np.bincount((m % MINUTES_PER_DAY) // 15, minlength=slots)[:slots].astype(int).tolist()


def _q(x: np.ndarray, qs: Sequence[float] = (0.1, 0.5, 0.9)) -> list[float | None]:
    x = np.asarray(x, dtype=np.float64)
    return [None if x.size == 0 else round(float(np.quantile(x, q)), 2) for q in qs]


def table_stats(cols: Mapping[str, np.ndarray], *, kind: np.ndarray | None = None) -> dict[str, Any]:
    """週の表の統計(曜日ごとの約束の数・空欄の数・出勤・始業・終業・帰宅の分位・通勤時間・日数の分布)。"""
    wd = np.asarray(cols["weekday"])
    cm = np.asarray(cols["commit"])
    out: dict[str, Any] = {"by_weekday": []}
    for d in range(N_DAYS):  # 逐次: 曜日
        m = wd == d
        w = m & (cm == COMMIT_WORK)
        s = m & (cm == COMMIT_SCHOOL)
        out["by_weekday"].append({
            "weekday": d, "work": int(w.sum()), "school": int(s.sum()), "blank": int((m & (cm == 0)).sum()),
            "school_time_blank": int((s & (np.asarray(cols["start_min"]) < 0)).sum()),
            "depart_q": _q(np.asarray(cols["depart_min"])[w]), "start_q": _q(np.asarray(cols["start_min"])[w]),
            "end_q": _q(np.asarray(cols["end_min"])[w]), "return_q": _q(np.asarray(cols["return_min"])[w]),
            "lead_q": _q(np.asarray(cols["lead_min"])[w]),
            "depart_hist15": hist15(np.asarray(cols["depart_min"])[w]),
            "start_hist15": hist15(np.asarray(cols["start_min"])[w]),
        })
    aid = np.asarray(cols["agent_id"])
    days = np.bincount(np.searchsorted(np.unique(aid), aid[cm == COMMIT_WORK]), minlength=np.unique(aid).size)
    workers = np.unique(aid[cm == COMMIT_WORK])
    dd = days[np.searchsorted(np.unique(aid), workers)] if workers.size else np.zeros(0, dtype=np.int64)
    out["work_days_per_week_hist"] = np.bincount(dd, minlength=N_DAYS + 1).astype(int).tolist()
    out["work_days_per_week_mean"] = None if dd.size == 0 else round(float(dd.mean()), 4)
    return out


# ============================================================================= 段(構築時 1 回)
def _world_columns(world_dir: Path) -> dict[str, list[Any]]:
    return C.read_parquet_columns(
        Path(world_dir) / "w16_population.parquet",
        ["agent_id", "kind", "age", "home_cell", "work_cell", "school_cell", "industry_key", "duty_role",
         "pool_layer", "pool_index"],
    )


def duty_role_check(attrs: Attributes, materials: Materials, census_area: Mapping[str, Any] | None
                    ) -> list[dict[str, Any]]:
    """duty_role の在庫と経済センサスの二重計上の確かめ(記録の表)。

    行=duty_role ごとに: 体の数・当てた産業と中分類・W16 の事業所で働く体(種別 0・2)のその産業の鍵の数・渋谷区の
    第6-2表のその中分類の従業者数・町丁目の表(W16 の入力=13 町丁目)のその中分類の従業者数。
    """
    roles = sorted({r for r in attrs.duty_role if r})
    ind = np.asarray(attrs.industry, dtype=object)
    kind = np.asarray(attrs.kind)
    w16_key = {}
    for k in set(ind[(kind == KIND_COMMUTER) | (kind == KIND_WORKER)].tolist()):
        w16_key[str(k)] = int(((ind == k) & ((kind == KIND_COMMUTER) | (kind == KIND_WORKER))).sum())
    out = []
    for r in roles:  # 逐次: duty_role の数(高々 25)
        spec = DUTY_ROLE_SPEC.get(r)
        n_r = int(sum(1 for x in attrs.duty_role if x == r))
        occ, ind_k, mids = (spec[0], spec[1], spec[2]) if spec else ("", "", ())
        ward = sum(float(materials.t62["middles"].get(m, {}).get("total", 0.0)) for m in mids)
        area = None
        if census_area is not None and mids:
            area = sum(float((census_area.get("by_middle", {}).get(m) or {}).get("employees") or 0.0) for m in mids)
        out.append({"duty_role": r, "bodies": n_r, "occupation": occ, "industry": ind_k, "census_middles": list(mids),
                    "w16_census_workers_same_key": w16_key.get(ind_k) if ind_k else None,
                    "ecensus_6_2_ward_employees": ward if mids else None,
                    "census_area_13chome_employees": area,
                    "has_commitment": bool(spec[5]) if spec else False})
    return out


def stage_params(n_weeks: int, rest_rule: Mapping[str, Any]) -> dict[str, Any]:
    """段の ``params``(``param_hash`` の元)。〔第 4 期 4-3 段 10〕差し替えの母集団で組む口(``build.pop.w21_apply``)も同じ関数を
    通す=W20cal の ``param_hash`` は母集団に依らない(値は第337 の版と同じ=試験)。"""
    return {"schema": SCHEMA, "seed_key": SEED_KEY, "week0_monday": WEEK0_MONDAY, "n_weeks": int(n_weeks),
            "day_classes": dict(DAY_CLASSES), "work_len_min": WORK_LEN_MIN, "work_len_max": WORK_LEN_MAX,
            "lead_default": LEAD_DEFAULT_MIN, "duty_role_spec": {k: list(v[:2]) + [list(v[2])] + list(v[3:])
                                                                 for k, v in DUTY_ROLE_SPEC.items()},
            "employment_to_status": dict(EMPLOYMENT_TO_STATUS), "teaching_stages": sorted(TEACHING_STAGES),
            "compulsory_age": list(COMPULSORY_AGE), "r99_build_files": dict(R99_BUILD_FILES),
            # 親の判断 第336: 曜日の予定の率=第74-6表(実現値=予定の下限)・第19表=年間の整合の計器・席があって非就業=空欄
            "weekday_rate_source": "t74-6", "t19_role": "annual_check", "seat_nonworking": "blank",
            # 親の判断 第337: 席が先(授業は空欄)・週 1 日の休み(規則の表の行)・切った体の帰宅は終業+通勤
            "seat_and_school": "work", "weekly_rest_rule": rest_rule, "return_after_clip": "end+lead",
            "rest_day_choice": "proportional_to_not_working_rate"}


def run(ctx: C.Ctx, *, anchor_path: Path | None = None, n_weeks: int = N_WEEKS) -> C.StageResult:
    """段 W20cal: W16+ペルソナ+構築側の表 → ``w20_calendar_1a.parquet``・材料の表・ヘッダ(``calendar_1a.header.json``)。

    ``ctx.out`` に W16 の出力(``w16_population.parquet``)がある置き場を渡す(W17 と同じ読み方)。検証側の表は開かない
    (守りの監査フックの下で回す)。逐次ループ宣言: :func:`build_materials`・:func:`read_pool_fields`・
    :func:`attributes_from_columns`(体の数ぶん=構築時 1 回)。
    """
    t0 = time.perf_counter()
    guard = R99Guard()
    ap = Path(anchor_path) if anchor_path is not None else TR.anchor_path()
    with guard.active():
        anchor = TR.load_anchor(ap)
        mat_doc = build_materials(ctx.data, anchor_path=ap, guard=guard)
        materials = Materials(mat_doc)
        cols = _world_columns(ctx.out)
        pool = read_pool_fields(ctx.data.joinpath(*PF_POOL_DIR), np.asarray(cols["pool_layer"]),
                                np.asarray(cols["pool_index"]))
        attrs = attributes_from_columns(cols, pool)
        employment = draw_employment_status(attrs, materials, anchor)
        rules_path = Path(__file__).resolve().parents[4] / RULES_TABLE_RELPATH
        rest_rule = load_weekly_rest_rule(rules_path)
        built = calendar_from_attributes(attrs, employment, materials, anchor, n_weeks=n_weeks, rest_rule=rest_rule)
        census_area = json.loads(ctx.data.joinpath(*CENSUS_MAP_FILE).read_text(encoding="utf-8"))
    tab = built["columns"]
    order = np.lexsort((tab["weekday"], tab["week"], tab["agent_id"]))
    if not np.array_equal(order, np.arange(order.size)):
        tab = {k: np.asarray(v)[order] for k, v in tab.items()}
    stats = table_stats(tab)
    status_share = {STATUS_WORDS[s]: int((employment.status == s).sum()) for s in range(len(STATUS_WORDS))}
    row_share = {EMP_ROWS[i]: int((employment.emp_row == i).sum()) for i in range(len(EMP_ROWS))}
    dup = duty_role_check(attrs, materials, census_area)
    ctx.out.mkdir(parents=True, exist_ok=True)
    outputs = [
        C.write_parquet(ctx.out, OUTPUT_NAME, tab, schema=TABLE_SCHEMA),
        C.write_json(ctx.out, MATERIALS_NAME, mat_doc),
    ]
    in_paths = [ctx.data.joinpath(*p) for p in INPUT_FILES] + [ap, ctx.out / "w16_population.parquet",
                                                               ctx.data.joinpath(*PF_POOL_DIR, "meta.json"), rules_path]
    #: 入力の名(置き場に依らない=data 根からの相対・リポの根からの相対・段の置き場は ``<out>/``)。
    in_labels = ["data/" + "/".join(p) for p in INPUT_FILES] + [
        "docs/bench/anchors/" + ap.name, "<out>/w16_population.parquet", "data/" + "/".join(PF_POOL_DIR) + "/meta.json",
        RULES_TABLE_RELPATH]
    params = stage_params(n_weeks, rest_rule)
    gates = [
        C.Gate("validation_tables_opened", len(set(guard.opened) & {x.lower() for x in R99_VALIDATION_FILES}), 0),
        C.Gate("r99_opened_within_allow", sorted(guard.opened),
               passed=set(guard.opened) <= {x.lower() for x in R99_BUILD_FILES.values()}),
        C.Gate("rows_equal_bodies_x_days", int(tab["agent_id"].size), int(attrs.n * n_weeks * N_DAYS)),
        C.Gate("work_days_per_week_mean", stats["work_days_per_week_mean"]),
    ]
    res = C.StageResult(
        stage=STAGE, stage_version=STAGE_VERSION,
        input_hash=C.input_hash([p for p in in_paths if p.exists()]),
        param_hash=C.param_hash(params), params=params, outputs=outputs, gates=gates,
        catalog_classes=["人(ペルソナ)", "約束(勤務・授業)"],
        expedients=[
            "始業・終業=第31/36表の逆算(入力の写し)・出勤と帰宅は同じ一様変数・勤務の長さ [4h, 12h]・"
            "切った体の帰宅=終業+片道",
            "片道の通勤時間=ペルソナの arrival_lead_min(v1 の在庫)・無ければ 30 分",
            "曜日の予定の率=第74-6表の地位・勤務形態の曜日の仕事の率(実現値=予定の下限・W16 に職業の列が無い)・"
            "曜日ごとに独立に引く・第19表は年間の整合の計器(診断)",
            "従業上の地位=ペルソナの employment(6 値)→ 第6-2表の 6 区分の写像(正規=無期・非正規=有期・役員=有給役員・"
            "自営業主=個人業主・家族従業者=無給の家族)→ 第31/36表の行(有期は全国人数比・臨時=アルバイト)",
            "duty_role(v1 の在庫)は第6-2表(渋谷区・中分類)の地位で引き直す・職業・産業・中分類・場所・交替制は "
            "DUTY_ROLE_SPEC・職業の分かる体だけ曜日の形に第74-9表の職業/総数の比・W16 の事業所の体の勤務場所は建物",
            "公務は産業の鍵の 15 語に無い=産業の欄は空欄(新しい語を足さない)",
            "授業の時間帯は空欄・通学は月〜金(規則)・保育所は授業でない",
            "非正規とシフトは週ごとの抽選(雇い主がエージェントになるまで)",
            "週 1 日の休み(労働基準法 35 条 1 項)の曜日=働かない率(1 − 第74-6表の率)に比例して体・週の鍵で 1 日・"
            "4 週 4 日の変形休日制(35 条 2 項)は入れない",
        ],
        notes={
            "stats": stats, "status_bodies": status_share, "emp_row_bodies": row_share,
            "status_source_bodies": {STATUS_SOURCE_WORDS[k]: int((np.asarray(employment.source) == k).sum())
                                     for k in range(len(STATUS_SOURCE_WORDS))},
            "employment_counters": employment.counters, "calendar_counters": built["counters"],
            "annual_check_t19": built["annual_check"],
            "duty_role_double_count": dup, "r99_opened": sorted(guard.opened),
            "validation_side_not_opened": list(R99_VALIDATION_FILES),
            "input_files": [{"path": lab, "md5": _md5(p)} for lab, p in zip(in_labels, in_paths) if p.exists()],
            "input_families": {k: list(v) for k, v in INPUT_FAMILIES.items()},
            "seconds_nondeterministic": round(time.perf_counter() - t0, 1),
        },
    )
    header = res.to_json()
    header["notes"] = {k: v for k, v in header["notes"].items() if k != "seconds_nondeterministic"}
    (ctx.out / HEADER_NAME).write_bytes(C.canonical_json_bytes(header) + b"\n")
    return res


def week_of(day: date) -> int:
    """日付 → 週の番号(:data:`WEEK0_MONDAY` の週を 0)。"""
    return (day - date.fromisoformat(WEEK0_MONDAY)).days // N_DAYS


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.sched.w20_calendar_1a")
    ap.add_argument("--out", required=True, type=Path, help="W16 の出力がある置き場(例 data/world/v2_stage_3-1)")
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--weeks", type=int, default=N_WEEKS)
    args = ap.parse_args(argv)
    ctx = C.Ctx(data=args.data.resolve(), out=args.out.resolve())
    res = run(ctx, n_weeks=int(args.weeks))
    for o in res.outputs:
        print(f"[{STAGE}] {o['path']} rows={o['rows']} sha256={o['sha256'][:16]}")
    for g in res.gates:
        print(f"[{STAGE}] gate {g.name} = {g.to_json()}")
    return 0 if res.all_passed else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
