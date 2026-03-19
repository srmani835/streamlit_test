import json
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig

def extract_structured_kyc(project_id: str, location: str, file_path: str):
    vertexai.init(project=project_id, location=location)
    
    # Use Pro for high-fidelity visual reasoning (color & hierarchy detection)
    model = GenerativeModel("gemini-1.5-pro-002")

    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    # Check if PDF or Image
    mime_type = "application/pdf" if file_path.lower().endswith(".pdf") else "image/jpeg"
    doc_part = Part.from_data(data=file_bytes, mime_type=mime_type)

    prompt = """
    ACT: Expert Regulatory Data Analyst.
    TASK: Extract KYC requirements from the table with strict attention to visual hierarchy.

    DATA EXTRACTION RULES:
    1. requirement_category: Extract any text that is colored BLUE (e.g., 'CDD', 'Beneficial Ownership'). This is the parent category.
    2. req: Extract text associated with bullet points. 
       - If multiple bullet points fall under a single 'Verify:' or 'Identify:' header, group them into a single coherent requirement string.
       - A single 'requirement_category' may contain multiple 'req' entries if they are logically distinct or separated by horizontal lines.
    3. applicable_client: Look at the far-right columns.
       - MAP headers: 'Individuals', 'Corporations', 'FIs', 'Govts' (Correct any typos like 'indiiiividuals').
       - LOGIC: Include a client type ONLY if the box is FILLED WITH BLUE. Ignore white/hollow boxes.
       - FORMAT: "Category (Sub-types)" e.g., "Corporations (S, M, L)".

    OUTPUT FORMAT:
    Return a JSON list of objects. Each object must strictly follow this schema:
    {
      "requirement_category": "String",
      "req": "String (Combined bullets/text)",
      "applicable_client": ["List of strings"]
    }
    """

    # Low temperature (0.0) ensures extraction is literal and not creative
    config = GenerationConfig(
        temperature=0.0,
        response_mime_type="application/json",
    )

    response = model.generate_content(
        [doc_part, prompt],
        generation_config=config
    )

    return json.loads(response.text)

# Execution
# results = extract_structured_kyc("your-project-id", "us-central1", "22123.jpg")
# print(json.dumps(results, indent=2))
