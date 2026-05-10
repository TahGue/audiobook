from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import io

router = APIRouter()


class PageText(BaseModel):
    page: int
    text: str


class PDFExtractResponse(BaseModel):
    pages: List[PageText]
    total_pages: int
    total_chars: int
    full_text: str


@router.post("/extract/", response_model=PDFExtractResponse)
async def extract_pdf_text(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    content = await file.read()

    try:
        import pdfplumber
        pages = []
        full_text = ""

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                pages.append(PageText(page=i, text=text))
                full_text += text + "\n\n"

        full_text = full_text.strip()
        return PDFExtractResponse(
            pages=pages,
            total_pages=total_pages,
            total_chars=len(full_text),
            full_text=full_text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")


@router.post("/ocr/", response_model=PDFExtractResponse)
async def ocr_pdf(file: UploadFile = File(...), language: str = "ar"):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    content = await file.read()

    try:
        import easyocr
        import fitz  # PyMuPDF
        import numpy as np
        from PIL import Image

        # Initialize reader with download enabled
        reader = easyocr.Reader([language, "en"], gpu=False, download_enabled=True)
        doc = fitz.open(stream=content, filetype="pdf")
        pages = []
        full_text = ""

        # Limit to first 5 pages for faster processing
        max_pages = min(5, len(doc))
        for i in range(1, max_pages + 1):
            page = doc[i - 1]
            pix = page.get_pixmap(dpi=150)  # Lower DPI for faster processing
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_array = np.array(img)
            results = reader.readtext(img_array, detail=0, paragraph=True)
            text = "\n".join(results)
            pages.append(PageText(page=i, text=text))
            full_text += text + "\n\n"

        full_text = full_text.strip()
        return PDFExtractResponse(
            pages=pages,
            total_pages=max_pages,
            total_chars=len(full_text),
            full_text=full_text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")
