#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Weekly arXiv survey for LAAP wiki ingest (cron mode).
Scrapes arxiv.org/search/ HTML pages (API is unreliable from Windows),
filters to last N days, dedupes, relevance-filters, and reports new papers
not already in the wiki.
"""
import urllib.request, urllib.parse, re, time, json, os, sys, html as html_mod

KEYWORDS = [
    "speculative decoding",
    "semi-autoregressive generation",
    "confidence-scheduled verification",
    "LLM inference acceleration",
    "draft model",
    "blockwise parallel decoding",
    "quantum reasoning neural network",
    "AGI cognitive architecture",
    "AI consciousness",
]

# Combined queries to reduce request count
QUERIES = [
    "speculative decoding",
    "semi-autoregressive",
    "confidence-scheduled verification",
    "LLM inference acceleration",
    "draft model decoding",
    "blockwise parallel decoding",
    "quantum reasoning neural network",
    "AGI cognitive architecture",
    "AI consciousness",
]

WIKI_DIR = "D:/LAAP/wiki"
PAPERS_DIR = os.path.join(WIKI_DIR, "raw/papers")
DAYS_BACK = int(sys.argv[1]) if len(sys.argv) > 1 else 10

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def fetch(url, retries=3):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            resp = opener.open(req, timeout=30)
            return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt == retries - 1:
                print(f"FETCH FAIL {url}: {e}", file=sys.stderr)
                return None
            time.sleep(4)


def parse_date(s):
    """Parse 'Submitted 30 July, 2026' or 'v1] Tue, 28 Jul 2026 ...' -> (year, month, day) tuple"""
    m = re.search(r"(\d{1,2})\s+([A-Z][a-z]+)[a-z]*,\s*(\d{4})", s)
    if not m:
        m = re.search(r"(\d{1,2})\s+([A-Z][a-z]+)[a-z]*\s+(\d{4})", s)
    if not m:
        return None
    day, mon, year = int(m.group(1)), m.group(2)[:3].lower(), int(m.group(3))
    months = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
    if mon not in months:
        return None
    return (year, months[mon], day)


def search(query, start=0, max_results=50):
    url = ("https://arxiv.org/search/?searchtype=all&query=" +
           urllib.parse.quote(query) + f"&start={start}")
    html = fetch(url)
    if not html:
        return []
    results = []
    blocks = html.split('<li class="arxiv-result"')
    for block in blocks[1:]:
        id_m = re.search(r'/abs/([0-9]{4}\.[0-9]{4,5})', block)
        if not id_m:
            continue
        aid = id_m.group(1)
        title_m = re.search(r'class="title is-5 mathjax">\s*(.*?)\s*</p>', block, re.DOTALL)
        abstract_m = re.search(r'class="abstract-full[^"]*">\s*(.*?)\s*</span>', block, re.DOTALL)
        date_m = re.search(r'class="tags is-inline list-title is-marginless">.*?Submitted\s+(.*?)</span>', block, re.DOTALL) or \
                 re.search(r'Submitted\s+([^<]+)</span>', block)
        authors_m = re.search(r'class="authors">\s*(.*?)\s*</div>', block, re.DOTALL)
        cats_m = re.findall(r'<span class="tag is-small is-white tooltip is-tooltip-top">([^<]+)</span>', block)
        if not date_m:
            continue
        dstr = html_mod.unescape(date_m.group(1)).strip()
        date = parse_date(dstr)
        if not date:
            continue
        title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else aid
        title = html_mod.unescape(title)
        abstract = re.sub(r'<[^>]+>', '', abstract_m.group(1)).strip() if abstract_m else ''
        abstract = html_mod.unescape(abstract)
        authors = re.sub(r'<[^>]+>', '', authors_m.group(1)).strip() if authors_m else ''
        authors = re.sub(r'^Authors:\s*', '', authors).strip()
        cats = [html_mod.unescape(c).strip() for c in cats_m]
        results.append({
            "id": aid,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "date": date,
            "date_str": dstr,
            "categories": cats,
            "query": query,
        })
        if len(results) >= max_results:
            break
    return results


def slugify(title):
    s = title.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s[:100]


def is_relevant(paper):
    """Relevance filter: speculative decoding / LLM inference acceleration / cognitive architecture / consciousness."""
    text = (paper["title"] + " " + paper["abstract"]).lower()
    relevant_terms = [
        "speculative decoding", "draft model", "drafting", "blockwise", "block-wise",
        "parallel decoding", "multi-token prediction", "multi-token", "mtp",
        "inference acceleration", "inference speedup", "latency", "throughput",
        "decoding acceleration", "self-speculative", "jacobi decoding", "lookahead decoding",
        "eagle", "medusa", "draft", "verification", "verify",
        "cognitive architecture", "agi architecture", "consciousness", "global workspace",
        "quantum reasoning", "quantum neural", "semi-autoregressive",
    ]
    hits = [t for t in relevant_terms if t in text]
    # Exclude clearly irrelevant domains
    exclude_terms = [
        "image generation", "diffusion model for image", "text-to-image", "video generation",
        "object detection", "segmentation", "quantization for gpu", "hardware accelerator",
        "fpga", "adversarial attack", "watermarking", "retrieval-augmented",
    ]
    ex_hits = [t for t in exclude_terms if t in text]
    if ex_hits and not any(t in text for t in ["speculative decoding", "draft", "cognitive", "consciousness"]):
        return False
    return len(hits) >= 1


def main():
    all_results = {}
    for q in QUERIES:
        print(f"### Query: {q}")
        try:
            res = search(q)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        print(f"  -> {len(res)} results")
        for p in res:
            if p["id"] not in all_results:
                all_results[p["id"]] = p
        time.sleep(4)

    print(f"\nTotal unique: {len(all_results)}")

    # Date filter: last DAYS_BACK days
    import datetime
    cutoff = datetime.date.today() - datetime.timedelta(days=DAYS_BACK)
    recent = {}
    for aid, p in all_results.items():
        y, m, d = p["date"]
        try:
            pdate = datetime.date(y, m, d)
        except ValueError:
            continue
        if pdate >= cutoff:
            recent[aid] = p

    print(f"After date filter (last {DAYS_BACK} days): {len(recent)}")

    # Relevance filter
    rel = {aid: p for aid, p in recent.items() if is_relevant(p)}
    print(f"After relevance filter: {len(rel)}")

    # Existing wiki slugs
    existing = set()
    if os.path.isdir(PAPERS_DIR):
        for f in os.listdir(PAPERS_DIR):
            existing.add(f[:-3] if f.endswith(".md") else f)

    new_papers = []
    for aid, p in sorted(rel.items(), key=lambda kv: kv[1]["date"], reverse=True):
        slug = slugify(p["title"])
        exists = slug in existing
        p["slug"] = slug
        p["exists"] = exists
        if not exists:
            new_papers.append(p)
        print(f"{'[EXISTS]' if exists else '[NEW]   '} {aid} {p['date_str']} | {p['title'][:80]}")

    out_path = "D:/LAAP/wiki/state/weekly_survey_results.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"date": str(datetime.date.today()), "cutoff": str(cutoff),
                   "total": len(all_results), "recent": len(recent),
                   "relevant": len(rel), "new": [p for p in new_papers],
                   "all_relevant": list(rel.values())}, f, ensure_ascii=False, indent=1)
    print(f"\nSaved {len(new_papers)} new papers to {out_path}")


if __name__ == "__main__":
    main()
