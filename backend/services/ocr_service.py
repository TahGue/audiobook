"""OCR Service supporting multiple engines: Surya (primary) and EasyOCR (fallback)."""

import os
import io
import tempfile
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import hashlib


class OCREngine(Enum):
    """Available OCR engines."""
    SURYA = "surya"  # Primary - fast, accurate, good Arabic
    EASYOCR = "easyocr"  # Fallback - supports 80+ languages


@dataclass
class OCRResult:
    """OCR extraction result."""
    text: str
    confidence: float
    bbox: Optional[List[float]] = None  # [x1, y1, x2, y2]
    page: int = 1


@dataclass
class OCROptions:
    """OCR processing options."""
    languages: List[str]
    engine: OCREngine = OCREngine.SURYA
    dpi: int = 200
    detect_only_text: bool = False


class OCRService:
    """Unified OCR service with multiple engine support."""
    
    def __init__(self, cache_dir: str = "./cache/ocr"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._surya_available = None
        self._easyocr_available = None
        self._easyocr_reader = None
    
    def _is_surya_available(self) -> bool:
        """Check if Surya OCR is installed."""
        if self._surya_available is None:
            try:
                import surya
                self._surya_available = True
            except ImportError:
                self._surya_available = False
        return self._surya_available
    
    def _is_easyocr_available(self) -> bool:
        """Check if EasyOCR is installed."""
        if self._easyocr_available is None:
            try:
                import easyocr
                self._easyocr_available = True
            except ImportError:
                self._easyocr_available = False
        return self._easyocr_available
    
    def _get_cache_key(self, content: bytes, options: OCROptions) -> str:
        """Generate cache key for OCR results."""
        key_data = f"{hashlib.md5(content).hexdigest()}:{options.engine.value}:{','.join(options.languages)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _render_pdf_page(self, pdf_content: bytes, page_num: int = 0, dpi: int = 200) -> 'PIL.Image':
        """Render a PDF page to an image."""
        import fitz  # PyMuPDF
        from PIL import Image
        
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        page = doc[page_num]
        
        # Render at specified DPI
        zoom = dpi / 72  # 72 is the default PDF DPI
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        
        return img
    
    def _ocr_surya(self, image: 'PIL.Image', options: OCROptions) -> List[OCRResult]:
        """Perform OCR using Surya."""
        from surya.ocr import run_ocr
        from surya.model.detection.model import load_model as load_det_model
        from surya.model.detection.processor import load_processor as load_det_processor
        from surya.model.recognition.model import load_model as load_rec_model
        from surya.model.recognition.processor import load_processor as load_rec_processor
        from PIL import Image
        
        # Load models (cached after first load)
        det_processor = load_det_processor()
        det_model = load_det_model()
        rec_model = load_rec_model()
        rec_processor = load_rec_processor()
        
        # Run OCR
        results = run_ocr(
            [image],
            [options.languages],
            det_model,
            det_processor,
            rec_model,
            rec_processor,
        )
        
        # Convert to OCRResult
        ocr_results = []
        for result in results:
            for text_line in result.text_lines:
                ocr_results.append(OCRResult(
                    text=text_line.text,
                    confidence=getattr(text_line, 'confidence', 0.9),
                    bbox=text_line.bbox if hasattr(text_line, 'bbox') else None,
                    page=1
                ))
        
        return ocr_results
    
    def _ocr_easyocr(self, image: 'PIL.Image', options: OCROptions) -> List[OCRResult]:
        """Perform OCR using EasyOCR as fallback."""
        import easyocr
        import numpy as np
        
        # Initialize reader if not already done
        if self._easyocr_reader is None:
            self._easyocr_reader = easyocr.Reader(
                options.languages,
                gpu=False,
                download_enabled=True
            )
        
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Run OCR
        results = self._easyocr_reader.readtext(img_array, detail=1)
        
        # Convert to OCRResult
        ocr_results = []
        for bbox, text, conf in results:
            ocr_results.append(OCRResult(
                text=text,
                confidence=conf,
                bbox=[bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1]],
                page=1
            ))
        
        return ocr_results
    
    def process_image(
        self,
        image: 'PIL.Image',
        options: Optional[OCROptions] = None
    ) -> List[OCRResult]:
        """Process a single image with OCR.
        
        Args:
            image: PIL Image to process
            options: OCR processing options
            
        Returns:
            List of OCR results
        """
        if options is None:
            options = OCROptions(languages=["en"])
        
        # Try primary engine first
        if options.engine == OCREngine.SURYA and self._is_surya_available():
            try:
                return self._ocr_surya(image, options)
            except Exception as e:
                print(f"Surya OCR failed, falling back to EasyOCR: {e}")
                if self._is_easyocr_available():
                    return self._ocr_easyocr(image, options)
                raise
        
        elif options.engine == OCREngine.EASYOCR and self._is_easyocr_available():
            return self._ocr_easyocr(image, options)
        
        # Fallback to whatever is available
        if self._is_surya_available():
            return self._ocr_surya(image, options)
        elif self._is_easyocr_available():
            return self._ocr_easyocr(image, options)
        else:
            raise ImportError(
                "No OCR engine available. Install either 'surya-ocr' or 'easyocr'."
            )
    
    def process_pdf(
        self,
        pdf_content: bytes,
        options: Optional[OCROptions] = None,
        max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process a PDF with OCR.
        
        Args:
            pdf_content: PDF file content as bytes
            options: OCR processing options
            max_pages: Maximum number of pages to process (None for all)
            
        Returns:
            Dictionary with extracted text and metadata
        """
        import fitz  # PyMuPDF
        
        if options is None:
            options = OCROptions(languages=["en"])
        
        # Open PDF
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        total_pages = len(doc)
        pages_to_process = min(total_pages, max_pages or total_pages)
        
        all_results = []
        full_text_parts = []
        
        for page_num in range(pages_to_process):
            # Render page to image
            image = self._render_pdf_page(pdf_content, page_num, options.dpi)
            
            # Process with OCR
            page_results = self.process_image(image, options)
            
            # Add page number to results
            for result in page_results:
                result.page = page_num + 1
            
            all_results.extend(page_results)
            
            # Combine text for this page
            page_text = "\n".join([r.text for r in page_results])
            full_text_parts.append(page_text)
        
        doc.close()
        
        # Combine all text
        full_text = "\n\n".join(full_text_parts).strip()
        
        # Calculate average confidence
        avg_confidence = sum(r.confidence for r in all_results) / len(all_results) if all_results else 0
        
        return {
            "text": full_text,
            "total_chars": len(full_text),
            "total_pages": pages_to_process,
            "ocr_results": all_results,
            "average_confidence": avg_confidence,
            "engine_used": options.engine.value,
        }
    
    def process_document(
        self,
        file_content: bytes,
        file_type: str,
        languages: List[str] = None,
        engine: OCREngine = None
    ) -> Dict[str, Any]:
        """Process any document type with OCR.
        
        Args:
            file_content: File content as bytes
            file_type: File extension (pdf, png, jpg, etc.)
            languages: List of language codes
            engine: OCR engine to use
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if languages is None:
            languages = ["en"]
        
        # Auto-select engine
        if engine is None:
            if self._is_surya_available():
                engine = OCREngine.SURYA
            elif self._is_easyocr_available():
                engine = OCREngine.EASYOCR
            else:
                raise ImportError("No OCR engine available")
        
        options = OCROptions(languages=languages, engine=engine)
        
        file_type = file_type.lower()
        
        if file_type == "pdf":
            return self.process_pdf(file_content, options)
        elif file_type in ["png", "jpg", "jpeg", "tiff", "bmp", "gif"]:
            from PIL import Image
            image = Image.open(io.BytesIO(file_content))
            results = self.process_image(image, options)
            full_text = "\n".join([r.text for r in results])
            return {
                "text": full_text,
                "total_chars": len(full_text),
                "total_pages": 1,
                "ocr_results": results,
                "average_confidence": sum(r.confidence for r in results) / len(results) if results else 0,
                "engine_used": engine.value,
            }
        else:
            raise ValueError(f"Unsupported file type for OCR: {file_type}")


# Global OCR service instance
ocr_service = OCRService()
