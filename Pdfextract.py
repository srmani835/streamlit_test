import fitz
import re
import numpy as np

def approx_blue(rgb):
    r, g, b = rgb
    if r > 1:
        r, g, b = r/255, g/255, b/255
    return b > 0.35 and b > r and b > g

def rect_center(r):
    return ((r.x0 + r.x1)/2, (r.y0 + r.y1)/2)


def extract_applicability(pdf_path):
    doc = fitz.open(pdf_path)
    all_rows = []

    for page_num, page in enumerate(doc):
        words = page.get_text("words")

        # --- detect colored boxes ---
        boxes = []
        for d in page.get_drawings():
            rect = d.get("rect")
            fill = d.get("fill")

            if rect and fill and approx_blue(fill[:3]):
                boxes.append(rect)

        labeled = []

        for r in boxes:
            x0, y0, x1, y1 = r
            cx, cy = rect_center(r)

            text_parts = []
            for w in words:
                wx0, wy0, wx1, wy1, txt = w[:5]
                wcx = (wx0 + wx1)/2
                wcy = (wy0 + wy1)/2

                if (x0-5 <= wcx <= x1+5) and (y0-5 <= wcy <= y1+5):
                    text_parts.append(txt)

            label = re.sub(r"[^A-Za-z0-9]", "", "".join(text_parts)).upper()

            if label:
                labeled.append({
                    "label": label,
                    "center": (cx, cy),
                    "x": cx,
                    "y": cy
                })

        if not labeled:
            continue

        # --- group rows ---
        labeled.sort(key=lambda x: x["y"])

        rows = []
        current = [labeled[0]]

        for i in range(1, len(labeled)):
            if abs(labeled[i]["y"] - current[-1]["y"]) < 10:
                current.append(labeled[i])
            else:
                rows.append(current)
                current = [labeled[i]]

        rows.append(current)

        # --- sort left → right ---
        for row in rows:
            row_sorted = sorted(row, key=lambda x: x["x"])
            all_rows.append({
                "page": page_num + 1,
                "y": np.mean([r["y"] for r in row]),
                "labels": [r["label"] for r in row_sorted]
            })

    return all_rows
