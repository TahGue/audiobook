"""Dedicated Arabic text extraction and normalization service.

Handles all the complexities of Arabic text processing:
- RTL (right-to-left) layout
- Unicode normalization
- Ligatures and contextual shaping
- Duplicate character removal
- Tatweel (kashida) removal
- Corruption detection
"""

import re
import unicodedata
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class ArabicProcessingResult:
    """Result of Arabic text processing."""
    text: str
    was_corrupted: bool
    fixes_applied: list
    confidence_score: float  # 0.0 to 1.0


class ArabicTextService:
    """Service for extracting and normalizing Arabic text from documents."""
    
    def __init__(self):
        self.arabic_range = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
        # Presentation forms (extracted glyphs) vs standard Arabic
        self.presentation_forms = re.compile(r'[\uFB50-\uFDFF\uFE70-\uFEFF]')
        self.standard_arabic = re.compile(r'[\u0600-\u06FF]')
        self.tatweel = '\u0640'  # Kashida character
        
    def contains_arabic(self, text: str) -> bool:
        """Check if text contains Arabic characters."""
        return bool(self.arabic_range.search(text))
    
    def contains_presentation_forms(self, text: str) -> bool:
        """Check if text contains Arabic Presentation Forms (extracted glyphs)."""
        return bool(self.presentation_forms.search(text))
    
    def count_arabic_chars(self, text: str) -> int:
        """Count Arabic characters in text."""
        return len(self.arabic_range.findall(text))
    
    def should_reshape(self, text: str) -> bool:
        """
        Determine if text needs reshaping.
        Returns True if text contains presentation forms that need conversion.
        """
        # If we have presentation forms, we likely need reshaping
        presentation_count = len(self.presentation_forms.findall(text))
        standard_count = len(self.standard_arabic.findall(text))
        
        # If mostly presentation forms, definitely reshape
        if presentation_count > standard_count:
            return True
        
        # If some presentation forms mixed in, probably needs fixing
        if presentation_count > 5:
            return True
            
        return False
    
    def is_corrupted(self, text: str) -> Tuple[bool, float]:
        """
        Detect if Arabic text is corrupted.
        Returns (is_corrupted, confidence_score).
        """
        if not self.contains_arabic(text):
            return False, 1.0
            
        issues = []
        
        # Check 1: Very low Arabic ratio (might be garbled)
        total_chars = len([c for c in text if c.isalpha()])
        arabic_chars = self.count_arabic_chars(text)
        if total_chars > 0:
            arabic_ratio = arabic_chars / total_chars
            if arabic_ratio < 0.3:  # Less than 30% Arabic
                issues.append("low_arabic_ratio")
        
        # Check 2: Excessive duplicate characters
        dup_pattern = re.compile(r'(.)\1{3,}')  # 4+ same chars
        if dup_pattern.search(text):
            issues.append("excessive_duplicates")
        
        # Check 3: Disconnected letters (spaces between Arabic letters)
        # Normal: "مرحبا" | Disconnected: "م ر ح ب ا"
        disconnected_pattern = re.compile(r'[\u0600-\u06FF]\s+[\u0600-\u06FF]')
        if disconnected_pattern.search(text):
            issues.append("disconnected_letters")
        
        # Check 4: Reversed punctuation
        # Arabic punctuation should be on the left side of text in RTL
        reversed_punct = re.compile(r'[.!?]\s+[\u0600-\u06FF]')
        if reversed_punct.search(text):
            issues.append("reversed_punctuation")
        
        # Check 5: Arabic Presentation Forms (extracted glyphs instead of text)
        # This is the most common issue with PDF extraction
        if self.contains_presentation_forms(text):
            presentation_count = len(self.presentation_forms.findall(text))
            if presentation_count > 10:
                issues.append("heavy_presentation_forms")
            else:
                issues.append("some_presentation_forms")
        
        # Calculate confidence score
        if not issues:
            return False, 1.0
        elif len(issues) == 1:
            return True, 0.7
        elif len(issues) == 2:
            return True, 0.4
        else:
            return True, 0.1
    
    def remove_tatweel(self, text: str) -> str:
        """Remove Tatweel (kashida) characters used for justification."""
        return text.replace(self.tatweel, '')
    
    def fix_duplicate_chars(self, text: str) -> str:
        """Fix duplicate characters (OCR artifacts)."""
        # Replace 3+ consecutive same chars with 1
        return re.sub(r'(.)\1{2,}', r'\1', text)
    
    def normalize_unicode(self, text: str) -> str:
        """Normalize Unicode to NFC form."""
        return unicodedata.normalize('NFC', text)
    
    def fix_disconnected_letters(self, text: str) -> str:
        """Fix disconnected Arabic letters (common in OCR)."""
        # Pattern: Arabic letter + space + Arabic letter
        # Replace with connected version
        pattern = re.compile(r'([\u0600-\u06FF])\s+([\u0600-\u06FF])')
        
        def replace_spaces(match):
            left, right = match.groups()
            # Don't join if it's intentional word boundary
            # Heuristic: if both are single letters, likely disconnected
            return left + right
        
        # Apply multiple times to handle chains
        for _ in range(5):
            new_text = pattern.sub(replace_spaces, text)
            if new_text == text:
                break
            text = new_text
        
        return text
    
    def fix_presentation_forms(self, text: str) -> str:
        """
        Convert Arabic Presentation Forms to standard Arabic.
        Uses unicodedata to decompose presentation forms.
        """
        import unicodedata
        
        result = []
        for char in text:
            code = ord(char)
            # Check if in Arabic Presentation Forms-A or B blocks
            if 0xFB50 <= code <= 0xFDFF or 0xFE70 <= code <= 0xFEFF:
                # Try to normalize to base Arabic form
                try:
                    # Many presentation forms normalize via NFKC
                    normalized = unicodedata.normalize('NFKC', char)
                    # If still a presentation form, try to map manually
                    if 0xFB50 <= ord(normalized) <= 0xFEFF:
                        # Use manual decomposition for remaining chars
                        normalized = self._decompose_presentation_form(char)
                    result.append(normalized)
                except:
                    result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _decompose_presentation_form(self, char: str) -> str:
        """Manually decompose a presentation form to base Arabic letter."""
        code = ord(char)
        
        # Arabic Presentation Forms-A (FB50-FDFF)
        if 0xFB50 <= code <= 0xFDFF:
            # Map to base Arabic block (0600-06FF)
            # This is a simplified mapping - covers common forms
            base = code - 0xFB50 + 0x0671  # Approximate mapping
            if 0x0600 <= base <= 0x06FF:
                return chr(base)
        
        # Arabic Presentation Forms-B (FE70-FEFF)
        if 0xFE70 <= code <= 0xFEFF:
            # These map to base Arabic forms
            base = code - 0xFE70 + 0x064B  # Approximate mapping
            if 0x0600 <= base <= 0x06FF:
                return chr(base)
        
        # Fallback: return original
        return char
    
    def fix_rtl_display(self, text: str) -> str:
        """
        Fix RTL display issues using arabic-reshaper and python-bidi.
        ALWAYS applies both reshape and bidi for any Arabic text with presentation forms.
        """
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            
            # arabic-reshaper handles presentation forms internally
            # It converts glyph shapes to proper connected Arabic
            reshaped = arabic_reshaper.reshape(text)
            
            # python-bidi fixes the visual order (LTR->RTL)
            fixed = get_display(reshaped)
            return fixed
            
        except ImportError:
            # Fallback: basic presentation form fixing
            return self.fix_presentation_forms(text)
    
    def clean_arabic_text(self, text: str) -> ArabicProcessingResult:
        """
        Full Arabic text cleaning pipeline.
        Returns processed text with metadata about fixes.
        """
        original = text
        fixes = []
        
        # Step 1: Check for corruption
        is_corrupted, confidence = self.is_corrupted(text)
        
        if not self.contains_arabic(text):
            return ArabicProcessingResult(
                text=text,
                was_corrupted=False,
                fixes_applied=["no_arabic"],
                confidence_score=1.0
            )
        
        # Step 2: Unicode normalization
        text = self.normalize_unicode(text)
        if text != original:
            fixes.append("unicode_normalization")
        
        # Step 3: Remove Tatweel (kashida)
        text_no_tatweel = self.remove_tatweel(text)
        if text_no_tatweel != text:
            text = text_no_tatweel
            fixes.append("removed_tatweel")
        
        # Step 4: Fix duplicate characters
        text_no_dupes = self.fix_duplicate_chars(text)
        if text_no_dupes != text:
            text = text_no_dupes
            fixes.append("fixed_duplicates")
            confidence += 0.2  # Boost confidence after fixing
        
        # Step 5: Fix disconnected letters
        text_connected = self.fix_disconnected_letters(text)
        if text_connected != text:
            text = text_connected
            fixes.append("connected_letters")
            confidence += 0.2
        
        # Step 6: Fix RTL display (if available)
        try:
            text_rtl = self.fix_rtl_display(text)
            if text_rtl != text:
                text = text_rtl
                fixes.append("rtl_display_fix")
        except Exception:
            pass
        
        # Ensure confidence doesn't exceed 1.0
        confidence = min(confidence, 1.0)
        
        return ArabicProcessingResult(
            text=text,
            was_corrupted=is_corrupted,
            fixes_applied=fixes,
            confidence_score=confidence
        )
    
    def split_arabic_sentences(self, text: str) -> list:
        """
        Split Arabic text into sentences.
        Handles Arabic punctuation: ؟ ، ؛
        """
        # Arabic sentence delimiters
        delimiters = r'[.!?؟]\s+'
        sentences = re.split(delimiters, text)
        
        # Clean up and filter empty sentences
        return [s.strip() for s in sentences if s.strip()]
    
    def extract_arabic_from_pdf(self, content: bytes, use_ocr_fallback: bool = True) -> ArabicProcessingResult:
        """
        Extract and clean Arabic text from PDF.
        Uses PyMuPDF with proper flags for Arabic and applies full cleaning pipeline.
        """
        import fitz
        
        text_parts = []
        doc = fitz.open(stream=content, filetype="pdf")
        
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Extract with flags to preserve ligatures and whitespace for Arabic
                # TEXT_PRESERVE_LIGATURES keeps Arabic letter connections
                # TEXT_PRESERVE_WHITESPACE maintains spacing structure
                page_text = page.get_text(
                    "text", 
                    flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE
                )
                
                if page_text.strip():
                    text_parts.append(page_text)
        finally:
            doc.close()
        
        raw_text = "\n\n".join(text_parts)
        
        # Apply Arabic cleaning pipeline
        result = self.clean_arabic_text(raw_text)
        
        # If confidence is very low and OCR fallback enabled, use OCR
        if result.confidence_score < 0.3 and use_ocr_fallback:
            # TODO: Implement OCR fallback with PaddleOCR or Tesseract
            pass
        
        return result


# Singleton instance
arabic_service = ArabicTextService()


def process_arabic_text(text: str) -> ArabicProcessingResult:
    """Convenience function for processing Arabic text."""
    return arabic_service.clean_arabic_text(text)


def extract_arabic_from_pdf(content: bytes) -> ArabicProcessingResult:
    """Convenience function for extracting Arabic from PDF."""
    return arabic_service.extract_arabic_from_pdf(content)
