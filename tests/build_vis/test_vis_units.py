"""build.vis の単体テスト(実データ不要)。

- PNG 書き出しの往復(自前エンコーダ → zlib で戻して画素一致)
- 合成場面での視線判定(壁の**後ろ**は見えない・壁の**横**は見える)
- 影ビットセットの詰め方(全影面・端数ビット)
- 太陽位置が W13 の ``solar_elevation_deg`` と一致すること(定義を1本にした証拠)
"""

from __future__ import annotations

import datetime as dt
import math
import struct
import zlib

import numpy as np
import pytest

from shibuya.build.field.w13_weather import solar_elevation_deg
from shibuya.build.vis import png as P
from shibuya.build.vis import w8_visibility as W8
from shibuya.build.vis import w9_shadow as W9


# ---------------------------------------------------------------- PNG


def _decode_png(data: bytes) -> tuple[int, int, int, np.ndarray]:
    """テスト用の最小 PNG デコーダ(フィルタ 0 のみ)。"""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    idat = b""
    width = height = color = 0
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        tag = data[pos + 4 : pos + 8]
        payload = data[pos + 8 : pos + 8 + length]
        crc = struct.unpack(">I", data[pos + 8 + length : pos + 12 + length])[0]
        assert crc == zlib.crc32(tag + payload) & 0xFFFFFFFF
        if tag == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", payload[:10])
            assert depth == 8
        elif tag == b"IDAT":
            idat += payload
        pos += 12 + length
    raw = zlib.decompress(idat)
    channels = 3 if color == 2 else 1
    stride = width * channels
    arr = np.frombuffer(raw, dtype=np.uint8).reshape(height, stride + 1)
    assert (arr[:, 0] == 0).all()  # フィルタ 0 固定
    body = arr[:, 1:].reshape(height, width, channels)
    return width, height, channels, (body[:, :, 0] if channels == 1 else body)


def test_png_roundtrip_gray_and_rgb(tmp_path):
    gray = (np.arange(7 * 5, dtype=np.uint8).reshape(7, 5) * 3).astype(np.uint8)
    w, h, ch, back = _decode_png(P.encode_png(gray))
    assert (w, h, ch) == (5, 7, 1)
    assert np.array_equal(back, gray)

    rgb = np.random.default_rng(0).integers(0, 256, size=(4, 6, 3), dtype=np.uint8)
    w, h, ch, back = _decode_png(P.encode_png(rgb))
    assert (w, h, ch) == (6, 4, 3)
    assert np.array_equal(back, rgb)

    path = tmp_path / "a.png"
    n = P.write_png(path, gray)
    assert path.stat().st_size == n
    # 同じ配列は同じバイト列(再構築でハッシュが動かない)
    assert P.encode_png(gray) == P.encode_png(gray.copy())


def test_png_rejects_bad_shapes():
    with pytest.raises(TypeError):
        P.encode_png(np.zeros((2, 2), dtype=np.float32))
    with pytest.raises(ValueError):
        P.encode_png(np.zeros((2, 2, 4), dtype=np.uint8))
    with pytest.raises(ValueError):
        P.encode_png(np.zeros((0, 3), dtype=np.uint8))


def test_ramp_and_canvas():
    v = np.array([0.0, 0.5, 1.0])
    cols = P.ramp_rgb(v)
    assert cols.shape == (3, 3) and cols.dtype == np.uint8
    assert tuple(cols[0]) == P.GRAY_RAMP[0]
    assert tuple(cols[-1]) == P.GRAY_RAMP[-1]

    cv = P.Canvas(0.0, 0.0, 100.0, 50.0, 5.0, background=(0, 0, 0))
    assert (cv.width, cv.height) == (20, 10)
    cv.square(50.0, 25.0, 1, (255, 0, 0))
    assert (cv.rgb[:, :, 0] == 255).sum() == 9
    cv.line(0.0, 0.0, 99.0, 0.0, (0, 255, 0))
    assert (cv.rgb[-1, :, 1] == 255).sum() >= 19
    # y は上が北: 北端の行は 0
    col, row = cv.to_px(np.array([0.0]), np.array([49.9]))
    assert (int(col[0]), int(row[0])) == (0, 0)


# ---------------------------------------------------------------- 視線(合成場面)


def _flat_scene(wall: bool = True, wall_h: float = 20.0) -> W8.Scene:
    """100m 四方・地盤 0m の平地に、y=50m の東西方向の壁(厚さ5m)を1枚立てた場面。

    厚さ 5m は 2.5m ラスタが必ず拾う幅。**2.5m より薄い建物はラスタから落ちる**
    (W8 の宣言済み近似)ことは ``test_rasterize_drops_walls_thinner_than_pitch`` で固定する。
    """
    dem = np.zeros((10, 10), dtype=np.float32)  # 10m 刻みの平坦 DEM
    polys = []
    base = np.zeros(0)
    hs = np.zeros(0)
    if wall:
        polys = [np.array([[20.0, 47.5], [60.0, 47.5], [60.0, 52.5], [20.0, 52.5]])]
        base = np.array([0.0])
        hs = np.array([wall_h])
    return W8.build_scene(
        polys, base, hs, dem, (0.0, 0.0), 10.0, (0.0, 0.0, 100.0, 100.0), pitch=W8.RASTER_M
    )


def _los(scene: W8.Scene, p, q, q_owner: int = -1) -> bool:
    return bool(
        W8._los(
            p[0], p[1], p[2], q[0], q[1], q[2], q_owner,
            scene.ground_z, scene.top_z, scene.owner,
            scene.x0, scene.y0, scene.pitch, scene.nx, scene.ny,
            W8.STEP_M, W8.NEAR_SKIP_M,
        )
    )


def test_los_wall_blocks_behind_but_not_beside():
    scene = _flat_scene()
    eye = (40.0, 20.0, 1.5)
    behind = (40.0, 80.0, 1.5)  # 壁の真後ろ
    beside = (95.0, 80.0, 1.5)  # 視線が y=50m を横切るのは x=67.5m = 壁の東端(60m)より外
    assert _los(scene, eye, behind) is False
    assert _los(scene, eye, beside) is True
    # 壁が無ければ後ろも見える
    assert _los(_flat_scene(wall=False), eye, behind) is True


def test_los_over_the_wall_when_high_enough():
    scene = _flat_scene(wall_h=5.0)
    eye = (40.0, 45.0, 1.5)
    # 壁のすぐ向こうの高い点(高さ 30m)は壁を越えて見える
    assert _los(scene, eye, (40.0, 55.0, 30.0)) is True
    # 同じ位置の地上高の点は見えない
    assert _los(scene, eye, (40.0, 55.0, 1.5)) is False


def test_los_target_own_building_does_not_occlude_itself():
    scene = _flat_scene(wall_h=20.0)
    eye = (40.0, 20.0, 1.5)
    inside = (40.0, 50.0, 10.0)  # 壁そのものの中の点
    assert _los(scene, eye, inside, q_owner=-1) is False
    assert _los(scene, eye, inside, q_owner=0) is True  # 自分の建物は遮らない


def test_rasterize_drops_walls_thinner_than_pitch():
    """2.5m ラスタ近似の**既知の穴**: 格子中心を1つも含まない薄い建物は遮蔽に効かない。"""
    dem = np.zeros((10, 10), dtype=np.float32)
    thin = [np.array([[20.0, 49.6], [60.0, 49.6], [60.0, 50.4], [20.0, 50.4]])]
    scene = W8.build_scene(thin, np.array([0.0]), np.array([20.0]), dem, (0.0, 0.0), 10.0,
                           (0.0, 0.0, 100.0, 100.0), pitch=W8.RASTER_M)
    assert scene.n_filled == 0
    assert _los(scene, (40.0, 20.0, 1.5), (40.0, 80.0, 1.5)) is True


def test_terrain_occludes():
    dem = np.zeros((10, 10), dtype=np.float32)
    dem[5, :] = 30.0  # y=50m 付近に尾根
    scene = W8.build_scene([], np.zeros(0), np.zeros(0), dem, (0.0, 0.0), 10.0,
                           (0.0, 0.0, 100.0, 100.0), pitch=W8.RASTER_M)
    assert _los(scene, (40.0, 20.0, 1.5), (40.0, 80.0, 1.5)) is False


def test_rasterize_marks_wall_cells_only():
    scene = _flat_scene()
    assert scene.n_filled > 0
    assert (scene.owner >= 0).sum() == scene.n_filled
    # 壁の外側は地盤高のまま
    assert float(scene.top_z[scene.owner < 0].max()) == pytest.approx(0.0)
    assert float(scene.top_z[scene.owner >= 0].max()) == pytest.approx(20.0)


# ---------------------------------------------------------------- 影


def test_all_shadow_plane_padding():
    for n in (1, 7, 8, 9, 356_732):
        plane = W9.all_shadow_plane(n)
        assert plane.shape[0] == (n + 7) // 8
        bits = np.unpackbits(plane)
        assert int(bits[:n].sum()) == n  # 有効ビットは全て 1
        assert int(bits[n:].sum()) == 0  # 端数ビットは 0(決定論)


def test_packbits_roundtrip():
    rng = np.random.default_rng(3)
    flags = rng.integers(0, 2, size=1234, dtype=np.uint8)
    assert np.array_equal(np.unpackbits(np.packbits(flags))[:1234], flags)


def test_sun_vector_matches_w13_elevation():
    date = dt.date(2026, 7, 28)
    for minute in (0.0, 300.0, 720.0, 1000.0, 1435.0):
        elev, az, tan_e = W9.sun_vector(date, minute)
        assert elev == pytest.approx(solar_elevation_deg(date, minute), abs=1e-9)
        assert 0.0 <= az < 360.0
        assert tan_e == pytest.approx(math.tan(math.radians(elev)), abs=1e-12)


def test_sun_azimuth_is_south_at_solar_noon_and_east_in_morning():
    date = dt.date(2026, 7, 28)
    # 南中(高度最大)の方位は南(180度)近傍
    best = max(range(0, 1440, 5), key=lambda m: W9.sun_vector(date, float(m))[0])
    _elev, az_noon, _ = W9.sun_vector(date, float(best))
    assert abs(az_noon - 180.0) < 2.0
    # 朝は東寄り(方位 < 180)・夕は西寄り(> 180)
    assert W9.sun_vector(date, float(best) - 240.0)[1] < 180.0
    assert W9.sun_vector(date, float(best) + 240.0)[1] > 180.0
