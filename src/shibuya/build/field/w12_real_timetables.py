"""W12 の実ダイヤの読み口(第 2 期 2-3b・回答 10-13 の 7・回答 10-13b §2)。

W12 の等間隔の推定(JR 山手線・埼京線〈湘南新宿ラインを含む〉・東急 東横線・田園都市線・京王 井の頭線)を、
読み取り済みの実ダイヤに置き換えるための読み口。**構築側だけ**(エンジンは ``w12_timetables.parquet`` の
``line・direction・calendar・departure_min`` を読むだけ=列は変えない)。読み取りの記録は
``docs/bench/analysis/wallbounce-1012/timetables/``(README §7・``extraction-jr.md``・``extraction-tokyu-metro.md``・
``keio-odpt-challenge.md``)。本モジュールの記録は ``docs/bench/analysis/wallbounce-1012/tt23b/README.md``。

入力(どれも gitignore の下・git に入れない・読むだけ)
    (a) ユーザーが各社の公式サイトから手で入手した時刻表の読み取り(``data/user_timetables/_extracted/*_final.csv``・
        列=会社,路線,駅,方面,平日土休,時,分,種別,行き先,版,md5,読み)。**渋谷駅の発車の表だけ**を
        :data:`USER_TABLES` の白い一覧で読む(他の表=到着・神泉・原宿・明治神宮前・代々木公園・代々木八幡・
        表参道・池尻大橋・代官山・成田エクスプレスは読まない)。JR の頁の印は別の表 ``JR_注記.final.csv``。
    (b) 京王 井の頭線は ODPT チャレンジ枠から作った CSV(``_extracted/odpt_challenge/``・同じ 12 列)。
        **チャレンジ枠の利用はチャレンジへの応募(作品=本シミュレーション)と照合の範囲**。生の行(時刻の一覧)は
        記録に写さない(本数と版だけ)。
    (c) 東京メトロ 銀座線は ODPT オープン枠の静的データ版 1(``data/realworld_live/odpt_static/2026-10-13/``)の
        ``odpt:TrainTimetable``。銀座線の列車のうち、最初の停車が渋谷(=起点)の列車の発車時刻
        (``odpt:departureTime``)。暦は ``odpt:calendar``(Weekday/SaturdayHoliday)。版=2026-09-19 改正
        (``dct:issued``)=**世界の時点(2026-07-13)より後の版**と宣言する(回答 10-13b §2)。
    半蔵門線・副都心線は今の 7 月の取得(``data/odpt/station_timetable_metro_*.json``)のまま
    (``w12_external_nodes.parse_metro_timetable``・本モジュールは読まない)。

方面の写像(表 → W12 の ``line``・``direction``)。``direction`` の値の集まりは今の W12 と同じ
{上り, 下り, TokyoMetro.Asakusa, TokyoMetro.Oshiage, TokyoMetro.Wakoshi} に保つ(エンジンの向きの番号
``didx`` を振り直さない)。今の等間隔の行の「上り/下り」は対称で意味を持たなかったので、各社の線の向きの
定義に合わせて次のように決めた:

    ======================================================  ==========  =====  ===========================================
    表(会社・路線・方面=CSV の値)                           line        向き   根拠
    ======================================================  ==========  =====  ===========================================
    JR東日本 山手線 品川・東京方面(内回り)                   山手線      上り   線路名称の山手線は品川起点(品川〜新宿〜
                                                                               田端)=渋谷 → 品川は起点の側=上り(推測・
                                                                               未リサーチ=expedient)
    JR東日本 山手線 新宿・池袋方面(外回り)                   山手線      下り   同上(渋谷 → 新宿は終点の側=下り)
    JR東日本 埼京線・川越線 大宮・川越方面(下り)             埼京線      下り   頁の題名
    JR東日本 埼京線・川越線 大崎方面(上り)                   埼京線      上り   頁の題名
    JR東日本 相鉄線直通 相鉄線方面(下り)                     埼京線      上り   題名は「下り」だが渋谷から大崎の向き(南行)。
                                                                               ODPT の埼京線 南行=大崎方面+相鉄線方面で
                                                                               全一致(extraction-jr.md §6)=向きで合わせる
    JR東日本 湘南新宿ライン 高崎・宇都宮方面(北行)           埼京線 ※    下り   北行=大宮方面と同じ向き
    JR東日本 湘南新宿ライン 横浜・大船方面(南行)             埼京線 ※    上り   南行=大崎方面と同じ向き
    東急 東横線 横浜・元町・中華街・新横浜・二俣川方面        東横線      下り   東急の表の方面(下り)=README §2-1
    東急 副都心線(東横線直通・東急の標準時刻表)池袋・和光市…  東横線      上り   東急の表の題名「TY01_渋谷(上り)」=東横線
                                                                               から副都心線へ直通する便
    東急 田園都市線 二子玉川・長津田・中央林間方面            田園都市線  下り   東急の表の方面(下り)=README §2-1
    東急 半蔵門線(田園都市線直通・東急の標準時刻表)押上…      田園都市線  上り   東急の表の題名「DT01_渋谷(上り)」
    京王 井の頭線 吉祥寺方面(渋谷発)                         井の頭線    下り   渋谷が起点(渋谷〜吉祥寺)・ODPT の
                                                                               railDirection=Outbound
    ODPT 銀座線 渋谷が起点の列車(TokyoMetro.Asakusa)          銀座線      TokyoMetro.Asakusa(今の値のまま)
    ======================================================  ==========  =====  ===========================================

    ※ 湘南新宿ラインの便は ``line=埼京線`` に畳む(:data:`FOLD_LINES`・expedient)。エンジンは方面ノード
    ``ext_rail_jr_saikyo_shonan`` を ``lines[0]``=埼京線に畳んで線を引き(``world.assets`` の expedient E2)、
    線別の定員・混雑率上限の表(``engine.processes.rail``)にも湘南新宿ラインの行が無い。別の線として足すと
    方面ノードの体がその便に乗れず、定員が既定値になる。畳まない形は ``fold_lines={}`` で作れる(切替口)。
    東横線・田園都市線の「上り」は直通の副都心線・半蔵門線の便と同じ列車(ODPT と 1 対 1 で一致=
    extraction-tokyu-metro.md §5)。W12 では線ごとに 1 回ずつ現れる(今の等間隔の行と同じ形=直通の二重は
    ``w12_external_nodes`` の ``through_running_caveat`` の範囲)。

渋谷の発車だけを使う(到着の表は使わない)。エンジンの便は「ホームに居る区間=発車の前の停車時分」で、着く体も
同じ便から降りる(今のメトロ 3 線と同じ扱い)。井の頭線と銀座線は渋谷が終点なので発車の 1 方向だけになる。

土休の ◆(運転日注意)の特急のうち ODPT に無い 4 本(踊り子 3・サフィール踊り子 1)は臨時と見て外す
(README §7・extraction-jr.md 親検収の (2)=推測)。見分けは種別(:data:`TEMPORARY_TRAIN_TYPES`)で行い、外す行に
◆ の印が付いていることを ``JR_注記.final.csv`` で確かめる(付いていなければ止まる)。

重複(同じ line・direction・calendar・発車時刻)は 1 本にまとめ、件数を返す(畳んだ埼京線で表どうしが重なる
場合に備える。今の表どうしの重なりは記録 extraction-jr.md §6 で 0)。

時刻は ``HH:MM``(0 時台は 00:MM=翌日の 0 時)で返す。運行日の分(``departure_min``)は
``w12_external_nodes._minute``(T0 の定数と運行日の切れ目)で計算する。

逐次ループ宣言(P4): 表の行(1 万行規模)と ODPT の列車(1 万本規模)を 1 回ずつ。構築時だけ。
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from shibuya.core.time_consts import HOURS_PER_DAY, MINUTES_PER_HOUR

#: 段の印(記録・版の表に書く)。
STAGE_TAG = "2-3b"
#: 世界の時点(``engine.calendar.DEFAULT_WORLD_START`` の日付と同じ=試験で照らす)。版が前か後かの宣言に使う。
WORLD_TIME_POINT = "2026-07-13"

#: 入力の置き場(data 根からの相対)。
USER_TIMETABLE_DIR: tuple[str, ...] = ("user_timetables", "_extracted")
ODPT_CHALLENGE_DIR: tuple[str, ...] = ("user_timetables", "_extracted", "odpt_challenge")
#: ODPT オープン枠の静的データ版 1(日付のフォルダで版を固定する)。
ODPT_STATIC_DIR: tuple[str, ...] = ("realworld_live", "odpt_static", "2026-10-13")
ODPT_STATIC_METRO_TRAIN_TIMETABLE = "traintimetable_TokyoMetro.json.gz"
#: JR の頁の印(◆・■・▲・【..】・〔..〕)の表。
JR_NOTES_FILE = "JR_注記.final.csv"

#: 入力の層(W19 の構築の入力の元=``BUILD_INPUT_FAMILIES`` の鍵)。
FAMILY_USER = "user_timetables"
FAMILY_CHALLENGE = "odpt_challenge"
FAMILY_STATIC = "odpt_static"
INPUT_FAMILIES: tuple[str, ...] = (FAMILY_USER, FAMILY_CHALLENGE, FAMILY_STATIC)

#: 〔第 2 期 2-4〕ODPT チャレンジ枠(京王 井の頭線)の表を読む切替口。True(既定)=読む(回答 10-13 の 3・7=作品は本
#: シミュレーション・チャレンジ枠は応募と照合用。PENDING 仮-15=ユーザーの最終の確認待ちの間は京王の行を含めたまま活性化)。
#: False=チャレンジ枠の表を読まない(入力の一覧・W19 の資産の表からも外れる)。井の頭線は実データの無い線になり、
#: W12 の等間隔の推定の道(``w12_external_nodes`` の残る線=notes ``equal_interval_lines``・ゲート
#: ``equal_interval_lines_remaining`` が 1)で作る=戻す口。W19 の ``BUILD_INPUT_FAMILIES``(元の宣言)は切替口に依らない。
USE_ODPT_CHALLENGE = True

#: 暦(CSV の値 → W12 の値)。
CALENDARS: tuple[tuple[str, str], ...] = (("平日", "Weekday"), ("土休", "SaturdayHoliday"))
CALENDAR_OF: dict[str, str] = dict(CALENDARS)

#: ``source`` の値(``real_<元>_<会社>``)。半蔵門線・副都心線は今の ``real`` のまま。
SRC_JR = "real_user_pdf_jr_east"
SRC_TOKYU = "real_user_pdf_tokyu"
SRC_KEIO = "real_odpt_challenge_keio"
SRC_GINZA = "real_odpt_open_metro_2026-09"

#: 中心駅(CSV の ``駅`` の値)。
HOME_STATION = "渋谷"

#: 湘南新宿ラインの便を埼京線に畳む(expedient・docstring の ※)。畳まないときは ``fold_lines={}``。
FOLD_LINES: dict[str, str] = {"湘南新宿ライン": "埼京線"}

#: 臨時と見て外す種別(土休の ◆ の特急 4 本=ODPT に無い・README §7・推測)。JR の表だけに当てる。
TEMPORARY_TRAIN_TYPES: tuple[str, ...] = ("特急(踊り子)", "特急(サフィール踊り子)")
#: 外す行に付いているべき印(運転日注意)。
TEMPORARY_MARK = "◆"


@dataclass(frozen=True)
class TableSpec:
    """渋谷の発車の表 1 つ(平日と土休の 2 ファイル)→ W12 の線と向き。"""

    stem: str
    family: str
    company: str
    route: str
    heading: str
    line: str
    direction: str
    operator: str
    source: str
    basis: str

    def file_name(self, cal_ja: str) -> str:
        suffix = "_final.csv" if self.family == FAMILY_USER else "_odpt.csv"
        return f"{self.stem}_{cal_ja}{suffix}"

    def rel_dir(self) -> tuple[str, ...]:
        return USER_TIMETABLE_DIR if self.family == FAMILY_USER else ODPT_CHALLENGE_DIR


_JR = "JR東日本"
_TOKYU = "東急"

#: 読む表の白い一覧(順=読む順=重複を除くときに先に来た方を残す)。line は畳む前の線の名。
USER_TABLES: tuple[TableSpec, ...] = (
    TableSpec("JR_山手線_渋谷_内回り", FAMILY_USER, _JR, "山手線", "品川・東京方面(内回り)",
              "山手線", "上り", "JR東日本", SRC_JR, "線路名称の山手線は品川起点=渋谷→品川は上り(推測・未リサーチ)"),
    TableSpec("JR_山手線_渋谷_外回り", FAMILY_USER, _JR, "山手線", "新宿・池袋方面(外回り)",
              "山手線", "下り", "JR東日本", SRC_JR, "線路名称の山手線は品川起点=渋谷→新宿は下り(推測・未リサーチ)"),
    TableSpec("JR_埼京線_渋谷_大宮方面", FAMILY_USER, _JR, "埼京線・川越線", "大宮・川越方面(下り)",
              "埼京線", "下り", "JR東日本", SRC_JR, "頁の題名(下り)"),
    TableSpec("JR_埼京線_渋谷_大崎方面", FAMILY_USER, _JR, "埼京線・川越線", "大崎方面(上り)",
              "埼京線", "上り", "JR東日本", SRC_JR, "頁の題名(上り)"),
    TableSpec("JR_相鉄線直通_渋谷_相鉄線方面", FAMILY_USER, _JR, "相鉄線直通", "相鉄線方面(下り)",
              "埼京線", "上り", "JR東日本", SRC_JR,
              "題名は下りだが渋谷→大崎の向き(南行)=ODPT 埼京線 南行=大崎方面+相鉄線方面"),
    TableSpec("JR_湘南新宿ライン_渋谷_北行", FAMILY_USER, _JR, "湘南新宿ライン", "高崎・宇都宮方面(北行)",
              "湘南新宿ライン", "下り", "JR東日本", SRC_JR, "北行=大宮方面と同じ向き"),
    TableSpec("JR_湘南新宿ライン_渋谷_南行", FAMILY_USER, _JR, "湘南新宿ライン", "横浜・大船方面(南行)",
              "湘南新宿ライン", "上り", "JR東日本", SRC_JR, "南行=大崎方面と同じ向き"),
    TableSpec("東急_東横線_渋谷_横浜方面", FAMILY_USER, _TOKYU, "東横線",
              "横浜・元町・中華街・新横浜・二俣川方面", "東横線", "下り", "東急電鉄", SRC_TOKYU,
              "東急の表の方面(下り)=時刻表の記録 README §2-1"),
    TableSpec("東急_副都心線_渋谷_和光市方面", FAMILY_USER, _TOKYU, "副都心線(東横線直通・東急の標準時刻表)",
              "池袋・和光市・森林公園・飯能方面", "東横線", "上り", "東急電鉄", SRC_TOKYU,
              "東急の表の題名 TY01_渋谷(上り)=副都心線へ直通する便"),
    TableSpec("東急_田園都市線_渋谷_中央林間方面", FAMILY_USER, _TOKYU, "田園都市線",
              "二子玉川・長津田・中央林間方面", "田園都市線", "下り", "東急電鉄", SRC_TOKYU,
              "東急の表の方面(下り)=時刻表の記録 README §2-1"),
    TableSpec("東急_半蔵門線_渋谷_押上方面", FAMILY_USER, _TOKYU, "半蔵門線(田園都市線直通・東急の標準時刻表)",
              "押上・久喜・南栗橋方面", "田園都市線", "上り", "東急電鉄", SRC_TOKYU,
              "東急の表の題名 DT01_渋谷(上り)=半蔵門線へ直通する便"),
    TableSpec("京王_井の頭線_渋谷_吉祥寺方面", FAMILY_CHALLENGE, "京王", "井の頭線", "吉祥寺方面",
              "井の頭線", "下り", "京王電鉄", SRC_KEIO, "渋谷が起点=渋谷発は下り(ODPT Outbound)"),
)


@dataclass(frozen=True)
class OdptTrainSpec:
    """ODPT の列車時刻表から「起点の駅の発車」を取る線。"""

    line: str
    operator: str
    railway: str
    origin_station: str
    source: str


#: 銀座線(9 月改正の版・ODPT オープン枠の静的データ版 1)。
GINZA_SPEC = OdptTrainSpec(
    line="銀座線",
    operator="東京メトロ",
    railway="odpt.Railway:TokyoMetro.Ginza",
    origin_station="odpt.Station:TokyoMetro.Ginza.Shibuya",
    source=SRC_GINZA,
)

#: 線ごとの版の宣言(``w12_timetable_versions.json`` に書く・値は記録 README §7 と各読み取りの記録から)。
VERSION_DECLARATIONS: dict[str, dict[str, str]] = {
    "山手線": {
        "declared": "2026-03-14 改正と同じ版と推測(頁は JR 時刻表 2026 年 10 月号に基づく・改正日の記載なし。"
                    "ODPT チャレンジ枠 dct:issued 2026-03-14 と全表で本数と時刻が一致=extraction-jr.md §7)",
        "relation_to_world_time": "before_inferred",
    },
    "埼京線": {
        "declared": "2026-03-14 改正と同じ版と推測(山手線と同じ根拠)。湘南新宿ライン・相鉄線直通の表を含む。"
                    "土休の ◆ 特急 4 本(踊り子・サフィール踊り子)は ODPT に無く臨時と見て外した(推測)",
        "relation_to_world_time": "before_inferred",
    },
    "東横線": {
        "declared": "2026-03-14 改正(東急の表の右下の記載・第330 の読み取り)。上りは東急が出す副都心線の"
                    "標準時刻表(ODPT 副都心線 2026-03-14 と全件一致)",
        "relation_to_world_time": "before",
    },
    "田園都市線": {
        "declared": "2026-03-14 改正(東急の表の右下の記載・第330 の読み取り)。上りは東急が出す半蔵門線の"
                    "標準時刻表(ODPT 半蔵門線 2026-03-14 と全件一致)",
        "relation_to_world_time": "before",
    },
    "井の頭線": {
        "declared": "ODPT チャレンジ枠 dct:issued 2025-03-17(平日)/2025-03-15(土休)・dc:date 2026-07-03。"
                    "改正日の欄は無い(空欄)。07-03〜07-13 に改正が無ければ世界の時点に効いていた版(推測)",
        "relation_to_world_time": "before_inferred",
    },
    "銀座線": {
        "declared": "ODPT オープン枠の静的データ版 1・dct:issued 2026-09-19(9 月改正)=世界の時点"
                    "(2026-07-13)より後の版(回答 10-13b §2 のユーザー決定)。07-13 時点の版"
                    "(07-07 取得・平日 2025-03-15/土休 2025-11-01)は使わない(記録として残す)",
        "relation_to_world_time": "after",
    },
    "半蔵門線": {
        "declared": "今の 7 月の取得(2026-07-07)のまま・dct:issued 2026-03-14",
        "relation_to_world_time": "before",
    },
    "副都心線": {
        "declared": "今の 7 月の取得(2026-07-07)のまま・dct:issued 2026-03-14",
        "relation_to_world_time": "before",
    },
}


# ---------------------------------------------------------------------- 入力の一覧
def table_rel_paths(spec: TableSpec) -> list[str]:
    """表 1 つの 2 ファイル(平日・土休)の data 根からの相対パス。"""
    return ["/".join((*spec.rel_dir(), spec.file_name(cal_ja))) for cal_ja, _ in CALENDARS]


def tables_in_use() -> tuple[TableSpec, ...]:
    """〔2-4〕読む表=:data:`USER_TABLES` から、切替口 :data:`USE_ODPT_CHALLENGE` が False ならチャレンジ枠の表を除く。"""
    return tuple(s for s in USER_TABLES if USE_ODPT_CHALLENGE or s.family != FAMILY_CHALLENGE)


def input_rel_paths(family: str, *, in_use: bool = True) -> tuple[str, ...]:
    """入力の層 → 読むファイル(data 根からの相対・読む順)。W19 の資産表と ``input_hash`` に使う。

    〔2-4〕``in_use=True``(既定)は読む表(:func:`tables_in_use`)だけ。``in_use=False`` は切替口に依らない元の宣言
    (W19 の ``BUILD_INPUT_FAMILIES``=holdout の層と同じ元かの照合に使う)。
    """
    specs = tables_in_use() if in_use else USER_TABLES
    if family == FAMILY_USER:
        out: list[str] = []
        for spec in specs:
            if spec.family == FAMILY_USER:
                out.extend(table_rel_paths(spec))
        out.append("/".join((*USER_TIMETABLE_DIR, JR_NOTES_FILE)))
        return tuple(out)
    if family == FAMILY_CHALLENGE:
        out = []
        for spec in specs:
            if spec.family == FAMILY_CHALLENGE:
                out.extend(table_rel_paths(spec))
        return tuple(out)
    if family == FAMILY_STATIC:
        return ("/".join((*ODPT_STATIC_DIR, ODPT_STATIC_METRO_TRAIN_TIMETABLE)),)
    raise ValueError(f"未知の入力の層: {family}")


def all_input_rel_paths() -> tuple[str, ...]:
    out: list[str] = []
    for fam in INPUT_FAMILIES:
        out.extend(input_rel_paths(fam))
    return tuple(out)


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------- 読み
def hhmm(hour: int, minute: int) -> str:
    """CSV の (時, 分) → ``HH:MM``(0 時台は 00:MM=翌日の 0 時)。範囲の外は ValueError。"""
    h, m = int(hour), int(minute)
    if not (0 <= h < HOURS_PER_DAY and 0 <= m < MINUTES_PER_HOUR):
        raise ValueError(f"時刻の範囲の外: {hour}:{minute}")
    return f"{h:02d}:{m:02d}"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """読み取りの CSV(UTF-8 BOM 付き)→ 行の辞書。"""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def rows_from_table(spec: TableSpec, cal_ja: str, raw: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    """表 1 ファイルの行 → W12 の行(畳む前の line)。CSV の会社・路線・駅・方面・平日土休が一覧と違えば止まる。"""
    out: list[dict[str, Any]] = []
    want = {"会社": spec.company, "路線": spec.route, "駅": HOME_STATION, "方面": spec.heading, "平日土休": cal_ja}
    for i, r in enumerate(raw):
        for k, v in want.items():
            if str(r.get(k, "")) != v:
                raise ValueError(f"{spec.file_name(cal_ja)} の {i} 行目: {k}={r.get(k)!r}(一覧では {v!r})")
        out.append({
            "line": spec.line,
            "operator": spec.operator,
            "direction": spec.direction,
            "calendar": CALENDAR_OF[cal_ja],
            "departure": hhmm(int(r["時"]), int(r["分"])),
            "source": spec.source,
            "train_type": str(r.get("種別", "")),
            "table": spec.stem,
            "version_text": str(r.get("版", "")),
            "_hm": (int(r["時"]), int(r["分"])),
        })
    return out


def jr_marks(notes: Sequence[Mapping[str, str]]) -> dict[tuple[str, str, int, int], str]:
    """``JR_注記.final.csv`` → (表, 平日土休, 時, 分) → 印の文字列。"""
    out: dict[tuple[str, str, int, int], str] = {}
    for r in notes:
        key = (str(r["表"]), str(r["平日土休"]), int(r["時"]), int(r["分"]))
        out[key] = out.get(key, "") + str(r["注記"])
    return out


def split_temporary(
    rows: Sequence[dict[str, Any]],
    marks: Mapping[tuple[str, str, int, int], str],
    types: Iterable[str] = TEMPORARY_TRAIN_TYPES,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(残す行, 外す行)。外す行に ◆ が付いていなければ ValueError(黙って外さない)。"""
    tset = set(types)
    keep: list[dict[str, Any]] = []
    drop: list[dict[str, Any]] = []
    cal_ja_of = {v: k for k, v in CALENDARS}
    for r in rows:
        if r["source"] == SRC_JR and r["train_type"] in tset:
            key = (r["table"], cal_ja_of[r["calendar"]], *r["_hm"])
            if TEMPORARY_MARK not in marks.get(key, ""):
                raise ValueError(f"臨時と見て外す行に {TEMPORARY_MARK} が無い: {r['table']} {r['calendar']} {r['train_type']}")
            drop.append(r)
        else:
            keep.append(r)
    return keep, drop


