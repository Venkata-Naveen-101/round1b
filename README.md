## 📄 Round 1B – Persona‑Driven Document Intelligence

This project builds upon the Round 1A outline extractor to identify and rank the most relevant sections from multiple PDFs based on a given persona and job‑to‑be‑done. It uses OCR, semantic similarity, and multilingual support to handle diverse document formats.

## 🔹 Approach

1️⃣ PDF Parsing & OCR

Uses PyMuPDF to extract text.

Falls back to OCR (pdf2image + pytesseract) for scanned PDFs.

2️⃣ Section Extraction

Identifies section titles using font size and text heuristics.

3️⃣ Semantic Matching

Loads a multilingual SentenceTransformer (≤ 200 MB).

Computes cosine similarity between each section and the job description.

4️⃣ Persona‑Based Ranking

Reads keywords & job description from persona_keywords.json.

Filters irrelevant phrases and assigns importance ranks based on semantic score.

5️⃣ Output JSON

Produces metadata, ranked sections, and sub‑section details in the required format.

## 📦 Libraries / Models Used

fitz (PyMuPDF)----	Extract text and font properties

pdf2image	----Convert PDFs to images for OCR

pytesseract----	OCR for scanned PDFs

langdetect----	Detect language of extracted text

sentence-transformers----	Semantic similarity scoring (multilingual)

PIL	----Image processing for OCR enhancement


The model is a local multilingual embedding model (< 200 MB) that works offline.

⚙️ How to Build and Run

As per the hackathon requirements, the solution must run using the Expected Execution commands below.

🐳 Build Docker Image


    docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
  
  
▶️ Run the Container

    docker run --rm \
  
      -v $(pwd)/input:/app/input \
    
      -v $(pwd)/output:/app/output \
    
      --network none \
  
      mysolutionname:somerandomidentifier
    
    
✅ The container will:

Load persona details from persona_keywords.json.

Process all PDFs in /app/input/.

Generate challenge1b_output.json inside /app/output/.

## 📂 Output JSON Example
  
    {
  
    "metadata": {
    
      "input_documents": ["doc1.pdf", "doc2.pdf"],
      
      "persona": "PhD Researcher in Computational Biology",
      
      "job_to_be_done": "Prepare a literature review on GNN for drug discovery",
      
      "processing_timestamp": "2025-07-28T14:00:00Z"
      
    },
    
    "extracted_sections": [
    
      {
      
        "document": "doc1.pdf",
        
        "page_number": 3,
        
        "section_title": "Graph Neural Networks Overview",
        
        "importance_rank": 1
        
      }
      
    ],

  
    "sub_section_analysis": [
    
      {
      
        "document": "doc1.pdf",
        
        "page_number": 3,
        
        "refined_text": "Graph Neural Networks are ..."
        
      }
      
    ]
    
    }
  
  
## 📄 Notes
✅ Works offline – no API calls

✅ Supports OCR for scanned PDFs

✅ Compatible with linux/amd64, CPU‑only execution

✅ Model size ≤ 200 MB


