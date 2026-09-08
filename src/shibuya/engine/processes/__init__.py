"""engine.processes — **世界過程 第1陣の振る舞い**(D-R2-5・§7.2 初回実装の前半)。

位置づけ
    ``world.processes`` は**宣言だけ**(台帳・レコード型3・関係4・成長宣言)を持つ。
    本パッケージはその宣言に対応する**実装**であり、
    「宣言に無い過程は動かせない」「動く過程は必ず台帳の行を持つ」の双方向を保つ。

正典
- 世界過程設計書 §6 **D-R2-5**(第1陣): 昼夜・天候(体感温度)・鉄道運行(ODPT 静的ダイヤ)・
  混雑場(密度段階)・営業時間(PlanSpec)・静的騒音場。
- 同 §7.2 初回実装(第1陣)のうち本サブの担当: **屋内占有の集約(在席・待ち行列)**・
  **断面自動車交通(C 類 + B 類域外発生)**。
- 同 §3 実装原則: (1) SoA 配列演算かイベント駆動 (2) 状態成長の宣言 (3) **書き込み口は
  ``engine.resolve`` 一本**——世界過程も例外にしない。
- 運用設計書 §2.6(乗車の意味論=混雑率上限型)・行動契約書 §2.1 乗車/降車・§2.2 開閉店。
- 知覚契約書 §3(人物①②・内受容)・§3.2(B4/B4b)。

層契約: ``engine`` → ``world``/``agents``/``perception``/``llm``/``core``/``manifest``。
``build`` は**実行時に import しない**(import-linter 契約)ので、構築段の関数
(``build.field.w13_weather.select_day`` 等)は本パッケージで**同型に書き直す**。
"""

from __future__ import annotations

from shibuya.engine.processes.crowd import CrowdProcess
from shibuya.engine.processes.environment import EnvironmentProcess
from shibuya.engine.processes.opening import OpeningProcess
from shibuya.engine.processes.rail import RailProcess
from shibuya.engine.processes.runner import WorldProcessRunner
from shibuya.engine.processes.traffic import TrafficProcess

__all__ = [
    "CrowdProcess",
    "EnvironmentProcess",
    "OpeningProcess",
    "RailProcess",
    "TrafficProcess",
    "WorldProcessRunner",
]