def fold(rows: Iterable[dict[str, Any]], fold_lines: Mapping[str, str]) -> list[dict[str, Any]]:
    """線を畳む(``fold_lines`` の鍵の線 → 値の線)。行の他の欄は変えない。"""
    out = []
    for r in rows:
        ln = fold_lines.get(r["line"], r["line"])
        out.append(r if ln == r["line"] else {**r, "line": ln, "line_raw": r["line"]})
    return out


def dedup(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """同じ (line, direction, calendar, departure) を 1 本に(先に来た行を残す)。返り値=(行, 除いた件数の表)。"""
    seen: set[tuple[str, str, str, str]] = set()
    out: list[dict[str, Any]] = []
    removed: Counter = Counter()
    for r in rows:
        key = (r["line"], r["direction"], r["calendar"], r["departure"])
        if key in seen:
            removed["|".join(key[:3])] += 1
            continue
        seen.add(key)
        out.append(r)
    return out, dict(sorted(removed.items()))


def parse_train_timetable_departures(doc: Any, spec: OdptTrainSpec) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """ODPT ``odpt:TrainTimetable`` → 起点の駅(``spec.origin_station``)の発車の行と点検の表。

    取るのは ``odpt:railway`` が ``spec.railway`` で、最初の停車(``odpt:trainTimetableObject`` の先頭)が
    起点の駅の列車の ``odpt:departureTime``。暦は ``odpt:calendar`` の末尾(Weekday/SaturdayHoliday 以外は止まる)。
    向きは ``odpt:railDirection`` の ``:`` の後(例 ``TokyoMetro.Asakusa``)。
    """
    data = doc.get("data", []) if isinstance(doc, Mapping) else list(doc)
    rows: list[dict[str, Any]] = []
    n_railway = 0
    origin_mismatch = 0
    issued: Counter = Counter()
    dates: Counter = Counter()
    for tr in data:
        if str(tr.get("odpt:railway", "")) != spec.railway:
            continue
        n_railway += 1
        objs = tr.get("odpt:trainTimetableObject") or []
        if not objs:
            continue
        first = objs[0]
        if str(first.get("odpt:departureStation", "")) != spec.origin_station:
            continue
        t = first.get("odpt:departureTime")
        if not t:
            continue
        cal = str(tr.get("odpt:calendar", "")).split(":")[-1]
        if cal not in ("Weekday", "SaturdayHoliday"):
            raise ValueError(f"暦が Weekday/SaturdayHoliday の外: {tr.get('odpt:calendar')!r}")
        origins = tr.get("odpt:originStation") or []
        if list(origins) != [spec.origin_station]:
            origin_mismatch += 1
        issued[str(tr.get("dct:issued", ""))] += 1
        dates[str(tr.get("dc:date", ""))] += 1
        rows.append({
            "line": spec.line,
            "operator": spec.operator,
            "direction": str(tr.get("odpt:railDirection", "")).split(":")[-1],
            "calendar": cal,
            "departure": str(t),
            "source": spec.source,
            "train_type": str(tr.get("odpt:trainType", "")).split(":")[-1],
            "table": f"odpt_static:{spec.railway.split(':')[-1]}",
            "version_text": str(tr.get("dct:issued", "")),
        })
    check = {
        "n_trains_of_railway": n_railway,
        "n_departures_from_origin": len(rows),
        "origin_station_field_mismatch": origin_mismatch,
        "dct_issued": dict(sorted(issued.items())),
        "dc_date": dict(sorted(dates.items())),
    }
    return rows, check


def load_odpt_static(path: Path) -> Any:
    """``*.json.gz``(ODPT の静的データの取得の形=``{"_meta":…, "data": [...]}``)を読む。"""
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------- まとめ
@dataclass
class RealTimetables:
    """実ダイヤの読みの結果(行は畳んだ後・重複を除いた後・臨時を外した後)。"""

    rows: list[dict[str, Any]]
    table_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    temporary_excluded: dict[str, dict[str, int]] = field(default_factory=dict)
    dedup_removed: dict[str, int] = field(default_factory=dict)
    ginza_check: dict[str, Any] = field(default_factory=dict)
    version_texts: dict[str, list[str]] = field(default_factory=dict)
    fold_lines: dict[str, str] = field(default_factory=dict)
    input_paths: list[Path] = field(default_factory=list)


def load_real_timetables(data_root: Path, *, fold_lines: Mapping[str, str] | None = None) -> RealTimetables:
    """data 根から実ダイヤを読む(白い一覧の表+ODPT の銀座線)。ファイルが無ければ FileNotFoundError。"""
    root = Path(data_root)
    fl = dict(FOLD_LINES if fold_lines is None else fold_lines)
    paths = [root.joinpath(*rel.split("/")) for rel in all_input_rel_paths()]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"W12 の実ダイヤの入力が無い: {p}")

    raw_rows: list[dict[str, Any]] = []
    counts: dict[str, dict[str, int]] = {}
    for spec in tables_in_use():  # 〔2-4〕切替口 USE_ODPT_CHALLENGE が False ならチャレンジ枠の表を読まない
        counts[spec.stem] = {}
        for cal_ja, cal in CALENDARS:
            p = root.joinpath(*spec.rel_dir(), spec.file_name(cal_ja))
            got = rows_from_table(spec, cal_ja, read_csv_rows(p))
            counts[spec.stem][cal] = len(got)
            raw_rows.extend(got)

    marks = jr_marks(read_csv_rows(root.joinpath(*USER_TIMETABLE_DIR, JR_NOTES_FILE)))
    keep, drop = split_temporary(raw_rows, marks)
    temp: dict[str, dict[str, int]] = defaultdict(dict)
    for r in drop:
        temp[r["table"]][r["calendar"]] = temp[r["table"]].get(r["calendar"], 0) + 1

    ginza_doc = load_odpt_static(root.joinpath(*ODPT_STATIC_DIR, ODPT_STATIC_METRO_TRAIN_TIMETABLE))
    ginza_rows, ginza_check = parse_train_timetable_departures(ginza_doc, GINZA_SPEC)
    counts[ginza_rows[0]["table"] if ginza_rows else "odpt_static:TokyoMetro.Ginza"] = dict(
        sorted(Counter(r["calendar"] for r in ginza_rows).items())
    )

    rows, removed = dedup(fold([*keep, *ginza_rows], fl))
    versions: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        versions[r["line"]].add(r["version_text"])
    return RealTimetables(
        rows=[{k: r[k] for k in ("line", "operator", "direction", "calendar", "departure", "source")} for r in rows],
        table_counts=counts,
        temporary_excluded={k: dict(sorted(v.items())) for k, v in sorted(temp.items())},
        dedup_removed=removed,
        ginza_check=ginza_check,
        version_texts={k: sorted(v) for k, v in sorted(versions.items())},
        fold_lines=fl,
        input_paths=paths,
    )


