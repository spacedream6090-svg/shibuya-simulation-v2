# -*- coding: utf-8 -*-
"""割る段(段 5a〜)の道具: 割る行(``kind="split"``)を 1 本ずつ当てる(親の裁定 Q10=案 A)。

名の単位の表(``map.toml`` の割る行の ``names``=全ファイルの表 §4 から ``cli.py map`` が作る)に従って、元のファイルの頂上の文を
割り先へ写す。書かない実行(報告と差分)が先にでき、``--apply`` は git の本体の作業木を断る(:mod:`pkgmove.cli`)。

計画の手順(:func:`make_split_plan`)
    1. 順(:data:`pkgmove.table.SPLIT_ORDER`)を確かめる: 木で済んだ割る行が順の頭から並び、当てる行が次の 1 本であること
       (:func:`split_state`)。段を飛ばす・済んだ行を当て直すのは断る。
    2. 元のファイルを頂上の文の「単位」に切る(:func:`units_of`。文の上の注の行と空行は、その文に付けて一緒に写す)。単位は
       docstring・``from __future__``・import・``__all__``・名を結ぶ文(関数・クラス・代入)・ほかの文(assert ほか)。1 行に 2 つ
       の文・頂上の ``if``/``try`` の中で名を結ぶ形・使われる途中の import・星の import は表せない=断る。どの割り先も使わない
       import(途中の再輸出を含む)と、import・``__all__`` の前と中の注は写さず、報告の ``unwritten`` に出す(検収 低-2)。
    3. 単位を割り先へ: 名を結ぶ文は表の割り先へ、ほかの文は読む名の割り先へ(1 つに決まらなければ主な割り先・それでも決まらなければ
       断る)。docstring は主な割り先へ(そのまま)。
    4. 割り先ごとに組み立てる(:func:`compose`): 新しいファイルは docstring(主な割り先は元のまま・2 つ目以降は決まった型)・
       ``from __future__``・その割り先の文が使う名の import(元の import の文の、その割り先が使う名だけ=全部の名を使うなら元の
       字面のまま。相対の import は絶対の形に作り直す)・兄弟の割り先からの import・``__all__``(元の並びで、その割り先に在る名
       だけ)・単位(元の順・元の字面)。元の頂上で結ぶ組み込みの名を覆う名(``def format`` など)も要る名に数える。既に在る割り先
       へは、import を在る import の後ろへ、``__all__`` の名を在る ``__all__`` の後ろへ、単位をファイルの後ろへ足す(在る名と
       同じ名を足す・``from __future__`` が元と食い違うのは断る)。割り先のモジュール自身を指す import は落とし、別名で読む形
       (``V.x``)は宣言した書き換え(``rewrites``・親の裁定 Q6)のときだけ ``x`` に書き換える(宣言の無い自己の別名と、``x`` が
       その場所の局所の名に捕まる形は断る)。
    5. 元のファイルを消す(頭なら、ディレクトリにほかのファイルが残る間は 0 バイトで残す)。古いディレクトリに 0 バイトの頭しか
       残らなければ頭を消す(親の裁定 Q14)。新しいディレクトリに 0 バイトの頭を足す。
    6. 読み手を書き換える: import の文(名の単位・``imports.py``)・道の文字列(src は許可の一覧 (b-src) の表・tests と tools は
       その割る行の道と名を持つ文字列だけ=走査で作る許可の一覧・``strings.py``)・固定の表のクラスの名の鍵(クラスの単位)・
       つなぎの台帳の道の表(主な割り先 → 元の道)。属性で読み割り先が 2 つ以上になる読み・相対の import と星の import で割る
       モジュールを読む読みは書き換えず「手で直す一覧」に出し、``strict`` なら断る。
    7. 守り(:func:`guards`)。1 つでも当たれば :class:`SplitStopped`(書かない)。

割り専用の守り(計画 §4-3 の ①〜④・記録 docs/bench/analysis/split5a-347 §2)
    ① 文: 元の頂上の文(import・docstring・``__all__``・``from __future__`` を除く)の AST の多重集合=割り先に足した文の多重集合
       (宣言した書き換えは元の側を同じ形に直してから比べる)。割り先ごとに、足した文の並び=元の並びからその割り先の文だけを
       抜いた並び(既に在る割り先は、在る文の並びが変わらず、その後ろに足した分の並び)。
    ② 定数: 元の文字列とバイト列の定数(モジュールの docstring と ① の文の中)の多重集合=割り先の(主な割り先の docstring と足した文)。
    ③ 名の結び: どの割り先でも(元のファイルが残るならそれも)、使う名が全部結ばれている(結ばれない名が元のファイルより増えない)。
       あわせて、元の頂上で結ぶ名(組み込みの名を覆う名を含む)を読む文は、割り先でも同じ物に結ばれる(頂上の定義なら名の割り先・
       import なら同じ出どころ)。
    ④ 宣言: つなぎの台帳の 6 形の宣言(``declared_in`` と項の数)の多重集合が、元と割り先とで同じ(台帳の道の表を通して比べる)。
       2 つ目以降の割り先に宣言が入るなら、台帳の道の表(今の道 → 台帳の道=1 対 1)で表せないので断る。
    ほかに段 4 の守り: 名の凍結・固定の表(値と網羅)・道の形の 74 種・許可の一覧の外の定数(割るファイルと割り先のほか)・import の
    文が結ぶ名(割るファイルと割り先のほか)・頭の ``__all__``。
    import の決まり(検収 高-1・``contracts_spec`` を渡したとき=``cli.py split`` は常に): 割る前と後の木で ``contracts.toml``
    から作る節を比べ、言えなくなった単位・決まりと古い決まりから外れた名が、宣言(``[[split_weakens]]``)のほかに増えたら止める。
    import の循環(G2 の 5 本目の欠陥の後): 読み込みの時に走る import(頂上と頂上の if・try・with の中。``TYPE_CHECKING`` の下と
    関数の中は除く・親の包みの頭を含む)のグラフで、割る前に無かった循環ができたら止める(:func:`new_import_cycles`。新しい
    割り先は元のモジュールの名に引き戻して比べる)。既に在る割り先へ足す import が、その割り先を読むモジュールと循環する形
    (5 本目の ``foundation/vocab/events.py`` → ``foundation/journal/log.py``)を、書く前に見つける。

〔割る段 5b の G0〕入口の扱い(計画 §8 の E2〜E4・親の裁定 Q6・Q7・Q9)
    E2 入口の転送(:data:`pkgmove.table.SPLIT_FORWARDERS`): 元のファイルを消さずに決まった型の転送
       (:func:`pkgmove.table.forwarder_text`)で書き直す。済んだかの判定(:func:`is_done`)は転送が型どおりのときだけ真、元の
       ファイルの判定(:func:`source_rel`)は転送を元と見ない。名の無い点の道(``"shibuya.cli"``)は書き換えない。守り
       「入口の転送」: 型と同じ・頂上で名を結ばない・つなぎの宣言が無い・呼ぶ ``main`` が割り先に在る。
    E3 入口の移し(:data:`pkgmove.table.SPLIT_ENTRIES`): ``if __name__ == "__main__":`` は宣言した割り先へ(宣言が無い入口と、
       読む名の割り先と食い違う宣言は断る)。名の無い点の道は ``-m`` の文脈(文字列の中の ``-m <名>``・並びの 1 つ前の要素が
       ``"-m"``)なら入口の割り先へ、それ以外は主な割り先へ黙って向けず「手で直す一覧」へ(:func:`pkgmove.strings.split_nameless`)。
       文字列の中の手で直す所(コードの文字列の import を含む)も「手で直す一覧」に入れる。
    E4 書き換えの範囲の外(:data:`SPLIT_EXCLUDE_PATHS`=byte-check の道具とその試験): 書き換えず、書き換えたはずの所を報告の
       ``excluded_sites`` に出す。
    〔G0 の直し 高-1〕``tests/_places.py`` の割る行の口(:data:`pkgmove.strings.TABLE_KEY_CALLS`)の第 1 引数=対応表の鍵は書き換えず、
       報告の ``table_key_sites`` に出す。〔高-2〕tests と tools の文字列を選ぶとき、コードの文字列の ``from <包み> import <割る
       モジュール>`` の形も拾う(:func:`pkgmove.strings.code_import_hits`)。機械で書き換えるか「手で直す一覧」に出す(黙って残さない)。
    〔G3 の前・E5〕別名の割り先の宣言(:data:`SPLIT_ALIAS_DESTS`): 差し替える名を呼ぶ時に読む関数の割り先が、名の定義の割り先と
       違う別名は、宣言の割り先へ向ける(守りは :func:`_declared_alias_dests` と「宣言が使われなかった」)。

〔割る段 6 の S6-G0〕道具の拡張(計画 §8・親の裁定 Q1・Q8・追記)
    E7 台帳の道の前向きの表: 宣言の入る 2 つ目以降の新しい割り先ごとに、前向きの表 ``LEDGER_PATHS_SPLIT`` に「割り先の今の道 →
       元のファイルの台帳の道」を書き足す(:func:`ledger_split_rows`・:func:`pkgmove.ledgerpaths.rewrite`)。守り ④ は、台帳の道
       (1 対 1 の表 → 前向きの表 → そのまま)で数える宣言の多重集合が割る前と後で同じことに加え、2 つ目以降の新しい割り先は
       「宣言がある ⇔ 前向きの表に行がある」・前向きの表の今の道は木に在り宣言を持つ・2 つの表の両方に載る今の道が無い、を見る。
       既に在る割り先(別の台帳の道を持つ)へ宣言が入る形は止める。
    E8 道の文字列の割り先の宣言(:data:`SPLIT_PATH_DESTS`): 名の手がかりの無い割るファイルの道を、宣言の割り先へ向ける。宣言も
       名の手がかりも無い道(斜線の道・``/`` の連鎖・名の無い点の道)は、割り先が 2 つ以上の行では主な割り先へ黙って向けず
       「手で直す一覧」へ(:func:`pkgmove.strings.split_path_dest`)。守りは :func:`_path_decl_errors` と「宣言が使われなかった」。
    E5-b 差し替えの届く先(:func:`patch_reach`): 割るモジュールの別名を通す差し替えが、割った後、その名を呼ぶ時に素の名で読んで
       いた関数の割り先の全部に向いているか。向かない割り先・集合の外へ向く差し替えは止める。読み込みの時にだけ読む文と、守りが
       見られなかった差し替えは別の一覧(報告の ``patch_load_time``・``patch_unseen``)。〔検収の後の直し〕主な割り先が元のファイルの
       行は元のモジュールを主な割り先として確かめる・割り先でないモジュールを指したままの差し替えは、別名が手で直す一覧に在るとき
       だけ「見られなかった」(無ければ止める)・``strict`` の当ては「見られなかった」が 1 つでも在れば断る(親の裁定)。
    E5-c 素で使ってよい別名(:class:`AliasDest` の ``bare``・親の裁定 T5): 別名を属性で読まずに渡す・返す・しまう・既定の引数に
       する・``is None`` で比べる形を、宣言の割り先へ書き換えて通す。宣言の ``reads``(渡した先・しまった先で読む名)が割り先の頂上に
       在ること・素の使い方が本当に在り形が許す形だけであること(:func:`_declared_alias_dests`)、``patches``(その別名を通す差し替えの
       名)の届かせる割り先の集合が宣言の割り先だけであること(:func:`patch_reach`)を確かめる。確かめた差し替えは報告の
       ``patch_declared``。印の無い別名の素の使い方は今までどおり手で直す一覧へ。

逐次ループ宣言: なし(道具=木のファイルの数ぶんの走査を 1 回・ランの中では動かない)。
"""
from __future__ import annotations

import ast
import builtins
import difflib
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from pkgmove import allow as AL
from pkgmove import classids as CI
from pkgmove import guard as G
from pkgmove import imports as IM
from pkgmove import ledgerpaths as LPT
from pkgmove import strings as ST
from pkgmove.model import (SRC_PREFIX, Ctx, Edit, Index, Text, Tree, apply_edits, area_of, docstrings_of, is_self, mod_of,
                           parse, resolve_from, symbols_of)
from pkgmove.table import SPLIT_ENTRIES, SPLIT_FORWARDERS, SPLIT_ORDER, MapDoc, Row, forwarder_text

#: 割る段で道の文字列を書き換えない (ファイル, 記号)(表の old を持つ固定の一覧=道の字面が値そのもの)。
STRING_EXCLUDE: frozenset[tuple[str, str]] = frozenset({
    ("tests/test_places_guard.py", "NON_MOVE_ROWS"),
    # llm の字の検出器の試験の材料(植えた文の字面そのものを確かめる)
    ("tests/build_pop/test_w21_stage8_9.py", "test_persona_does_not_reference_llm_ports"),
    # 〔割る段 5b の G0〕元の置き場の道(``src_origins()`` の値=割った後も元の道のまま)と比べる字面(``engine/presence.py``)。
    # 今の道へ書き換えると比べる相手が無くなり、計画実行層の ablation_id(AB-PLAN-EXECUTOR)を黙って拾わなくなる
    ("tools/c8/c8lib.py", "scan_engine_ablation_ids"),
    # 〔割る段 5b の G2 の直し・親の裁定〕古い commit(``LEGACY_COMMIT``)の src の写しでだけ回す子のコード=古い置き場の名のまま。
    # 今の置き場へ書き換えると、古い src で ``No module named`` になる
    ("tests/engine/test_state_format_10f.py", "_HEAD_CHILD"),
    # 〔割る段 6 の S6-G0・親の裁定 R2〕偽の木(tmp の合成の木)に書く見本のコード。字面の ``shibuya.engine.resolve`` は合成の木の
    # 見本の resolve を指し、本物の src を読まない(同じ試験がカードの文の ``shibuya.engine.resolve`` を確かめる=字面をそろえて残す)
    ("tests/tools/test_repo_guide.py", "LAYER_SRC"),
    # 〔割る段 6 の S6-G0・親の裁定(表と順の検収の後)〕``allow.py`` に ``RESOLVE_FILES`` の無い見本の木で読む 1 本(決め事 3)。
    # ``test_repo_guide`` の見本の木がこの道に resolve の材料を置く(書き換えると試験が落ちる)。割った後の本物の木では使われない
    ("tools/repo_guide/guide_permits.py", "RESOLVE_FILE"),
})


@dataclass(frozen=True)
class AliasDest:
    """〔割る段 5b・E5〕別名の割り先の宣言の 1 行: 割る行 ``old`` を当てるとき、ファイル ``file`` で割るモジュールを結んだ別名
    ``alias`` を、名の定義の割り先でなく割り先 ``dest`` へ向ける。``absent`` はこの別名で読むが割り先に無いのが正しい名(常に偽の
    ``hasattr`` で守られた読みなど)。

    〔割る段 6・E5-c・親の裁定 T5〕``bare`` は「素で使ってよい別名」の印: 別名を属性で読まずに渡す・返す・しまう・既定の引数にする・
    ``is None`` で比べる(:data:`pkgmove.imports.BARE_OK`)形を許し、import を ``dest`` へ書き換える(手で直す一覧に出さない)。
    印のある宣言には、``reads``(素で渡した先・しまった先で、そのモジュールの属性として読み書きする名=親と検収役が渡した先の関数を
    読んで確かめた名)・``patches``(その別名を通す差し替えの名=字面で見える差し替えと、素で使った先の差し替えの全部)・``why``
    (渡した先・しまった先の関数と読む名)を書く。"""

    old: str
    file: str
    alias: str
    dest: str
    absent: tuple[str, ...] = ()
    bare: bool = False
    reads: tuple[str, ...] = ()
    patches: tuple[str, ...] = ()
    why: str = ""


