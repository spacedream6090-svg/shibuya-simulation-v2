"""第 2 期 2-4 V1: W9 の影の 1 日の大きさを形ごとに測る(読むだけ・記録 vb24 の V1)。

    python docs/bench/analysis/wallbounce-1012/vb24/tools/w9_shapes.py data/world/v2_stage_2-4 > v1_w9_shapes.json

A=今の形(288 面 × ceil(N/8) B の packbits・memmap で読む)
B1=昼の面だけ(夜の面は全ビット 1=太陽の高度から作り直せる)
B2=zlib(level 6)で 1 日を丸ごと圧縮(読むときに展開)
B3=昼の面だけ+zlib
"""
import json
import sys
import time
import zlib
from pathlib import Path

import numpy as np


def main() -> None:
    root = Path(sys.argv[1])
    out = {}
    for p in sorted(root.glob("w9_shadow_*.npy")):
        a = np.load(p, mmap_mode="r")
        arr = np.asarray(a)
        full = arr.nbytes
        allones = np.all(arr[:, :-1] == 0xFF, axis=1) & (arr[:, -1] == arr[0, -1])
        day = arr[~allones]
        t0 = time.perf_counter()
        z = zlib.compress(arr.tobytes(), 6)
        tz = time.perf_counter() - t0
        t0 = time.perf_counter()
        zlib.decompress(z)
        tdz = time.perf_counter() - t0
        zd = zlib.compress(day.tobytes(), 6)
        out[p.name[len("w9_shadow_"):-4]] = {
            "file_bytes": p.stat().st_size,
            "planes": int(arr.shape[0]),
            "bytes_per_plane": int(arr.shape[1]),
            "A_now": int(full),
            "night_planes_all_ones": int(allones.sum()),
            "B1_daylight_only": int(day.nbytes),
            "B2_zlib6": len(z),
            "B3_daylight_zlib6": len(zd),
            "zlib_compress_s": round(tz, 3),
            "zlib_decompress_s": round(tdz, 3),
        }
    sys.stdout.reconfigure(newline="\n")  # 改行は LF(Windows の標準出力の CRLF にしない)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
