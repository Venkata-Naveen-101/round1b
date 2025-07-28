import os
import json
import re
import unicodedata
from datetime import datetime
import fitz  # PyMuPDF
from langdetect import detect
from sentence_transformers import SentenceTransformer, util
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

# ----------- CONFIGURATION -----------
PDF_FOLDER = "input/"
OUTPUT_FOLDER = "output/"
PERSONA_FILE = "persona_keywords.json"
# -------------------------------------

# Load semantic model (multilingual, <200MB)
model = SentenceTransformer("local_model")

# Optional: Set Tesseract path (Windows only)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def normalize_text(text):
    return unicodedata.normalize("NFKC", text).strip()

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def ocr_image(img):
    img = img.convert("L")
    img = img.filter(ImageFilter.MedianFilter())
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    return pytesseract.image_to_string(img, lang="eng+jpn+hin")

def extract_text_with_ocr(pdf_path):
    images = convert_from_path(pdf_path, dpi=200)
    text = ""
    for img in images:
        text += ocr_image(img) + "\n"
    return text

def clean_section_title(title):
    title = normalize_text(title)
    title = re.sub(r'^第\s*\d+\s*課\s*', '', title)
    title = re.sub(r'[▶:・\-©\s]+$', '', title)
    title = re.sub(r'^[©\s]+', '', title)
    return title.strip()

def semantic_score(section_text, job_description):
    emb_section = model.encode(section_text, convert_to_tensor=True)
    emb_job = model.encode(job_description, convert_to_tensor=True)
    score = util.pytorch_cos_sim(emb_section, emb_job).item()
    return round(score * 100, 2)

def preprocess_text(page_obj):
    sections = []
    current_section = None
    current_text = ""

    for block in page_obj.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = normalize_text(span["text"])
                font_size = span["size"]

                if font_size > 12 and len(text) < 80:
                    if current_text and current_section:
                        cleaned_title = clean_section_title(current_section)
                        sections.append((cleaned_title, current_text.strip()))
                    current_section = text
                    current_text = ""
                else:
                    current_text += " " + text

    if current_text and current_section:
        cleaned_title = clean_section_title(current_section)
        sections.append((cleaned_title, current_text.strip()))

    return sections

def prompt_persona(persona_data):
    import os

    persona_env = os.environ.get("PERSONA")
    if persona_env:
        choice = persona_env.strip()
    else:
        print("\nAvailable personas:")
        persona_list = list(persona_data.keys())
        for i, persona in enumerate(persona_list, start=1):
            print(f"{i}. {persona}")
        print(f"{len(persona_list)+1}. Create a custom persona")
        try:
            choice = input("\nEnter persona name or number: ").strip()
        except EOFError:
            print("❌ No input provided and PERSONA env variable not set.")
            exit()

    persona_list = list(persona_data.keys())

    if choice.isdigit():
        index = int(choice)
        if 1 <= index <= len(persona_list):
            selected = persona_list[index - 1]
            return selected, persona_data[selected]["keywords"], persona_data[selected]["job"]
        elif index == len(persona_list) + 1:
            return create_custom_persona()
        else:
            print("❌ Invalid selection.")
            exit()

    normalized_choice = choice.lower()
    matched_persona = next((p for p in persona_list if p.lower() == normalized_choice), None)

    if matched_persona:
        return matched_persona, persona_data[matched_persona]["keywords"], persona_data[matched_persona]["job"]
    else:
        print("❌ Invalid persona name.")
        exit()


def create_custom_persona():
    import os

    persona = os.environ.get("PERSONA", "").strip()
    job = os.environ.get("CUSTOM_JOB", "").strip()
    keyword_str = os.environ.get("CUSTOM_KEYWORDS", "").strip()

    if not persona or not job or not keyword_str:
        print("❌ Missing one or more required environment variables for custom persona.")
        print("   Required: PERSONA, CUSTOM_JOB, CUSTOM_KEYWORDS")
        exit()

    keywords = [k.strip() for k in keyword_str.split(',') if k.strip()]
    if not keywords:
        print("❌ No keywords provided.")
        exit()

    return persona, keywords, job


def main():
    if not os.path.exists(PERSONA_FILE):
        print(f"❌ Missing {PERSONA_FILE}")
        return

    with open(PERSONA_FILE, "r", encoding="utf-8") as f:
        persona_data = json.load(f)

    persona, keywords, job_to_be_done = prompt_persona(persona_data)

    extracted_sections = []
    input_documents = []

    irrelevant_phrases = [
        "grammar", "lesson", "kanji", "v-", "タ形", "experience learning japanese",
        "starter", "elementary", "listening script", "tips for life in japan"
    ]

    for filename in os.listdir(PDF_FOLDER):
        if filename.endswith(".pdf"):
            full_path = os.path.join(PDF_FOLDER, filename)
            input_documents.append(filename)
            doc = fitz.open(full_path)

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text().strip()

                if not text:
                    text = extract_text_with_ocr(full_path)

                if not text.strip():
                    continue

                sections = preprocess_text(page)

                for section_title, section_text in sections:
                    if any(phrase in section_text.lower() for phrase in irrelevant_phrases):
                        continue

                    score = semantic_score(section_text, job_to_be_done)
                    if score > 20:
                        extracted_sections.append({
                            "document": filename,
                            "page_number": page_num + 1,
                            "section_title": section_title,
                            "refined_text": section_text.strip(),
                            "importance_rank": score
                        })

    extracted_sections.sort(key=lambda x: x["importance_rank"], reverse=True)
    for i, section in enumerate(extracted_sections):
        section["importance_rank"] = i + 1

    output = {
        "metadata": {
            "input_documents": input_documents,
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": [
            {
                "document": sec["document"],
                "page_number": sec["page_number"],
                "section_title": sec["section_title"],
                "importance_rank": sec["importance_rank"]
            }
            for sec in extracted_sections
        ],
        "sub_section_analysis": [
            {
                "document": sec["document"],
                "page_number": sec["page_number"],
                "refined_text": sec["refined_text"]
            }
            for sec in extracted_sections
        ]
    }

    if not extracted_sections:
        print("\n⚠️ No relevant sections found.")
        output["note"] = "No matching content found for the selected persona."

    output_path = os.path.join(OUTPUT_FOLDER, "challenge1b_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Output saved to {output_path}")

if __name__ == "__main__":
    main()