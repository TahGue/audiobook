"""Unified document extraction router supporting PDF, EPUB, and DOCX."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import io
import hashlib

router = APIRouter()


class DocumentExtractResponse(BaseModel):
    """Response model for document text extraction."""
    text: str
    total_chars: int
    file_type: str
    file_name: str
    cached: bool = False


def get_file_hash(content: bytes) -> str:
    """Generate MD5 hash of file content for caching."""
    return hashlib.md5(content).hexdigest()


def clean_arabic_text(text: str) -> str:
    """Clean and fix common issues with Arabic text extraction."""
    import re
    
    # Remove duplicate consecutive characters (common PDF extraction issue)
    # Replace 3+ same characters with 1
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    
    # Fix common ligature issues
    # Replace presentation forms with standard Arabic
    text = text.replace('\ufb50', '\u0627')  # alef with hamza
    text = text.replace('\ufb51', '\u0627')  # alef with hamza
    text = text.replace('\ufb52', '\u0628')  # beh
    text = text.replace('\ufb56', '\u062a')  # teh
    text = text.replace('\ufb5a', '\u062b')  # theh
    text = text.replace('\ufb5e', '\u062c')  # jeem
    text = text.replace('\ufb62', '\u062d')  # hah
    text = text.replace('\ufb66', '\u062e')  # khah
    
    # Remove zero-width characters and control characters
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e\ufeff]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # multiple spaces/tabs to single space
    text = re.sub(r'\n{3,}', '\n\n', text)  # 3+ newlines to 2
    
    return text.strip()


def extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF using PyMuPDF (better Arabic support)."""
    import fitz  # PyMuPDF
    
    text_parts = []
    doc = fitz.open(stream=content, filetype="pdf")
    
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Extract text with layout preservation
            text = page.get_text("text")
            if text.strip():
                text_parts.append(text)
    finally:
        doc.close()
    
    raw_text = "\n\n".join(text_parts).strip()
    return clean_arabic_text(raw_text)


def extract_epub_text(content: bytes) -> str:
    """Extract text from EPUB using ebooklib."""
    from ebooklib import epub
    from bs4 import BeautifulSoup
    
    # Write to temp file since ebooklib needs a file path
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        book = epub.read_epub(tmp_path)
        text_parts = []
        
        # Extract text from all HTML documents in the EPUB
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                html_content = item.get_content().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                text_parts.append(text)
        
        return "\n\n".join(text_parts).strip()
    finally:
        os.unlink(tmp_path)


def extract_docx_text(content: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    from docx import Document
    
    doc = Document(io.BytesIO(content))
    text_parts = []
    
    # Extract text from paragraphs
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)
    
    # Extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                if cell.text.strip():
                    row_text.append(cell.text.strip())
            if row_text:
                text_parts.append(" | ".join(row_text))
    
    return "\n\n".join(text_parts).strip()


@router.post("/extract/", response_model=DocumentExtractResponse)
async def extract_document(
    file: UploadFile = File(...),
    use_cache: bool = True
):
    """
    Extract text from uploaded document (PDF, EPUB, or DOCX).
    
    Supports:
    - PDF (.pdf)
    - EPUB (.epub)  
    - Word Documents (.docx)
    
    Returns extracted text with metadata.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # Determine file type
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.pdf'):
            text = extract_pdf_text(content)
            file_type = "pdf"
        elif filename.endswith('.epub'):
            text = extract_epub_text(content)
            file_type = "epub"
        elif filename.endswith('.docx'):
            text = extract_docx_text(content)
            file_type = "docx"
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.filename}. Supported: PDF, EPUB, DOCX"
            )
        
        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail="No text could be extracted from the document. The file may be empty, corrupted, or contain only images."
            )
        
        return DocumentExtractResponse(
            text=text,
            total_chars=len(text),
            file_type=file_type,
            file_name=file.filename,
            cached=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract text from {file.filename}: {str(e)}"
        )


@router.get("/supported-formats/")
async def get_supported_formats():
    """Get list of supported document formats."""
    return {
        "formats": [
            {
                "extension": ".pdf",
                "mime_type": "application/pdf",
                "name": "PDF Document",
                "description": "Portable Document Format"
            },
            {
                "extension": ".epub",
                "mime_type": "application/epub+zip",
                "name": "EPUB eBook",
                "description": "Electronic Publication format"
            },
            {
                "extension": ".docx",
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "name": "Word Document",
                "description": "Microsoft Word Open XML format"
            }
        ],
        "recommended_for_arabic": [".pdf", ".epub"],
        "max_file_size_mb": 50
    }
