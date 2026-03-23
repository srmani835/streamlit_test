import pdfplumber
import json
import re

def extract_pdf_data(pdf_path):
    results = []
    
    # Mapping for the 'Client Types' column based on horizontal positions (x-coordinates)
    # You may need to adjust these pixel values based on your specific PDF's layout
    applicability_map = {
        "individuals_w": (780, 800),
        "corporations_s": (810, 825),
        "corporations_m": (825, 840),
        "corporations_l": (840, 855),
        "corporations_xl": (855, 870),
        "corporations_np": (870, 885),
        "fis_b": (895, 910),
        "fis_nb": (910, 925),
        "fis_f": (925, 940),
        "fis_m": (940, 955)
    }

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # 1. Extract the Table
            table = page.extract_table({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
            })

            if not table:
                continue

            current_category = None
            
            for row in table[1:]:  # Skip header row
                content_col = row[0] if row[0] else ""
                
                # Logic to identify 'Requirement Category' vs 'Requirement'
                # Usually, Headers are Uppercase or have specific formatting
                lines = content_col.split('\n')
                
                header_match = re.match(r'^[A-Z\s/&()]+$', lines[0].strip())
                if header_match and len(lines[0]) > 3:
                    current_category = lines[0].strip()
                    requirement_text = " ".join(lines[1:]).strip()
                else:
                    requirement_text = content_col.strip()

                # 2. Extract Applicability (Visual Detection)
                # We look for non-white objects in the 4th column's x-range
                active_applicability = []
                
                # Get all 'rects' (rectangles/boxes) on the page
                for app_key, (x0, x1) in applicability_map.items():
                    # Check if there is a colored object within this x-range in the current row's y-range
                    # This is a simplified detection logic
                    boxes = [r for r in page.rects if x0 <= r['x0'] <= x1]
                    if boxes:
                        active_applicability.append(app_key)

                if current_category and requirement_text:
                    results.append({
                        "requirement_category": current_category,
                        "requirement": requirement_text.replace('\u2022', '').strip(),
                        "applicability": active_applicability
                    })

    return results

# Usage
# data = extract_pdf_data("your_policy_document.pdf")
# print(json.dumps(data, indent=2))
