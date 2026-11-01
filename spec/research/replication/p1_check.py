"""P1: list every number in the Morgan Stanley note, so the claim "nothing to reproduce" can be checked.

The page text passes through the recipient filter. Phone lines are dropped. Writes p1_results.json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from pdfkit import EVIDENCE, HERE, pymupdf, safe_text


def main():
    doc = pymupdf.open(EVIDENCE / "local_disk/MS_Eurodollar_Pain_Trade_Monitor_2014-10-16_page1.pdf")
    page = doc[0]
    text = "\n".join(line for line in safe_text(page).splitlines() if not re.search(r"\+1 |@|\d{3}-\d{4}", line))
    tokens = re.findall(r"\d[\d,.\-]*%?", text)
    res = {"pages": len(doc), "drawings": len(page.get_drawings()), "images": len(page.get_images()), "numeric_tokens": tokens,
           "output_values_found": [t for t in tokens if "%" in t or "," in t or "." in t.strip(".") or (t.isdigit() and int(t) not in (1, 2, 3, 14, 16, 30, 2014))]}
    print(res)
    (HERE / "p1_results.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