#: 〔割る段 5b・E5・親の裁定(G3)〕別名の割り先の宣言。差し替え(``monkeypatch.setattr(別名, "名", …)``)は、その名を呼ぶ時に読む
#: 関数の割り先のモジュールへ向ける必要がある。それが名の定義の割り先と違うとき(道具の既定=定義の割り先か再輸出の主な割り先)は
#: ここに宣言する。読む関数が 2 つの割り先に分かれた名は、割り先ごとの別名で両方を差し替える。守り: 別名が割るモジュールを
#: import していない・宣言の割り先がその行の割り先でない・別名で読む名が割り先の頂上で結ばれていない(``absent`` のほか)・名で
#: 読まない使い方がある・宣言が使われなかった、のどれかで止める(:func:`_declared_alias_dests`)。〔割る段 6・E5-c〕印 ``bare`` の
#: 宣言は、名で読まない使い方を許す代わりに、素の使い方が無い(印の腐り)・許さない形・``reads`` か ``why`` が無い・``reads`` と
#: ``patches`` の名が割り先の頂上に無い・``patches`` の届かせる割り先が宣言の割り先だけでない(:func:`patch_reach`)で止める。
SPLIT_ALIAS_DESTS: tuple[AliasDest, ...] = (
    # build_ledger_bundle を呼ぶ時に読むのは run(main)=差し替えは run を呼ぶのと同じ main の別名で
    AliasDest("cli.py", "tests/engine/test_resume_10d.py", "cli", "interfaces/cli/main.py"),
    # 台帳の型を読むのは、作る側の build_ledger_bundle(wire_economy)と札を決める側の main()(main)の両方。GoodsLedger は作る側だけ
    AliasDest("cli.py", "tests/economy/_stage2_outside.py", "cli", "interfaces/cli/main.py"),
    AliasDest("cli.py", "tests/economy/_stage2_outside.py", "cli_wire", "interfaces/cli/wire_economy.py"),
    # 上の助けの main の側の差し替えを確かめる試験(この助けを使うほかの試験は cli.main を呼ばない)
    AliasDest("cli.py", "tests/economy/cp2/test_cp2_nine_ops_equivalence.py", "cli", "interfaces/cli/main.py"),
    AliasDest("cli.py", "tests/economy/cp2/test_cp2_nine_ops_equivalence.py", "cli_wire",
              "interfaces/cli/wire_economy.py"),
    # 常に偽の hasattr で守られた読み(build_parser は cli に無い=確かめる事の無い行・段 8 の文の掃除の候補)。入口の main へ
    AliasDest("cli.py", "tests/engine/test_classical_policy.py", "cli", "interfaces/cli/main.py",
              absent=("build_parser",)),
    # 〔割る段 6 の S6-G0・E5-c・親の裁定 T5〕素で使ってよい別名 4 つ(渡した先・しまった先の関数を読んで確かめた名)
    AliasDest("engine/resolve.py", "tests/engine/test_conversation_invite.py", "R_TALK", "act/ops/talk.py", bare=True,
              reads=("talk_within_reach", "set_conversing", "end_conversation", "revert_conversation"),
              why="runtime/run.py の _settle_pending_invites(引数 R)へ渡す。中で R から読むのは talk_within_reach・"
                  "set_conversing・end_conversation・revert_conversation の 4 名(差し替えは無い)"),
    AliasDest("engine/resolve.py", "tests/engine/test_defect_fixes_1103.py", "R_TALK", "act/ops/talk.py", bare=True,
              reads=("talk_within_reach", "set_conversing", "end_conversation", "revert_conversation"),
              why="runtime/run.py の _settle_pending_invites(引数 R)へ渡す(5 か所)。中で R から読むのは talk_within_reach・"
                  "set_conversing・end_conversation・revert_conversation の 4 名(差し替えは無い)"),
    AliasDest("engine/resolve.py", "tools/c7/attr_arms.py", "module", "act/apply.py", bare=True,
              reads=("apply",), patches=("apply",),
              why="AgentCellRecorder.attach が self._module にしまい、module.apply を包みに差し替える。detach が "
                  "self._module.apply を元に戻す(しまった先で読み書きするのは apply だけ)"),
    AliasDest("engine/resolve.py", "tools/c7/occupancy_series.py", "module", "act/apply.py", bare=True,
              reads=("apply",), patches=("apply",),
              why="OccupancyRecorder.attach(module=None)が引数で受けるか import し(is None で比べる)、self._module に"
                  "しまい、module.apply を包みに差し替える。detach が self._module.apply を元に戻す(読み書きするのは apply だけ)"),
    # 〔検収の後の続き・親の裁定〕src の別名の分け(S6-G1 の下ごしらえ)の後の judge.py。印のある宣言を足すときは、宣言が腐らない
    # 試験(test_pkgmove の _BARE_RECEIVERS)に受け手を足す(README の E5-c の決まり)
    # 〔割る段 6 の M0・検収の低-2(意味の側)〕patches に set_conversing を足した。23 本目は当たっているので、この宣言は履歴への
    # 当て直しでだけ使う
    AliasDest("engine/resolve.py", "src/shibuya/runtime/systems/judge.py", "R_TALK", "act/ops/talk.py", bare=True,
              reads=("talk_within_reach", "set_conversing", "end_conversation", "revert_conversation"),
              patches=("set_conversing",),
              why="sys_apply_responses が runtime/run.py の _settle_pending_invites(引数 R)へ渡す(1 か所)。中で R から読むのは "
                  "talk_within_reach・set_conversing・end_conversation・revert_conversation の 4 名。tests/engine/proximity/"
                  "test_runs.py の _recorded_run が talk の set_conversing を差し替え、ランの中ではその読みがこの別名を通る(受け手の "
                  "_settle_pending_invites が R.set_conversing を読む=届く先は act/ops/talk.py)"),
)


@dataclass(frozen=True)
class PathDest:
    """〔割る段 6・E8・親の裁定 Q8〕道の文字列の割り先の宣言の 1 行: 割る行 ``old`` を当てるとき、ファイル ``file`` の記号 ``symbol``
    (:mod:`pkgmove.strings` が文字列の持ち主として出す名=頂上の関数・クラス・代入の左辺・メソッドは ``クラス.メソッド``。
    :data:`STRING_EXCLUDE` と同じ見方)の中の、名の手がかりの無い割るファイルの道(斜線の道・``/`` の連鎖・名の無い点の道)を、
    主な割り先でなく割り先 ``dest`` へ向ける。"""

    old: str
    file: str
    symbol: str
    dest: str


#: 〔割る段 6・E8・親の裁定 Q8〕道の文字列の割り先の宣言(形は :data:`SPLIT_ALIAS_DESTS` にそろえる)。宣言はその割る行でだけ使う。
#: 守り: 宣言のファイルと記号が木に在る・宣言の割り先がその行の割り先・記号が書き換えの範囲の中(:data:`STRING_EXCLUDE` と
#: :data:`SPLIT_EXCLUDE_PATHS` の外)・同じ記号に宣言が 2 つ無い・使われなかった宣言は止める(:func:`_path_decl_errors`)。
SPLIT_PATH_DESTS: tuple[PathDest, ...] = (
    # 〔割る段 6 の S6-G0・裁定 Q8〕収入の書きの許可 ``AstAllow("engine/resolve.py", "_require_thawed(world, world.pois.revenue)")``
    # の字面が在るのは ``_complete_buy``・``_complete_eat``=``act/ops/shop.py``(主な割り先 act/apply.py ではない)
    PathDest("engine/resolve.py", "src/shibuya/runtime/state/ledger.py", "_ALLOW_REVENUE", "act/ops/shop.py"),
    # 〔同〕``site.path == "engine/resolve.py" and site.func.startswith("restore")`` は再開の復元(``restore_soa``・``restore_items``)
    # =``runtime/state/restore.py``(``startswith("restore")`` は変えない)
    PathDest("engine/resolve.py", "src/shibuya/runtime/state/ledger_ast.py", "ext_reason", "runtime/state/restore.py"),
    # 〔割る段 6 の M0・親の裁定(仮採用)〕``PORT = "society/speech/port.py"`` は ``SpeechPort`` の書き手の置き場(割った後も元の
    # ファイル)=主な割り先へ向ける(字面は変わらない。後で元のファイルが動けば道具が見る)
    PathDest("engine/speech/port.py", "tests/engine/speech/test_speech_writers_ast.py", "PORT", "society/speech/port.py"),
)
#: 〔割る段 5b・E4・親の裁定 Q9 の (a)〕割る段で書き換えないファイル(道筋か、``/`` で終わるディレクトリ)。byte-check は基準の側
#: (割る前の木)と比べる側(割った後の木)を道具のリポの同じコードで回すので、ランの入口は道具が自分で解く
#: (``tools/bytecheck/check.py`` の ``resolve_run``)。偽のエンジン(``shibuya/cli.py`` を一時の木に作る試験)も書き換えない。
#: 書き換えたはずの所は報告の ``excluded_sites`` に出す(黙って落とさない)。
SPLIT_EXCLUDE_PATHS: tuple[str, ...] = ("tools/bytecheck/", "tests/tools/test_bytecheck.py")


def is_split_excluded(path: str) -> bool:
    return any(path == p or (p.endswith("/") and path.startswith(p)) for p in SPLIT_EXCLUDE_PATHS)
_BUILTINS = frozenset(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__", "__package__", "__builtins__",
                                         "__loader__", "__path__", "__annotations__", "__class__", "__dict__"}
LEDGER_REL = "docs/design/bridging-ledger.json"


class SplitRefused(Exception):
    """断った(表せない・順が違う・使い方)。終了コード 2。"""


class SplitStopped(Exception):
    """守りが止めた(書かない)。終了コード 2(親の発注=守りが「同じ」でなければ当てない)。"""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors[:5]))
        self.errors = errors


# ------------------------------------------------------------------ 済んだ割る行と順
def top_names(text: str) -> set[str]:
    """ファイルの頂上で結ぶ名(関数・クラス・代入の左辺。``__all__`` を除く)。"""
    out: set[str] = set()
    for st in parse(text).body:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(st.name)
        elif isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            tg = st.targets if isinstance(st, ast.Assign) else [st.target]
            out |= {n.id for x in tg for n in ast.walk(x) if isinstance(n, ast.Name)}
    out.discard("__all__")
    return out


def is_forwarder(tree: Tree, row: Row) -> bool:
    """〔割る段 5b・E2〕元のファイルが入口の転送(:data:`pkgmove.table.SPLIT_FORWARDERS` の行で、中身が決まった型そのもの)か。"""
    fw = SPLIT_FORWARDERS.get(row.old)
    return fw is not None and tree.files.get(SRC_PREFIX + row.old) == forwarder_text(row.old, fw)


def forwarder_problems(text: str | None, old: str, dest: str) -> list[str]:
    """〔割る段 5b・E2 の守り〕転送が決まった型か(字面が型と同じ・頂上で名を結ばない・import は ``if __name__ == "__main__":`` の
    中の 1 つだけ・その中身は ``from <割り先> import main`` と ``raise SystemExit(main())`` だけ)。違う所の一覧(空なら型どおり)。"""
    if text is None:
        return ["転送のファイルが無い"]
    out: list[str] = []
    if text != forwarder_text(old, dest):
        out.append("字面が決まった型と違う")
    try:
        t = parse(text)
    except SyntaxError:
        return [*out, "構文の誤り"]
    body = list(t.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    else:
        out.append("docstring が無い")
    if top_names(text) or [s for s in body if isinstance(s, (ast.Import, ast.ImportFrom))]:
        out.append("頂上で名を結ぶ(古い道の口になる)")
    if len(body) != 1 or not _is_main_guard(body[0]) or body[0].orelse:
        out.append("頂上の文が if __name__ == \"__main__\": の 1 つでない")
        return out
    inner = body[0].body
    imp_ok = (len(inner) == 2 and isinstance(inner[0], ast.ImportFrom) and inner[0].level == 0
              and inner[0].module == mod_of(dest) and [(a.name, a.asname) for a in inner[0].names] == [("main", None)])
    call = inner[1] if len(inner) == 2 else None
    raise_ok = (isinstance(call, ast.Raise) and isinstance(call.exc, ast.Call) and isinstance(call.exc.func, ast.Name)
                and call.exc.func.id == "SystemExit" and len(call.exc.args) == 1 and isinstance(call.exc.args[0], ast.Call)
                and isinstance(call.exc.args[0].func, ast.Name) and call.exc.args[0].func.id == "main"
                and not call.exc.args[0].args and not call.exc.args[0].keywords)
    if not (imp_ok and raise_ok):
        out.append(f"if の中が「from {mod_of(dest)} import main」と「raise SystemExit(main())」だけでない")
    return out


def _is_main_guard(st: ast.stmt) -> bool:
    """``if __name__ == "__main__":`` の文か。"""
    if not isinstance(st, ast.If):
        return False
    t = st.test
    return (isinstance(t, ast.Compare) and isinstance(t.left, ast.Name) and t.left.id == "__name__" and len(t.ops) == 1
            and isinstance(t.ops[0], ast.Eq) and len(t.comparators) == 1 and isinstance(t.comparators[0], ast.Constant)
            and t.comparators[0].value == "__main__")


def source_rel(tree: Tree, row: Row) -> str | None:
    """割る行の元のファイルの今の道(``src/shibuya`` からの相対)。段 4 で主な割り先へ移ったもの(18 本目)は主な割り先。
    〔割る段 5b・E2〕元のファイルが入口の転送になっていれば、元の中身はもう無い(``None``)。"""
    if is_forwarder(tree, row):
        return None
    if tree.files.get(SRC_PREFIX + row.old):  # 元のファイルに中身がある
        return row.old
    if row.new and SRC_PREFIX + row.new in tree.files and _in_place_pending(tree, row):
        return row.new
    return None


def _in_place_pending(tree: Tree, row: Row) -> bool:
    text = tree.files.get(SRC_PREFIX + row.new, "")
    have = top_names(text) if text else set()
    return any(d != row.new and n in have for n, d in row.names)


def is_done(tree: Tree, row: Row) -> bool:
    """割る行が当たっているか: どの名も割り先のファイルの頂上に在り、元のファイルは無いか 0 バイトの頭(主な割り先へ移ったもの
    は、ほかの割り先へ行く名が元に残っていない)。〔割る段 5b・E2〕入口の転送の行は、元のファイルが決まった型の転送のとき
    だけ済んだ(転送が無い・型と違うなら済んでいない)。"""
    if not row.names:
        return False
    for n, d in row.names:
        t = tree.files.get(SRC_PREFIX + d)
        if t is None or n not in top_names(t):
            return False
    if row.old in SPLIT_FORWARDERS:
        return is_forwarder(tree, row)
    return not (row.old != row.new and tree.files.get(SRC_PREFIX + row.old))  # 元のファイルは無いか 0 バイトの頭


def split_state(tree: Tree, mapdoc: MapDoc, order: tuple[str, ...] | None = None) -> list[str] | None:
    """済んだ割る行(順の頭から)。順の途中が抜けていれば ``None``(段を飛ばした木)。``order`` は割る段の順(既定は
    :data:`pkgmove.table.SPLIT_ORDER`。〔割る段 6・E9〕``cli.py split --map`` は表の ``split_order`` から読んだ順を渡す)。"""
    order = SPLIT_ORDER if order is None else tuple(order)
    by = mapdoc.by_old()
    done = [o for o in order if o in by and is_done(tree, by[o])]
    if done != list(order[: len(done)]):
        return None
    return done


def next_split(tree: Tree, mapdoc: MapDoc, order: tuple[str, ...] | None = None) -> str | None:
    order = SPLIT_ORDER if order is None else tuple(order)
    st = split_state(tree, mapdoc, order)
    if st is None:
        raise SplitRefused("木の割る段が順と合わない(段を飛ばしたか、逆の順で当てた木)")
    return order[len(st)] if len(st) < len(order) else None


# ------------------------------------------------------------------ 単位
@dataclass
class Unit:
    kind: str  # doc・future・import・all・named・other
    node: ast.stmt
    first: int  # 単位の最初の行(1 から・前の注と空行を含む)
    start: int  # 文の最初の行(飾りを含む)
    end: int
    names: list[str] = field(default_factory=list)
    text: str = ""
    dest: str = ""


def _lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def units_of(text: str, path: str) -> list[Unit]:
    """頂上の文の単位(前の注と空行を付ける)。表せない形は :class:`SplitRefused`。"""
    tree = parse(text)
    L = _lines(text)
    out: list[Unit] = []
    prev_end = 0
    for i, st in enumerate(tree.body):
        start = min([st.lineno] + [d.lineno for d in getattr(st, "decorator_list", [])])
        if out and start <= out[-1].end:
            raise SplitRefused(f"{path}:{st.lineno}: 1 行に 2 つの文がある=表せない")
        if i == 0 and isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
            kind, names = "doc", []
        elif isinstance(st, ast.ImportFrom) and st.module == "__future__":
            kind, names = "future", []
        elif isinstance(st, (ast.Import, ast.ImportFrom)):
            kind, names = "import", []
        elif isinstance(st, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "__all__" for x in st.targets):
            kind, names = "all", []
        elif isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind, names = "named", [st.name]
        elif isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            tg = st.targets if isinstance(st, ast.Assign) else [st.target]
            names = [n.id for x in tg for n in ast.walk(x) if isinstance(n, ast.Name)]
            kind = "named"
        elif isinstance(st, (ast.If, ast.Try, ast.For, ast.While, ast.With)) and _binds(st):
            raise SplitRefused(f"{path}:{st.lineno}: 頂上の {type(st).__name__} の中で名を結ぶ=表せない")
        else:
            kind, names = "other", []
        first = prev_end + 1
        out.append(Unit(kind, st, first, start, st.end_lineno, names, "".join(L[first - 1: st.end_lineno])))
        prev_end = st.end_lineno
    tail = "".join(L[prev_end:])
    if tail.strip():
        if not out:
            raise SplitRefused(f"{path}: 文が無い")
        out[-1].text += tail  # 末尾の注の行は最後の単位に付ける
    return out


def _binds(st: ast.stmt) -> bool:
    for n in ast.walk(st):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            return True
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            return True
    return False


def free_names(u: "Unit", keep: frozenset[str] | set[str] = frozenset()) -> set[str]:
    """単位の中で結ばれない名(=割り先のモジュールの頂上で結ぶ要る名)と、文字列の注釈の中の名。``keep`` は組み込みの名でも
    数える名(元のモジュールの頂上で結ぶ名=組み込みを覆う名・検収 中-1)。"""
    return unbound_names(u.text.lstrip("\n") or "pass\n", keep=keep) | _string_annotation_names(u.node)


def _string_annotation_names(node: ast.AST) -> set[str]:
    out: set[str] = set()
    for n in ast.walk(node):
        anns = []
        if isinstance(n, ast.arg) and n.annotation is not None:
            anns.append(n.annotation)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns is not None:
            anns.append(n.returns)
        if isinstance(n, ast.AnnAssign):
            anns.append(n.annotation)
        for a in anns:
            for c in ast.walk(a):
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    try:
                        out |= {x.id for x in ast.walk(ast.parse(c.value, mode="eval")) if isinstance(x, ast.Name)}
                    except SyntaxError:
                        pass
    return out


def names_used(node: ast.AST) -> set[str]:
    """文が読む名(読み・注釈の名・文字列の注釈の中の名。結ぶ名は含めない)。局所の名も含む(多めに数える)。"""
    out: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            out.add(n.id)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.isidentifier():
            pass
    for n in ast.walk(node):  # 文字列の注釈
        anns = []
        if isinstance(n, ast.arg) and n.annotation is not None:
            anns.append(n.annotation)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns is not None:
            anns.append(n.returns)
        if isinstance(n, ast.AnnAssign):
            anns.append(n.annotation)
        for a in anns:
            for c in ast.walk(a):
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    try:
                        out |= {x.id for x in ast.walk(ast.parse(c.value, mode="eval")) if isinstance(x, ast.Name)}
                    except SyntaxError:
                        pass
    return out


# ------------------------------------------------------------------ 結ばれない名(守り ③)
def unbound_names(text: str, keep: frozenset[str] | set[str] = frozenset()) -> set[str]:
    """頂上・関数・クラスの中で読むのに、どこでも結ばれない名(組み込みを除く。``keep`` の名は組み込みでも数える)。比べるための
    多めの近似(内包の変数と、関数の中の全部の結びを関数の局所と見る)。"""
    builtins_ = _BUILTINS - set(keep)
    tree = parse(text)
    module_bound = set(_bound_in(tree.body, top=True))
    comp_bound: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.comprehension):
            comp_bound |= {x.id for x in ast.walk(n.target) if isinstance(x, ast.Name)}
        if isinstance(n, ast.Global):
            module_bound |= set(n.names)
    out: set[str] = set()

    def visit(node: ast.AST, scopes: list[set[str]], in_class: set[str] | None) -> None:
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                if not isinstance(ch, ast.Lambda):
                    for d in ch.decorator_list:
                        visit_expr(d, scopes, in_class)
                a = ch.args
                for x in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]:
                    if x is not None and x.annotation is not None:
                        visit_expr(x.annotation, scopes, in_class)
                for d in [*a.defaults, *[k for k in a.kw_defaults if k is not None]]:
                    visit_expr(d, scopes, in_class)
                if not isinstance(ch, ast.Lambda) and ch.returns is not None:
                    visit_expr(ch.returns, scopes, in_class)
                local = {x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if x is not None}
                body = ch.body if isinstance(ch.body, list) else [ch.body]
                local |= set(_bound_in(body, top=False))
                for b in body:
                    visit_stmt(b, [*scopes, local], None)
            elif isinstance(ch, ast.ClassDef):
                for d in [*ch.decorator_list, *ch.bases, *[k.value for k in ch.keywords]]:
                    visit_expr(d, scopes, in_class)
                cls_local = set(_bound_in(ch.body, top=False))
                for b in ch.body:
                    visit_stmt(b, scopes, cls_local)
            else:
                visit_generic(ch, scopes, in_class)

    def visit_stmt(st: ast.AST, scopes: list[set[str]], in_class: set[str] | None) -> None:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            wrapper = ast.Module(body=[st], type_ignores=[])
            visit(wrapper, scopes, in_class)
        else:
            visit_generic(st, scopes, in_class)

    def visit_expr(e: ast.AST, scopes: list[set[str]], in_class: set[str] | None) -> None:
        visit_generic(e, scopes, in_class)

    def visit_generic(node: ast.AST, scopes: list[set[str]], in_class: set[str] | None) -> None:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            nm = node.id
            if not (nm in builtins_ or nm in module_bound or nm in comp_bound or any(nm in s for s in scopes)
                    or (in_class is not None and nm in in_class)):
                out.add(nm)
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            visit(ast.Module(body=[node], type_ignores=[]) if not isinstance(node, ast.Lambda)
                  else ast.Expression(body=node), scopes, in_class)
            return
        for ch in ast.iter_child_nodes(node):
            visit_generic(ch, scopes, in_class)

    for st in tree.body:
        visit_stmt(st, [], None)
    return out


