"""T0: same input -> same output for build-stage pure functions touched by the literal replacement.
Run once with PYTHONPATH=<HEAD copy src> and once with PYTHONPATH=<worktree src>; prints one sha + the src root.
"""
import datetime as dt
import hashlib
import json

import shibuya
from shibuya.build.field import common as C
from shibuya.build.field import w7_planspec as W7
from shibuya.build.field import w12_external_nodes as W12
from shibuya.build.field import w13_weather as W13
from shibuya.build.lang import w14_signage as W14
from shibuya.build.sched import pool_facts as PF
from shibuya.build.sched import trial as TR
from shibuya.build.sched import vocab as V
from shibuya.build.sched import w17_schedule as W17
from shibuya.build.vis import w9_shadow as W9

out = {}
out["hhmm_to_min"] = [C.hhmm_to_min(s) for s in ("00:00", "09:30", "23:59", "24:00", "26:15")]
out["min_to_hhmm"] = [C.min_to_hhmm(m) for m in (0, 59, 61, 570, 1439, 1440, 1575)]
out["w7_ranges"] = [W7._parse_time_ranges(s) for s in ("10:00-22:00", "18:00-02:00", "00:00-24:00", "11:00-14:00,17:00-23:30")]
out["w7_opening"] = [W7.parse_opening_hours(s) for s in ("24/7", "Mo-Fr 09:00-18:00; Sa 10:00-17:00", "Mo-Su 18:00-03:00", "11:00-14:00,17:00-23:00")]
out["w7_holiday"] = [W7.parse_holiday_hours(s) for s in ("Sa,Su,PH 10:00-20:00", "PH off", "Mo-Su,PH 00:00-24:00", "Mo-Fr 09:00-18:00")]
out["w7_prohib"] = [W7.prohibited_intervals(a) for a in ([(1380, 2040)], [(0, 600), (1320, 1440)])]
out["w14_fmt"] = [W14._fmt_hm(m) for m in (0, 61, 1439, 1440, 1500)]
out["pf_parse"] = [PF.parse_hhmm(s) for s in ("7:30", "23:00", "0:05")]
out["tr_bin"] = TR._bin_minutes(["01_-4:45", "02_5:00", "40_22:45", "54_0:00", "60_3:45", "71_不詳"])
out["tr_defuzz"] = [TR._defuzz(m) for m in (0, 30, 45, 60, 61, 1410)]
out["tr_cuts"] = TR._cuts_to_lines([(0, "睡眠", "自宅"), (420, "食事", "自宅"), (480, "仕事", "職場")], {"自宅", "職場"})
out["vocab_fmt"] = V.format_line(1, 425, 1440, 0, 0)
out["vocab_parse"] = repr(V.parse_line("d1 0700-0745 食事 自宅", 1))
out["w17_hm"] = [W17._hm(m) for m in (0, 61, 1439, 1500, -1)]
out["w12_minute"] = [W12._minute(s) for s in ("05:00", "23:59", "00:30", "01:15")]
out["w13_sun"] = [W13.sun_times(dt.date(2026, m, 15)) for m in (1, 4, 7, 10)]
out["w9_sun"] = [W9.sun_vector(dt.date(2026, 7, 13), m) for m in (360.0, 720.0, 1080.0)]
raw = json.dumps(out, ensure_ascii=False, sort_keys=True, default=repr)
print(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16], shibuya.__file__)
print(raw[:600])
