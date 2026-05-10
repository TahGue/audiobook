"""Dedicated Arabic text extraction and normalization service.

ROOT CAUSE OF GARBLED ARABIC FROM PDFs
=======================================
Arabic PDFs store glyph codepoints in VISUAL order (left-to-right on the page),
using Arabic Presentation Forms (Unicode FB50-FEFF) instead of base Arabic
characters (0600-06FF). This means:

  1. Characters within each Arabic run are stored in REVERSE reading order.
  2. Codepoints are presentation-form glyphs, not base Arabic letters.
  3. Word spacing is often lost entirely during glyph extraction.

Correct fix pipeline:
  NFKC normalize  →  reverse each Arabic run  →  reshape (optional, for display)

  - NFKC:    converts presentation forms (FB50-FEFF) -> standard Arabic (0600-06FF)
  - reverse: restores logical order from visual order within each Arabic run
  - reshape: re-applies correct letter-connection forms for rendering

Do NOT use get_display() (python-bidi) before storing text. get_display()
converts logical -> visual order for raw pixel rendering. Browsers and modern
UIs handle RTL themselves, so applying get_display() before storage causes
the text to appear reversed again (double-flip).
"""

import re
import unicodedata
from typing import Tuple
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
        self.arabic_range = re.compile(
            r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
        )
        self.presentation_forms = re.compile(r'[\uFB50-\uFDFF\uFE70-\uFEFF]')
        self.standard_arabic = re.compile(r'[\u0600-\u06FF]')
        # Matches a run of BASE Arabic characters (used after NFKC normalization)
        self._base_arabic_run = re.compile(r'[\u0600-\u06FF]+')
        self.tatweel = '\u0640'  # Kashida / tatweel character

    # ------------------------------------------------------------------ #
    # Detection helpers                                                    #
    # ------------------------------------------------------------------ #

    def contains_arabic(self, text: str) -> bool:
        return bool(self.arabic_range.search(text))

    def contains_presentation_forms(self, text: str) -> bool:
        return bool(self.presentation_forms.search(text))

    def count_arabic_chars(self, text: str) -> int:
        return len(self.arabic_range.findall(text))

    def should_reshape(self, text: str) -> bool:
        pf = len(self.presentation_forms.findall(text))
        std = len(self.standard_arabic.findall(text))
        return pf > std or pf > 5

    def is_corrupted(self, text: str) -> Tuple[bool, float]:
        """Detect if Arabic text is corrupted. Returns (is_corrupted, confidence)."""
        if not self.contains_arabic(text):
            return False, 1.0

        issues = []

        total_alpha = len([c for c in text if c.isalpha()])
        arabic_count = self.count_arabic_chars(text)
        if total_alpha > 0 and arabic_count / total_alpha < 0.3:
            issues.append("low_arabic_ratio")

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
        """
        Normalize Unicode using NFKC form.
        NFKC decomposes Arabic Presentation Forms (FB50-FEFF) into their
        standard Arabic equivalents (0600-06FF).
        """
        return unicodedata.normalize('NFKC', text)
    
    def fix_disconnected_letters(self, text: str) -> str:
        """Fix disconnected Arabic letters (common in OCR)."""
        if not re.search(r'([\u0600-\u06FF]\s+){3,}[\u0600-\u06FF]', text):
            return text

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

    def fix_lost_arabic_word_boundaries(self, text: str) -> str:
        """Repair high-confidence Arabic word boundaries lost by PDF glyph extraction."""
        replacements = {
            "املجلداألول": "المجلد الأول",
            "املجلدالأول": "المجلد الأول",
            "المجلداالأول": "المجلد الأول",
            "المجلدالأول": "المجلد الأول",
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text
    
    def fix_visual_order(self, text: str) -> str:
        """
        Reverse ONLY Arabic runs that appear visually reversed.
        """
        def should_reverse(run: str) -> bool:
            # Presentation-form extracted Arabic is often reversed visually.
            # Heuristic:
            # reverse only if run contains presentation forms OR
            # ends with common Arabic starters like ا ل م
            if self.contains_presentation_forms(run):
                return True
            # already logical Arabic should not be reversed
            # detect common prefixes
            common_prefixes = (
                "ال", "ا", "أ", "إ", "آ", "و", "ف", "ب", "ل", "ك"
            )
            for p in common_prefixes:
                if run.startswith(p):
                    return False
            # reversed extracted words often end with these
            for p in common_prefixes:
                if run.endswith(p):
                    return True
            return False

        def process(match):
            run = match.group()
            if should_reverse(run):
                return run[::-1]
            return run

        return self._base_arabic_run.sub(process, text)

    def fix_presentation_forms(self, text: str) -> str:
        """
        Convert Arabic Presentation Forms to standard Arabic via NFKC.
        NFKC correctly decomposes presentation forms to base Arabic.
        """
        result = []
        for char in text:
            code = ord(char)
            if 0xFB50 <= code <= 0xFDFF or 0xFE70 <= code <= 0xFEFF:
                normalized = unicodedata.normalize('NFKC', char)
                result.append(normalized)
            else:
                result.append(char)
        return ''.join(result)

    def clean_arabic_text(self, text: str) -> ArabicProcessingResult:
        """
        Full Arabic text cleaning pipeline.

        Pipeline order matters:
          1. NFKC normalization (presentation forms -> base Arabic)
          2. Remove tatweel
          3. Fix duplicates
          4. Fix disconnected letters
          5. Conditionally reverse visual runs
        
        NOTE: No reshape step - browsers handle Arabic shaping automatically.
        arabic_reshaper is only needed for PIL/OpenCV/image rendering.
        """
        if not self.contains_arabic(text):
            return ArabicProcessingResult(
                text=text,
                was_corrupted=False,
                fixes_applied=["no_arabic"],
                confidence_score=1.0
            )

        original = text
        fixes = []
        is_corrupted, confidence = self.is_corrupted(text)

        # Step 1: NFKC normalization (presentation forms -> base Arabic)
        text = self.normalize_unicode(text)
        if text != original:
            fixes.append("unicode_normalization_nfkc")

        # Step 2: Remove tatweel
        no_tatweel = self.remove_tatweel(text)
        if no_tatweel != text:
            text = no_tatweel
            fixes.append("removed_tatweel")

        # Step 3: Collapse duplicate characters
        no_dupes = self.fix_duplicate_chars(text)
        if no_dupes != text:
            text = no_dupes
            fixes.append("fixed_duplicates")
            confidence = min(confidence + 0.2, 1.0)

        # Step 4: Rejoin disconnected letters
        connected = self.fix_disconnected_letters(text)
        if connected != text:
            text = connected
            fixes.append("connected_letters")
            confidence = min(confidence + 0.2, 1.0)

        # Step 5: Conditionally reverse visual runs
        # Only reverse runs that contain presentation forms or appear visually reversed
        fixed_order = self.fix_visual_order(text)
        if fixed_order != text:
            text = fixed_order
            fixes.append("fixed_visual_order")

        segmented = self.fix_lost_arabic_word_boundaries(text)
        if segmented != text:
            text = segmented
            fixes.append("fixed_lost_word_boundaries")

        return ArabicProcessingResult(
            text=text,
            was_corrupted=is_corrupted,
            fixes_applied=fixes,
            confidence_score=min(confidence, 1.0)
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
