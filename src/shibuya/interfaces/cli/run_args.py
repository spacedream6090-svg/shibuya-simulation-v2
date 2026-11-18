"""interfaces.cli.run_args — 割る段で ``engine/run.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``runtime/run.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
from shibuya.foundation.types import MINUTES_PER_SIM_DAY
from shibuya.runtime.state import growth_decl as GD
from shibuya.world.facts.calendar import DEFAULT_HOLIDAY_CSV
from shibuya.world.model.geometry import DEFAULT_GEOMETRY, GEOMETRY_MODES
from shibuya.world.laws.presence_plan import DERIVE_RULES as PRESENCE_DERIVE_RULES
from shibuya.world.laws.presence import EXIT_MODES as PRESENCE_EXIT_MODES
from shibuya.runtime.inference.fleet import FleetClient
from shibuya.world.model.space import nav1 as _NAV1
from shibuya.world.model.assets import AREA_SOURCES, DEFAULT_AREA_SOURCE
from shibuya.world.model.state import World
from shibuya.runtime.run import resolve_population_seed, run_day

__all__ = [
    "add_fleet_args", "fleet_from_args", "main",
]


# ------------------------------------------------------------------ CLI
def add_fleet_args(ap: "argparse.ArgumentParser") -> None:
    """実艦隊の共通引数(``engine.run`` と ``shibuya.cli`` で同じ綴りにするため 1 か所に置く)。

    ``--mode`` は **run manifest の実行モード**(smoke/calibration/holdout/ablation/production・
    運用設計書 §1.2)であって、``run_day(mode=...)`` の record/replay ではない。
    ``cache_salt`` の勘定分離(較正と holdout が prefix キャッシュを共有しない)に効く。
    """
    from shibuya.foundation.ports.inference import DEFAULT_T1_MAX_TOKENS, DEFAULT_TEMPERATURE
    from shibuya.foundation.manifest.schema import Mode as _Mode

    ap.add_argument("--llm", choices=("mock", "fleet"), default="mock",
                    help="LLM 経路(fleet=実 vLLM 艦隊・--endpoints 必須)")
    ap.add_argument("--endpoints", type=str, default="",
                    help="カンマ区切り http://host:port(既定艦隊は 7 本=xxhash(call_id) mod 7)")
    ap.add_argument("--model", type=str, default="",
                    help="served-model-name(空なら /v1/models の先頭)")
    ap.add_argument("--mode", choices=[m.value for m in _Mode], default="smoke",
                    help="実行モード(cache_salt の勘定分離・record/replay とは別物)")
    ap.add_argument("--run-id", type=str, default="",
                    help="manifest の run_id(cache_salt の第2要素)")
    ap.add_argument("--tape", type=str, default="", help="録画テープの出力先ディレクトリ")
    ap.add_argument(
        "--temperature", type=float, default=DEFAULT_TEMPERATURE,
        help=("T1 の温度(既定 0.7=知覚契約書 §2.5/卒業条件表・運用設計書 §1.3 の本番値。"
              "運用設計書 §1.2 の設定節は欄形だけで数値を持たない)"),
    )
    ap.add_argument(
        "--max-tokens", type=int, default=DEFAULT_T1_MAX_TOKENS,
        help="T1 の max_tokens(既定 96=2 行形の最大 ≒70 tok に余裕・expedient)",
    )
    ap.add_argument(
        "--fleet-debug-dir", type=str, default="",
        help=("書式の原因分析用 jsonl の置き場(既定 off・診断のみ)。初回パースが落ちた呼の "
              "プロンプト/初回の生応答/再生成の生応答/実効・厳密の判定/理由 を 1 行 1 呼で書く"),
    )
    ap.add_argument("--fleet-wait-s", type=float, default=0.0,
                    help="④′ で未応答が残るとき tick ごとに最大この秒数だけ艦隊を待つ(既定 0=純非ブロッキング・本番の運用は 120)")
    ap.add_argument("--fleet-queue-capacity", type=int, default=0,
                    help=("艦隊の受理待ち+実行中の合計上限(既定 0=FleetConfig の既定 max_in_flight×4)。"
                          "C7 本番(D-55/D-58): 計画呼数 2,709/tick に対し既定 1,792 だと 33.8%% が queue full で"
                          "繰り延べ→テープに残らず再生不能。計画呼数以上(例 4096)にすると繰り延べ ≈0"))


def add_calendar_args(ap: "argparse.ArgumentParser") -> None:
    """暦の口の引数(10a・A1-1・A1-2。``engine.run`` と ``shibuya.cli`` で同じ綴りにするため 1 か所に置く)。"""
    ap.add_argument("--start-date", type=str, default="",
                    help="開始日 YYYY-MM-DD(A1-1・manifest の start_sim_datetime)。空=2026-07-13(月)+ --day-index 日")
    ap.add_argument("--holiday-csv", type=str, default=DEFAULT_HOLIDAY_CSV,
                    help="内閣府の祝日 CSV(cp932)。読めなければ開始日の検査で止める(既定 data/calendar/syukujitsu.csv)")
    ap.add_argument("--school-holidays", type=str, default="",
                    help="学校の長期休みの区間 YYYY-MM-DD:YYYY-MM-DD をカンマ区切り(開始日の検査・既定は空)")
    # 10d(親の答え 7): 複数日の通しランと再開の口(同じ綴りを engine.run と shibuya.cli で使う)
    ap.add_argument("--sim-days", type=int, default=1,
                    help="通しで回す日数(10d)。2 以上では各日の終わりに締め・日の頭の初期化は走らせない(既定 1)")
    ap.add_argument("--resume-from", type=str, default="",
                    help="再開する状態のファイル(10d・state-T<T>.npz)。設定は親と同じにする(違えば止める)")
    ap.add_argument("--state-out", type=str, default="",
                    help="状態の書き出し先のディレクトリ(10d)。各日の締めの後とランの最後に state-T<T>.npz を書く")
    # 10e(B6): 天気を揺らす(同じ綴りを engine.run と shibuya.cli で使う)
    ap.add_argument("--weather-perturb", action="store_true",
                    help=("天気を揺らす(10e B6・アンサンブル)。窓の中でも同じ季節 × 平日/土休の層から天候型を日数の"
                          "割合で引く(鍵は --environment-seed)。既定は付けない=その日の実際の天気"))



def calendar_kwargs_from_args(args: Any) -> dict[str, Any]:
    """``add_calendar_args``(10d の ``--sim-days``・``--resume-from``・``--state-out``・10e の ``--weather-perturb`` を含む)の
    結果 → ``run_day`` の引数。"""
    out: dict[str, Any] = {
        "start_sim_datetime": (getattr(args, "start_date", "") or None),
        "holiday_csv": str(getattr(args, "holiday_csv", DEFAULT_HOLIDAY_CSV)),
        "school_holidays": str(getattr(args, "school_holidays", "") or ""),
    }
    # 10d: 複数日と再開の口(既定のときは欄を足さない=既定の引数は今のまま)
    if int(getattr(args, "sim_days", 1) or 1) != 1:
        out["sim_days"] = int(args.sim_days)
    if getattr(args, "resume_from", ""):
        out["resume_from"] = str(args.resume_from)
    if getattr(args, "state_out", ""):
        out["state_out"] = str(args.state_out)
    # 10e(B6): 天気を揺らす(未指定のときは欄を足さない=既定の引数は今のまま)
    if getattr(args, "weather_perturb", False):
        out["weather_perturb"] = True
    return out


def fleet_from_args(args: Any, ap: "argparse.ArgumentParser | None" = None) -> FleetClient | None:
    """``add_fleet_args`` の結果 → ``FleetClient``(``--llm mock`` なら ``None``)。"""
    from shibuya.runtime.inference.fleet import FleetConfig
    from shibuya.foundation.manifest.schema import Mode as _Mode

    if getattr(args, "llm", "mock") != "fleet":
        return None
    eps = tuple(e.strip() for e in str(args.endpoints).split(",") if e.strip())
    if not eps:
        msg = "--llm fleet には --endpoints(カンマ区切り http://host:port)が要る"
        if ap is not None:
            ap.error(msg)
        raise SystemExit(msg)
    from shibuya.foundation.ports.inference import DEFAULT_T1_MAX_TOKENS, DEFAULT_TEMPERATURE

    return FleetClient(
        FleetConfig(
            endpoints=eps,
            model=str(args.model),
            mode=_Mode(args.mode),
            run_id=str(getattr(args, "run_id", "")),
            run_seed=int(getattr(args, "seed", 0)),
            temperature=float(getattr(args, "temperature", DEFAULT_TEMPERATURE)),
            t1_max_tokens=int(getattr(args, "max_tokens", DEFAULT_T1_MAX_TOKENS)),
            # 0/未指定なら None=既定(max_in_flight×4)。C7 D-58 の回し直しで計画呼数以上を渡す。
            queue_capacity=(int(getattr(args, "fleet_queue_capacity", 0) or 0) or None),
        )
    )


def main(argv: list[str] | None = None) -> int:
    """``python -m shibuya.engine.run --agents 5000 --seed 1 --world data/world/v2``。"""
    ap = argparse.ArgumentParser(description="C2 エンジンの 1 シミュ日 mock ラン(予算行 W2)")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--population-seed", type=int, default=None,
                    help="10f(K21 (a))母集団の seed(省略=--seed と同じ)。--seed は動きの seed(salt)")
    ap.add_argument("--environment-seed", type=int, default=None,
                    help="10f 環境の seed(気象・大きな催し・道路工事。省略=--seed と同じ)")
    ap.add_argument("--world", type=str, default="data/world/v2",
                    help="世界資産ディレクトリ(無ければ合成小世界へ落ちる)")
    ap.add_argument("--cells", type=int, default=139, help="合成世界のセル数")
    ap.add_argument("--ticks", type=int, default=MINUTES_PER_SIM_DAY)
    ap.add_argument("--checkpoint-every", type=int, default=360)
    ap.add_argument("--day", type=int, default=0, help="曜日(0=月曜)")
    ap.add_argument("--growth-yaml", action="store_true", help="状態成長宣言 YAML を出力して終了")
    ap.add_argument("--no-processes", action="store_true",
                    help="世界過程(C4 第1陣)を止める(ablation の下限対照)")
    ap.add_argument("--no-population", action="store_true",
                    help="W16 母集団を使わず合成個体で回す(下限対照)")
    ap.add_argument("--ablate", action="append", default=[],
                    help="止める過程(過程 id か AB-* の感度試験 id・複数可)")
    ap.add_argument("--no-sleep-suppression", action="store_true",
                    help="D-56 就寝抑止を切る(=D-56 前の挙動・帰無腕)")
    ap.add_argument("--no-plan-sleep", action="store_true",
                    help="D-62「就寝は計画の実行」を切る(=D-62 前の挙動・帰無腕。"
                         "就寝境界も LLM に判断させ・tick 0 は全員 SLEEPING)")
    ap.add_argument("--no-plan-executor", action="store_true",
                    help="D-66 計画実行層(engine.presence)を切る(=現行挙動・帰無腕)")
    ap.add_argument("--group-norms", choices=("on", "off"), default="on",
                    help="群・規範の計器(D-107 (a)・読むだけ)を回すか(第309 Q150・既定 on)")
    ap.add_argument("--exit-mode", choices=PRESENCE_EXIT_MODES, default="immediate",
                    help="退出の実行形(immediate のみ実装・他は予約)")
    ap.add_argument("--derive-rule", choices=PRESENCE_DERIVE_RULES, default="v2",
                    help="在圏ブロックの読み口(v2=§2 追補・v1=原則のまま)")
    ap.add_argument("--no-outside-suppression", action="store_true",
                    help="D-66 域外抑止を切る(=D-66 前の挙動・帰無腕)")
    ap.add_argument("--geometry", choices=GEOMETRY_MODES, default=DEFAULT_GEOMETRY,
                    help="位置幾何(C9 G1/G2)。node=1 tick 1 ノード(既定・バイト不変)/"
                         "edge=辺上の連続位置+希望速度 1.00〜1.60 m/s+Kladek 減速")
    _NAV1.add_space_args(ap)
    ap.add_argument("--area-source", choices=AREA_SOURCES, default=DEFAULT_AREA_SOURCE,
                    help="歩行可能面積の出所(C9c-1 G8 (b))。legacy=街路点×6.25 m²(既定・"
                         "バイト不変)/ plateau=c9c_walkable_area.parquet(PLATEAU 歩道部+"
                         "OSM×道路構造令の実測)")
    add_fleet_args(ap)
    add_calendar_args(ap)
    args = ap.parse_args(argv)

    if args.growth_yaml:
        print(GD.to_yaml())
        return 0

    _pop_seed = resolve_population_seed(args.seed, args.population_seed)  # 10f: 合成世界は母集団の側
    world = World.load_or_synthetic(Path(args.world), n_cells=args.cells, seed=_pop_seed)
    res = run_day(
        n_agents=args.agents,
        seed=args.seed,
        population_seed=args.population_seed,
        environment_seed=args.environment_seed,
        world=world,
        ticks=args.ticks,
        checkpoint_every=args.checkpoint_every,
        day_index=args.day,
        world_dir=args.world,
        fleet=fleet_from_args(args, ap),
        fleet_wait_s=float(args.fleet_wait_s),
        fleet_debug_dir=args.fleet_debug_dir or None,
        tape_path=args.tape or None,
        processes=not args.no_processes,
        processes_disabled=tuple(args.ablate) or None,
        population=False if args.no_population else None,
        sleep_suppression=not args.no_sleep_suppression,
        plan_sleep=not args.no_plan_sleep,
        plan_executor=not args.no_plan_executor,
        exit_mode=str(args.exit_mode),
        group_norms=str(args.group_norms),
        derive_rule=str(args.derive_rule),
        outside_suppression=not args.no_outside_suppression,
        geometry=str(args.geometry),
        area_source=str(args.area_source),
        space=_NAV1.space_from_args(args),
        **calendar_kwargs_from_args(args),
    )
    print(res.summary())
    return 0 if (res.conserved and res.min_stock >= 0) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
