import fitz  # PyMuPDF
import pdfplumber

# -------- CONFIG --------
PDF_PATH = "input.pdf"

# Blue color threshold (tune if needed)
def is_blue(color):
    if not color:
        return False
    r, g, b = color
    return b > 0.5 and g > 0.4 and r < 0.4  # detect cyan/blue


# -------- STEP 1: GET BLUE BOX POSITIONS (FITZ) --------
def get_blue_rows(pdf_path):
    doc = fitz.open(pdf_path)
    blue_rows = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if "lines" not in b:
                continue

            for line in b["lines"]:
                for span in line["spans"]:
                    color = span.get("color", None)

                    # Convert int color to RGB
                    if isinstance(color, int):
                        r = ((color >> 16) & 255) / 255
                        g = ((color >> 8) & 255) / 255
                        b_ = (color & 255) / 255
                        rgb = (r, g, b_)
                    else:
                        rgb = None

                    if rgb and is_blue(rgb):
                        y0 = span["bbox"][1]
                        y1 = span["bbox"][3]

                        blue_rows.append({
                            "page": page_num,
                            "y0": y0,
                            "y1": y1
                        })

    doc.close()
    return blue_rows


# -------- STEP 2: EXTRACT TEXT WITH POSITIONS (PDFPLUMBER) --------
def extract_text_rows(pdf_path):
    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            words = page.extract_words(use_text_flow=True)

            for w in words:
                rows.append({
                    "page": page_num,
                    "text": w["text"],
                    "top": w["top"],
                    "bottom": w["bottom"]
                })

    return rows


# -------- STEP 3: GROUP TEXT INTO LINES --------
def group_lines(words, y_tolerance=3):
    lines = []

    words = sorted(words, key=lambda x: (x["page"], x["top"]))

    current_line = []
    current_y = None

    for w in words:
        if current_y is None:
            current_line = [w]
            current_y = w["top"]
            continue

        if abs(w["top"] - current_y) < y_tolerance:
            current_line.append(w)
        else:
            lines.append(current_line)
            current_line = [w]
            current_y = w["top"]

    if current_line:
        lines.append(current_line)

    return lines


# -------- STEP 4: MATCH BLUE ROWS WITH TEXT --------
def match_blue_to_text(blue_rows, lines):
    results = []

    for blue in blue_rows:
        page = blue["page"]
        y0 = blue["y0"]
        y1 = blue["y1"]

        for line in lines:
            if line[0]["page"] != page:
                continue

            line_top = line[0]["top"]
            line_bottom = line[0]["bottom"]

            # Overlap check
            if not (line_bottom < y0 or line_top > y1):
                text = " ".join([w["text"] for w in line])

                results.append(text)

    return results


# -------- STEP 5: GET CATEGORY --------
def extract_category(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()

        # crude but effective
        if "Beneficial Ownership" in text:
            return "Beneficial Ownership"

    return "Unknown"


# -------- MAIN PIPELINE --------
def extract_requirements(pdf_path):
    blue_rows = get_blue_rows(pdf_path)
    words = extract_text_rows(pdf_path)
    lines = group_lines(words)

    matched_lines = match_blue_to_text(blue_rows, lines)
    category = extract_category(pdf_path)

    # Merge lines into full requirement blocks
    final = []
    buffer = ""

    for line in matched_lines:
        if line.startswith("For") or line.startswith("•"):
            if buffer:
                final.append(buffer.strip())
            buffer = line
        else:
            buffer += " " + line

    if buffer:
        final.append(buffer.strip())

    return [
        {"req_category": category, "req": req}
        for req in final
    ]


# -------- RUN --------
if __name__ == "__main__":
    results = extract_requirements(PDF_PATH)

    import json
    print(json.dumps(results, indent=2))
