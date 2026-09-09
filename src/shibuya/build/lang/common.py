"""build.lang.common — W14/W15 が共有する純粋ヘルパ。

内訳
- **プロンプト jsonl の入出力**(``tools/gen/fleet_gen.py`` の形式に合わせる)。
- **正規化**(知覚契約書 §2.4 の 9 項・``perception.normalize`` を通す)。
- **検証器**: ①rep 間バイト一致 ②固有名詞の捏造検査(D-W18 のゲート)③数字の捏造検査
  ④評価語・誘導表現・命令文の検査(広告答申 §4)⑤長さ上限(§3.2 のチャネル枠)
  ⑥個体依存語(§2.4 ⑧)。
- **凍結**: 合格した文だけを parquet へ。落ちた行は理由つきでゲート json に残す。

逐次ループ宣言(P4): 本モジュールのループは**プロンプト件数**(W14 2,337・W15 520)ぶんの
1 本だけ。個体数・tick 数には比例しない(構築時 1 回・I1 初期化予算)。

expedient(本モジュールぶん・登録簿へ)
- 生成モデル・復号パラメータ: ``MODEL_HINT``/``TEMPERATURE=0.0``/``SEED=20260909``/``REPEAT=2``。
  seed の値そのものに根拠はない(日付由来)。**rep 間で seed をずらさない**のが
  「同一 seed・同一プロンプトで 2 回」というバイト一致ゲートの定義(fleet_gen と同じ読み)。
- 固有名詞検査の規則(``scan_proper_nouns`` の N1-N6)。日本語の固有名詞は形態素解析なしでは
  同定できないので、**字種と接尾辞**で候補を拾い「入力文字列の部分文字列か」で判定する
  保守的な検査にした。裸の地名(接尾辞を持たない「渋谷」「原宿」等)は N5 の既知語リストで
  しか捕まらない=**残余リスク**(登録簿に明記)。
- ``GENERIC_KATAKANA``/``GENERIC_PLACE``/``KNOWN_PROPER``/``BANNED_EVALUATIVE``/
  ``BANNED_INDUCEMENT`` の語リスト(自前)。
- 不合格率の閾値(``W14_MAX_FAIL_RATE``/``W15_MAX_FAIL_RATE``)。
- トークン推定法= ``perception.channels.estimate_tokens``(UTF-8 文字数 ÷ 2)。**知覚側の
  予算判定と同じ関数**を使う(別の推定法だと枠に収まる/収まらないが食い違う)。
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterable, Sequence

# --- 層契約の例外(build → perception・__init__ の docstring に理由)------------------
from shibuya.perception import normalize as N
from shibuya.perception.attention import strip_imperatives
from shibuya.perception.channels import estimate_tokens

from ..geo import common as C

__all__ = [
    "MODEL_HINT",
    "TEMPERATURE",
    "SEED",
    "REPEAT",
    "W14_MAX_FAIL_RATE",
    "W15_MAX_FAIL_RATE",
    "Prompt",
    "prompts_sha256",
    "write_prompts",
    "read_prompts",
    "read_responses",
    "Violation",
    "normalize_generated",
    "scan_proper_nouns",
    "check_banned_words",
    "check_individual_words",
    "Verdict",
    "verify_one",
    "IngestReport",
]

# --------------------------------------------------------------- 復号パラメータ(D-W18)
#: D-W18「T2(32B AWQ TP1)で1回生成(温度0)→バイト凍結」。served-model-name は
#: fleet_gen が ``/v1/models`` から解決するので、ここでは**記録用のヒント**にとどめる。
MODEL_HINT: Final[str] = "Qwen3-32B-AWQ"
#: 温度(§0-8「温度とseedを固定」)。
TEMPERATURE: Final[float] = 0.0
#: seed(固定・値は日付由来=expedient)。rep ごとにずらさない。
SEED: Final[int] = 20260909
#: 同一プロンプトの生成回数(§1 W14 ゲート「同店2回生成でバイト一致」)。
REPEAT: Final[int] = 2

#: 不合格率の上限(expedient)。フォールバック(従来の合成文)があるので世界は壊れないが、
#: これを超えたら「プロンプトかモデルの問題」として段階ゲートを落とす。
W14_MAX_FAIL_RATE: Final[float] = 0.10
W15_MAX_FAIL_RATE: Final[float] = 0.05


# --------------------------------------------------------------- プロンプト jsonl
@dataclass(frozen=True)
class Prompt:
    """1 呼ぶんのプロンプト(``fleet_gen`` の入力行)。

    Attributes:
        id: 呼の識別子(W14=poi_id・W15=place_id)。
        system / user: チャット 2 役の本文。
        max_tokens: 生成上限(§3.2 のチャネル枠から導く)。
        allowed: **固有名詞・数字の検査に使う入力文字列**(通常は user 本文)。
            凍結時の検査で「入力に無い固有名詞/数字」を判定する母集合。
        regex: 構造化出力の正規表現(``fleet_gen`` が vLLM ``structured_outputs`` へ渡す)。
            **空なら行に出さない**——既に生成済みの段階(W14)のプロンプト SHA を動かさない
            ため。長さの上限を文法で強制する用途に使う(W15)。
    """

    id: str
    system: str
    user: str
    max_tokens: int
    allowed: str = ""
    regex: str = ""

    def to_json(self) -> dict[str, Any]:
        """fleet_gen が読む行(**キー順は canonical_json_bytes が整列**)。"""
        row: dict[str, Any] = {
            "id": self.id,
            "system": self.system,
            "user": self.user,
            "max_tokens": int(self.max_tokens),
            "temperature": TEMPERATURE,
            "seed": SEED,
            "repeat": REPEAT,
            "thinking": False,
        }
        if self.regex:
            row["regex"] = self.regex
        return row


def _jsonl_bytes(prompts: Sequence[Prompt]) -> bytes:
    """プロンプト列 → jsonl のバイト列(決定論・LF 固定)。"""
    return b"".join(C.canonical_json_bytes(p.to_json()) + b"\n" for p in prompts)


def prompts_sha256(prompts: Sequence[Prompt]) -> str:
    """プロンプト列の版ハッシュ(文面を変えたら値が変わる=改版の検出器)。"""
    return C.sha256_bytes(_jsonl_bytes(prompts))


def write_prompts(out_dir: Path, name: str, prompts: Sequence[Prompt]) -> dict[str, Any]:
    """プロンプト jsonl を書く(``common.write_json`` と同じ記録を返す)。"""
    path = out_dir / name
    path.write_bytes(_jsonl_bytes(prompts))
    return {
        "path": path.relative_to(out_dir).as_posix(),
        "sha256": C.sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": len(prompts),
    }


def read_prompts(path: Path) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def read_responses(path: Path) -> dict[tuple[str, int], str]:
    """応答 jsonl → ``(id, rep) → text``。

    同じ ``(id, rep)`` が複数行あるとき(fleet_gen の resume で二重に書かれた等)は
    **最後の行**を採る(fleet_gen は追記型)。
    """
    out: dict[tuple[str, int], str] = {}
    with open(path, "r", encoding="utf-8") as fh:
        for ln in fh:
            if not ln.strip():
                continue
            r = json.loads(ln)
            out[(str(r["id"]), int(r.get("rep", 0)))] = str(r.get("text", "") or "")
    return out


# --------------------------------------------------------------- 正規化(§2.4)
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_WRAPPING_QUOTES: Final[tuple[tuple[str, str], ...]] = (
    ("「", "」"), ("『", "』"), ('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’"),
)
#: 句読点まわりの空白(``strip_imperatives`` が落とす位置と同じ)。
_PUNCT_SPACE: Final[re.Pattern[str]] = re.compile(r"[ ]*([、。！？!?])[ ]*")

#: 先頭の見出し語(**自前・expedient**)。W15 の system は「「見えるもの:」に続けて読まれる
#: 文として書く」と指示するが、第3回のパイロットでは 3 件中 2 件がその見出しを本文へ
#: 書き写した(「見えるもの: 地上に街区があり…」)。レンダラのテンプレ ``B2.visible`` が
#: 既に「見えるもの: 」を持つので、そのまま凍結すると**見出しが二重になる**。
#: コロンは全角/半角どちらも受け、後続の空白も落とす。**先頭にある場合だけ**除去する
#: (文中の「説明: 」は本文の一部かもしれないので触らない)。
_LEADING_HEADINGS: Final[tuple[str, ...]] = (
    "見えるもの", "見える物", "説明", "区画の説明", "静的な説明", "区画の静的な説明",
    "本文", "出力", "回答", "答え", "記述", "描写", "店頭表示", "表示",
)
_LEADING_HEADING: Final[re.Pattern[str]] = re.compile(
    r"^(?:" + "|".join(_LEADING_HEADINGS) + r")[ ]*[:：][ ]*"
)


def normalize_generated(raw: str) -> tuple[str, str]:
    """生成文 → (正規化文, 異常理由)。理由が空文字なら正常。

    手順(**この順序ごと凍結**):
      1. ``<think>…</think>`` を落とす(fleet_gen は ``enable_thinking=False`` だが保険)。
      2. ``perception.normalize.canonical_whitespace``(NFKC・改行 LF・空白畳み・端の空白落とし)。
      3. 空行を落として**1 行**であること(複数行は ``multiline`` で不合格)。
      4. 全体を囲む引用符を外す。
      5. **先頭の見出し語**(``_LEADING_HEADINGS`` + コロン)を落とす(無くなるまで繰り返す)。
      6. 句読点まわりの空白を落とす。
      (W15 のみ、呼び出し側 ``verify_one`` が末尾の句点をさらに落とす)

    この関数は**冪等**(``normalize_generated(normalize_generated(x)[0])[0] == …``)。
    ``verify_one`` が冪等性を検査し、破れたら ``normalize_mismatch`` で不合格にする。
    """
    text = _THINK.sub("", str(raw))
    text = N.canonical_whitespace(text)
    lines = [ln for ln in text.split("\n") if ln.strip()]
    if not lines:
        return "", "empty"
    if len(lines) > 1:
        return "", "multiline"
    text = lines[0].strip()
    for lq, rq in _WRAPPING_QUOTES:
        if len(text) >= 2 and text.startswith(lq) and text.endswith(rq):
            text = text[len(lq): -len(rq)].strip()
            break
    # 5. 先頭の見出し語を落とす(「見えるもの: 地上に…」→「地上に…」)。テンプレ側が
    #    既に見出しを持つので二重になる。**無くなるまで繰り返す**=冪等
    #    (1 回だけだと「見えるもの: 説明: …」で 2 度目の正規化が動き normalize_mismatch)。
    while True:
        stripped = _LEADING_HEADING.sub("", text, count=1).strip()
        if stripped == text:
            break
        text = stripped
    # 6. 句読点まわりの空白を落とす。**理由**: 描画時に通る ``strip_imperatives`` は文単位で
    #    ``strip()`` してから連結するので、句点のあとに空白が残っていると「凍結したバイト列」と
    #    「描画されるバイト列」がずれる(文面凍結宣言が壊れる)。
    text = _PUNCT_SPACE.sub(r"\1", text).strip()
    if not text:
        return "", "empty"
    return text, ""


# --------------------------------------------------------------- 固有名詞・数字の検査
@dataclass(frozen=True)
class Violation:
    """検査の指摘 1 件。"""

    rule: str
    found: str

    def to_json(self) -> dict[str, str]:
        return {"rule": self.rule, "found": self.found}


#: N1 ラテン**語**(店名・ブランド名は英字が多い)。**空白と数字では割る**
#: (「Skechers 11」のように入力の英字店名へ後続の数字が連結すると 1 トークン扱いになり、
#:  第1回生成で 47 件の偽陽性を出した=2026-09-09 の親の全件分析)。``&`` は語内に残す
#: (「C&C」「H&M」を 1 語として見るため)。アクセント付きラテン文字も語に含める
#: (「Créa」を C+ré+a に割らない)。
_LATIN_RUN: Final[re.Pattern[str]] = re.compile(
    r"[A-Za-zÀ-ÖØ-öø-ÿĀ-ſ][A-Za-zÀ-ÖØ-öø-ÿĀ-ſ&'’.\-]*"
)
#: N2 カタカナ列。
_KATAKANA_RUN: Final[re.Pattern[str]] = re.compile(r"[ァ-ヶーヴ・]{2,}")
#: N4 算用数字の並び。
_DIGIT_RUN: Final[re.Pattern[str]] = re.compile(r"[0-9]+")
#: N6 漢数字+助数詞(算用数字の検査を漢数字で迂回されないように)。
_KANSUJI_COUNTER: Final[re.Pattern[str]] = re.compile(
    r"[〇一二三四五六七八九十百千万]+(?:軒|人|階|棟|本|基|台|件|個|店|箇所|か所)"
)
#: N7(W14 のみ)漢字列。**3 文字以上**に限る(2 文字漢語は一般名詞になりやすく、
#: 第1回生成では 113 件中ほぼ全部が「開校/開館/参拝/診療/利用/軽食」型の偽陽性だった)。
_KANJI_RUN: Final[re.Pattern[str]] = re.compile(r"[一-龥々]{3,}")
#: 完全な曜日名(「月曜」「月曜日」)。**略記ではない**。
_WEEKDAY_FULL: Final[re.Pattern[str]] = re.compile(r"[月火水木金土日]曜日?")
#: A1 曜日の**略記**=「曜」を伴わない曜日字の連なり(「月金」「土日」)。**⑥ 省略記法**として
#: 扱う(N7 の対象外=親指示 2026-09-09)。入力にそのまま在る表現は略記でない。
#: **完全な曜日名の連結**(「土曜日曜」「火曜金曜」)は略記ではない(第2回生成で 56 件・
#: 入力の「土日は…」をモデルが曜日名へ展開した形=親指示 2026-09-09 第3回)。
_WEEKDAY_BARE_RUN: Final[re.Pattern[str]] = re.compile(r"[月火水木金土日]{2,}")


def _strip_weekday_names(text: str) -> str:
    """完全な曜日名を落とす(略記判定・N7 残差の前処理)。"""
    return _WEEKDAY_FULL.sub("", str(text))

#: N3 地物・組織の接尾辞(これで終わる語は固有名詞の疑い)。
PLACE_SUFFIXES: Final[tuple[str, ...]] = (
    "駅", "ビル", "通り", "坂", "交差点", "公園", "神社", "寺", "橋", "丁目", "会館",
    "タワー", "センター", "広場", "ホール", "百貨店", "大学", "美術館", "博物館",
    "劇場", "スタジアム", "歩道橋", "小学校", "中学校", "高校", "病院", "銀行",
)
_PLACE_RUN: Final[re.Pattern[str]] = re.compile(
    r"[一-龥々ヶA-Za-zァ-ヶー0-9]{1,15}(?:" + "|".join(PLACE_SUFFIXES) + ")"
)
#: 1 文字の接尾辞(``_residual`` の残りがこれだけでも N3 とみなす)。
_SINGLE_CHAR_SUFFIXES: Final[frozenset[str]] = frozenset(
    s for s in PLACE_SUFFIXES if len(s) == 1
)

#: N2 の除外(入力に無くてよい一般カタカナ語・expedient)。第1回生成(2026-09-09)の
#: 偽陽性(スイーツ/パチンコ/クリニック/イタリアン/デザート/サンドイッチ/グッズ/
#: カレーハウス/アイスクリーム/ヘアケア/ファストフード/ブランド/トラック)を取り込んで
#: 約 100 語へ拡張した。**複合語は分解して照合**するので、基語を入れておけば足りる。
GENERIC_KATAKANA: Final[frozenset[str]] = frozenset(
    """ビル オフィス マンション アパート コンビニ カフェ レストラン バー ホテル デッキ
    テナント アーケード ガード スロープ エレベーター エスカレーター ベンチ ガードレール
    タイル アスファルト ネオン シャッター テラス ショップ スーパー ドラッグストア
    パーキング バス タクシー ビジョン サイン ロータリー プラザ モール パーク フロア
    ガラス コンクリート メートル レジ カウンター テーブル メニュー サービス セール
    オープン クローズ ランチ ディナー モーニング テイクアウト イートイン セット
    ドリンク コーヒー ケーキ パン カレー ラーメン ピザ ワイン ビール
    スイーツ デザート アイス クリーム アイスクリーム サンド サンドイッチ ハウス
    パチンコ スロット ゲームセンター クリニック サロン ヘア ヘアー ヘアケア
    アクセサリー コスメ グッズ ブランド アパレル ファッション インテリア キッチン
    バッグ シューズ スニーカー ジュエリー メガネ ドラッグ クリーニング
    イタリアン フレンチ チャイニーズ エスニック ステーキ ハンバーガー バーガー
    ファストフード ファミリー ビュッフェ バイキング テイクアウト デリ ベーカリー
    スタンド キオスク コインランドリー ジム スタジオ スクール オフィスビル
    エントランス ロビー ホーム プラットホーム コーナー スペース ブース
    トラック トラックヤード バイク シェアサイクル タワーマンション""".split()
)
#: N3 の除外(接尾辞を持つが固有名詞ではない一般語・expedient)。
GENERIC_PLACE: Final[frozenset[str]] = frozenset(
    """歩道橋 交差点 横断歩道 雑居ビル 商業ビル 高層ビル 低層ビル 複合ビル 駅ビル
    地下街 立体駐車場 大学 病院 銀行 公園 神社 寺 橋 坂 通り 駅""".split()
)
#: N7 の除外(W14 の漢字厳格モードで入力に無くてよい一般語・expedient)。
#: 第1回生成(2026-09-09)の偽陽性(開校/開館/参拝/診療/利用/軽食/紹介/用品)を取り込んだ。
GENERIC_KANJI: Final[frozenset[str]] = frozenset(
    """営業 定休 終日 年中無休 時間 価格 中程度 表示 店頭 案内 本日 現在 毎日 平日
    土日 祝日 休業 無休 開店 閉店 料金 店内 販売 提供 飲食 物販 宿泊 施設 入口
    地上 地下 階段 通行 表示板 看板 建物 一部 以外 以上 以下 前後
    開館 閉館 休館 開校 休校 参拝 診療 休診 利用 軽食 紹介 用品 受付 見学 入場
    予約 相談 対応 時間営業 深夜 早朝 午前 午後 週末 曜日 時刻 各日 全日 通年
    通常 臨時 変更 歯科 内科 外科 医院 薬局 教室 講座 事務 物件 交流 礼拝 説法
    展示 常設 上映 公演 料理 中華 和食 洋食 定食 弁当 惣菜 喫茶 珈琲 専門 専門店
    書店 古書 雑貨 美容 理容 整体 接骨 保育 学習 郵便 交番 駐車 駐輪 入館 開場
    閉場 営業時間 提供 併設 取扱 販売店 飲食店 物販店 総菜""".split()
)
#: N5 既知の固有名詞(裸の地名・ブランド。入力に無ければ**捏造**・expedient)。
KNOWN_PROPER: Final[tuple[str, ...]] = (
    "渋谷", "原宿", "表参道", "青山", "代官山", "恵比寿", "新宿", "池袋", "六本木",
    "銀座", "東京", "道玄坂", "宮益坂", "センター街", "スペイン坂", "宇田川",
    "神南", "桜丘", "円山町", "松濤", "代々木", "明治神宮", "ハチ公", "スクランブル",
    "ヒカリエ", "パルコ", "マルイ", "ロフト", "東急", "西武", "小田急", "京王",
    "山手線", "井の頭", "田園都市", "副都心", "半蔵門", "銀座線", "東横",
    "ドンキホーテ", "ドン・キホーテ", "スターバックス", "マクドナルド", "セブンイレブン",
    "ファミリーマート", "ローソン", "ユニクロ", "無印良品", "タワーレコード",
)

#: 評価語(広告答申 §4「看板は構造化属性へ還元」= 評価・煽りを載せない)。
BANNED_EVALUATIVE: Final[tuple[str, ...]] = (
    "人気", "おすすめ", "お勧め", "オススメ", "絶品", "話題", "限定", "名物", "自慢",
    "こだわり", "厳選", "評判", "最高", "最安", "激安", "お得", "格安", "本格", "極上",
    "有名", "定番", "必見", "満足", "美味", "おいしい", "うまい", "新鮮", "豊富",
    "自信", "話題の", "上質", "贅沢", "至福", "特別",
)
#: 誘導表現(同上・来店を誘う語)。
BANNED_INDUCEMENT: Final[tuple[str, ...]] = (
    "ぜひ", "是非", "どうぞ", "ください", "下さい", "いかが", "お立ち寄り", "立ち寄",
    "来店", "今すぐ", "チェック", "お待ち", "歓迎", "お越し", "ご利用ください",
    "してみ", "みませんか",
)
#: 個体依存語(§2.4 ⑧・B0-B4 に置けない語)。``normalize.assert_no_agent_dependent_words``
#: が拾うのは ID・所持金・内受容なので、二人称/一人称の語をここで足す。
#: 「僕」「俺」「我々」は W15 の system が名指しで禁じている語なので表にも入れる
#: (入力由来の語は先に除くので、「俺のフレンチ」のような店名は落ちない)。
INDIVIDUAL_WORDS: Final[tuple[str, ...]] = (
    "あなた", "わたし", "私", "自分", "君", "お客様", "あなたの", "手持ち", "所持",
    "僕", "ぼく", "俺", "おれ", "我々", "われわれ", "私たち",
)


def _digit_runs(text: str) -> set[str]:
    return set(_DIGIT_RUN.findall(text))


def _fold_latin(text: str) -> str:
    """ラテン語の照合用の畳み込み: アクセント除去 + 空白除去 + 小文字化。

    「Curry Shop C & C」の店名に対しモデルが「C&C」と書く/「Créa」に対し「Creá」と
    書く形の**表記ゆれ**を捏造扱いしないため(第1回生成で観測)。
    """
    t = unicodedata.normalize("NFKD", str(text))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return "".join(t.split()).casefold()


def scan_proper_nouns(text: str, allowed: str, *, kanji_strict: bool = False) -> list[Violation]:
    """固有名詞・数字の捏造検査(D-W18 のゲート「固有名詞は入力(POI名)由来のみ」)。

    候補を字種で拾い、``allowed``(=プロンプトに与えた事実の本文)の**部分文字列**なら
    合格、そうでなければ違反にする。一般語は語リストで除外する。

    Args:
        text: 検査する生成文(正規化済み)。
        allowed: 入力として与えた文字列(通常は user プロンプト本文)。
        kanji_strict: True なら N7(漢字列も入力由来に限る)を適用する。
            出力の語彙が強く制約される W14 でだけ True にする(W15 の自由記述では
            誤検出が多すぎて使えない=登録簿に宣言)。

    Returns:
        違反の並び(空なら合格)。規則 id は ``N1``-``N7``。
    """
    v: list[Violation] = []
    # 入力側も NFKC へ寄せる(生成文は ``normalize_generated`` で NFKC 済み。POI 名に全角
    # 数字・全角英字が入っていると、正規化の差だけで偽陽性が出る=第1回生成で 11 件)。
    allowed = unicodedata.normalize("NFKC", str(allowed))
    allowed_folded = _fold_latin(allowed)
    ok_digits = _digit_runs(allowed)

    for m in _LATIN_RUN.finditer(text):  # N1 ラテン(語単位・アクセント/空白/大小を無視)
        s = m.group(0).strip(".-'’")
        if len(s) < 2:
            continue
        if _fold_latin(s) not in allowed_folded:
            v.append(Violation("N1_latin", s))
    for m in _KATAKANA_RUN.finditer(text):  # N2 カタカナ
        s = m.group(0)
        if s in GENERIC_KATAKANA or s in allowed:
            continue
        # 複合語(「ドリンクメニュー」=一般語×2)は分解して残りだけを見る
        rest = _residual(s, allowed, GENERIC_KATAKANA)
        if re.search(r"[ァ-ヶーヴ]{2,}", rest):
            v.append(Violation("N2_katakana", s))
    for m in _PLACE_RUN.finditer(text):  # N3 地物接尾辞
        s = m.group(0)
        if s in GENERIC_PLACE or s in allowed:
            continue
        # 入力の名称に空白や括弧書きが挟まる形(「KOMEHYO (コメ兵) 買取センター渋谷」に対し
        # 「KOMEHYO買取センター」)を捏造扱いしない=文字単位で入力由来の部分を消す。
        rest = _residual(s, allowed, GENERIC_PLACE)
        # 残りが 1 文字でも、それが**接尾辞そのもの**なら固有名詞の付与とみなす
        # (「渋谷駅」で「渋谷」が入力にあるとき残る「駅」= 駅の存在を足している)。
        if len(rest) >= 2 or rest in _SINGLE_CHAR_SUFFIXES:
            v.append(Violation("N3_place_suffix", s))
    for s in sorted(set(_DIGIT_RUN.findall(text))):  # N4 数字
        if s not in ok_digits:
            v.append(Violation("N4_digit", s))
    for s in KNOWN_PROPER:  # N5 既知の固有名詞
        if s in text and s not in allowed:
            v.append(Violation("N5_known_proper", s))
    for m in _KANSUJI_COUNTER.finditer(text):  # N6 漢数字+助数詞
        v.append(Violation("N6_kansuji", m.group(0)))
    if kanji_strict:
        for m in _KANJI_RUN.finditer(text):  # N7 漢字列 3 文字以上(W14 のみ)
            s = m.group(0)
            if s in GENERIC_KANJI or s in allowed:
                continue
            # 複合語(「終日営業」=一般語×2)は分解して残りだけを見る
            rest = _residual(s, allowed, GENERIC_KANJI)
            # 曜日名・曜日の略記は N7 ではなく A1(⑥ 省略記法)の担当
            rest = _WEEKDAY_BARE_RUN.sub("", _strip_weekday_names(rest))
            if re.search(r"[一-龥々]{2,}", rest):
                v.append(Violation("N7_kanji", s))
    # 同じ指摘を重複させない(規則 id, 文字列)で去重・順序は決定論
    seen: set[tuple[str, str]] = set()
    out: list[Violation] = []
    for x in v:
        key = (x.rule, x.found)
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


def check_banned_words(text: str) -> list[Violation]:
    """評価語・誘導表現・命令文の検査(広告答申 §4・憲法6)。"""
    v = [Violation("E1_evaluative", w) for w in BANNED_EVALUATIVE if w in text]
    v += [Violation("E2_inducement", w) for w in BANNED_INDUCEMENT if w in text]
    if strip_imperatives(text).kept != text:
        v.append(Violation("E3_imperative", text))
    return v


def check_individual_words(text: str, allowed: str = "") -> list[Violation]:
    """§2.4 ⑧ 個体依存語の検査(B2 はセル共有ブロック=個体語を置けない)。

    I1(一人称・二人称の語)は **``allowed`` に現れる語を先に取り除いた残り**に掛ける
    (``check_abbreviation`` と同じ扱い)。POI 名の「**私**立青山学院中等部」「陳家**私**菜」で
    「私」が当たる偽陽性が第3回で 10 件出た(W14 7・W15 3・**すべて入力由来**)ため
    (親承認 2026-09-09)。人称としての「私は…」は入力に無いので残る。

    I2(``normalize.assert_no_agent_dependent_words``: 人ID・所持金・内受容)は
    **本文そのもの**に掛ける(P-12 のような ID が POI 名に入ることは想定しない)。
    """
    body = _strip_known(text, unicodedata.normalize("NFKC", str(allowed))) if allowed else text
    v = [Violation("I1_individual", w) for w in INDIVIDUAL_WORDS if w in body]
    try:
        N.assert_no_agent_dependent_words(text, where="W14/W15 凍結文")
    except N.AgentDependentWordError as exc:
        v.append(Violation("I2_agent_dependent", str(exc)))
    return v


def check_abbreviation(text: str, allowed: str) -> list[Violation]:
    """§2.4 ⑥ 省略記法の検査。

    入力由来の固有名詞に「〜等」が含まれることがある(OSM 名称)ので、**入力文字列を
    先に取り除いた残り**にだけ規約⑥を掛ける(``renderer`` が B2 を規約⑥の対象外に
    している理由と同じ・登録簿)。

    **曜日の略記**(「月金」=「月曜から金曜」の略)もここで見る(親指示 2026-09-09:
    N7 漢字列ではなく ⑥ の担当)。判定は「**完全な曜日名を落としたあとに残る、曜日字の
    2 文字以上の連なり**」。したがって

    - 「月金」「土日」→ 略記(入力にその表現が在れば通す)
    - 「土曜日曜」「土曜日曜日」「火曜金曜」→ **略記ではない**(曜日名を並べただけ。
      第2回生成で 56 件出た形で、入力の「土日は…」をモデルが展開したもの)
    """
    allowed = unicodedata.normalize("NFKC", str(allowed))
    rest = _strip_known(text, allowed)
    out: list[Violation] = []
    try:
        N.assert_no_abbreviation(rest, "W14/W15 凍結文")
    except ValueError as exc:
        out.append(Violation("A1_abbreviation", str(exc)))
    for m in _WEEKDAY_BARE_RUN.finditer(_strip_weekday_names(text)):
        s = m.group(0)
        if s not in allowed:
            out.append(Violation("A1_weekday_abbr", s))
    return out


def _allowed_words(allowed: str) -> list[str]:
    """``allowed``(入力本文)を区切り文字で割って 2 文字以上の語を長い順に返す。"""
    return sorted(
        {s for s in re.split(r"[\s、。:,()（）\[\]「」/]+", allowed) if len(s) >= 2},
        key=len,
        reverse=True,
    )


#: ``_residual`` が文字単位の走査を掛ける候補長の上限(超えたら語単位だけで落とす)。
_RESIDUAL_MAX_LEN: Final[int] = 24


def _residual(token: str, allowed: str, generic: Iterable[str]) -> str:
    """``token`` から「一般語」と「入力に現れる部分文字列」を取り除いた残り。

    複合語(「終日営業」=一般語×2・「ドリンクメニュー」)を 1 語として弾かないための分解。
    残りに 2 文字以上のまとまりが出たときだけ捏造とみなす。

    入力側の照合は**語単位ではなく文字単位**(長い部分文字列から貪欲に消す)。語単位だと
    「営業時間: 月曜から日曜は6時から17時」のような 1 トークンの中の「日曜」が拾えず、
    生成文の「分日曜」が偽陽性になる(第1回生成で観測)。
    """
    out = token
    for s in sorted((g for g in generic if len(g) >= 2), key=len, reverse=True):
        out = out.replace(s, "")
    if len(out) > _RESIDUAL_MAX_LEN:
        for s in _allowed_words(allowed):
            out = out.replace(s, "")
        return out
    changed = True
    while changed and len(out) >= 2:
        changed = False
        for n in range(len(out), 1, -1):
            for i in range(0, len(out) - n + 1):
                sub = out[i: i + n]
                if sub in allowed:
                    out = out[:i] + out[i + n:]
                    changed = True
                    break
            if changed:
                break
    return out


def _strip_known(text: str, allowed: str) -> str:
    """``allowed`` に現れる 2 文字以上の語(長い順)を ``text`` から取り除く。

    **省略記法の語そのもの**(``normalize.ABBREVIATIONS``)は除去しない。プロンプトに
    「「など」を使わない」という禁止文を書くと、その「など」が ``allowed`` の語として
    拾われ、規約⑥ の検査が素通りしてしまうため(2026-09-09 に実際に踏んだ)。
    """
    out = text
    for s in _allowed_words(allowed):
        if s in N.ABBREVIATIONS:
            continue
        out = out.replace(s, "")
    return out


# --------------------------------------------------------------- 1 件の判定
@dataclass(frozen=True)
class Verdict:
    """1 プロンプトぶんの判定。"""

    id: str
    ok: bool
    text: str
    reasons: tuple[str, ...] = ()
    violations: tuple[Violation, ...] = ()
    tokens: int = 0
    chars: int = 0
    raw_reps_match: bool | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ok": self.ok,
            "reasons": list(self.reasons),
            "violations": [x.to_json() for x in self.violations],
            "tokens": self.tokens,
            "chars": self.chars,
            "raw_reps_match": self.raw_reps_match,
        }


def verify_one(
    prompt_id: str,
    reps: Sequence[str],
    allowed: str,
    *,
    token_cap: int,
    kanji_strict: bool,
    repeat: int = REPEAT,
    strip_trailing_kuten: bool = False,
) -> Verdict:
    """1 プロンプトぶんの応答を検証して凍結可否を決める。

    ゲート(この順に評価し、全部の理由を集めてから判定する):
      ``missing`` 応答が足りない / ``rep_mismatch`` rep 間で生バイトが違う(温度0 なのに
      揺れた) / ``multiline``・``empty`` 正規化で落ちた / ``normalize_mismatch``
      正規化が冪等でない / ``too_long`` チャネル枠超過 / 固有名詞・数字・禁止語・個体語。
    """
    reasons: list[str] = []
    violations: list[Violation] = []

    if len(reps) < repeat or any(r is None for r in reps):
        return Verdict(prompt_id, False, "", ("missing",), (), 0, 0, None)

    raw_match = all(r == reps[0] for r in reps)
    if not raw_match:
        reasons.append("rep_mismatch")

    text, why = normalize_generated(reps[0])
    if why:
        return Verdict(prompt_id, False, "", tuple([*reasons, why]), (), 0, 0, raw_match)
    if strip_trailing_kuten:
        # テンプレ側が句点を持つ枠(``B2.visible``)へ入れるので末尾の「。」を落とす。
        text = text.rstrip("。").strip()
        if not text:
            return Verdict(prompt_id, False, "", tuple([*reasons, "empty"]), (), 0, 0, raw_match)
    # 正規化の冪等性(凍結するのは「通したもの」=もう一度通しても動かない)
    again, why2 = normalize_generated(text)
    if why2 or again != text:
        reasons.append("normalize_mismatch")

    tokens = estimate_tokens(text)
    if tokens > token_cap:
        reasons.append("too_long")

    violations += scan_proper_nouns(text, allowed, kanji_strict=kanji_strict)
    violations += check_banned_words(text)
    violations += check_individual_words(text, allowed)
    violations += check_abbreviation(text, allowed)
    if violations:
        reasons += sorted({x.rule for x in violations})

    ok = not reasons
    return Verdict(
        id=prompt_id,
        ok=ok,
        text=text if ok else "",
        reasons=tuple(reasons),
        violations=tuple(violations),
        tokens=tokens,
        chars=len(text),
        raw_reps_match=raw_match,
    )


# --------------------------------------------------------------- 取り込みの集計
@dataclass
class IngestReport:
    """応答取り込みの結果(ゲート json の中身)。"""

    n_prompts: int
    verdicts: list[Verdict] = field(default_factory=list)
    responses_sha256: str = ""
    responses_path: str = ""

    @property
    def frozen(self) -> list[Verdict]:
        return [v for v in self.verdicts if v.ok]

    @property
    def rejected(self) -> list[Verdict]:
        return [v for v in self.verdicts if not v.ok]

    @property
    def fail_rate(self) -> float:
        return len(self.rejected) / self.n_prompts if self.n_prompts else 0.0

    @property
    def rep_match_rate(self) -> float:
        """**全応答**の rep 間バイト一致率(**報告値**)。"""
        got = [v.raw_reps_match for v in self.verdicts if v.raw_reps_match is not None]
        return sum(1 for x in got if x) / len(got) if got else 0.0

    @property
    def rep_mismatch_count(self) -> int:
        """rep 間でバイトが違った応答の件数(**報告値**・全て不合格になっている)。"""
        return sum(1 for v in self.verdicts if v.raw_reps_match is False)

    @property
    def frozen_rep_match_rate(self) -> float:
        """**凍結した行**の rep 間バイト一致率(**合否**・構造上 1.0 になる pin)。"""
        frozen = self.frozen
        if not frozen:
            return 1.0
        return sum(1 for v in frozen if v.raw_reps_match) / len(frozen)

    def violation_count(self, prefix: str, frozen_only: bool = False) -> int:
        """規則 id が ``prefix`` で始まる指摘の件数。"""
        rows = self.frozen if frozen_only else self.verdicts
        return sum(1 for v in rows for x in v.violations if x.rule.startswith(prefix))

    def reason_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for v in self.rejected:
            for r in v.reasons:
                counts[r] = counts.get(r, 0) + 1
        return dict(sorted(counts.items()))

    def to_json(self) -> dict[str, Any]:
        frozen = self.frozen
        toks = [v.tokens for v in frozen]
        return {
            "n_prompts": self.n_prompts,
            "n_frozen": len(frozen),
            "n_rejected": len(self.rejected),
            "fail_rate": round(self.fail_rate, 6),
            "rep_byte_match_rate": round(self.rep_match_rate, 6),
            "rep_mismatch_count": self.rep_mismatch_count,
            "rep_mismatch_ids": [
                v.id for v in self.verdicts if v.raw_reps_match is False
            ][:50],
            "frozen_rep_byte_match_rate": round(self.frozen_rep_match_rate, 6),
            "individual_word_violations_all": self.violation_count("I"),
            "individual_word_violations_frozen": self.violation_count("I", frozen_only=True),
            "reasons": self.reason_counts(),
            "tokens_max": max(toks) if toks else 0,
            "tokens_mean": round(sum(toks) / len(toks), 3) if toks else 0.0,
            "chars_max": max((v.chars for v in frozen), default=0),
            "responses_sha256": self.responses_sha256,
            "responses_path": self.responses_path,
            "rejected_sample": [v.to_json() for v in self.rejected[:20]],
        }


def gate_rows(report: IngestReport, max_fail_rate: float) -> list[C.Gate]:
    """取り込み結果 → 段階ゲート行。

    **ゲートの母集団は「凍結した行」**(親決定 2026-09-09)。不合格になった応答の欠陥は
    ``fail_rate_within_threshold`` が一括で見るので、**個別の欠陥ゲートで二重に数えない**
    (第3回の W15 は fail_rate 0.0154 で合格しながら、rep 不一致 2 件・個体語 3 件だけで
    段階が落ちていた。どの行も凍結されておらず、レンダラは合成文へフォールバックする)。

    ``frozen_rep_byte_match_rate`` は **pin(構造的な不変条件の釘付け)**であって実測ではない:
    ``verify_one`` が rep 不一致を ``rep_mismatch`` で不合格にする以上、凍結行の一致率は
    必ず 1.0 になる。将来 ``verify_one`` を緩めたらここで落ちる、という保険。**実測の情報は
    ``rep_byte_match_rate_all`` / ``rep_mismatch_count``**(いずれも報告のみ)。
    """
    return [
        C.Gate("responses_present", True, True),
        # 合否(pin): 凍結した行は必ず rep 一致
        C.Gate("frozen_rep_byte_match_rate", round(report.frozen_rep_match_rate, 6), 1.0),
        # 報告のみ: 全応答での実測(温度0+構造化出力でも揺れることがある)
        C.Gate("rep_byte_match_rate_all", round(report.rep_match_rate, 6)),
        C.Gate("rep_mismatch_count", report.rep_mismatch_count),
        C.Gate(
            "fail_rate_within_threshold",
            round(report.fail_rate, 6),
            f"<= {max_fail_rate}",
            passed=report.fail_rate <= max_fail_rate,
        ),
        C.Gate("n_frozen", len(report.frozen)),
        C.Gate("n_rejected", len(report.rejected)),
    ]


def iter_chunks(items: Iterable[Any], size: int) -> Iterable[list[Any]]:
    """(補助)決定論的なチャンク分け。"""
    buf: list[Any] = []
    for x in items:
        buf.append(x)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf
