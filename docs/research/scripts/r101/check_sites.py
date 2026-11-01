"""R-101: 学校の公式サイトについて、robots.txt と規約の頁と時程・年間行事の頁の「有無」だけを確かめる。

読むだけ。頁の中身(時刻・日付)は保存も出力もしない。出力は標準出力の TSV(答申の表の材料)。
各頁は 1 回だけ読み、サイトごとに 1 秒あける。
  - robots: Disallow の要約(全体禁止か)と、AI 系のクローラー名(GPTBot・CCBot・ClaudeBot など)の記載の有無
  - top: トップ頁のリンクの名前から、規約系(サイトポリシー・利用規約・著作権・このサイトについて)と
         時程系(時程・日課・時間割・授業時間)と年間行事系(年間行事・行事予定・学年暦・学事暦・カレンダー)を拾う
  - policy: 規約系のリンクの先頭 1 件を読み、語(複製・転載・無断・自動・クローラ・スクレイピング・機械学習・生成AI・AI)の有無
"""
import re
import sys
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (research; read-only)"
AI_BOTS = ["GPTBot", "CCBot", "ClaudeBot", "anthropic", "Google-Extended", "PerplexityBot", "Bytespider", "ChatGPT-User"]
POLICY = re.compile(r"(サイトポリシー|サイト・ポリシー|利用規約|ご利用にあたって|著作権|このサイトについて|当サイトについて|サイトのご利用|Terms|Site ?Policy|Copyright)", re.I)
TIMETABLE = re.compile(r"(時程|日課|時間割|授業時間|タイムテーブル|一日の流れ|1日の流れ|学校生活の一日)")
CALENDAR = re.compile(r"(年間行事|行事予定|学年暦|学事暦|学年暦|年間予定|アカデミックカレンダー|Academic Calendar|学事日程|授業日程|年間スケジュール|カレンダー)", re.I)
POLICY_WORDS = ["複製", "転載", "無断", "自動", "クローラ", "スクレイピング", "機械学習", "生成AI", "生成 AI", "人工知能", "AI"]


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read(3_000_000)
        final = r.geturl()
    for enc in ("utf-8", "cp932", "euc-jp"):
        try:
            return b.decode(enc), final
        except UnicodeDecodeError:
            pass
    return b.decode("utf-8", "ignore"), final


def links(html, base):
    out = []
    for href, text in re.findall(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
        t = re.sub(r"<[^>]+>", " ", text)
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            m = re.search(r'alt="([^"]+)"', text)
            t = m.group(1) if m else ""
        out.append((t[:40], urllib.parse.urljoin(base, href)))
    return out


def check(name, url):
    row = {"name": name, "url": url}
    p = urllib.parse.urlparse(url)
    try:
        rb, _ = get(f"{p.scheme}://{p.netloc}/robots.txt")
        if "<html" in rb.lower()[:500]:
            row["robots"] = "無し(HTML が返る)"
        else:
            dis_all = bool(re.search(r"(?im)^\s*Disallow:\s*/\s*$", rb))
            bots = [b for b in AI_BOTS if b.lower() in rb.lower()]
            row["robots"] = ("Disallow:/ あり" if dis_all else "全体禁止なし") + (f"・AI 名 {','.join(bots)}" if bots else "")
    except Exception as e:  # noqa: BLE001
        row["robots"] = f"読めず({type(e).__name__})"
    time.sleep(1)
    try:
        html, final = get(url)
        row["final"] = final
        ls = links(html, final)
        pol = [(t, u) for t, u in ls if POLICY.search(t)]
        tt = sorted({t for t, u in ls if TIMETABLE.search(t)})
        cal = sorted({t for t, u in ls if CALENDAR.search(t)})
        row["timetable_links"] = " / ".join(tt[:3]) or "-"
        row["calendar_links"] = " / ".join(cal[:3]) or "-"
        row["policy_link"] = pol[0][1] if pol else "-"
        if pol:
            time.sleep(1)
            try:
                ph, _ = get(pol[0][1])
                text = re.sub(r"<[^>]+>", " ", ph)
                row["policy_words"] = ",".join(w for w in POLICY_WORDS if w in text) or "-"
            except Exception as e:  # noqa: BLE001
                row["policy_words"] = f"読めず({type(e).__name__})"
        else:
            row["policy_words"] = "-"
    except Exception as e:  # noqa: BLE001
        row["final"] = f"読めず({type(e).__name__})"
    return row


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cols = ["name", "url", "final", "robots", "policy_link", "policy_words", "timetable_links", "calendar_links"]
    print("\t".join(cols))
    for line in open(sys.argv[1], encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, url = line.split("\t")
        r = check(name, url)
        print("\t".join(str(r.get(c, "")) for c in cols), flush=True)
        time.sleep(1)
