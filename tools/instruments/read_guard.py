# -*- coding: utf-8 -*-
"""read_guard — 計器の読み口を**許可の一覧(allow list)**で縛る(第 2 期 2-0・較正側の錨の計器)。

なぜ要るか
    2-0 の計器は「較正側の錨だけで測る」(計画 2-0・回答 10-13b §1 1-8)。検証側(holdout・PT の検証側・
    第 30 表由来の錨)と区分が未決の層(〔灰〕)は **1 バイトも読まない**(R-115 §2 の印・パターン台帳 §10)。
    道具の中で読むファイルを役割(role)ごとに名指しで許し、一覧の外は開く前に落とす。

二重の守り
    1. **読み口の検査**(``ReadGuard.check``): 計器が開くファイルはすべて ``ReadGuard`` の読み口
       (``read_bytes``・``read_json``・``read_parquet``・``np_load``)を通す。道筋に封印の語があれば
       ``SealedPathError``、許可の一覧に無ければ ``NotAllowedError``。どちらも**開く前**に落ちる。
    2. **open の監査フック**(``ReadGuard.active``・``sys.addaudithook``): 守りの間に Python の ``open`` が
       (読み口を通らずに)封印の語のある道筋を開こうとしたら落とす。守る根(``data/``・``docs/``・世界資産の
       置き場)の下は、許可の一覧に無ければ落とす。import の .pyc などは根の外なので触らない。

監査に出ない抜け道(宣言・検収 L7)
    Python の ``open`` の監査イベントを通らない読みは、2 の監査フックでは止まらない。次の 5 つである。
    - **pyarrow**(``parquet.read_table``・``pyarrow.fs``。C++ の読み)。計器は parquet を 1 の読み口
      (``read_parquet``=開く前の検査)だけで縛る。md5 を取るときの Python の open は 2 にも出る。
    - **sqlite3**(C の読み)。計器は使わない。
    - **subprocess**(外のコマンドが読む)。計器は ``record``/``run`` の段の git と子プロセスだけで使う。
    - **os.listdir・os.scandir**(名だけを読む)。計器はプールの part の名の一覧にだけ使う。
    - **hard link**(一覧にある名で、実体が別のファイル)。名と実体の道筋(junction・symlink)は照らすが、
      hard link の実体は見分けられない。

モードは 2 つ
    - ``ReadGuard.sealed_only()``: 封印の層(``SEALED_TOKENS``)だけを落とす。エンジンのラン(記録を取る段)を
      包むのに使う(エンジンは世界資産と自分の錨を読む=計器の許可の一覧では縛らない)。``track_roots`` を
      渡すと、その下で Python の ``open`` が開いた道筋を控える(検収 M1=ランの段でエンジンが開いたファイルの一覧)。
    - ``ReadGuard(files=…, dirs=…, protect=…)``: 計器の段。``GAUGE_DENY_TOKENS``(封印+検証側+〔灰〕)と
      許可の一覧の両方で縛る。

語の照らし方(検収 L8): まず生の道筋の文字列(渡した形・絶対の形)で照らし、当たればファイルシステムに触らずに
落とす。当たらないときだけ実体の道筋(``realpath``=junction・symlink・8.3 の短い名を解く)を取って照らす。

監査フックは一度入れたら外せない(Python の仕様)ので、フックは ``_ACTIVE`` が空なら何もしない。
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

#: 封印した層と現実の生の取得(値も列名も読まない)。パターン台帳 §10-1・W19 ``HOLDOUT_LAYERS``・指示 2-0。
SEALED_TOKENS: tuple[str, ...] = (
    "kddi",               # kddi_la と KDDI の比較記録(開封済みの holdout の比較も読まない)
    "jinryu",             # shibuya_jinryu・shibuya_jinryu_k5・data/jinryu
    "boundary_counts",    # 封印 boundary_counts.json
    "realworld_live",     # data/realworld_live/(現実の生の取得)
    "/holdout/",          # docs/bench/c7/holdout/ ほか holdout の照合の記録
    "holdout_compare",
    "calib/pt2018",       # PT 2018 の c-2(0240〜0243 の集中量=検証側)・b-4(検証側)・c-3・c-4(〔灰〕)
    "pt6_c-2", "pt6_b-4", "pt6_c-3", "pt6_c-4",
)
#: 計器の段で足して落とす語(検証側〔検〕と区分が未決〔灰〕のファイル・R-115 §2)。
GAUGE_EXTRA_DENY_TOKENS: tuple[str, ...] = (
    "diversity_anchors",          # 第 30 表由来の錨(tokyo_weekday_depart_* ほか)=〔検〕
    "presence_anchors",           # pt_area_daytime_peak(〔灰〕)と wake_rate(第 4-1 表=〔検〕)が混ざる(2-4 V6 で分けた前の 1 本)
    "presence_validation_anchors",  # 〔2-4 V6〕分けた検証側(PT 由来〔灰〕・第 4-1 表〔検〕ほか)。較正側 presence_calib_anchors は読める
    "hunger_energy_anchors",      # 第 4-1・7-1・18-1 表の検証の行が混ざる(K6 (i))(2-4 V6 で分けた前の 1 本)
    "hunger_energy_validation_anchors",  # 〔2-4 V6〕分けた検証側(第 10・18-1 表・15 分の食事率)。構築側 hunger_energy_build_anchors は読める
    "calib/hunger",               # 同上の原表
    "000032224420",               # 第 30 表(東京都)=影の段の比較(〔検〕)
    "research_cache/r99",         # 第 14・15 表(使っていない表=〔検〕)
    "line_capacity_12",           # 〔灰〕(boundary_counts と同じ元・R-115 §5 空欄 1)
    "transfer_12",                # 〔灰〕(peak_hourly と gate の行)
    "station_od13_13",            # 〔灰〕
    "station_flow_12",            # 定期・普通の内訳が〔灰〕(計器は W12 の出力から線の割合を読む)
)
GAUGE_DENY_TOKENS: tuple[str, ...] = SEALED_TOKENS + GAUGE_EXTRA_DENY_TOKENS

#: 記録の段が書くランの記録(体の journal)の名の形。どこに置いてもよい(作業用の場所)が、名はこの形に限る。
JOURNAL_PREFIX = "anchor_journal_"
JOURNAL_SUFFIX = ".npz"


class SealedPathError(PermissionError):
    """封印・検証側・〔灰〕の語を含む道筋を開こうとした(開く前に落とす)。"""


class NotAllowedError(PermissionError):
    """許可の一覧に無い道筋を開こうとした(開く前に落とす)。"""


def _abs(p: Any) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(p))).replace("\\", "/")


def _real(p: Any) -> str:
    try:
        return os.path.normcase(os.path.realpath(os.fspath(p))).replace("\\", "/")
    except (OSError, ValueError):  # pragma: no cover - 壊れた道筋
        return _abs(p)


def _under(path: str, root: str) -> bool:
    root = root.rstrip("/")
    return path == root or path.startswith(root + "/")


def _hit(forms: Sequence[str], tokens: Sequence[str]) -> str | None:
    for tok in tokens:
        t = tok.lower()
        if any(t in f for f in forms):
            return tok
    return None


def deny_hit(path: Any, tokens: Sequence[str] = GAUGE_DENY_TOKENS) -> str | None:
    """道筋に落とす語があれば、その語を返す(無ければ None)。

    検収 L8: まず生の文字列(渡した形・絶対の形)だけで照らす。当たればファイルシステムに触らない
    (``realpath`` は属性を読むために handle を開くことがある)。当たらないときだけ実体の形を取って照らす。
    """
    raw = (os.fspath(path).replace("\\", "/").lower(), _abs(path).lower())
    hit = _hit(raw, tokens)
    if hit:
        return hit
    return _hit((_real(path).lower(),), tokens)


@dataclass
class ReadGuard:
    """許可の一覧(役割 → ファイル / 役割 → ディレクトリ)と守る根。

    Attributes:
        files: 役割 → 許すファイル(そのもの)。
        dirs: 役割 → 許すディレクトリ(その下のファイルは全部)。
        protect: 守る根。監査フックは、この下を一覧の外で開こうとしたら落とす。
        tokens: 落とす語(既定=計器の段の全部)。
        allow_journals: ``anchor_journal_*.npz`` の名の記録を許すか。
        track_roots: 監査フックが開いた道筋を控える根(検収 M1・ランの段)。空なら控えない。
        log: 読み口を通って読んだファイル(役割・相対の道筋・バイト数・md5)。
        opened: ``track_roots`` の下で Python の ``open`` が開いた道筋(相対・重複なし・開いた順)。
    """

    files: dict[str, Path] = field(default_factory=dict)
    dirs: dict[str, Path] = field(default_factory=dict)
    protect: list[Path] = field(default_factory=list)
    tokens: tuple[str, ...] = GAUGE_DENY_TOKENS
    allow_journals: bool = True
    repo_root: Path | None = None
    track_roots: list[Path] = field(default_factory=list)
    log: list[dict[str, Any]] = field(default_factory=list)
    opened: list[str] = field(default_factory=list)
    _seen: set[str] = field(default_factory=set, repr=False)

    def __post_init__(self) -> None:
        # 一覧そのものに封印の語があれば、組んだ時点で落とす(負の対照: kddi_la の道筋を渡す)
        for role, p in list(self.files.items()) + list(self.dirs.items()):
            hit = deny_hit(p, self.tokens)
            if hit:
                raise SealedPathError(f"許可の一覧に封印・検証側・〔灰〕の道筋がある(役割 {role}・語 {hit!r})")
        self.files = {r: Path(p) for r, p in self.files.items()}
        self.dirs = {r: Path(p) for r, p in self.dirs.items()}

    # ------------------------------------------------------------------ 組み立て
    @classmethod
    def sealed_only(cls, *, track_roots: Sequence[Path] = (), repo_root: Path | None = None) -> "ReadGuard":
        """封印の層だけを落とす守り(エンジンのランを包む)。``track_roots`` の下で開いた道筋を控える。"""
        return cls(files={}, dirs={}, protect=[], tokens=SEALED_TOKENS, allow_journals=True,
                   repo_root=repo_root, track_roots=list(track_roots))

    # ------------------------------------------------------------------ 判定
    def role_of(self, path: Any) -> str | None:
        a, r = _abs(path), _real(path)
        for role, p in self.files.items():
            if a in (_abs(p), _real(p)) or r in (_abs(p), _real(p)):
                return role
        for role, d in self.dirs.items():
            for root in (_abs(d), _real(d)):
                if _under(a, root) or _under(r, root):
                    return role
        name = os.path.basename(a)
        if self.allow_journals and name.startswith(JOURNAL_PREFIX) and name.endswith(JOURNAL_SUFFIX):
            return "journal"
        return None

    def check(self, path: Any) -> str:
        """開く前の検査。役割を返す(封印の語 → ``SealedPathError``・一覧の外 → ``NotAllowedError``)。"""
        hit = deny_hit(path, self.tokens)
        if hit:
            raise SealedPathError(f"封印・検証側・〔灰〕の語 {hit!r} を含む道筋は開かない: {self._raw_name(path)}")
        role = self.role_of(path)
        if role is None:
            raise NotAllowedError(f"許可の一覧に無い道筋は開かない: {self.rel(path)}")
        return role

    def _protected(self, path: Any) -> bool:
        a, r = _abs(path), _real(path)
        for root in self.protect:
            for rr in (_abs(root), _real(root)):
                if _under(a, rr) or _under(r, rr):
                    return True
        return False

    def audit(self, path: Any) -> None:
        """監査フックの判定(封印の語はどこでも落とす・守る根の下は一覧の中だけ・控えの根の下は道筋を控える)。"""
        hit = deny_hit(path, self.tokens)
        if hit:
            raise SealedPathError(f"[監査] 封印・検証側・〔灰〕の語 {hit!r} を含む道筋を開こうとした: "
                                  f"{self._raw_name(path)}")
        if self.protect and self._protected(path) and self.role_of(path) is None:
            raise NotAllowedError(f"[監査] 守る根の下で許可の一覧に無い道筋を開こうとした: {self.rel(path)}")
        if self.track_roots:
            self._track(path)

    def _track(self, path: Any) -> None:
        name = os.fspath(path)
        if name.endswith((".py", ".pyc", ".pyd", ".dll")):
            return  # import(コード)は控えない
        a, r = _abs(path), _real(path)
        for root in self.track_roots:
            if any(_under(x, y) for x in (a, r) for y in (_abs(root), _real(root))):
                rel = self.rel(path)
                if rel not in self.opened:
                    self.opened.append(rel)
                return

    @staticmethod
    def _raw_name(path: Any) -> str:
        """落とすときの文言に使う名(実体の道筋は取らない=ファイルシステムに触らない)。"""
        return os.path.basename(os.fspath(path).replace("\\", "/"))

    # ------------------------------------------------------------------ 読み口
    def rel(self, path: Any) -> str:
        """記録に書く道筋(リポの中は相対・data は junction の先でも ``data/…``・外は名だけ)。"""
        a = _abs(path)
        raw_a = os.path.abspath(os.fspath(path)).replace("\\", "/")  # 大文字小文字はそのまま(normcase は判定だけ)
        if self.repo_root is not None:
            repo = _abs(self.repo_root)
            if _under(a, repo):
                return raw_a[len(repo) + 1:]
            data_real = _real(Path(self.repo_root) / "data")
            r = _real(path)
            if _under(r, data_real):
                raw_r = os.path.realpath(os.fspath(path)).replace("\\", "/")
                return "data/" + raw_r[len(data_real) + 1:]
        return os.path.basename(raw_a)

    def _note(self, role: str, path: Any, data: bytes | None = None) -> None:
        key = _abs(path)
        if key in self._seen:
            return
        self._seen.add(key)
        if data is None:
            h = hashlib.md5()
            with open(os.fspath(path), "rb") as fh:  # 許可済みの道筋だけ(check の後)
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            md5, size = h.hexdigest(), os.path.getsize(os.fspath(path))
        else:
            md5, size = hashlib.md5(data).hexdigest(), len(data)
        self.log.append({"role": role, "path": self.rel(path), "bytes": int(size), "md5": md5})

    def annotate(self, path: Any, **fields: Any) -> None:
        """読み口の記録の行に欄を足す(例: journal の配列だけの hash=検収 L10)。"""
        key = self.rel(path)
        for row in self.log:
            if row["path"] == key:
                row.update(fields)

    def read_bytes(self, path: Any) -> bytes:
        role = self.check(path)
        data = Path(path).read_bytes()
        self._note(role, path, data)
        return data

    def read_json(self, path: Any) -> Any:
        return json.loads(self.read_bytes(path).decode("utf-8"))

    def read_parquet(self, path: Any, columns: Sequence[str] | None = None) -> dict[str, Any]:
        """parquet の列(numpy 配列の辞書)。pyarrow の読みは監査に出ない=ここの検査だけで縛る。"""
        import numpy as np
        import pyarrow.parquet as pq

        role = self.check(path)
        t = pq.read_table(os.fspath(path), columns=list(columns) if columns is not None else None)
        self._note(role, path)
        return {n: np.asarray(t.column(n).to_numpy(zero_copy_only=False)) for n in t.column_names}

    def np_load(self, path: Any) -> dict[str, Any]:
        import numpy as np

        role = self.check(path)
        with np.load(os.fspath(path), allow_pickle=False) as z:
            out = {k: np.asarray(z[k]) for k in z.files}
        self._note(role, path)
        return out

    def note_dir_files(self, role: str, paths: Sequence[Any]) -> None:
        """読み口の外(``pool_facts.read_facts`` など)で読んだ許可済みのファイルを記録に足す。"""
        for p in paths:
            got = self.check(p)
            if got != role:
                raise NotAllowedError(f"役割が違う({got} ≠ {role}): {self.rel(p)}")
            self._note(role, p)

    # ------------------------------------------------------------------ 監査フック
    @contextlib.contextmanager
    def active(self) -> Iterator["ReadGuard"]:
        """この守りを監査フックに載せる(入れ子は内側が優先)。"""
        _install_hook()
        _ACTIVE.append(self)
        try:
            yield self
        finally:
            _ACTIVE.remove(self)


_ACTIVE: list[ReadGuard] = []
_HOOK_INSTALLED = False


def _hook(event: str, args: tuple[Any, ...]) -> None:
    if event != "open" or not _ACTIVE:
        return
    path = args[0] if args else None
    if not isinstance(path, (str, bytes, os.PathLike)):
        return  # fd(int)など
    if isinstance(path, bytes):
        try:
            path = path.decode(sys.getfilesystemencoding())
        except UnicodeDecodeError:  # pragma: no cover
            return
    _ACTIVE[-1].audit(path)


def _install_hook() -> None:
    global _HOOK_INSTALLED
    if not _HOOK_INSTALLED:
        sys.addaudithook(_hook)
        _HOOK_INSTALLED = True


def files_listing(guard: ReadGuard) -> list[dict[str, Any]]:
    """読んだファイルの一覧(役割と道筋で並べた写し)。"""
    return sorted((dict(r) for r in guard.log), key=lambda r: (r["role"], r["path"]))


def roles_table(guard: ReadGuard) -> Mapping[str, str]:
    """許可の一覧(役割 → 相対の道筋)。記録に載せる。"""
    out = {r: guard.rel(p) for r, p in guard.files.items()}
    out.update({r: guard.rel(p) + "/" for r, p in guard.dirs.items()})
    if guard.allow_journals:
        out["journal"] = f"{JOURNAL_PREFIX}*{JOURNAL_SUFFIX}(記録の段の出力)"
    return out
