import time
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, JSONResponse, FileResponse
from typing import Dict, Any

from .models import DocumentProcessResponse, ClassificationResult
from .ocr_engine import preprocess_and_load_file, run_paddle_ocr
from .classifier import classify_document
from .extractors import extract_and_validate
from .sample_generator import get_sample_bytes

app = FastAPI(
    title="Indian Document Classification & Extraction Engine",
    description="Intelligent OCR pipeline using PaddleOCR, OpenCV, and Regex Rules for Aadhaar, PAN, SSC Marks Card, Passport, and Income Certificate.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "supported_documents": ["aadhaar", "pan", "ssc", "passport", "income_cert"],
        "ocr_engine": "PaddleOCR 3.7 (PP-OCRv6)",
        "pdf_renderer": "pypdfium2"
    }

@app.post("/api/process", response_model=DocumentProcessResponse)
async def process_document(file: UploadFile = File(...)):
    start_time = time.time()
    filename = file.filename or "uploaded_document"
    
    # Read file bytes
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    return run_pipeline(content, filename, start_time)

@app.post("/api/process-sample/{doc_type}", response_model=DocumentProcessResponse)
async def process_sample(doc_type: str):
    valid_types = ["aadhaar", "pan", "ssc", "passport", "income_cert"]
    if doc_type not in valid_types:
        raise HTTPException(status_code=404, detail=f"Sample type '{doc_type}' not found. Choose from {valid_types}")

    start_time = time.time()
    sample_bytes = get_sample_bytes(doc_type)
    filename = f"sample_{doc_type}.png"
    return run_pipeline(sample_bytes, filename, start_time)

@app.get("/api/sample/{doc_type}")
async def get_sample_image(doc_type: str):
    valid_types = ["aadhaar", "pan", "ssc", "passport", "income_cert"]
    if doc_type not in valid_types:
        raise HTTPException(status_code=404, detail="Invalid sample type")
    
    img_bytes = get_sample_bytes(doc_type)
    return Response(content=img_bytes, media_type="image/png")

def run_pipeline(content: bytes, filename: str, start_time: float) -> DocumentProcessResponse:
    # 1. Preprocessing & Page Loading
    pages = preprocess_and_load_file(content, filename)
    if not pages:
        raise HTTPException(status_code=400, detail="Unable to extract pages from uploaded file.")

    # 2. PaddleOCR Execution & CV Feature Extraction
    ocr_meta = run_paddle_ocr(pages)
    lines = ocr_meta.get("lines", [])
    full_text = ocr_meta.get("full_text", "")

    # 3. Document Classification
    classification = classify_document(full_text, lines)

    # 4. Document-Specific Extraction & Validation
    extracted_data, validation_issues, val_status = extract_and_validate(
        classification.doc_type,
        lines,
        ocr_meta
    )

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    return DocumentProcessResponse(
        filename=filename,
        page_count=len(pages),
        classification=classification,
        extracted_data=extracted_data,
        validation_status=val_status,
        validation_issues=validation_issues,
        raw_ocr_lines=lines,
        processing_time_ms=elapsed_ms
    )

# Serve frontend static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend index.html not found"}
