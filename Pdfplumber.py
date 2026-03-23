import pdfplumber
import re
import json

APPLICABILITY_MAP = {
    "W": "individuals_w",
    "S": "corporations_s",
    "M": "corporations_m",
    "L": "corporations_l",
    "XL": "corporations_xl",
    "NP": "corporations_np",
    "B": "fis_b",
    "NB": "fis_nb",
    "F": "fis_f",
    "G": "govt_g"
}

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def extract_requirements(text):
    lines = text.split("\n")
    requirements = []
    buffer = ""

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Bullet point start
        if line.startswith("▪") or line.startswith("-"):
            if buffer:
                requirements.append(clean_text(buffer))
            buffer = line[1:].strip()
        else:
            buffer += " " + line

    if buffer:
        requirements.append(clean_text(buffer))

    return requirements


def extract_applicability(chars):
    """
    Extract colored applicability codes from right column
    """
    applicability = []

    for ch in chars:
        text = ch["text"].strip()

        # Only take valid codes
        if text in APPLICABILITY_MAP:
            applicability.append(APPLICABILITY_MAP[text])

    return list(set(applicability))


def process_pdf(pdf_path):
    results = []
    last_applicability = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):

            width = page.width

            # Column splits (tune if needed)
            col1_bbox = (0, 0, width * 0.55, page.height)
            col4_bbox = (width * 0.75, 0, width, page.height)

            col1_text = page.within_bbox(col1_bbox).extract_text() or ""
            col4_chars = page.within_bbox(col4_bbox).chars

            requirements = extract_requirements(col1_text)
            applicability = extract_applicability(col4_chars)

            if not applicability:
                applicability = last_applicability
            else:
                last_applicability = applicability

            for req in requirements:
                results.append({
                    "page_number": page_num,
                    "requirement": req,
                    "applicability": applicability
                })

    return results


# Run
output = process_pdf("input.pdf")

with open("output.json", "w") as f:
    json.dump(output, f, indent=2)