def _bound_in(body: Iterable[ast.stmt], *, top: bool) -> list[str]:
    """文の並びが結ぶ名(入れ子の関数とクラスの中は見ない・名だけ)。"""
    out: list[str] = []
    stack: list[ast.AST] = list(body)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append(n.name)
            continue
        if isinstance(n, ast.Lambda):
            continue
        if isinstance(n, ast.Import):
            out += [a.asname or a.name.split(".")[0] for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            out += [a.asname or a.name for a in n.names]
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.append(n.id)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            out.append(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            out += list(n.names)
        elif isinstance(n, ast.MatchAs) and n.name:
            out.append(n.name)
        stack.extend(ast.iter_child_nodes(n))
    return out


# ------------------------------------------------------------------ 計画
@dataclass
class SplitPlan:
    row: Row
    src_rel: str
    in_place: bool
    before: Tree
    after: Tree
    dests: dict[str, str] = field(default_factory=dict)  # 割り先 → new・existing・in_place
    names_by_dest: dict[str, list[str]] = field(default_factory=dict)
    others_by_dest: dict[str, int] = field(default_factory=dict)
    changed: dict[str, list[Edit]] = field(default_factory=dict)
    import_stats: dict[str, IM.ImportStats] = field(default_factory=dict)
    import_files: Counter = field(default_factory=Counter)
    str_stats: ST.StrStats = field(default_factory=ST.StrStats)
    manual: list[str] = field(default_factory=list)
    dropped_reexports: list[str] = field(default_factory=list)
    dropped_imports: list[str] = field(default_factory=list)
    rewrites_applied: dict[str, int] = field(default_factory=dict)
    rebuilt_imports: list[str] = field(default_factory=list)
    class_keys: int = 0
    ledger_paths_added: int = 0
    created_heads: list[str] = field(default_factory=list)
    emptied_heads: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    guards: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    string_sites: list[str] = field(default_factory=list)
    #: 割り先 → その割り先が import で結ぶ名(元の import から持ち込んだ名と、既に在る割り先が同じ物に結んでいる名)。
    kept_bindings: dict[str, set[str]] = field(default_factory=dict)
    #: 〔検収 低-2〕写さなかった import と注(黙って落とさない=報告に出す)。
    unwritten: list[str] = field(default_factory=list)
    #: 〔検収 高-1〕割る前と後の import の決まり(:func:`pkgmove.contracts.weakened`)。決まりの元を渡したときだけ。
    contracts: dict = field(default_factory=dict)
    #: 〔割る段 5b・E2〕入口の転送で書き直した元のファイル(リポの根からの道)。無ければ空。
    forwarder: str = ""
    #: 〔割る段 5b・E3〕``if __name__ == "__main__":`` の割り先(宣言した入口)。無ければ空。
    entry: str = ""
    #: 〔割る段 5b・E4〕書き換えの範囲から外したファイル(:data:`SPLIT_EXCLUDE_PATHS`)で、外さなければ書き換えた所(ファイル・数)。
    excluded_sites: list[str] = field(default_factory=list)
    #: 〔割る段 5b・E5〕使った別名の割り先の宣言(:data:`SPLIT_ALIAS_DESTS`)。ファイル・別名 → 割り先・読む名の数・無くてよい名。
    alias_declared: list[str] = field(default_factory=list)
    #: 〔割る段 6・E7〕前向きの表(``LEDGER_PATHS_SPLIT``)に足した行(割り先の今の道 → 台帳の道)。
    ledger_paths_split: list[str] = field(default_factory=list)
    #: 〔割る段 6・E8〕使った道の文字列の割り先の宣言(:data:`SPLIT_PATH_DESTS`)。ファイル::記号 → 割り先・当てた道の数。
    path_declared: list[str] = field(default_factory=list)
    #: 〔割る段 6・E5-b〕差し替えの届く先の守り(:func:`patch_reach`): 確かめた差し替え(ファイル::記号 名 → 割り先)・見られなかった
    #: 差し替え・読み込みの時にだけ読む文(差し替えが効かない読み)。
    patch_checked: list[str] = field(default_factory=list)
    patch_unseen: list[str] = field(default_factory=list)
    patch_load_time: list[str] = field(default_factory=list)
    #: 〔割る段 6・E5-c〕素で使ってよい別名の宣言で確かめた差し替え(ファイル: 別名 の名 → 宣言の割り先・字面で見えた差し替えの数)。
    #: 確かめた(``patch_checked``)・見られなかった(``patch_unseen``)とは分ける。
    patch_declared: list[str] = field(default_factory=list)


def alias_modules(text: str, path: str) -> dict[str, set[str]]:
    """〔割る段 5b・E5〕ファイルの import が別名に結ぶモジュールの名(どの有効範囲でも・同じ別名を 2 つのモジュールに結べば 2 つ)。
    ``from P import x as X`` は ``P.x``・``import M as X`` は ``M``(別名の無い ``import a.b`` は ``a``)。"""
    own = mod_of(path[len(SRC_PREFIX):]) if path.startswith(SRC_PREFIX) else ""
    pkg = own if path.endswith("/__init__.py") else own.rpartition(".")[0]
    out: dict[str, set[str]] = {}
    for n in ast.walk(parse(text)):
        if isinstance(n, ast.ImportFrom):
            m = resolve_from(pkg, n) if n.level else n.module
            for a in n.names:
                out.setdefault(a.asname or a.name, set()).add(f"{m}.{a.name}")
        elif isinstance(n, ast.Import):
            for a in n.names:
                top = a.name.split(".")[0]
                out.setdefault(a.asname or top, set()).add(a.name if a.asname else top)
    return out


def _declared_alias_dests(ctx: Ctx, p: str, text: str, decls: list[AliasDest], dests: set[str], src_mod: str,
                          after: Tree) -> tuple[dict[str, str], list[str], list[str]]:
    """〔割る段 5b・E5〕ファイル ``p`` の別名の割り先の宣言を確かめる。返すのは (別名 → 宣言の割り先のモジュール・止める文・使った
    宣言の報告の行)。宣言の別名が木のファイルに無ければ何も返さない(呼ぶ側が「使われなかった」で止める)。"""
    binds = alias_modules(text, p)
    uses = IM.alias_uses(ctx, text, p)
    over: dict[str, str] = {}
    errs: list[str] = []
    notes: list[str] = []
    for d in decls:
        where = f"{p}: 別名 {d.alias} → {d.dest}"
        mods = binds.get(d.alias)
        if not mods:
            continue
        bad: list[str] = []
        if mods != {src_mod}:
            bad.append(f"別名が割るモジュール {src_mod} を import していない(結ぶのは {sorted(mods)})")
        if d.dest not in dests:
            bad.append(f"宣言の割り先がこの割る行の割り先でない(割り先 {sorted(dests)})")
        u = uses.get(d.alias)
        attrs = set(u.attrs) if u is not None else set()
        forms = list(u.bare_forms) if u is not None else []
        if d.bare:  # 〔割る段 6・E5-c〕素で使ってよい別名: 素の使い方の形・渡した先で読む名・わけを確かめる
            if u is None or not u.bare_lines:
                bad.append("素で使ってよい印があるのに、素の使い方が 1 つも無い(印の腐り=印を外す)")
            odd = [f"行 {ln}: {f}" for ln, f in forms if f not in IM.BARE_OK]
            if odd:
                bad.append(f"宣言で表せない素の使い方 {odd}(許すのは {'・'.join(IM.BARE_OK)})")
            if not d.reads:
                bad.append("素で渡した先・しまった先で読む名(reads)が無い")
            if not d.why:
                bad.append("わけ(why=渡した先・しまった先の関数と読む名)が無い")
        else:
            if u is not None and u.bare_lines:
                bad.append(f"名で読まない使い方がある(行 {list(u.bare_lines)})=読む名を確かめられない")
            if d.reads or d.patches:
                bad.append("素で使ってよい印(bare)が無いのに、reads・patches を書いている")
        dtext = after.files.get(SRC_PREFIX + d.dest)
        top = set(_bound_in(parse(dtext).body, top=True)) if dtext is not None else set()
        if d.dest in dests:
            lack = sorted(attrs - top - set(d.absent))
            if lack:
                bad.append(f"別名で読む名 {lack} が割り先の頂上で結ばれていない(定義でも import でもない)")
            stale = sorted(set(d.absent) - attrs)
            if stale:
                bad.append(f"無くてよいと挙げた名 {stale} をこの別名で読んでいない")
            there = sorted(set(d.absent) & top)
            if there:
                bad.append(f"無くてよいと挙げた名 {there} が割り先の頂上に在る")
            if d.bare:
                lack_r = sorted(set(d.reads) - top)
                if lack_r:
                    bad.append(f"素で渡した先・しまった先で読む名 {lack_r} が割り先の頂上で結ばれていない(定義でも import でもない)")
                lack_p = sorted(set(d.patches) - top)
                if lack_p:
                    bad.append(f"差し替える名 {lack_p} が割り先の頂上で結ばれていない(定義でも import でもない)")
        if bad:
            errs += [f"{where}: {b}" for b in bad]
            over[d.alias] = ""  # 使った(「使われなかった」と二重に言わない)が、向けない
            continue
        over[d.alias] = mod_of(d.dest)
        tail = f"・無くてよい名 {', '.join(d.absent)}" if d.absent else ""
        if d.bare:  # 〔E5-c〕素の使い方の形ごとの数・渡した先で読む名・差し替える名
            used = "・".join(f"{f} {sum(1 for _ln, x in forms if x == f)}" for f in IM.BARE_OK
                            if any(x == f for _ln, x in forms))
            tail += (f"・素の使い方 {used}・渡した先で読む名 {', '.join(d.reads)}"
                     + (f"・差し替える名 {', '.join(d.patches)}" if d.patches else ""))
        notes.append(f"{where}(読む名 {len(attrs)}{tail})")
    return over, errs, notes


def _import_bindings(st: ast.stmt) -> list[tuple[str, ast.alias]]:
    if isinstance(st, ast.Import):
        return [(a.asname or a.name.split(".")[0], a) for a in st.names]
    assert isinstance(st, ast.ImportFrom)
    return [(a.asname or a.name, a) for a in st.names]


def _import_target(st: ast.stmt, a: ast.alias, pkg: str, ix: Index) -> tuple[str, str | None]:
    """結んだ名の出どころ: (モジュール, 名)。モジュールそのものなら名は ``None``。"""
    if isinstance(st, ast.Import):
        return (a.name if a.asname else a.name.split(".")[0]), None
    from pkgmove.model import resolve_from
    m = resolve_from(pkg, st) or ""
    sub = f"{m}.{a.name}"
    if ix.exists(sub):
        return sub, None
    return m, a.name


def _render_import(st: ast.stmt, aliases: list[ast.alias], pkg: str) -> str:
    """元の文の名のうち ``aliases`` だけの import の文(1 行・長ければ括弧で折る)。"""
    def al(a: ast.alias) -> str:
        return f"{a.name} as {a.asname}" if a.asname else a.name
    if isinstance(st, ast.Import):
        return "\n".join(f"import {al(a)}" for a in aliases) + "\n"
    assert isinstance(st, ast.ImportFrom)
    if st.level:  # 〔検収 中-2〕相対の import は元の包みから解いた絶対の形(割り先は別の包みのことがある)
        from pkgmove.model import resolve_from
        mod = resolve_from(pkg, st)
        if not mod:
            raise SplitRefused(f"相対の import(行 {st.lineno})を元の包み {pkg} から解けない=表せない")
    else:
        mod = st.module or ""
    one = f"from {mod} import {', '.join(al(a) for a in aliases)}"
    if len(one) <= 120:
        return one + "\n"
    return f"from {mod} import (\n" + "".join(f"    {al(a)},\n" for a in aliases) + ")\n"


def _render_all(names: list[str], indent: str = "    ") -> str:
    lines: list[str] = []
    cur = ""
    for n in names:
        piece = f'"{n}", '
        if len(indent) + len(cur) + len(piece) > 118 and cur:
            lines.append(indent + cur.rstrip())
            cur = ""
        cur += piece
    if cur:
        lines.append(indent + cur.rstrip())
    return "\n".join(lines)


def _all_names(st: ast.stmt) -> list[str]:
    v = st.value if isinstance(st, ast.Assign) else None
    if not isinstance(v, (ast.List, ast.Tuple)):
        raise SplitRefused(f"__all__ が並びの形でない(行 {st.lineno})=表せない")
    out = []
    for e in v.elts:
        if not (isinstance(e, ast.Constant) and isinstance(e.value, str)):
            raise SplitRefused(f"__all__ の要素が文字列でない(行 {st.lineno})=表せない")
        out.append(e.value)
    return out


def _rewrite_alias(text: str, alias: str) -> tuple[str, int]:
    """単位の字面の ``alias.x`` を ``x`` に(宣言した書き換え)。``alias`` だけの使い方が残れば :class:`SplitRefused`。"""
    tree = ast.parse(text)
    caught = _alias_captures(tree, alias)
    if caught:
        raise SplitRefused(f"宣言した書き換え {alias}.x → x の x が、その有効範囲の局所の名に捕まる({caught[:3]})=表せない")
    t = Text(text)
    edits: list[Edit] = []
    attr_vals: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == alias:
            s, e = t.span(n)
            edits.append(Edit(s, e, n.attr, "alias", "", f"{alias}.{n.attr}"))
            attr_vals.add(id(n.value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id == alias and id(n) not in attr_vals:
            raise SplitRefused(f"宣言した書き換えの別名 {alias} が属性のほかの形で使われる=表せない")
    return (apply_edits(text, edits) if edits else text), len(edits)


def _alias_captures(tree: ast.AST, alias: str) -> list[str]:
    """〔検収 低-1〕``alias.x`` のうち、その場所を囲む関数・ラムダ・内包・クラスの本体で ``x`` が局所に結ばれているもの
    (``x`` に書き換えると局所の名を読む)。頂上(モジュールの有効範囲)の結びは割り先の頂上の ``x`` と同じ物なので数えない。"""
    hits: list[str] = []

    def comp_targets(n: ast.AST) -> set[str]:
        return {x.id for g in n.generators for x in ast.walk(g.target) if isinstance(x, ast.Name)}

    def visit(node: ast.AST, scopes: list[tuple[set[str], bool]]) -> None:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == alias:
            if any(node.attr in s for s, _cls in scopes):
                hits.append(f"行 {node.lineno}: {alias}.{node.attr}")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = node.args
            outer = [*getattr(node, "decorator_list", []), *a.defaults, *[k for k in a.kw_defaults if k is not None],
                     *[x.annotation for x in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]
                       if x is not None and x.annotation is not None]]
            if not isinstance(node, ast.Lambda) and node.returns is not None:
                outer.append(node.returns)
            for p in outer:
                visit(p, scopes)
            body = node.body if isinstance(node.body, list) else [node.body]
            local = {x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if x is not None}
            local |= set(_bound_in(body, top=False))
            inner = [(s, c) for s, c in scopes if not c]  # 関数の本体はクラスの有効範囲を見ない
            for b in body:
                visit(b, [*inner, (local, False)])
            return
        if isinstance(node, ast.ClassDef):
            for p in [*node.decorator_list, *node.bases, *[k.value for k in node.keywords]]:
                visit(p, scopes)
            cls_local = set(_bound_in(node.body, top=False))
            for b in node.body:
                visit(b, [*scopes, (cls_local, True)])
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for ch in ast.iter_child_nodes(node):
                visit(ch, [*scopes, (comp_targets(node), False)])
            return
        for ch in ast.iter_child_nodes(node):
            visit(ch, scopes)

    visit(tree, [])
    return hits


def _strip_alias_dump(node: ast.AST, alias: str) -> str:
    """守り ① のための正規化: ``alias.x`` を ``x`` にした AST の dump。"""
    class T(ast.NodeTransformer):
        def visit_Attribute(self, n: ast.Attribute):  # noqa: N802
            self.generic_visit(n)
            if isinstance(n.value, ast.Name) and n.value.id == alias:
                return ast.copy_location(ast.Name(id=n.attr, ctx=n.ctx), n)
            return n
    import copy
    return ast.dump(T().visit(copy.deepcopy(node)), include_attributes=False)


def _dump(node: ast.AST) -> str:
    return ast.dump(node, include_attributes=False)


def template_docstring(dest: str, row: Row, src_rel: str) -> str:
    """2 つ目以降の新しい割り先の docstring(決まった型。凍結の値・expedient の見出しを書かない)。"""
    return (f'"""{mod_of(dest)[len("shibuya."):]} — 割る段で ``{row.old}`` を割った割り先(全ファイルの表 §4・名の表は\n'
            f"``tools/pkgmove/map.toml`` の割る行)。\n\n"
            f"中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の\n"
            f"方針は、主な割り先 ``{row.new}`` に残した元の docstring を読むこと。\n"
            f'"""\n')


def compose(tree: Tree, row: Row, src_rel: str, ix: Index, plan: SplitPlan) -> dict[str, str]:
    """割り先ごとの新しい字面(既に在る割り先は書き足した後の全文・元のファイルが主な割り先なら書き直した全文)。"""
    text = tree.files[SRC_PREFIX + src_rel]
    units = units_of(text, src_rel)
    nm = row.name_map
    src_mod = mod_of(src_rel)
    pkg = src_mod if src_rel.endswith("__init__.py") else src_mod.rpartition(".")[0]
    main = row.new
    named = [u for u in units if u.kind == "named"]
    others = [u for u in units if u.kind == "other"]
    imports = [u for u in units if u.kind == "import"]
    futures = [u for u in units if u.kind == "future"]
    alls = [u for u in units if u.kind == "all"]
    doc = next((u for u in units if u.kind == "doc"), None)
    # 〔検収 中-1〕星の import は結ぶ名が決まらない=表せない
    for u in imports:
        if isinstance(u.node, ast.ImportFrom) and any(a.name == "*" for a in u.node.names):
            raise SplitRefused(f"{src_rel}:{u.start}: 星の import(from … import *)は結ぶ名が決まらない=表せない")
    # 〔検収 中-1〕元の頂上で結ぶ名のうち組み込みの名を覆うもの(def format など)は、組み込みでも要る名に数える
    shadow = frozenset((set(_bound_in(parse(text).body, top=True)) - {"__all__"}) & _BUILTINS)
    # 途中の import(再輸出のほか)は表せない
    first_code = next((u.start for u in units if u.kind in ("named", "other")), None)
    # 名を結ぶ文 → 割り先
    defined: dict[str, str] = {}
    for u in named:
        ds = {nm.get(n) for n in u.names}
        if None in ds:
            raise SplitRefused(f"{src_rel}:{u.start}: 名 {[n for n in u.names if n not in nm]} の割り先が表に無い")
        if len(ds) != 1:
            raise SplitRefused(f"{src_rel}:{u.start}: 1 つの文の名 {u.names} が 2 つの割り先に分かれる=表せない")
        u.dest = ds.pop()
        for n in u.names:
            defined[n] = u.dest
    missing = sorted(set(nm) - set(defined))
    if missing:
        raise SplitRefused(f"{src_rel}: 表の名がファイルに無い: {missing}")
    for u in others:
        ds = {defined[n] for n in names_used(u.node) if n in defined}
        u.dest = ds.pop() if len(ds) == 1 else (main if (not ds or main in ds) else "")
        if not u.dest:
            raise SplitRefused(f"{src_rel}:{u.start}: 頂上のほかの文の割り先が 1 つに決まらない({sorted(ds)})")
    # 〔割る段 5b・E2・E3〕入口(if __name__ == "__main__":)は宣言した割り先へ(読む名の割り先と同じでなければ断る)。宣言の無い
    # 割る行に入口があれば断る(`-m <元>` の文字列の行き先が決まらない)
    entry = SPLIT_ENTRIES.get(row.old) or SPLIT_FORWARDERS.get(row.old)
    mains = [u for u in others if _is_main_guard(u.node)]
    if entry is None and mains:
        raise SplitRefused(f"{src_rel}:{mains[0].start}: 入口(if __name__ == \"__main__\":)があるが、入口の割り先の宣言"
                           f"(table.SPLIT_ENTRIES・SPLIT_FORWARDERS)が無い")
    if entry is not None:
        if not mains:
            raise SplitRefused(f"{src_rel}: 入口の宣言({entry})があるが、if __name__ == \"__main__\": が無い")
        bad = [u.start for u in mains if u.dest != entry]
        if bad:
            raise SplitRefused(f"{src_rel}: 入口(行 {bad})の割り先が宣言した {entry} でない(行き先は読む名の割り先で決まる)")
        plan.entry = entry
    # 結んだ名(元の import)
    bind: dict[str, tuple[ast.stmt, ast.alias, Unit]] = {}
    for u in imports:
        if first_code is not None and u.start > first_code:
            # 途中の import: どの単位も使わない再輸出なら落とす(llm/__init__.py の末尾)・使うなら表せない
            pass
        for b, a in _import_bindings(u.node):
            bind[b] = (u.node, a, u)
    used_by: dict[str, set[str]] = {}
    for u in [*named, *others]:
        for n in names_used(u.node):
            used_by.setdefault(n, set()).add(u.dest)
    for u in imports:
        if first_code is not None and u.start > first_code:
            if any(used_by.get(b) for b, _a in _import_bindings(u.node)):
                raise SplitRefused(f"{src_rel}:{u.start}: 途中の import が使われる=表せない")
    all_names = _all_names(alls[0].node) if alls else []
    # 割り先の並び(表の順)
    dests = list(dict.fromkeys([main, *[d for _n, d in row.names]]))
    out: dict[str, str] = {}
    rewrites = dict(row.rewrites)
    sib_edges: dict[str, set[str]] = {}
    verbatim: set[int] = set()  # 元の字面のまま写した import の単位(最初の行)
    for d in dests:
        d_units = [u for u in units if u.kind in ("named", "other") and u.dest == d]
        if not d_units and d != main:
            continue
        d_mod = mod_of(d)
        exists = SRC_PREFIX + d in tree.files and d != src_rel
        in_place = d == src_rel
        plan.dests[d] = "in_place" if in_place else ("existing" if exists else "new")
        plan.names_by_dest[d] = [n for u in d_units for n in u.names]
        plan.others_by_dest[d] = sum(1 for u in d_units if u.kind == "other")
        need: set[str] = set()
        for u in d_units:
            need |= free_names(u, shadow)
        own = {n for u in d_units for n in u.names}
        ex_text = tree.files.get(SRC_PREFIX + d, "") if exists else ""
        ex_names = top_names(ex_text) if exists else set()
        ex_bind = _existing_bindings(ex_text, d_mod, ix) if exists else {}
        clash = sorted(own & (ex_names | set(ex_bind)))
        if clash:  # 〔検収 中-2〕後ろに足すと在る名を上書きする
            raise SplitRefused(f"{src_rel}: 既に在る割り先 {d} が名 {clash} を既に結んでいる(後ろに足すと上書きする)=表せない")
        alias_rw: str | None = None
        # 元の import の文のうち、この割り先が使う名
        imp_lines: list[str] = []
        for u in imports:
            keep: list[ast.alias] = []
            for b, a in _import_bindings(u.node):
                if b not in need or b in own:
                    continue
                tm, tn = _import_target(u.node, a, pkg, ix)
                if tm == d_mod:  # 割り先のモジュール自身
                    if tn is None:  # 自己の別名(V.x)
                        if rewrites.get(d) != b:
                            raise SplitRefused(f"{src_rel}: 割り先 {d} は自分を別名 {b} で読む文を受ける。宣言した書き換え"
                                               f"(§4 の注「宣言した書き換え」)が無い=表せない")
                        alias_rw = b
                    elif tn not in ex_names and tn not in own:
                        raise SplitRefused(f"{src_rel}: 割り先 {d} は自分から名 {tn} を読むが、その名が割り先に無い")
                    plan.dropped_imports.append(f"{d}: {b}(割り先のモジュール自身)")
                    continue
                if exists and b in ex_bind:
                    if ex_bind[b] != (tm, tn):
                        raise SplitRefused(f"{src_rel}: 割り先 {d} は名 {b} を別の物に結んでいる=表せない")
                    plan.kept_bindings.setdefault(d, set()).add(b)
                    continue
                if exists and b in ex_names:
                    raise SplitRefused(f"{src_rel}: 割り先 {d} は名 {b} を既に定義している=表せない")
                keep.append(a)
            if not keep:
                continue
            plan.kept_bindings.setdefault(d, set()).update(a.asname or (a.name if isinstance(u.node, ast.ImportFrom)
                                                                        else a.name.split(".")[0]) for a in keep)
            all_b = [a for _b, a in _import_bindings(u.node)]
            rel = isinstance(u.node, ast.ImportFrom) and u.node.level > 0
            if len(keep) == len(all_b) and not rel:
                imp_lines.append("".join(_lines(tree.files[SRC_PREFIX + src_rel])[u.start - 1: u.end]))
                verbatim.add(u.start)
            else:
                imp_lines.append(_render_import(u.node, keep, pkg))  # 〔検収 中-2〕相対の import は絶対の形に作り直す
                plan.rebuilt_imports.append(f"{d}:{u.start}" + ("(相対 → 絶対)" if rel else ""))
        # 兄弟の割り先からの import
        sib: dict[str, list[str]] = {}
        for n in sorted(need):
            if n in own or n not in defined or defined[n] == d:
                continue
            sib.setdefault(defined[n], []).append(n)
        for sd, ns in sib.items():
            sib_edges.setdefault(d, set()).add(sd)
            if exists and any(n in ex_names for n in ns):
                raise SplitRefused(f"{src_rel}: 割り先 {d} は名 {ns} を既に持つ")
            if mod_of(sd) == d_mod:
                continue
            imp_lines.append(_render_import(ast.ImportFrom(module=mod_of(sd), names=[ast.alias(name=n) for n in ns],
                                                           level=0), [ast.alias(name=n) for n in ns], pkg))
        if rewrites.get(d) and alias_rw is None:
            raise SplitRefused(f"{src_rel}: 宣言した書き換え(割り先 {d} の別名 {rewrites[d]})が当たらない")
        # 単位の字面(宣言した書き換え)
        body_parts: list[str] = []
        for u in d_units:
            t = u.text
            if alias_rw is not None:
                t, k = _rewrite_alias(t, alias_rw)
                plan.rewrites_applied[d] = plan.rewrites_applied.get(d, 0) + k
            body_parts.append(t)
        d_all = [n for n in all_names if n in own]
        if exists:
            out[d] = _append_to_existing(ex_text, d, imp_lines, d_all, body_parts,
                                         {a.name for f in futures for a in f.node.names})
        else:
            if d == main and doc is not None:
                header = "".join(_lines(text)[: doc.end])
            else:
                header = template_docstring(d, row, src_rel)
            parts = [header]
            if futures:
                parts.append("\n" + "".join("".join(_lines(text)[f.start - 1: f.end]) for f in futures))
            if imp_lines:
                parts.append("\n" + "".join(imp_lines))
            if d_all:
                parts.append("\n__all__ = [\n" + _render_all(d_all) + "\n]\n")
            body = "".join(body_parts).lstrip("\n")
            parts.append("\n\n" + body)
            s = "".join(parts)
            out[d] = s.rstrip("\n") + "\n"
    for a, bs in sib_edges.items():  # 割り先どうしが互いに頂上で読み合う=循環の import
        for b in bs:
            if a in sib_edges.get(b, set()):
                raise SplitRefused(f"{src_rel}: 割り先 {a} と {b} が互いの名を読む(循環の import)=表せない")
    dropped = [n for n in all_names if n not in defined]
    plan.dropped_reexports = dropped
    plan.unwritten = _unwritten(text, units, plan, verbatim, main)
    return out


def _unwritten(text: str, units: list[Unit], plan: SplitPlan, verbatim: set[int], main: str) -> list[str]:
    """〔検収 低-2〕割り先へ写さなかった import(どの割り先も使わない名・途中の import)と注(import・``from __future__``・
    ``__all__`` の前の注、作り直した import と ``__all__`` の中の注、主な割り先へ docstring を写さないときの前の注)。"""
    import io
    import tokenize

    kept: set[str] = set().union(*plan.kept_bindings.values()) if plan.kept_bindings else set()
    selfs = {x.split(": ", 1)[1].split("(", 1)[0] for x in plan.dropped_imports}
    first_code = next((u.start for u in units if u.kind in ("named", "other")), None)
    L = _lines(text)
    out: list[str] = []
    for u in units:
        if u.kind != "import":
            continue
        bs = [b for b, _a in _import_bindings(u.node)]
        gone = [b for b in bs if b not in kept and b not in selfs]
        if not gone:
            continue
        late = "途中の import・" if first_code is not None and u.start > first_code else ""
        what = f"`{L[u.start - 1].strip()}`" + ("" if len(gone) == len(bs) else f" の名 {gone}")
        out.append(f"import 行 {u.start}: {what} — {late}どの割り先も使わない(写さなかった)")
    main_new = plan.dests.get(main) in ("new", "in_place")
    for tk in tokenize.generate_tokens(io.StringIO(text).readline):
        if tk.type != tokenize.COMMENT:
            continue
        line = tk.start[0]
        u = next((x for x in units if x.first <= line <= x.end), None)
        tail = u is None and bool(units) and line > units[-1].end
        if tail:
            u = units[-1]
        if u is None or u.kind in ("named", "other"):
            continue
        if u.kind == "doc":
            if main_new:
                continue
            where = "docstring の前(主な割り先へ docstring を写さない)"
        elif tail:
            where = f"ファイルの末尾(最後の単位が {u.kind})"
        elif line < u.start:
            where = {"import": "import の前", "future": "from __future__ の前", "all": "__all__ の前"}[u.kind]
        elif u.kind == "import":
            if u.start in verbatim:
                continue
            where = ("作り直した import の中" if any(b in kept for b, _a in _import_bindings(u.node))
                     else "写さなかった import の中")
        elif u.kind == "future":
            continue  # 行ごと写す
        else:
            where = "__all__ の中(割り先ごとに作り直した)"
        out.append(f"注 行 {line}: `{tk.string}` — {where}")
    return out


def _existing_bindings(text: str, d_mod: str, ix: Index) -> dict[str, tuple[str, str | None]]:
    pkg = d_mod.rpartition(".")[0]
    out: dict[str, tuple[str, str | None]] = {}
    for st in parse(text).body:
        if isinstance(st, (ast.Import, ast.ImportFrom)) and not (isinstance(st, ast.ImportFrom) and st.module == "__future__"):
            for b, a in _import_bindings(st):
                out[b] = _import_target(st, a, pkg, ix)
    return out


def _append_to_existing(text: str, d: str, imp_lines: list[str], d_all: list[str], body_parts: list[str],
                        src_future: set[str]) -> str:
    tree = parse(text)
    t = Text(text)
    have = {a.name for s in tree.body if isinstance(s, ast.ImportFrom) and s.module == "__future__" for a in s.names}
    if src_future - have:
        raise SplitRefused(f"既に在る割り先 {d} に from __future__ import {sorted(src_future - have)} が無い=注釈の意味が変わる")
    if "annotations" in have and "annotations" not in src_future:  # 〔検収 低-3〕逆向き=元の注釈は読む時に評価していた
        raise SplitRefused(f"既に在る割り先 {d} は from __future__ import annotations を持つが、元は持たない=注釈の意味が変わる")
    edits: list[Edit] = []
    if imp_lines:
        last_imp = [s for s in tree.body if isinstance(s, (ast.Import, ast.ImportFrom))]
        if not last_imp:
            raise SplitRefused(f"既に在る割り先 {d} に import の文が無い=差し込む所が決まらない")
        e_line = last_imp[-1].end_lineno
        pos = t.starts[e_line] if e_line < len(t.starts) else len(text)
        edits.append(Edit(pos, pos, "".join(imp_lines), "import", "<module>", "割る段の import"))
    alln = next((s for s in tree.body if isinstance(s, ast.Assign) and any(
        isinstance(x, ast.Name) and x.id == "__all__" for x in s.targets)), None) if d_all else None
    if d_all and alln is None:
        # 前の本が作った割り先(元のファイルの __all__ にその割り先の名が無かった)=import の後ろに、足す名だけの __all__ を作る
        anchor = [s for s in tree.body if isinstance(s, (ast.Import, ast.ImportFrom))]
        if not anchor:
            raise SplitRefused(f"既に在る割り先 {d} に import の文も __all__ も無い=__all__ を置く所が決まらない")
        e_line = anchor[-1].end_lineno
        pos = t.starts[e_line] if e_line < len(t.starts) else len(text)
        edits.append(Edit(pos, pos, "\n__all__ = [\n" + _render_all(d_all) + "\n]\n", "all", "__all__", "割る段の __all__ を作った"))
    elif d_all:
        if not isinstance(alln.value, ast.List):
            raise SplitRefused(f"既に在る割り先 {d} の __all__ が並び(リスト)の形でない=名を足せない")
        close_line = alln.value.end_lineno
        line = t.line(close_line)
        if line.strip() != "]":
            raise SplitRefused(f"既に在る割り先 {d} の __all__ の閉じ括弧が 1 行でない=名を足せない")
        indent = re.match(r"\s*", t.line(alln.value.elts[-1].lineno)).group(0) if alln.value.elts else "    "
        last_line = t.line(alln.value.elts[-1].end_lineno) if alln.value.elts else ""
        if alln.value.elts and not last_line.rstrip().endswith(","):
            raise SplitRefused(f"既に在る割り先 {d} の __all__ の最後の要素に「,」が無い=名を足せない")
        pos = t.starts[close_line - 1]
        edits.append(Edit(pos, pos, _render_all(d_all, indent) + "\n", "all", "__all__", "割る段の名"))
    body = "".join(body_parts).lstrip("\n")
    edits.append(Edit(len(text), len(text), ("" if text.endswith("\n") else "\n") + "\n\n" + body.rstrip("\n") + "\n",
                      "body", "<module>", "割る段の文"))
    return apply_edits(text, edits)


# ------------------------------------------------------------------ 計画の本体
def make_split_plan(tree: Tree, mapdoc: MapDoc, old: str, *, frozen: G.Frozen | None = None,
                    ledger_text: str | None = None, strict: bool = True, check_order: bool = True,
                    compose_fn=None, contracts_spec=None, order: tuple[str, ...] | None = None) -> SplitPlan:
    """割る行 ``old`` を当てた後の木と報告(守りを通らなければ :class:`SplitStopped`・表せなければ :class:`SplitRefused`)。
    ``strict`` が偽なら「手で直す」読みを残したまま計画を返す(書かない実行の報告用)。``compose_fn`` は試験の差し替えの口。
    ``contracts_spec``(``contracts.toml`` の :class:`pkgmove.contracts.Spec`)を渡すと、割る前と後の import の決まりを比べる守り
    (〔検収 高-1〕)も回す(``cli.py split`` は常に渡す)。``order`` は割る段の順(既定は :data:`pkgmove.table.SPLIT_ORDER`=
    〔割る段 6・E9〕``cli.py split --map`` は表から読んだ順を渡す)。"""
    order = SPLIT_ORDER if order is None else tuple(order)
    by = mapdoc.by_old()
    row = by.get(old)
    if row is None or row.kind != "split":
        raise SplitRefused(f"割る行でない: {old}")
    if not row.names_complete:
        raise SplitRefused(f"割る行 {old} の名の表が揃っていない(全ファイルの表 §4)")
    if check_order:
        if old not in order:
            raise SplitRefused(f"割る段の順に無い行: {old}")
        nxt = next_split(tree, mapdoc, order)
        if is_done(tree, row):
            raise SplitRefused(f"当たっている(済んだ)割る行: {old}")
        if nxt != old:
            raise SplitRefused(f"割る段の順が違う: 次に当てる行は {nxt}・当てようとした行は {old}(段を飛ばさない)")
    src_rel = source_rel(tree, row)
    if src_rel is None:
        raise SplitRefused(f"割る行 {old} の元のファイルが木に無い")
    ix = Index(tree)
    plan = SplitPlan(row=row, src_rel=src_rel, in_place=(src_rel == row.new), before=tree, after=tree.copy())
    texts = (compose_fn or compose)(tree, row, src_rel, ix, plan)
    src_mod = mod_of(src_rel)
    for d, s in texts.items():
        plan.after.files[SRC_PREFIX + d] = s
    # 元のファイル
    src_p = SRC_PREFIX + src_rel
    fw = SPLIT_FORWARDERS.get(row.old)
    if fw is not None:  # 〔割る段 5b・E2〕消さずに決まった型の転送で書き直す(親の裁定 Q6 の (a)・Q7)
        if plan.in_place or src_rel != row.old:
            raise SplitRefused(f"入口の転送の行 {row.old} の元のファイルが元の置き場に無い")
        plan.after.files[src_p] = forwarder_text(row.old, fw)
        plan.forwarder = src_p
    elif not plan.in_place:
        if src_rel.endswith("__init__.py"):
            d0 = src_p.rsplit("/", 1)[0] + "/"
            if any(x.startswith(d0) and x != src_p for x in [*plan.after.files, *plan.after.blobs]):
                plan.after.files[src_p] = ""
                plan.emptied_heads.append(src_p)
            else:
                del plan.after.files[src_p]
                plan.deleted.append(src_p)
        else:
            del plan.after.files[src_p]
            plan.deleted.append(src_p)
    # 古いディレクトリに 0 バイトの頭だけが残れば消す(親の裁定 Q14)
    d = src_p.rsplit("/", 1)[0]
    while d + "/" != SRC_PREFIX and d.startswith(SRC_PREFIX):
        h = d + "/__init__.py"
        rest = [x for x in [*plan.after.files, *plan.after.blobs] if x.startswith(d + "/") and x != h]
        if h in plan.after.files and plan.after.files[h] == "" and not rest:
            del plan.after.files[h]
            plan.deleted.append(h)
            if h in plan.emptied_heads:
                plan.emptied_heads.remove(h)
            d = d.rsplit("/", 1)[0]
            continue
        break
    # 新しいディレクトリの頭
    for dd in texts:
        parts = dd.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            h = SRC_PREFIX + "/".join(parts[:i]) + "/__init__.py"
            if h not in plan.after.files:
                plan.after.files[h] = ""
                plan.created_heads.append(h)
    # 読み手の書き換え
    namemap = {src_mod: {n: mod_of(dd) for n, dd in row.names}}
    reexp: dict[str, str] = {}
    for dd in [row.new, *[x for x in plan.kept_bindings if x != row.new]]:  # 主な割り先を先に
        for b in sorted(plan.kept_bindings.get(dd, ())):
            reexp.setdefault(b, mod_of(dd))
    ctx = Ctx(index=ix, modmap={}, heads_changed=set(),
              frozen_tokens=frozenset(frozen.id_tokens()) if frozen is not None else frozenset(),
              namemap=namemap, split_main={src_mod: mod_of(row.new)}, split_reexports={src_mod: reexp},
              split_entry={src_mod: mod_of(SPLIT_ENTRIES[row.old])} if row.old in SPLIT_ENTRIES else {},
              split_forwarders=frozenset({src_mod}) if fw is not None else frozenset())
    # 〔割る段 6・E8〕道の文字列の割り先の宣言(この割る行の分)と、宣言も名の手がかりも無い道を手で直す一覧へ出す割るファイル
    # (割り先が 2 つ以上の行)
    pdecls = [d for d in SPLIT_PATH_DESTS if d.old == row.old]
    rules = ST.PathRules(relmap={src_rel: row.new} if not plan.in_place else {}, names={src_rel: dict(row.names)},
                         declared={(d.file, d.symbol): d.dest for d in pdecls},
                         nameless_manual=frozenset({src_rel}) if len(plan.dests) >= 2 else frozenset())
    from pkgmove.move import locate
    src_tables = {}
    for f, sym, _why in AL.SRC_TABLES:
        src_tables.setdefault(locate(tree, mapdoc, f), {})[sym] = "exact"
    class_path = locate(tree, mapdoc, AL.CLASS_IDS_TABLE[0])
    lp_path = locate(tree, mapdoc, AL.LEDGER_PATHS_TABLE[0])
    path_errs = _path_decl_errors(tree, pdecls, set(plan.dests))
    if path_errs:
        raise SplitStopped([f"道の文字列の割り先の宣言の守り: {e}" for e in path_errs])
    skip = {src_p, *[SRC_PREFIX + d for d in texts]}
    # 〔割る段 5b・E5〕この割る行の別名の割り先の宣言(使ったものを数え、使われなかった宣言と守りに当たった宣言で止める)
    decls = [d for d in SPLIT_ALIAS_DESTS if d.old == row.old]
    alias_errs: list[str] = []
    alias_used: set[tuple[str, str]] = set()
    for p in sorted(plan.after.files):
        if is_self(p):
            continue
        text = plan.after.files[p]
        if p in skip and p not in [SRC_PREFIX + d for d in texts]:
            continue
        try:
            t = parse(text)
        except SyntaxError as e:
            plan.warnings.append(f"{p}: 構文の誤りで読めない({e.msg})=触らない")
            continue
        syms = symbols_of(text)
        area = area_of(p)
        excluded = is_split_excluded(p)  # 〔割る段 5b・E4〕範囲の外: 書き換えを数えるだけ(当てない・統計と手で直す一覧に入れない)
        stt = IM.ImportStats() if excluded else plan.import_stats.setdefault(area, IM.ImportStats())
        n0 = stt.statements
        ctx.alias_dests = IM.alias_dests(ctx, text, p)
        mine = [d for d in decls if d.file == p]
        if mine and not excluded:
            over, errs, notes = _declared_alias_dests(ctx, p, text, mine, set(plan.dests), src_mod, plan.after)
            alias_errs += errs
            plan.alias_declared += notes
            alias_used |= {(p, a) for a in over}
            ctx.alias_dests.update({a: m for a, m in over.items() if m})
        edits = IM.rewrite_file(ctx, p, text, t, syms, stt)
        if stt.statements > n0 and not excluded:
            plan.import_files[area] += 1
        # 道の文字列(src は許可の一覧の表・tests と tools と docs の記録の道具は割るファイルを指す文字列)
        probe = None
        if p in src_tables:
            edits += ST.rewrite_file_strings(ctx, rules, p, text, t, syms, src_tables[p], plan.str_stats)
        elif area in ("tests", "tools") and p not in [SRC_PREFIX + d for d in texts]:  # docs の記録の道具は import だけ(親の決定 7)
            probe = SplitPlan(row=row, src_rel=src_rel, in_place=plan.in_place, before=tree, after=tree) if excluded else plan
            edits += _scan_strings(ctx, rules, p, text, t, syms, probe, src_rel, src_mod)
        if excluded:
            n_man = sum(1 for w in stt.warnings if IM.MANUAL in w)
            if probe is not None and probe is not plan:
                # 〔検収の後の直し 3〕文字列の中の手で直す所(E8 の名の無い道・名の無い点の道ほか)も数える。E8 の前は名の無い道を
                # 書き換えに数えたので報告に出た=範囲の外でも「在る」ことは報告に残す
                n_man += sum(1 for x in probe.str_stats.skipped if IM.MANUAL in x.get("reason", ""))
            if edits or n_man:
                plan.excluded_sites.append(f"{p}: 書き換え {len(edits)}・手で直す {n_man}(範囲の外=書き換えない)")
            continue
        if edits:
            new = apply_edits(text, edits)
            if new != text:
                plan.after.files[p] = new
                plan.changed[p] = edits
    for d in decls:
        if (d.file, d.alias) not in alias_used:
            alias_errs.append(f"{d.file}: 別名 {d.alias} → {d.dest}: 宣言が使われなかった(ファイルが木に無いか範囲の外・"
                              f"別名を結ぶ import が無い)")
    if alias_errs:
        raise SplitStopped([f"別名の割り先の宣言の守り: {e}" for e in alias_errs])
    # 〔割る段 6・E8〕道の文字列の割り先の宣言: 使われなかった宣言は止める(ファイルや記号が範囲の外・名の手がかりの無い道が無い)
    unused = [d for d in pdecls if not plan.str_stats.declared_used.get((d.file, d.symbol))]
    if unused:
        raise SplitStopped([f"道の文字列の割り先の宣言の守り: {d.file}::{d.symbol} → {d.dest}: 宣言が使われなかった(記号の中に"
                            f"名の手がかりの無い割るファイルの道が無いか、書き換えの範囲の外)" for d in unused])
    plan.path_declared = [f"{d.file}::{d.symbol} → {d.dest}(道 {plan.str_stats.declared_used[(d.file, d.symbol)]})"
                          for d in pdecls]
    for area, stt in plan.import_stats.items():
        for w in stt.warnings:
            if IM.MANUAL in w:
                plan.manual.append(w)
            else:
                plan.warnings.append(w)
    # 〔割る段 5b・E3〕文字列の中の手で直す所(名の無い点の道・コードの文字列の import)も「手で直す一覧」へ(黙って落とさない)
    for s in plan.str_stats.skipped:
        if IM.MANUAL in s.get("reason", ""):
            plan.manual.append(f"{s['file']}::{s['symbol']}: {s['reason']}")
    # 固定の表の鍵(クラスの単位)
    if frozen is not None:
        quals = {q: None for q, _n in G._class_defs(parse(tree.files[src_p]))}
        dest_of_top = {n: mod_of(dd) for n, dd in row.names}
        try:
            keymap = CI.split_keymap(quals, src_mod, dest_of_top)
            new2, cres = CI.rewrite(plan.after.files[class_path], keymap, frozen.class_qual, keyfn=CI.split_table,
                                    check=CI.check_split_keys)
        except CI.ClassIdError as e:
            raise SplitStopped([f"固定の表の鍵の守り: {e}"]) from e
        plan.class_keys = cres.rewritten
        if new2 != plan.after.files[class_path]:
            plan.after.files[class_path] = new2
            plan.changed.setdefault(class_path, []).append(Edit(0, 0, "", "class_key", "CLASS_IDS", f"鍵 {cres.rewritten}"))
    # つなぎの台帳の道の表(主な割り先 → 元の道)。〔割る段 6・E7〕宣言の入る 2 つ目以降の新しい割り先 → 元の台帳の道を前向きの表へ
    if lp_path in plan.after.files:
        lp_text = plan.after.files[lp_path]
        moves = {} if plan.in_place else {src_p: SRC_PREFIX + row.new}
        try:
            split_add = ledger_split_rows(plan, lp_text)
            new3, _nadd = LPT.rewrite(lp_text, moves, split_add)
        except (LPT.LedgerPathsError, CI.ClassIdError) as e:
            raise SplitStopped([f"台帳の道の対応の表: {e}"]) from e
        plan.ledger_paths_added = len(moves)
        plan.ledger_paths_split = [f"{k} → {v}" for k, v in split_add.items()]
        if new3 != lp_text:
            plan.after.files[lp_path] = new3
            plan.changed.setdefault(lp_path, []).append(
                Edit(0, 0, "", "ledger_path", LPT.MAIN_TABLE, f"行 {len(moves)}・前向きの表 {len(split_add)}"))
    if strict and plan.manual:
        raise SplitRefused("属性で読み割り先が 2 つ以上になる読み(手で直す一覧)があるので当てない: "
                           + "; ".join(plan.manual[:20]))
    guards(plan, mapdoc, frozen, ledger_text, class_path, lp_path, ix=ix, spec=contracts_spec)
    # 〔検収の後の直し 2・親の裁定〕厳しい当てでは、差し替えの届く先の守りが見られなかった差し替えが 1 つでも在れば断る(手で直す一覧と
    # 同じ扱い・宣言して通す口は作らない)。strict=False(--through の報告)は一覧に出すだけ
    if strict and plan.patch_unseen:
        raise SplitRefused("差し替えの届く先の守りが見られなかった差し替えがあるので当てない(見られる形に直す): "
                           + "; ".join(plan.patch_unseen[:20]))
    return plan


def _scan_strings(ctx: Ctx, rules: ST.PathRules, p: str, text: str, t: ast.Module, syms: dict[int, str],
                  plan: SplitPlan, src_rel: str, src_mod: str) -> list[Edit]:
    """tests・tools・docs の記録の道具の文字列のうち、割るファイルの道か名を指すものの (ファイル, 記号) を許可の一覧として書き換える。"""
    hit_syms: set[str] = set()
    pat_slash = re.compile(r"(?<![\w./\\-])((?:src/)?shibuya/)?" + re.escape(src_rel) + r"(?![\w/])")
    pat_dot = re.compile(r"(?<![\w.])" + re.escape(src_mod) + r"(?![\w])")
    ds = set()
    from pkgmove.model import docstrings_of
    ds = docstrings_of(text)
    for n in ast.walk(t):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in ds:
            # 〔割る段 5b の G0 の直し 高-2〕コードの文字列の ``from <包み> import <葉>`` の形も拾う(前は点の道と斜線の道だけ)
            if pat_slash.search(n.value) or pat_dot.search(n.value) or ST.code_import_hits(ctx, n.value):
                s = syms.get(id(n), "")
                if (p, s) not in STRING_EXCLUDE:
                    hit_syms.add(s)
    # / の結合(SRC / "engine" / "x.py")は単独の定数に道が入らない=記号ごとに見る。〔割る段 6・E8〕手で直す一覧に出る連鎖(宣言も名の
    # 手がかりも無い道)の記号も拾う。前はほかの記号に当たりがあるファイルで連鎖の記号を見なかった(書き換えも一覧も無く残った)ので、
    # 当たりの有無に依らず足す
    probe = ST.StrStats()
    edits0 = ST.chain_edits(Text(text), t, rules, syms, None, p, probe)
    hit_syms |= {e.symbol for e in edits0 if (p, e.symbol) not in STRING_EXCLUDE}
    hit_syms |= {s["symbol"] for s in probe.skipped
                 if s.get("kind") == ST.CHAIN_NAMELESS and (p, s["symbol"]) not in STRING_EXCLUDE}
    if not hit_syms:
        return []
    rule_of = {s: "paths" for s in hit_syms}
    edits = ST.rewrite_file_strings(ctx, rules, p, text, t, syms, rule_of, plan.str_stats)
    for e in edits:
        plan.string_sites.append(f"{p}::{e.symbol}")
    return edits


# ------------------------------------------------------------------ 守り
def _stmt_seq(text: str, *, skip_doc: bool = True) -> list[str]:
    """頂上の文の dump の並び(docstring・import・``__all__`` を除く)。"""
    out: list[str] = []
    for i, st in enumerate(parse(text).body):
        if i == 0 and skip_doc and isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) \
                and isinstance(st.value.value, str):
            continue
        if isinstance(st, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(st, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "__all__" for x in st.targets):
            continue
        out.append(_dump(st))
    return out


def _stmt_dumps(text: str, *, skip_doc: bool = True) -> Counter:
    return Counter(_stmt_seq(text, skip_doc=skip_doc))


def _top_binding(text: str, d: str, name: str, ix: Index) -> tuple[str, str | None] | None:
    """割り先 ``d`` の頂上で ``name`` を結ぶ物: 頂上の定義なら (割り先のモジュール, 名)・import なら出どころ・無ければ ``None``。"""
    tree = parse(text)
    d_mod = mod_of(d)
    if name in top_names(text):
        return d_mod, name
    pkg = d_mod if d.endswith("__init__.py") else d_mod.rpartition(".")[0]
    got = None
    for st in tree.body:
        if isinstance(st, (ast.Import, ast.ImportFrom)) and not (isinstance(st, ast.ImportFrom) and st.module == "__future__"):
            for b, a in _import_bindings(st):
                if b == name:
                    got = _import_target(st, a, pkg, ix)
    return got


def _consts(node: ast.AST) -> Counter:
    return Counter(n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)))


def _scan_decls(text: str, path: str) -> list:
    try:
        from shibuya.validation.static import bridging_scan as BS  # src の走査の関数(純な関数だけを呼ぶ)
    except Exception as e:  # noqa: BLE001
        raise SplitRefused(f"つなぎの宣言の走査を読めない(PYTHONPATH に木の src を置く): {e}") from e
    return BS.scan_source(text, path)


def _decl_keys(text: str, path: str, led) -> Counter:
    """宣言の (台帳の道で作った ``declared_in``, 項の数) の多重集合。``led`` は今の道 → 台帳の道(〔割る段 6・E7〕1 対 1 の表 →
    前向きの表 → そのまま)。"""
    out: Counter = Counter()
    for d in _scan_decls(text, path):
        suffix = d.declared_in.split("#", 1)[1]
        out[(led(path) + "#" + suffix, d.items)] += 1
    return out


def _lp_tables(tree: Tree, lp_path: str) -> tuple[dict[str, str], dict[str, str] | None]:
    """〔割る段 6・E7〕木の台帳の道の表(1 対 1 の表, 前向きの表か ``None``)。表のファイルが無ければ ``({}, None)``。"""
    if lp_path not in tree.files:
        return {}, None
    text = tree.files[lp_path]
    return LPT.table_of(text), LPT.split_table_of(text)


def ledger_split_rows(plan: SplitPlan, lp_text: str) -> dict[str, str]:
    """〔割る段 6・E7・親の裁定 Q1 の (ii)〕前向きの表に足す行: つなぎの台帳の宣言が 1 つ以上入る、2 つ目以降の新しい割り先の今の道
    → 元のファイルの台帳の道(1 対 1 の表 → 前向きの表 → そのまま、で引く)。宣言の入らない割り先の行は書かない(条件 ③)。"""
    main = LPT.table_of(lp_text)
    split = LPT.split_table_of(lp_text)
    led = LPT.ledger_of(main, split, SRC_PREFIX + plan.src_rel)
    out: dict[str, str] = {}
    for d, kind in plan.dests.items():
        if d == plan.row.new or kind != "new":
            continue
        p = SRC_PREFIX + d
        if _scan_decls(plan.after.files[p], p):
            out[p] = led
    return out


def _path_decl_errors(tree: Tree, decls: list["PathDest"], dests: set[str]) -> list[str]:
    """〔割る段 6・E8〕道の文字列の割り先の宣言の守り(当てる前): ファイルが木に在る・記号がそのファイルの記号に在る・宣言の割り先が
    その割る行の割り先・記号が書き換えの範囲の中・同じ記号に宣言が 2 つ無い。使われなかった宣言は当てた後に止める。"""
    errs: list[str] = []
    seen: set[tuple[str, str]] = set()
    for d in decls:
        where = f"{d.file}::{d.symbol} → {d.dest}"
        if (d.file, d.symbol) in seen:
            errs.append(f"{where}: 同じ記号に宣言が 2 つある")
        seen.add((d.file, d.symbol))
        text = tree.files.get(d.file)
        if text is None:
            errs.append(f"{where}: ファイルが木に無い")
            continue
        try:
            syms = set(symbols_of(text).values())
        except SyntaxError:
            syms = set()
        if d.symbol not in syms:
            errs.append(f"{where}: 記号がファイルに無い")
        if d.dest not in dests:
            errs.append(f"{where}: 宣言の割り先がこの割る行の割り先でない(割り先 {sorted(dests)})")
        if (d.file, d.symbol) in STRING_EXCLUDE or is_split_excluded(d.file) or is_self(d.file):
            errs.append(f"{where}: 記号が書き換えの範囲の外(STRING_EXCLUDE・SPLIT_EXCLUDE_PATHS・道具の自分)")
    return errs


def guards(plan: SplitPlan, mapdoc: MapDoc, frozen: G.Frozen | None, ledger_text: str | None, class_path: str,
           lp_path: str, *, ix: Index | None = None, spec=None) -> None:
    errs: list[str] = []
    row = plan.row
    before, after = plan.before, plan.after
    src_p = SRC_PREFIX + plan.src_rel
    src_text = before.files[src_p]
    src_tree = parse(src_text)
    rewrites = dict(row.rewrites)
    dests = list(plan.dests)
    # ① 文の多重集合と、割り先ごとの順(〔検収 中-3〕足した文の並び=元の文の並びからその割り先の文だけを抜いた並び)
    want: Counter = Counter()
    want_seq: dict[str, list[str]] = {}
    unit_dest: list[tuple[Unit, str]] = []
    nm = row.name_map
    units = units_of(src_text, plan.src_rel)
    defined = {n: nm[n] for u in units if u.kind == "named" for n in u.names}
    for u in units:
        if u.kind not in ("named", "other"):
            continue
        dest = defined[u.names[0]] if u.kind == "named" else None
        if dest is None:
            ds = {defined[n] for n in names_used(u.node) if n in defined}
            dest = ds.pop() if len(ds) == 1 else row.new
        unit_dest.append((u, dest))
        alias = rewrites.get(dest) if plan.rewrites_applied.get(dest) else None
        key = _strip_alias_dump(u.node, alias) if alias else _dump(u.node)
        want[(dest, key)] += 1
        want_seq.setdefault(dest, []).append(key)
    got: Counter = Counter()
    order_bad: list[str] = []
    for d in dests:
        a_seq = _stmt_seq(after.files[SRC_PREFIX + d])
        if plan.dests[d] == "existing":
            b_seq = _stmt_seq(before.files[SRC_PREFIX + d])
            if a_seq[: len(b_seq)] != b_seq:
                order_bad.append(f"{d}(在る文の並びが変わった)")
            a_seq = a_seq[len(b_seq):]
        for k in a_seq:
            got[(d, k)] += 1
        if a_seq != want_seq.get(d, []):
            order_bad.append(d)
    if want != got:
        miss = sum((want - got).values())
        extra = sum((got - want).values())
        errs.append(f"① 文: 元の頂上の文と割り先に足した文が違う(足りない {miss}・余る {extra})")
    elif order_bad:
        errs.append(f"① 文: 割り先の文の順が元の順と違う {order_bad}")
    plan.guards["stmts"] = "同じ" if want == got and not order_bad else "違う"
    # ② 定数の多重集合(モジュールの docstring と文の中)
    c_before: Counter = Counter()
    for i, st in enumerate(src_tree.body):
        if isinstance(st, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(st, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "__all__" for x in st.targets):
            continue
        c_before += _consts(st)
    c_after: Counter = Counter()
    for d in dests:
        a_tree = parse(after.files[SRC_PREFIX + d])
        b_cnt: Counter = Counter()
        if plan.dests[d] == "existing":
            for st in parse(before.files[SRC_PREFIX + d]).body:
                if not isinstance(st, (ast.Import, ast.ImportFrom)) and not (
                        isinstance(st, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "__all__" for x in st.targets)):
                    b_cnt += _consts(st)
        a_cnt = Counter()
        for i, st in enumerate(a_tree.body):
            if isinstance(st, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(st, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "__all__" for x in st.targets):
                continue
            if i == 0 and plan.dests[d] == "new" and d != row.new and isinstance(st, ast.Expr):
                continue  # 2 つ目以降の新しい割り先の決まった型の docstring
            a_cnt += _consts(st)
        c_after += a_cnt - b_cnt
    if c_before != c_after:
        d1 = sorted(map(repr, (c_before - c_after).elements()))[:3]
        d2 = sorted(map(repr, (c_after - c_before).elements()))[:3]
        errs.append(f"② 定数: 元と割り先で文字列とバイト列の定数が違う(元だけ {d1}・割り先だけ {d2})")
    plan.guards["constants"] = "同じ" if c_before == c_after else "違う"
    # ③ 名の結び
    base = unbound_names(src_text)
    bad: dict[str, list[str]] = {}
    for d in dests:
        extra = sorted(unbound_names(after.files[SRC_PREFIX + d]) - base
                       - (unbound_names(before.files[SRC_PREFIX + d]) if plan.dests[d] == "existing" else set()))
        if extra:
            bad[d] = extra
    if bad:
        errs.append(f"③ 名の結び: 割り先で結ばれない名が増えた {bad}")
    # ③ の 2〔検収 中-1〕元の頂上で結ぶ名(組み込みの名を覆う名も)を読む文は、割り先でも同じ物に結ばれる
    ix = ix or Index(before)
    src_mod = mod_of(plan.src_rel)
    src_pkg = src_mod if plan.src_rel.endswith("__init__.py") else src_mod.rpartition(".")[0]
    src_bind: dict[str, tuple[str, str | None]] = {}
    for st in src_tree.body:
        if isinstance(st, (ast.Import, ast.ImportFrom)) and not (isinstance(st, ast.ImportFrom) and st.module == "__future__"):
            for b, a in _import_bindings(st):
                src_bind[b] = _import_target(st, a, src_pkg, ix)
    for n, dd in defined.items():
        src_bind[n] = (mod_of(dd), n)
    keep = frozenset(src_bind)
    unbound_same: dict[str, list[str]] = {}
    for d in dests:
        uses: set[str] = set()
        for u, ud in unit_dest:
            if ud == d:
                uses |= free_names(u, keep)
        alias = rewrites.get(d) if plan.rewrites_applied.get(d) else None
        a_text = after.files[SRC_PREFIX + d]
        for n in sorted(uses & keep):
            if n == alias:
                continue
            got_b = _top_binding(a_text, d, n, ix)
            if got_b != src_bind[n]:
                unbound_same.setdefault(d, []).append(f"{n}(元 {src_bind[n]}・割り先 {got_b})")
    if unbound_same:
        errs.append(f"③ 名の結び: 元の頂上で結ぶ名が、割り先で同じ物に結ばれない {unbound_same}")
    plan.guards["bindings"] = "同じ" if not bad and not unbound_same else "違う"
    # ④ つなぎの宣言(〔割る段 6・E7〕台帳の道は 1 対 1 の表 → 前向きの表 → そのまま、で引く。比べの厳しさは前と同じ=台帳の道で
    # 数える宣言の多重集合が同じ。2 つ目以降の新しい割り先は「宣言がある ⇔ 前向きの表に行がある」)
    mb, sb = _lp_tables(before, lp_path)
    ma, sa = _lp_tables(after, lp_path)
    led_b = lambda q: LPT.ledger_of(mb, sb, q)  # noqa: E731
    led_a = lambda q: LPT.ledger_of(ma, sa, q)  # noqa: E731
    e_decl: list[str] = []
    k_before = _decl_keys(src_text, src_p, led_b)
    k_after: Counter = Counter()
    for d in dests:
        p = SRC_PREFIX + d
        kb = _decl_keys(before.files[p], p, led_b) if plan.dests[d] == "existing" else Counter()
        ka = _decl_keys(after.files[p], p, led_a)
        k_before += kb
        k_after += ka
        second_new = d != row.new and plan.dests[d] == "new"
        in_split = sa is not None and p in sa
        if second_new and ka and not in_split:
            e_decl.append(f"④ 宣言: 2 つ目以降の割り先 {d} につなぎの台帳の宣言が入るが、台帳の道の前向きの表({LPT.SPLIT_TABLE})に"
                      f"行が無い(1 対 1 の表では表せない)")
        if second_new and not ka and in_split:
            e_decl.append(f"④ 宣言: 宣言の無い 2 つ目以降の割り先 {d} の行が前向きの表に在る(裁定 Q1 の条件 ③)")
        if d != row.new and plan.dests[d] == "existing" and (ka - kb):
            e_decl.append(f"④ 宣言: 既に在る割り先 {d} につなぎの台帳の宣言が入る(台帳の道が元のファイルと別=表せない)")
    if k_before != k_after:
        e_decl.append(f"④ 宣言: つなぎの台帳の宣言が元と割り先とで違う(元だけ {sorted(k_before - k_after)[:3]}・"
                  f"割り先だけ {sorted(k_after - k_before)[:3]})")
    if lp_path in after.files:  # 表の守り: 今の道は木に在る・2 つの表の両方に無い・前向きの表の今の道は宣言を持つ・台帳の行が届く
        exists = lambda q: q in after.files or q in after.blobs  # noqa: E731
        e_decl += [f"④ 台帳の道の表: {x}" for x in LPT.check(ma, exists, ledger_text, split=sa)]
        e_decl += [f"④ 台帳の道の表: 前向きの表の今の道 {k} に宣言が無い(裁定 Q1 の条件 ③)" for k in (sa or {})
               if k in after.files and not _scan_decls(after.files[k], k)]
    errs += e_decl
    plan.guards["declarations"] = "同じ" if not e_decl else "違う"
    # 段 4 の守り
    if frozen is not None:
        pre = G.check_names(before, frozen) + G.check_class_ids(before, frozen, class_path)
        if pre:
            raise SplitStopped(["割る前の木が凍結と既に違う: " + "; ".join(pre)])
        e1 = G.check_names(after, frozen)
        plan.guards["names_frozen"] = "同じ" if not e1 else "違う"
        e2 = G.check_class_ids(after, frozen, class_path)
        plan.guards["class_ids"] = "同じ" if not e2 else "違う"
        errs += e1 + e2
        kinds = frozen.shaped_kinds()
        skip_values = {plan.src_rel, row.new, SRC_PREFIX + plan.src_rel, SRC_PREFIX + row.new, *dests,
                       *[SRC_PREFIX + d for d in dests]}
        cb = G.shaped_counts(before, kinds, skip_values, class_path)
        ca = G.shaped_counts(after, kinds, skip_values, class_path)
        d3 = {k: (cb[k], ca[k]) for k in kinds if cb[k] != ca[k]}
        plan.guards["shaped_74"] = "同じ" if not d3 else f"違う {d3}"
        if d3:
            errs.append(f"道の形の名(74 種)の出てくる数が変わった: {d3}")
    skip_files = {src_p, *[SRC_PREFIX + d for d in dests], *plan.created_heads, *plan.deleted, *plan.emptied_heads}
    skip_files |= {p for p in before.files if is_self(p)}
    allowed = {(p, e.symbol) for p, es in plan.changed.items() for e in es if e.kind == "path"}
    # 〔割る段 6・E7〕前向きの表(LEDGER_PATHS_SPLIT)も台帳の道の表と同じく許可の一覧の記号
    table_sites = {(class_path, AL.CLASS_IDS_TABLE[1]), (lp_path, AL.LEDGER_PATHS_TABLE[1]), (lp_path, LPT.SPLIT_TABLE)}
    allowed |= table_sites
    allowed |= {(p, s) for p, s in (x.split("::", 1) for x in plan.string_sites)}
    e4 = G.check_outside(before, after, {}, allowed, skip_files | {p for p in before.files if p not in after.files},
                         frozen.id_tokens() if frozen is not None else set(), table_sites)
    plan.guards["outside_allowlist"] = "同じ" if not e4 else f"違う {len(e4)}"
    errs += e4
    e6 = G.check_bound_names(before, after, {}, skip_files | {p for p in before.files if p not in after.files}, {})
    plan.guards["import_names"] = "同じ" if not e6 else f"違う {len(e6)}"
    errs += e6
    e7 = G.check_head_all(after)
    plan.guards["head_all"] = "同じ" if not e7 else f"違う {len(e7)}"
    errs += e7
    # 〔割る段 5b・E2〕入口の転送: 決まった型そのもの(名を結ばない)・つなぎの宣言が無い・呼ぶ main が割り先の頂上に在る
    fw = SPLIT_FORWARDERS.get(row.old)
    if fw is not None:
        a_fw = after.files.get(src_p)
        e8 = forwarder_problems(a_fw, row.old, fw)
        if a_fw is not None and not e8 and _scan_decls(a_fw, src_p):
            e8.append("つなぎの台帳の宣言がある")
        if "main" not in top_names(after.files.get(SRC_PREFIX + fw, "")):
            e8.append(f"呼ぶ main が割り先 {fw} の頂上に無い")
        plan.guards["forwarder"] = "同じ" if not e8 else f"違う {len(e8)}"
        errs += [f"入口の転送 {src_p}: {x}" for x in e8]
    # 〔G2 の 5 本目の欠陥の後〕読み込みの時の import の新しい循環(既に在る割り先へ足す import が、その割り先を読むモジュールと循環する)
    cyc = new_import_cycles(before, after, mod_of(plan.src_rel), [d for d, k in plan.dests.items() if k == "new"])
    plan.guards["import_cycles"] = "同じ" if not cyc else f"違う {len(cyc)}"
    errs += [f"import の循環: {c}" for c in cyc]
    # 〔割る段 6・E5-b〕差し替えの届く先(割る前にその名を呼ぶ時に読んでいた関数の割り先の全部へ向いているか)
    e9 = patch_reach(plan)
    plan.guards["patch_reach"] = "同じ" if not e9 else f"違う {len(e9)}"
    errs += [f"差し替えの届く先の守り: {x}" for x in e9]
    if spec is not None:
        errs += _contract_guard(plan, mapdoc, spec)
    if errs:
        raise SplitStopped(errs)


def _contract_guard(plan: SplitPlan, mapdoc: MapDoc, spec) -> list[str]:
    """〔検収 高-1〕割る前の木と後の木で import の決まり(``contracts.toml`` から作る節)を比べ、言えなくなった単位・決まりと、
    古い決まりから外れた名が、宣言(``[[split_weakens]]``)のほかに増えたら止める(黙って弱めない)。"""
    from pkgmove import contracts as CT
    from pkgmove import move as MV

    try:
        stage = CT.stage_of(plan.before, mapdoc, spec)
        if not stage:
            raise CT.ContractsError(f"木の段が決まらない({stage!r})")
        _c0, r0 = CT.build(spec, mapdoc, plan.before, stage)
        _c1, r1 = CT.build(spec, mapdoc, plan.after, stage)
    except (CT.ContractsError, MV.Refused) as e:
        plan.guards["contracts"] = "違う(比べられない)"
        return [f"決まり: import の決まりを割る前と後で比べられない({e})"]
    w = CT.weakened(spec, plan.row.old, r0, r1)
    plan.contracts = {"stage": stage, **w}
    plan.warnings += [f"決まり: 宣言した弱まりが当たらない: {x}" for x in w["unused"]]
    if w["undeclared"]:
        plan.guards["contracts"] = f"違う {len(w['undeclared'])}"
        return [f"決まり: 割った後に import の決まりが黙って弱まる(宣言の外 {len(w['undeclared'])}・宣言は contracts.toml の "
                f"[[split_weakens]]): {w['undeclared'][:6]}"]
    plan.guards["contracts"] = f"宣言どおり {len(w['declared'])}" if w["declared"] else "同じ"
    return []


# ------------------------------------------------------------------ 守り: 頂上の import の循環(G2 の 5 本目の欠陥の後に足した)
def _is_type_checking(test: ast.expr) -> bool:
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING")


def _toplevel_imports(body: list[ast.stmt]) -> Iterable[ast.stmt]:
    """読み込みの時に走る import の文(頂上と、頂上の if・try・with の中。``if TYPE_CHECKING:`` の下と関数・クラスの中は除く)。"""
    for st in body:
        if isinstance(st, (ast.Import, ast.ImportFrom)):
            yield st
        elif isinstance(st, ast.If):
            if not _is_type_checking(st.test):
                yield from _toplevel_imports(st.body)
            yield from _toplevel_imports(st.orelse)
        elif isinstance(st, ast.Try):
            for part in (st.body, *[h.body for h in st.handlers], st.orelse, st.finalbody):
                yield from _toplevel_imports(part)
        elif isinstance(st, ast.With):
            yield from _toplevel_imports(st.body)


def import_graph(tree: Tree) -> dict[str, dict[str, list[str]]]:
    """src のモジュール → 読み込みの時に読むモジュール(``shibuya`` の中・親の包みの頭を含む)→ 読む文の場所(道:行 名)。"""
    from pkgmove.model import resolve_from

    mods: dict[str, tuple[str, bool]] = {}
    for p in tree.files:
        if p.startswith(SRC_PREFIX) and p.endswith(".py"):
            rel = p[len(SRC_PREFIX):]
            mods[mod_of(rel)] = (p, rel.endswith("__init__.py"))
    root = mod_of("__init__.py")
    out: dict[str, dict[str, list[str]]] = {}
    for m, (p, is_pkg) in mods.items():
        try:
            t = parse(tree.files[p])
        except SyntaxError:
            continue
        pkg = m if is_pkg else m.rpartition(".")[0]
        edges: dict[str, list[str]] = {}
        for st in _toplevel_imports(t.body):
            targets: list[tuple[str, str]] = []
            if isinstance(st, ast.Import):
                targets = [(a.name, a.name) for a in st.names]
            else:
                base = resolve_from(pkg, st) or ""
                for a in st.names:
                    sub = f"{base}.{a.name}"
                    targets.append((sub if sub in mods else base, a.name))
            for tgt, name in targets:
                if not (tgt == root or tgt.startswith(root + ".")):
                    continue
                parts = tgt.split(".")
                for i in range(1, len(parts) + 1):  # 親の包みの頭も読み込みの時に走る
                    t_mod = ".".join(parts[:i])
                    if t_mod in mods and t_mod != m:
                        edges.setdefault(t_mod, []).append(f"{p}:{st.lineno} {name}")
        out[m] = edges
    return out


def _sccs(graph: dict[str, dict[str, list[str]]]) -> list[set[str]]:
    """強く連結した成分のうち、2 つ以上のモジュールを持つもの(Tarjan・逐次でなく再帰を使わない形)。"""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on: set[str] = set()
    stack: list[str] = []
    out: list[set[str]] = []
    counter = 0
    for start in sorted(graph):
        if start in index:
            continue
        work = [(start, iter(sorted(graph.get(start, {}))))]
        index[start] = low[start] = counter
        counter += 1
        stack.append(start)
        on.add(start)
        while work:
            v, it = work[-1]
            nxt = next(it, None)
            if nxt is not None:
                if nxt not in graph:
                    continue
                if nxt not in index:
                    index[nxt] = low[nxt] = counter
                    counter += 1
                    stack.append(nxt)
                    on.add(nxt)
                    work.append((nxt, iter(sorted(graph.get(nxt, {})))))
                elif nxt in on:
                    low[v] = min(low[v], index[nxt])
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp: set[str] = set()
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.add(w)
                    if w == v:
                        break
                if len(comp) > 1:
                    out.append(comp)
    return out


def new_import_cycles(before: Tree, after: Tree, src_mod: str, new_dests: Iterable[str]) -> list[str]:
    """〔G2 の 5 本目の欠陥〕割った後の木で、読み込みの時の import が作る循環のうち、割る前に無かったもの(循環の中の新しい辺と
    読む文の場所)。新しい割り先(と元のモジュール)は元のモジュールの名に引き戻して、割る前の循環と比べる。"""
    back = {mod_of(d): src_mod for d in new_dests}
    g0, g1 = import_graph(before), import_graph(after)
    comp_of: dict[str, int] = {}
    for i, comp in enumerate(_sccs(g0)):
        for m in comp:
            comp_of[m] = i
    edges0 = {(a, b) for a, es in g0.items() for b in es}
    out: list[str] = []
    for comp in _sccs(g1):
        mapped = {back.get(m, m) for m in comp}
        ids = {comp_of.get(m) for m in mapped}
        if len(ids) == 1 and None not in ids:
            continue  # 割る前からの循環(同じモジュールの組)
        new = sorted(f"{a} -> {b}({', '.join(sorted(set(g1[a][b])))})" for a in comp for b in g1.get(a, {})
                     if b in comp and (back.get(a, a), back.get(b, b)) not in edges0)
        out.append(f"循環 {sorted(comp)} の新しい辺: {new}")
    return out


# ------------------------------------------------------------------ 守り: 差し替えの届く先(割る段 6・E5-b・親の裁定の追記)
#: 差し替えの呼び出し: ``<何か>.setattr``・``.delattr``・``.object``(``monkeypatch``・``mock.patch.object``)と組み込みの
#: ``setattr``・``delattr``。文字列の的は ``<何か>.setattr("pkg.mod.名", …)``・``.delattr("pkg.mod.名")``・``patch("pkg.mod.名")``。
_PATCH_ATTRS = frozenset({"setattr", "delattr", "object"})
_PATCH_FUNCS = frozenset({"setattr", "delattr"})
_PATCH_STR = frozenset({"setattr", "delattr", "patch"})


@dataclass(frozen=True)
class _Patch:
    """差し替え 1 か所: ファイル・関数(記号。コードの文字列の中は「記号(コードの文字列)」)・名・行・向くモジュール・形。"""

    file: str
    group: str
    name: str
    line: int
    module: str
    form: str
    #: 〔検収の後の直し 1〕別名を通す差し替えなら、その有効範囲で別名を結ぶ import の行(手で直す一覧の行と突き合わせる)。
    binds: tuple[int, ...] = ()
    #: 〔割る段 6・E5-c〕別名を通す差し替えなら、その別名(素で使ってよい別名の宣言と突き合わせる)。
    alias: str = ""


def _dotted_name(e: ast.AST) -> str | None:
    parts: list[str] = []
    while isinstance(e, ast.Attribute):
        parts.append(e.attr)
        e = e.value
    if not isinstance(e, ast.Name):
        return None
    parts.append(e.id)
    return ".".join(reversed(parts))


def _module_dict(e: ast.AST) -> bool:
    """``vars(X)`` か ``X.__dict__``(モジュールの名の辞書を通す書き換え)。"""
    return (isinstance(e, ast.Call) and isinstance(e.func, ast.Name) and e.func.id == "vars") or (
        isinstance(e, ast.Attribute) and e.attr == "__dict__")


def _module_bindings(tree: ast.AST, syms: dict[int, str], pkg: str,
                     lines: dict[str, dict[str, set[int]]] | None = None) -> dict[str, dict[str, set[str]]]:
    """記号 → 名 → import が結ぶモジュールの名の候補(``from P import m [as X]`` は ``P.m``・``import M as X`` は ``M``)。
    モジュールかどうかは呼ぶ側が見張るモジュールの集合と比べて決める(名の import は見張るモジュールに当たらない)。``lines`` を
    渡せば、記号 → 名 → その名を結ぶ import の文の行も入れる(〔検収の後の直し 1〕手で直す一覧と突き合わせる)。"""
    out: dict[str, dict[str, set[str]]] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            m = resolve_from(pkg, n) if n.level else n.module
            if not m:
                continue
            for a in n.names:
                out.setdefault(syms.get(id(n), "<module>"), {}).setdefault(a.asname or a.name, set()).add(f"{m}.{a.name}")
                if lines is not None:
                    lines.setdefault(syms.get(id(n), "<module>"), {}).setdefault(a.asname or a.name, set()).add(n.lineno)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.asname:
                    out.setdefault(syms.get(id(n), "<module>"), {}).setdefault(a.asname, set()).add(a.name)
                    if lines is not None:
                        lines.setdefault(syms.get(id(n), "<module>"), {}).setdefault(a.asname, set()).add(n.lineno)
    return out


def _collect_patches(text: str, path: str, watched: set[str], *, code_of: str | None = None,
                     base_line: int = 0) -> tuple[list[_Patch], list[str]]:
    """ファイル(``code_of`` を渡せば、その記号の中のコードの文字列)で、``watched`` のモジュールの属性を差し替える所と、見られなかった
    所(動的な名・的を組み立てる形・別名が 2 つのモジュールに結ばれる形)。コードの文字列(子のプロセスへ渡す台本)の中も同じ形で見る。"""
    try:
        tree = ast.parse(text) if code_of is not None else parse(text)
    except SyntaxError:
        return [], []
    syms = {} if code_of is not None else symbols_of(text)
    docs = frozenset() if code_of is not None else docstrings_of(text)
    own = mod_of(path[len(SRC_PREFIX):]) if path.startswith(SRC_PREFIX) and code_of is None else ""
    pkg = own if path.endswith("/__init__.py") else own.rpartition(".")[0]
    blines: dict[str, dict[str, set[int]]] = {}
    binds = _module_bindings(tree, syms, pkg, blines)
    sites: list[_Patch] = []
    unseen: list[str] = []
    tag = "(コードの文字列)" if code_of is not None else ""

    def group(n: ast.AST) -> str:
        return f"{code_of}(コードの文字列)" if code_of is not None else syms.get(id(n), "<module>")

    def bound(name: str, n: ast.AST) -> set[str]:
        return binds.get(group(n) if code_of is None else "<module>", {}).get(name) \
            or binds.get("<module>", {}).get(name) or set()

    def bound_lines(e: ast.AST, n: ast.AST) -> tuple[int, ...]:
        """差し替える物 ``e`` が別名なら、その有効範囲で別名を結ぶ import の行(``bound`` と同じ引き方)。"""
        if not isinstance(e, ast.Name):
            return ()
        key = group(n) if code_of is None else "<module>"
        got = blines.get(key, {}).get(e.id) if binds.get(key, {}).get(e.id) else blines.get("<module>", {}).get(e.id)
        return tuple(sorted(base_line + x for x in (got or ())))

    def target(e: ast.AST, n: ast.AST) -> tuple[str | None, bool]:
        """差し替える物 ``e`` が見張るモジュールなら (モジュール, 真)・見張るモジュールに触れるが決められなければ (None, 真)。"""
        if isinstance(e, ast.Name):
            mods = bound(e.id, n)
            hit = mods & watched
            if hit and len(mods) == 1:
                return next(iter(hit)), True
            return None, bool(hit)
        dn = _dotted_name(e)
        if dn is not None and dn in watched:
            return dn, True
        touch = any(isinstance(x, ast.Name) and bound(x.id, n) & watched for x in ast.walk(e)) or any(
            isinstance(x, ast.Constant) and isinstance(x.value, str) and any(w in x.value for w in watched)
            for x in ast.walk(e))
        return None, touch

    def where(n: ast.AST) -> str:
        return f"{path}:{base_line + getattr(n, 'lineno', 0)}"

    def add(n: ast.AST, mod: str, name: str, form: str, via: ast.AST | None = None) -> None:
        sites.append(_Patch(path, group(n), name, base_line + n.lineno, mod, form + tag,
                            bound_lines(via, n) if via is not None else (),
                            via.id if isinstance(via, ast.Name) else ""))

    def str_target(s: str) -> tuple[str, str] | None:
        best = max((w for w in watched if s.startswith(w + ".")), key=len, default=None)
        if best is None:
            return None
        rest = s[len(best) + 1:].split(".")[0]
        return (best, rest) if rest else None

    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            is_patch = (isinstance(f, ast.Attribute) and fname in _PATCH_ATTRS) or (
                isinstance(f, ast.Name) and fname in _PATCH_FUNCS)
            if n.args and fname in _PATCH_STR and (is_patch or fname == "patch"):
                a0 = n.args[0]
                if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                    hit = str_target(a0.value)
                    if hit is not None:
                        add(n, hit[0], hit[1], f"{fname}(文字列の的)")
                    continue
                if isinstance(a0, (ast.JoinedStr, ast.BinOp)) and target(a0, n)[1]:
                    unseen.append(f"{where(n)} {fname}: 的の文字列を組み立てる(名を確かめられない)")
                    continue
            if is_patch and n.args:
                mod, touch = target(n.args[0], n)
                if mod is not None:
                    a1 = n.args[1] if len(n.args) > 1 else None
                    if isinstance(a1, ast.Constant) and isinstance(a1.value, str):
                        add(n, mod, a1.value, f"{fname}(別名)", n.args[0])
                    else:
                        unseen.append(f"{where(n)} {fname}: 名が字面の定数でない(名を確かめられない)")
                elif touch and not isinstance(n.args[0], ast.Attribute):  # 別名.物 への差し替えは物の書き換え(モジュールの差し替えでない)
                    unseen.append(f"{where(n)} {fname}: 差し替える物を決められない(動的・別名が 2 つのモジュールに結ばれる)")
        elif isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Delete)):
            tgs = n.targets if isinstance(n, (ast.Assign, ast.Delete)) else [n.target]
            for tg in tgs:
                for x in ast.walk(tg):
                    if isinstance(x, ast.Attribute) and isinstance(x.ctx, (ast.Store, ast.Del)):
                        mod, touch = target(x.value, n)
                        if mod is not None:
                            add(n, mod, x.attr, "del" if isinstance(n, ast.Delete) else "属性への代入", x.value)
                        elif touch and not isinstance(x.value, ast.Attribute):  # 別名.物.属性 は物の書き換え(モジュールの差し替えでない)
                            unseen.append(f"{where(n)} 属性への代入: 差し替える物を決められない")
                    elif isinstance(x, ast.Subscript) and isinstance(x.ctx, (ast.Store, ast.Del)) and _module_dict(x.value) \
                            and target(x.value, n)[1]:
                        unseen.append(f"{where(n)} 辞書への代入(vars・__dict__): 名を確かめられない")
        elif (code_of is None and isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs
              and "import" in n.value and any(w in n.value or w.rpartition(".")[2] in n.value for w in watched)):
            s2, u2 = _collect_patches(n.value, path, watched, code_of=syms.get(id(n), "<module>"),
                                      base_line=n.lineno - 1)
            sites += s2
            unseen += u2
    return sites, unseen


def _fn_locals(fn: ast.AST) -> set[str]:
    """関数(かラムダ)の有効範囲で結ぶ名(引数・代入・import・入れ子の定義の名ほか。``global`` の名を除く)。内包の変数は内包の局所。"""
    a = fn.args  # type: ignore[attr-defined]
    out = {x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if x is not None}
    body = fn.body if isinstance(fn.body, list) else [fn.body]  # type: ignore[attr-defined]
    glob: set[str] = set()
    stack: list[ast.AST] = list(body)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
            continue
        if isinstance(n, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            continue
        if isinstance(n, ast.Global):
            glob |= set(n.names)
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.add(n.id)
        elif isinstance(n, ast.Import):
            out |= {x.asname or x.name.split(".")[0] for x in n.names}
        elif isinstance(n, ast.ImportFrom):
            out |= {x.asname or x.name for x in n.names}
        elif isinstance(n, ast.ExceptHandler) and n.name:
            out.add(n.name)
        elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and n.name:
            out.add(n.name)
        elif isinstance(n, ast.Nonlocal):
            out |= set(n.names)
        stack.extend(ast.iter_child_nodes(n))
    return out - glob


def _global_reads(stmt: ast.stmt, fut: bool) -> list[tuple[str, int, bool, str]]:
    """頂上の文 1 つの中で、モジュールの頂上の名を素の名で読む所: (名, 行, 呼ぶ時か, どこ)。関数・ラムダの本体は呼ぶ時、デコレータ・
    既定の引数・(``from __future__ import annotations`` が無ければ)注釈・クラスの親と本体・頂上の文は読み込みの時。局所の名
    (引数・代入・内包の変数)に覆われた読みは数えない。"""
    out: list[tuple[str, int, bool, str]] = []

    def visit(node: ast.AST, scopes: list[tuple[set[str], bool]], call: bool, w: str) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = node.args
            lw = w if call else f"{w}(デコレータ・既定の引数・注釈=読み込みの時)"
            outer = [*getattr(node, "decorator_list", []), *a.defaults, *[k for k in a.kw_defaults if k is not None]]
            if not fut and not isinstance(node, ast.Lambda):
                outer += [x.annotation for x in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]
                          if x is not None and x.annotation is not None]
                if node.returns is not None:
                    outer.append(node.returns)
            for d in outer:
                visit(d, scopes, call, lw)
            inner = [s for s in scopes if not s[1]] + [(_fn_locals(node), False)]
            body = node.body if isinstance(node.body, list) else [node.body]
            for b in body:
                visit(b, inner, True, w)
            return
        if isinstance(node, ast.ClassDef):
            for d in [*node.decorator_list, *node.bases, *[k.value for k in node.keywords]]:
                visit(d, scopes, call, w if call else f"{w}(クラスの親・デコレータ=読み込みの時)")
            cls_locals = set(_bound_in(node.body, top=False))
            for b in node.body:
                bw = f"{w}.{b.name}" if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) else (
                    w if call else f"{w}(クラスの本体=読み込みの時)")
                visit(b, [*scopes, (cls_locals, True)], call, bw)
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            gens = node.generators
            visit(gens[0].iter, scopes, call, w)
            tg = {x.id for g in gens for x in ast.walk(g.target) if isinstance(x, ast.Name)}
            inner = [s for s in scopes if not s[1]] + [(tg, False)]
            for ch in ast.iter_child_nodes(node):
                if ch is gens[0]:
                    for part in [ch.target, *ch.ifs]:
                        visit(part, inner, call, w)
                    continue
                visit(ch, inner, call, w)
            return
        if isinstance(node, ast.AnnAssign):
            if node.value is not None:
                visit(node.value, scopes, call, w)
            visit(node.target, scopes, call, w)
            if not fut and not call:
                visit(node.annotation, scopes, call, w)
            return
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load) and not any(node.id in s for s, _c in scopes):
                out.append((node.id, node.lineno, call, w))
            return
        for ch in ast.iter_child_nodes(node):
            visit(ch, scopes, call, w)

    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        visit(stmt, [], False, stmt.name)
    elif isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        tg = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        names = ",".join(n.id for x in tg for n in ast.walk(x) if isinstance(n, ast.Name))
        visit(stmt, [], False, f"頂上の代入 {names}(読み込みの時)")
    else:
        visit(stmt, [], False, f"頂上の文 行 {stmt.lineno}(読み込みの時)")
    return out


