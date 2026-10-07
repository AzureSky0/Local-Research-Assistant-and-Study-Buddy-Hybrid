"""Download a benchmark corpus of arXiv papers (Decision 034).

Usage:
    python scripts/benchmark/download_arxiv_corpus.py [output_dir] [--recent N]

- A fixed set of well-known papers, so quality questions have known answers.
- Recent papers from several fields, so the corpus resembles what students
  and researchers collect.

Downloads follow arXiv's guidance for automated access: the export server,
one request every three seconds. Already downloaded files are skipped,
so the script can be stopped and resumed. The corpus is for local
benchmarking only and is never committed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

API_URL = "https://export.arxiv.org/api/query"
PDF_URL = "https://export.arxiv.org/pdf/{arxiv_id}"
USER_AGENT = "LocalResearchAssistant-benchmark/0.1 (local research tool; polite crawler)"
DELAY_SECONDS = 3.0
MAX_PDF_BYTES = 25 * 1024 * 1024

ATOM = "{http://www.w3.org/2005/Atom}"

# Well-known papers referenced by the quality questions.
CLASSIC_PAPERS = {
    "1706.03762": "Attention Is All You Need",
    "1810.04805": "BERT",
    "1412.6980": "Adam",
    "1512.03385": "Deep Residual Learning (ResNet)",
    "1406.2661": "Generative Adversarial Networks",
    "1312.6114": "Auto-Encoding Variational Bayes",
    "1301.3781": "Word2vec",
    "1502.03167": "Batch Normalization",
    "1607.06450": "Layer Normalization",
    "2005.14165": "GPT-3: Language Models are Few-Shot Learners",
    "2010.11929": "Vision Transformer (ViT)",
    "2106.09685": "LoRA",
    "2005.11401": "Retrieval-Augmented Generation",
    "2006.11239": "Denoising Diffusion Probabilistic Models",
    "2103.00020": "CLIP",
    "1910.10683": "T5",
    "1409.3215": "Sequence to Sequence Learning",
    "1409.0473": "Neural Machine Translation by Jointly Learning to Align and Translate",
    "1505.04597": "U-Net",
    "1503.02531": "Distilling the Knowledge in a Neural Network",
    "2203.02155": "InstructGPT",
    "1707.06347": "Proximal Policy Optimization",
    "1312.5602": "Playing Atari with Deep Reinforcement Learning",
    "2201.11903": "Chain-of-Thought Prompting",
    "1609.02907": "Graph Convolutional Networks",
}

# Recent papers per category (fields beyond computer science included).
RECENT_CATEGORIES = {
    "cs.LG": 50,
    "cs.CL": 50,
    "cs.CV": 40,
    "stat.ML": 35,
    "q-bio.NC": 35,
    "econ.EM": 30,
    "physics.ed-ph": 35,
}


def request(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def query_recent(category: str, count: int) -> list[dict[str, str]]:
    params = urllib.parse.urlencode(
        {
            "search_query": f"cat:{category}",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": count,
        }
    )
    root = ET.fromstring(request(f"{API_URL}?{params}"))

    papers = []
    for entry in root.findall(f"{ATOM}entry"):
        arxiv_id = entry.findtext(f"{ATOM}id", "").rsplit("/abs/", 1)[-1]
        title = " ".join(entry.findtext(f"{ATOM}title", "").split())
        if arxiv_id:
            papers.append({"id": arxiv_id, "title": title, "category": category, "classic": False})

    return papers


def safe_file_name(arxiv_id: str) -> str:
    return arxiv_id.replace("/", "_") + ".pdf"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("output_dir", nargs="?", default="data/benchmark/arxiv")
    parser.add_argument("--recent-scale", type=float, default=1.0, help="scale recent counts")
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"

    papers: list[dict] = [
        {"id": arxiv_id, "title": title, "category": "classic", "classic": True}
        for arxiv_id, title in CLASSIC_PAPERS.items()
    ]

    for category, count in RECENT_CATEGORIES.items():
        wanted = max(1, round(count * args.recent_scale))
        print(f"Listing {wanted} recent papers in {category}…", flush=True)
        try:
            papers.extend(query_recent(category, wanted))
        except (urllib.error.URLError, ET.ParseError) as error:
            print(f"  could not list {category}: {error}", flush=True)
        time.sleep(DELAY_SECONDS)

    # Unique by id, keeping the first (classic) entry.
    seen: set[str] = set()
    papers = [p for p in papers if not (p["id"] in seen or seen.add(p["id"]))]

    downloaded = skipped = failed = 0

    for position, paper in enumerate(papers, start=1):
        target = output / safe_file_name(paper["id"])
        paper["file"] = target.name

        if target.exists() and target.stat().st_size > 0:
            skipped += 1
            continue

        try:
            data = request(PDF_URL.format(arxiv_id=paper["id"]))
        except urllib.error.URLError as error:
            print(f"[{position}/{len(papers)}] {paper['id']}: failed ({error})", flush=True)
            paper["error"] = str(error)
            failed += 1
            time.sleep(DELAY_SECONDS)
            continue

        if not data.startswith(b"%PDF"):
            paper["error"] = "not a PDF (may be withdrawn or HTML-only)"
            failed += 1
        elif len(data) > MAX_PDF_BYTES:
            paper["error"] = "larger than 25 MB"
            failed += 1
        else:
            target.write_bytes(data)
            downloaded += 1
            print(
                f"[{position}/{len(papers)}] {paper['id']} {len(data) // 1024} KB  {paper['title'][:60]}",
                flush=True,
            )

        manifest_path.write_text(json.dumps(papers, indent=2), encoding="utf-8")
        time.sleep(DELAY_SECONDS)

    manifest_path.write_text(json.dumps(papers, indent=2), encoding="utf-8")
    print(f"Done: {downloaded} downloaded, {skipped} already present, {failed} failed.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
