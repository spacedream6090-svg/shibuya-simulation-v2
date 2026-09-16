# -*- coding: utf-8 -*-
"""_style.py — 図の共通設定(書体・配色・保存・サイドカー)。

配色の出どころ
    Claude Code スキル ``dataviz`` の ``references/palette.md``(light モード)。
    本ファイルは**その値をそのまま写した**だけで、独自の色は作らない。使った組み合わせは
    同スキルの ``scripts/validate_palette.py`` で検査済み(結果は
    ``docs/bench/figures/README.md`` の「配色の検査」節)。

書体
    日本語が出る書体を候補順に探す(Yu Gothic → Meiryo → MS Gothic → Noto Sans CJK JP →
    IPAexGothic)。**1 つも無ければ警告を出して英語ラベルに落とす**(``JA_OK=False``)。
    ラベルは全て ``T(日本語, English)`` を通すので、書体が無い環境でも図は壊れない。

出力の規律
    - PNG(dpi 150)+ SVG + サイドカー JSON の 3 点。
    - PNG/SVG のメタデータから生成時刻とソフト名を**消す**(同じ入力なら同じバイト列)。
    - JSON に書くパスは ``rel()`` を通す = リポジトリ相対のみ(絶対パス・個人名を出さない)。
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")  # 画面の無い環境で確実に描く(import より前に決める)

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

#: リポジトリの根(``tools/fig/_style.py`` から 2 つ上)。
REPO_ROOT = Path(__file__).resolve().parents[2]

#: 保存解像度。
DPI = 150

#: SVG の内部 id(clip-path 等)を決めるための固定塩。既定は**セッションごとに乱数**なので、
#: 同じ図を作り直すと SVG のバイト列だけが変わってしまう。固定して差分をゼロにする。
SVG_HASHSALT = "shibuya-simulation-v2/tools/fig"

# ---------------------------------------------------------------- 配色(dataviz/references/palette.md)

#: 図の地(light chart surface)。
SURFACE = "#fcfcfb"
#: 主インク。
INK = "#0b0b0b"
#: 副インク(注記)。
INK2 = "#52514e"
#: 目盛り・軸ラベル。
MUTED = "#898781"
#: 罫線(実線のヘアライン・破線にしない)。
GRID = "#e1e0d9"
#: 軸線。
AXIS = "#c3c2b7"

#: カテゴリ配色の**固定順**(1..8)。循環させない・9 本目は作らない。
CAT: tuple[str, ...] = (
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
)

#: 順序尺度の青ランプ 3 段(step 250/450/700)。light では 250 より明るくしない規則。
ORDINAL_BLUE3: tuple[str, ...] = ("#86b6ef", "#2a78d6", "#0d366b")

#: 現実側アンカーの色(= カテゴリ slot 2。青=シミュレーション / 橙=現実 の 2 語で通す)。
ANCHOR = CAT[1]

# ---------------------------------------------------------------- 書体

#: 日本語書体の候補(順に探す)。
JA_FONT_CANDIDATES: tuple[str, ...] = (
    "Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP", "IPAexGothic",
)


def pick_ja_font(candidates: Sequence[str] = JA_FONT_CANDIDATES) -> str | None:
    """候補順に**実在する**書体名を返す。1 つも無ければ ``None``。"""
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in installed:
            return name
    return None


#: 選ばれた日本語書体(無ければ None)。
JA_FONT: str | None = pick_ja_font()
#: 日本語ラベルを出してよいか。
JA_OK: bool = JA_FONT is not None

if not JA_OK:  # pragma: no cover - 書体のある環境では通らない
    warnings.warn(
        "日本語書体が見つからない(候補: " + " / ".join(JA_FONT_CANDIDATES) + ")。"
        "図のラベルは英語に落とす。",
        RuntimeWarning,
        stacklevel=2,
    )


def T(ja: str, en: str) -> str:
    """ラベル 1 つ。日本語書体があれば ``ja``・無ければ ``en``。"""
    return ja if JA_OK else en


def use_style() -> None:
    """rcParams を図の共通設定にする(**呼ぶたびに同じ状態**になる)。"""
    plt.rcdefaults()
    family = [JA_FONT] if JA_OK else []
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": family + ["DejaVu Sans"],
        "axes.unicode_minus": False,          # 和文書体にマイナス記号が無いことがある
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "figure.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "axes.labelcolor": INK2,
        "axes.titlecolor": INK,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linestyle": "-",                # 破線の罫線は使わない
        "grid.linewidth": 0.7,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "legend.frameon": False,
        "legend.fontsize": 9,
        "legend.labelcolor": INK2,
        "lines.linewidth": 2.0,               # 細い線(太い塗りは使わない)
        "lines.markersize": 4.5,
        "text.color": INK,
        "svg.fonttype": "path",               # 書体の有無に依らず同じ絵になる
        "svg.hashsalt": SVG_HASHSALT,         # clip-path の id を固定(再実行で同じバイト列)
    })


# ---------------------------------------------------------------- 経路とサイドカー


def rel(path: str | Path) -> str:
    """パスを**リポジトリ相対の POSIX 文字列**にする。外にあるときはファイル名だけ。

    出力物に絶対パス(=個人名を含むホームディレクトリ)を書かないための関門。
    """
    p = Path(path).expanduser()
    try:
        p = p.resolve()
    except OSError:  # pragma: no cover - 解決できない経路
        pass
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return p.name


def declutter(values: Sequence[float], min_gap: float,
              lo: float | None = None, hi: float | None = None) -> list[float]:
    """直接ラベルの y 位置を ``min_gap`` 以上離す(順序は保つ)。**純関数**。

    重なったラベルは読めない=「棒や線に数字を貼る」形の前提。値そのものは動かさない
    (動かすのは**ラベルの置き場所**だけ)。
    """
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [float(v) for v in values]
    prev: float | None = None
    for i in order:
        v = out[i]
        if prev is not None and v - prev < min_gap:
            v = prev + min_gap
        out[i] = v
        prev = v
    if hi is not None and out and max(out) > hi:
        shift = max(out) - hi
        out = [v - shift for v in out]
    if lo is not None and out and min(out) < lo:
        shift = lo - min(out)
        out = [v + shift for v in out]
    return out


def save(fig: "matplotlib.figure.Figure", out_dir: str | Path, stem: str) -> dict[str, str]:
    """PNG と SVG を書く。戻りは**相対パス**の辞書。

    生成時刻とソフト名をメタデータから外す(同じ入力 → 同じバイト列にする)。
    """
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    png = d / f"{stem}.png"
    svg = d / f"{stem}.svg"
    fig.savefig(png, dpi=DPI, facecolor=SURFACE, metadata={"Software": None})
    # SVG はバイナリ handle で渡す: テキストモードだと Windows で CRLF になり、git の eol=lf 正規化と
    # 食い違って「再実行でバイト一致」が checkout 後に崩れる(第202・親検収で発見)。
    with open(svg, "wb") as fh:
        fig.savefig(fh, format="svg", facecolor=SURFACE, metadata={"Date": None, "Creator": "tools/fig"})
    return {"png": rel(png), "svg": rel(svg)}


def write_sidecar(out_dir: str | Path, stem: str, payload: Mapping[str, Any]) -> str:
    """数値サイドカー JSON を書く。UTF-8・LF・``ensure_ascii=False``。戻りは相対パス。"""
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{stem}.json"
    text = json.dumps(payload, ensure_ascii=False, indent=1) + "\n"
    p.write_text(text, encoding="utf-8", newline="\n")
    return rel(p)


def note(fig: "matplotlib.figure.Figure", lines: Iterable[str], *, y: float = 0.012) -> None:
    """図の下端に注記を置く(出典・expedient・未使用データの宣言)。"""
    fig.text(0.008, y, "\n".join(lines), ha="left", va="bottom",
             fontsize=7.6, color=INK2, linespacing=1.5)


def thousands(v: float) -> str:
    """3 桁区切り(軸目盛りと直接ラベルで同じ書き方をする)。"""
    return f"{int(round(v)):,}"