def metro_station_versions(doc: Mapping[str, Any]) -> dict[str, Any]:
    """ODPT の駅の時刻表(今の 7 月の取得)→ 暦ごとの dct:issued・dc:date と取得の時刻。"""
    meta = doc.get("_meta", {}) if isinstance(doc.get("_meta"), Mapping) else {}
    out: dict[str, Any] = {"fetched_at": str(meta.get("fetched_at", "")), "tables": {}}
    for t in doc.get("data", []):
        cal = str(t.get("odpt:calendar", "")).split(":")[-1]
        out["tables"][cal] = {"dct_issued": str(t.get("dct:issued", "")), "dc_date": str(t.get("dc:date", ""))}
    out["tables"] = dict(sorted(out["tables"].items()))
    return out


def spec_rows() -> list[dict[str, str]]:
    """方面の写像の表(params と記録に書く形)。"""
    return [
        {"table": s.stem, "family": s.family, "company": s.company, "route": s.route, "heading": s.heading,
         "line": s.line, "direction": s.direction, "source": s.source, "basis": s.basis}
        for s in USER_TABLES
    ] + [{"table": "odpt_static:TokyoMetro.Ginza", "family": FAMILY_STATIC, "company": "東京メトロ",
          "route": "銀座線", "heading": "渋谷が起点の列車", "line": GINZA_SPEC.line, "direction": "odpt:railDirection",
          "source": GINZA_SPEC.source, "basis": "ODPT TrainTimetable の起点=渋谷の列車の発車"}]