def _call_time_ids(tree: ast.AST) -> set[int]:
    """呼ぶ時に評価するノード(関数とラムダの本体の中)。デコレータ・既定の引数・クラスの本体・頂上の文は読み込みの時。"""
    out: set[int] = set()

    def visit(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            body = node.body if isinstance(node.body, list) else [node.body]
            for b in body:
                out.update(id(x) for x in ast.walk(b))
            for ch in ast.iter_child_nodes(node):
                if not any(ch is b for b in body):
                    visit(ch)
            return
        for ch in ast.iter_child_nodes(node):
            visit(ch)

    visit(tree)
    return out


def _dest_modules(plan: SplitPlan) -> dict[str, str]:
    """〔検収の後の直し 1〕割り先のモジュールの名 → 割り先の道。主な割り先が元のファイルの行では元のモジュールも主な割り先として入る。"""
    return {mod_of(d): d for d in plan.dests}


def _listed_manual(manual: list[str], p: str, s: _Patch) -> bool:
    """〔検収の後の直し 1〕割る前の差し替え ``s`` の別名が、手で直す一覧に在るか(別名を結ぶ import の文の行の項・コードの文字列は
    その記号の項)。文字列の的(別名を通さない)は在ると見ない。"""
    if s.group.endswith("(コードの文字列)"):
        sym = s.group[: -len("(コードの文字列)")]
        return any(m.startswith(f"{p}::{sym}:") for m in manual)
    return any(m.startswith(f"{p}:{ln}:") for ln in s.binds for m in manual)


def patch_reach(plan: SplitPlan) -> list[str]:
    """〔割る段 6・E5-b・親の裁定の追記〕差し替えの届く先の守り。止める文の一覧を返し、確かめた差し替え・見られなかった差し替え・
    読み込みの時にだけ読む文を ``plan`` に入れる。

    1. 割る前の読み手(src・tests〔c7 を除く〕・tools・docs の記録の道具。道具の自分と元のファイルを除く)から、割るモジュールの
       別名を通す差し替え(``setattr``・``patch.object``・属性への代入・``del``・文字列の的・コードの文字列の中の同じ形)を集める。
    2. 名ごとに届かせる割り先の集合: (a) 元のファイルの中で、その名を関数の本体で素の名で読む頂上の関数(メソッドはクラス)の
       割り先 (b) src のほかのモジュールが呼ぶ時に別名の属性で読むなら、名を定義する割り先 (c) (a)(b) が空なら名を結ぶ割り先
       (定義の割り先か、import で結ぶ名は再輸出の割り先)。
    3. 割った後の字面で、同じ関数の中の差し替えが向くモジュールが 2 の集合と同じか。届かない割り先・集合の外の割り先があれば止める。
    4. 読み込みの時にだけ読む文(デコレータ・既定の引数・クラスの親と本体・頂上の代入と表)は (a) に数えず ``patch_load_time`` に出す。
    5. 見られなかった形(名が字面でない・的を組み立てる・範囲の外・割った後も別名が元のモジュールを指し、その別名が手で直す一覧
       ``plan.manual`` に在る)は ``patch_unseen`` に出す(ここでは止めない。〔検収の後の直し 2・親の裁定〕``strict`` の当ては
       :func:`make_split_plan` が ``patch_unseen`` が 1 つでも在れば断る)。
    〔検収の後の直し 1〕主な割り先が元のファイルの行(元のモジュールが残る)では、元のモジュールを主な割り先として、ほかの割り先と同じに
    確かめる。割り先でないモジュールを指したままの差し替えは、別名が手で直す一覧に在るときだけ「見られなかった」・無ければ止める。
    """
    row = plan.row
    before, after = plan.before, plan.after
    src_p = SRC_PREFIX + plan.src_rel
    src_mod = mod_of(plan.src_rel)
    leaf = src_mod.rpartition(".")[2]
    dest_of_mod = {mod_of(d): d for d in plan.dests}
    groups: dict[tuple[str, str], list[_Patch]] = {}
    unseen: list[str] = []
    for p in sorted(before.files):
        if p == src_p or is_self(p) or p.startswith("tests/c7/"):
            continue
        text = before.files[p]
        if leaf not in text and src_mod not in text:
            continue
        sites, uns = _collect_patches(text, p, {src_mod})
        unseen += uns
        for s in sites:
            groups.setdefault((s.file, s.group), []).append(s)
    plan.patch_checked, plan.patch_load_time, plan.patch_declared = [], [], []
    # 〔割る段 6・E5-c〕素で使ってよい別名の宣言(この割る行の分): 差し替える名は、字面で見えなくても届く先を確かめる
    bare_decls = {(d.file, d.alias): d for d in SPLIT_ALIAS_DESTS if d.old == row.old and d.bare}
    if not groups and not any(d.patches for d in bare_decls.values()):
        plan.patch_unseen = unseen
        return []
    names = sorted({s.name for ss in groups.values() for s in ss} | {n for d in bare_decls.values() for n in d.patches})
    # 2 (a) 元のファイルの中の読み
    src_text = before.files[src_p]
    units = units_of(src_text, plan.src_rel)
    nm = row.name_map
    defined = {n: nm[n] for u in units if u.kind == "named" for n in u.names}
    fut = any(isinstance(st, ast.ImportFrom) and st.module == "__future__" and any(a.name == "annotations" for a in st.names)
              for st in parse(src_text).body)
    inner: dict[str, set[tuple[str, str]]] = {}
    load: dict[str, list[str]] = {}
    for u in units:
        if u.kind not in ("named", "other"):
            continue
        if u.kind == "named":
            dest = defined[u.names[0]]
        elif _is_main_guard(u.node) and plan.entry:
            dest = plan.entry
        else:
            ds = {defined[n] for n in names_used(u.node) if n in defined}
            dest = ds.pop() if len(ds) == 1 else row.new
        for name, line, call, w in _global_reads(u.node, fut):
            if name not in names:
                continue
            if call:
                inner.setdefault(name, set()).add((dest, f"{plan.src_rel}:{line} {w}"))
            else:
                load.setdefault(name, []).append(f"{plan.src_rel}:{line} {w}")
    # 2 (b) src のほかのモジュールの別名の属性の読み
    outer: dict[str, list[str]] = {}
    for p in sorted(before.files):
        if not p.startswith(SRC_PREFIX) or p == src_p or is_self(p):
            continue
        text = before.files[p]
        if leaf not in text and src_mod not in text:
            continue
        tree = parse(text)
        syms = symbols_of(text)
        own = mod_of(p[len(SRC_PREFIX):])
        binds = _module_bindings(tree, syms, own if p.endswith("/__init__.py") else own.rpartition(".")[0])
        ct = _call_time_ids(tree)
        for n in ast.walk(tree):
            got: tuple[ast.AST, str, int] | None = None
            if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Load) and isinstance(n.value, ast.Name):
                got = (n.value, n.attr, n.lineno)
            elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("getattr", "hasattr")
                  and len(n.args) >= 2 and isinstance(n.args[0], ast.Name) and isinstance(n.args[1], ast.Constant)
                  and isinstance(n.args[1].value, str)):
                got = (n.args[0], n.args[1].value, n.lineno)
            if got is None or got[1] not in names:
                continue
            al = got[0].id  # type: ignore[attr-defined]
            mods = binds.get(syms.get(id(n), "<module>"), {}).get(al) or binds.get("<module>", {}).get(al) or set()
            if src_mod not in mods:
                continue
            if id(n) in ct:
                outer.setdefault(got[1], []).append(f"{p}:{got[2]}")
            else:
                load.setdefault(got[1], []).append(f"{p}:{got[2]}(別名の属性・読み込みの時)")
    reexp: dict[str, str] = {}
    for dd in [row.new, *[x for x in plan.kept_bindings if x != row.new]]:
        for b in sorted(plan.kept_bindings.get(dd, ())):
            reexp.setdefault(b, dd)
    need: dict[str, set[str]] = {}
    why: dict[str, list[str]] = {}
    for name in names:
        nd = {d for d, _w in inner.get(name, ())}
        why[name] = [f"{w}→{d}" for d, w in sorted(inner.get(name, ()), key=lambda x: x[1])]
        if outer.get(name) and name in defined:
            nd.add(defined[name])
            why[name] += [f"{x}(別名の属性)→{defined[name]}" for x in outer[name][:3]]
        if not nd:
            b = defined.get(name) or reexp.get(name)
            if b:
                nd = {b}
                why[name].append(f"(呼ぶ時に読む所が無い=名を結ぶ割り先)→{b}")
        need[name] = nd
    plan.patch_load_time = [f"名 {n}: {x}" for n in names for x in load.get(n, [])]
    # 3 割った後の字面で、同じ関数の中の差し替えが向くモジュール
    watched = {src_mod, *dest_of_mod}
    after_sites: dict[str, list[_Patch]] = {}
    errs: list[str] = []
    seen_decl: Counter = Counter()  # 〔E5-c〕(ファイル, 別名, 名) → 字面で見えた差し替えの数(宣言の別名を通すもの)
    for (p, g), ss in sorted(groups.items()):
        lines_of = {n: sorted({s.line for s in ss if s.name == n}) for n in {s.name for s in ss}}
        if is_split_excluded(p):
            unseen += [f"{p}::{g} 名 {n}(行 {ls}): 書き換えの範囲の外(SPLIT_EXCLUDE_PATHS)" for n, ls in lines_of.items()]
            continue
        if p not in after_sites:
            text_a = after.files.get(p)
            after_sites[p] = _collect_patches(text_a, p, watched)[0] if text_a is not None else []
        for name, lines in sorted(lines_of.items()):
            nd = need[name]
            here = f"{p}::{g} の名 {name}(差し替え 行 {lines})"
            if not nd:
                unseen.append(f"{here}: 名が元のファイルで結ばれていない(届かせる割り先が決まらない)")
                continue
            mods = {s.module for s in after_sites[p] if s.group == g and s.name == name}
            # 〔検収の後の直し 1〕割り先でないモジュール(元のモジュールが残らない行の元・転送)を指したままの差し替え。主な割り先が元の
            # ファイルの行は、元のモジュールが主な割り先=ほかの割り先と同じに確かめる(ここに来ない)
            stale = sorted(mods - set(_dest_modules(plan)))
            if stale:
                if all(_listed_manual(plan.manual, p, s) for s in ss if s.name == name):
                    unseen.append(f"{here}: 割った後も差し替えが元のモジュール {stale} を指す(手で直す一覧の別名)=届く先を"
                                  f"見られない")
                else:
                    errs.append(f"{here}: 割った後も差し替えが割り先でないモジュール {stale} を指す(手で直す一覧に無い)=どの割り先"
                                f"にも届かない(届かせる割り先 {sorted(nd)})")
                continue
            if not mods:
                unseen.append(f"{here}: 割った後の字面で差し替えが見つからない")
                continue
            pointed = {_dest_modules(plan)[m] for m in mods}
            missing, extra = sorted(nd - pointed), sorted(pointed - nd)
            if missing:
                errs.append(f"{here}: 届かない割り先 {missing}(呼ぶ時に読む所: {why[name][:4]})")
            if extra:
                errs.append(f"{here}: 集合の外の割り先 {extra} へ向く(その名を呼ぶ時に読む関数が無い=空振り・届かせる割り先 "
                            f"{sorted(nd)})")
            # 〔E5-c〕素で使ってよい別名を通す差し替えは、宣言の差し替える名(patches)に在ること。確かめは宣言の欄に出す
            via = [bare_decls[(p, s.alias)] for s in ss if s.name == name and (p, s.alias) in bare_decls]
            off = sorted({d.alias for d in via if name not in d.patches})
            if off:
                errs.append(f"{here}: 素で使ってよい別名 {off} を通す差し替えの名が、宣言の差し替える名(patches)に無い")
                continue
            if not missing and not extra:
                for d in via:
                    seen_decl[(p, d.alias, name)] += 1
                if len(via) < sum(1 for s in ss if s.name == name):  # 印の無い別名を通す差し替えも在る=確かめた欄にも出す
                    plan.patch_checked.append(f"{p}::{g} {name} → {sorted(pointed)}(差し替え {len(lines)})")
    # 〔E5-c〕素で使ってよい別名の差し替える名: 届かせる割り先の集合に宣言の割り先が入り、ほかの割り先が無いこと(素で使った先の
    # 差し替えは、宣言の割り先のモジュールにしか向かない=集合のほかの割り先には届かない)
    for (f, al), d in sorted(bare_decls.items()):
        for name in d.patches:
            nd = need.get(name, set())
            here = f"{f}: 素で使ってよい別名 {al} の差し替える名 {name}(宣言の割り先 {d.dest})"
            if not nd:
                errs.append(f"{here}: 名が元のファイルで結ばれていない(届かせる割り先が決まらない)")
            elif d.dest not in nd:
                errs.append(f"{here}: 宣言の割り先が届かせる割り先の集合 {sorted(nd)} に無い(空振り・呼ぶ時に読む所: "
                            f"{why[name][:4]})")
            elif nd - {d.dest}:
                errs.append(f"{here}: 届かない割り先 {sorted(nd - {d.dest})}(呼ぶ時に読む所: {why[name][:4]})")
            else:
                plan.patch_declared.append(f"{f}: 別名 {al} の名 {name} → ['{d.dest}'](字面で見えた差し替え "
                                           f"{seen_decl[(f, al, name)]}・素で使った先は宣言)")
    plan.patch_unseen = unseen
    return errs


