#!/usr/bin/env python3
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib import request, error

URL_RE = re.compile(r"https?://[^\s)]+")


def extract_urls(text: str):
    return sorted({u.rstrip('.,') for u in URL_RE.findall(text)})


def fetch(url: str, method: str, timeout: int = 10):
    req = request.Request(url, method=method, headers={"User-Agent": "Mozilla/5.0 (link-checker)"})
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.geturl()


def check_url(url: str):
    try:
        try:
            code, final = fetch(url, "HEAD")
        except Exception:
            code, final = fetch(url, "GET")
        return url, code, final, None
    except error.HTTPError as e:
        return url, e.code, e.geturl(), None
    except Exception as e:
        return url, None, None, str(e)


def main(path: str):
    text = Path(path).read_text(encoding='utf-8')
    urls = extract_urls(text)
    print(f"Found {len(urls)} unique URLs in {path}")

    ok, warn, fail = [], [], []
    with ThreadPoolExecutor(max_workers=24) as ex:
        futures = [ex.submit(check_url, u) for u in urls]
        for f in as_completed(futures):
            url, code, final, err = f.result()
            if err:
                fail.append((url, err))
            elif 200 <= code < 400:
                ok.append((url, code, final))
            elif code in (401, 403, 405, 429):
                warn.append((url, code, final))
            else:
                fail.append((url, f"HTTP {code} -> {final}"))

    fail_by_reason = Counter(msg for _, msg in fail)
    samples = defaultdict(list)
    for u, msg in fail:
        if len(samples[msg]) < 5:
            samples[msg].append(u)

    lines = [
        "# Link Check Report",
        "",
        f"- Source: `{path}`",
        f"- Total unique URLs: **{len(urls)}**",
        f"- ✅ OK: **{len(ok)}**",
        f"- ⚠️ Warn (restricted/rate-limit): **{len(warn)}**",
        f"- ❌ Fail: **{len(fail)}**",
        "",
        "## Failure reason summary",
    ]

    if fail_by_reason:
        for reason, count in fail_by_reason.most_common():
            lines.append(f"- **{count}** × {reason}")
            for s in samples[reason]:
                lines.append(f"  - sample: `{s}`")
    else:
        lines.append("- None")

    Path("link_check_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote report to link_check_report.md")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "ai_signal_links.md"
    raise SystemExit(main(target))
