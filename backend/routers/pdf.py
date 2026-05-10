from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List

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
        import fitz
        from services.arabic_text_service import arabic_service

        pages = []
        text_parts = []
        doc = fitz.open(stream=content, filetype="pdf")

        try:
            total_pages = len(doc)
            for i in range(total_pages):
                page = doc[i]
                raw_text = page.get_text(
                    "text",
                    flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE
                )
                processed = arabic_service.clean_arabic_text(raw_text).text if raw_text.strip() else ""
                pages.append(PageText(page=i + 1, text=processed))
                if processed:
                    text_parts.append(processed)
        finally:
            doc.close()

        full_text = "\n\n".join(text_parts).strip()
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