# ------------------------------------------------------------------ 報告・差分・書く
def report(plan: SplitPlan) -> dict:
    st = {a: s.statements for a, s in plan.import_stats.items()}
    sp = {a: s.split for a, s in plan.import_stats.items()}
    return {
        "row": plan.row.old, "split_order": plan.row.split_order, "source": plan.src_rel, "in_place": plan.in_place,
        "dests": plan.dests, "names_by_dest": {d: len(v) for d, v in plan.names_by_dest.items()},
        "other_statements_by_dest": plan.others_by_dest,
        "rewrites_applied": plan.rewrites_applied, "rebuilt_imports": plan.rebuilt_imports,
        "dropped_imports": plan.dropped_imports, "dropped_reexports": plan.dropped_reexports,
        "import_statements": {a: st.get(a, 0) for a in ("src", "build", "tests", "tools", "docs")},
        "import_files": {a: plan.import_files.get(a, 0) for a in ("src", "build", "tests", "tools", "docs")},
        "import_split_statements": {a: sp.get(a, 0) for a in ("src", "build", "tests", "tools", "docs")},
        "path_strings": dict(plan.str_stats.rewritten), "path_string_sites": sorted(set(plan.string_sites)),
        "skipped_strings": plan.str_stats.skipped,
        "class_id_keys": plan.class_keys, "ledger_paths_added": plan.ledger_paths_added,
        "created_heads": plan.created_heads, "emptied_heads": plan.emptied_heads, "deleted": plan.deleted,
        "changed_files": len(plan.changed), "manual": plan.manual, "guards": plan.guards, "warnings": plan.warnings,
        "unwritten": plan.unwritten, "contracts": plan.contracts,
        "forwarder": plan.forwarder, "entry": plan.entry, "excluded_sites": plan.excluded_sites,
        # 〔割る段 5b の G0 の直し 高-1〕書き換えなかった対応表の鍵(tests/_places の割る行の口の第 1 引数)
        "table_key_sites": sorted({f"{s['file']}::{s['symbol']}: {s['token']}" for s in plan.str_stats.skipped
                                   if s.get("kind") == "table_key"}),
        # 〔割る段 5b・E5〕使った別名の割り先の宣言
        "alias_declared": plan.alias_declared,
        # 〔割る段 6・E7〕前向きの表に足した行・〔E8〕使った道の文字列の割り先の宣言
        "ledger_paths_split": plan.ledger_paths_split, "path_declared": plan.path_declared,
        # 〔割る段 6・E5-b〕差し替えの届く先: 確かめた差し替え・見られなかった差し替え・読み込みの時にだけ読む文
        "patch_checked": plan.patch_checked, "patch_unseen": plan.patch_unseen, "patch_load_time": plan.patch_load_time,
        # 〔割る段 6・E5-c〕素で使ってよい別名の宣言で確かめた差し替え
        "patch_declared": plan.patch_declared,
    }


def unified_diff(plan: SplitPlan) -> str:
    out: list[str] = []
    b, a = plan.before, plan.after
    for p in sorted(set(b.files) | set(a.files)):
        old, new = b.files.get(p), a.files.get(p)
        if old == new:
            continue
        out += difflib.unified_diff((old or "").splitlines(keepends=True), (new or "").splitlines(keepends=True),
                                    f"a/{p}" if old is not None else "/dev/null", f"b/{p}" if new is not None else "/dev/null", n=1)
        if out and not out[-1].endswith("\n"):
            out.append("\n")
    return "".join(out)


def apply(plan: SplitPlan, root: Path) -> list[str]:
    """計画の木を ``root`` へ書く(変わったファイルだけ・消すファイル)。``__pycache__`` だけのディレクトリを消す。"""
    import os

    from pkgmove.move import prune_cache_only_dirs
    b, a = plan.before, plan.after
    for p, text in a.files.items():
        if b.files.get(p) == text:
            continue
        dst = root / p
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    for p in b.files:
        if p not in a.files and (root / p).is_file():
            (root / p).unlink()
    for p in sorted({str(Path(x).parent) for x in b.files if x not in a.files}, key=len, reverse=True):
        d = root / p
        while d != root and d.is_dir() and not any(d.iterdir()):
            os.rmdir(d)
            d = d.parent
    return prune_cache_only_dirs(root)
