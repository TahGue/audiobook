"""
Chapter Auto-Split Service

Intelligently splits long text into chapters based on:
- Headings and subheadings
- Paragraph breaks
- Content length thresholds
- Natural language processing cues
"""
import re
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class ChapterSplit:
    title: str
    content: str
    start_index: int
    end_index: int


class ChapterSplitService:
    """Service for automatically splitting text into chapters."""
    
    def __init__(self, target_chapter_length: int = 5000):
        """
        Initialize the chapter split service.
        
        Args:
            target_chapter_length: Target character count per chapter
        """
        self.target_chapter_length = target_chapter_length
        self.min_chapter_length = target_chapter_length // 2
        self.max_chapter_length = target_chapter_length * 2
    
    def split_text(self, text: str, language: str = 'en') -> List[ChapterSplit]:
        """
        Split text into chapters automatically.
        
        Args:
            text: Input text to split
            language: Text language (affects heading detection patterns)
            
        Returns:
            List of ChapterSplit objects
        """
        if not text or len(text) < self.min_chapter_length:
            # Text too short, return as single chapter
            return [ChapterSplit(
                title=self._generate_title(text, 0),
                content=text,
                start_index=0,
                end_index=len(text)
            )]
        
        # Try heading-based split first
        chapters = self._split_by_headings(text, language)
        
        # If heading-based split didn't work well, try paragraph-based
        if len(chapters) < 2 or all(len(c.content) > self.max_chapter_length for c in chapters):
            chapters = self._split_by_paragraphs(text)
        
        # Merge very short chapters
        chapters = self._merge_short_chapters(chapters)
        
        # Split very long chapters
        chapters = self._split_long_chapters(chapters)
        
        # Ensure all chapters have titles
        for i, chapter in enumerate(chapters):
            if not chapter.title.strip():
                chapter.title = self._generate_title(chapter.content, i)
        
        return chapters
    
    def _split_by_headings(self, text: str, language: str) -> List[ChapterSplit]:
        """Split text based on headings."""
        chapters = []
        
        # Common heading patterns
        heading_patterns = [
            r'\n([A-Z][^\n]{1,100})\n',  # All caps or title case lines
            r'\n(Chapter \d+[:\s].+?)\n',  # Chapter X: Title
            r'\n(Part \d+[:\s].+?)\n',  # Part X: Title
            r'\n(#{1,3}\s.+?)\n',  # Markdown headings
            r'\n(\d+\.\s.+?)\n',  # Numbered sections
        ]
        
        # Find all potential heading positions
        heading_positions = []
        for pattern in heading_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                heading_positions.append((match.start(), match.group(1).strip()))
        
        # Sort by position
        heading_positions.sort(key=lambda x: x[0])
        
        # Create chapters based on headings
        for i, (start, title) in enumerate(heading_positions):
            end = heading_positions[i + 1][0] if i + 1 < len(heading_positions) else len(text)
            content = text[start:end].strip()
            
            # Skip if content is too short
            if len(content) < self.min_chapter_length:
                continue
            
            chapters.append(ChapterSplit(
                title=title,
                content=content,
                start_index=start,
                end_index=end
            ))
        
        # If no headings found, return empty list
        if not chapters:
            return []
        
        return chapters
    
    def _split_by_paragraphs(self, text: str) -> List[ChapterSplit]:
        """Split text by paragraphs, aiming for target length."""
        paragraphs = text.split('\n\n')
        chapters = []
        current_content = []
        current_length = 0
        chapter_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph would exceed max length, start new chapter
            if current_length + len(para) > self.max_chapter_length and current_length >= self.min_chapter_length:
                content = '\n\n'.join(current_content).strip()
                chapters.append(ChapterSplit(
                    title=self._generate_title(content, chapter_index),
                    content=content,
                    start_index=0,  # Will be recalculated
                    end_index=0
                ))
                current_content = []
                current_length = 0
                chapter_index += 1
            
            current_content.append(para)
            current_length += len(para)
        
        # Add remaining content
        if current_content:
            content = '\n\n'.join(current_content).strip()
            chapters.append(ChapterSplit(
                title=self._generate_title(content, chapter_index),
                content=content,
                start_index=0,
                end_index=0
            ))
        
        return chapters
    
    def _merge_short_chapters(self, chapters: List[ChapterSplit]) -> List[ChapterSplit]:
        """Merge chapters that are too short."""
        if len(chapters) <= 1:
            return chapters
        
        merged = []
        i = 0
        
        while i < len(chapters):
            current = chapters[i]
            
            # If chapter is too short, merge with next
            if len(current.content) < self.min_chapter_length and i + 1 < len(chapters):
                next_chapter = chapters[i + 1]
                merged_content = current.content + '\n\n' + next_chapter.content
                merged.append(ChapterSplit(
                    title=current.title,
                    content=merged_content,
                    start_index=current.start_index,
                    end_index=next_chapter.end_index
                ))
                i += 2  # Skip the merged chapter
            else:
                merged.append(current)
                i += 1
        
        return merged
    
    def _split_long_chapters(self, chapters: List[ChapterSplit]) -> List[ChapterSplit]:
        """Split chapters that are too long."""
        result = []
        
        for chapter in chapters:
            if len(chapter.content) <= self.max_chapter_length:
                result.append(chapter)
                continue
            
            # Split long chapter
            paragraphs = chapter.content.split('\n\n')
            sub_chapters = self._split_by_paragraphs(chapter.content)
            
            # Update titles for sub-chapters
            for i, sub_chapter in enumerate(sub_chapters):
                sub_chapter.title = f"{chapter.title} - Part {i + 1}"
            
            result.extend(sub_chapters)
        
        return result
    
    def _generate_title(self, content: str, index: int) -> str:
        """Generate a title for a chapter based on content."""
        # Try to extract first meaningful line
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 3 and len(line) < 100:
                # Check if it looks like a heading (short, possibly capitalized)
                if len(line.split()) <= 10:
                    return line
        
        # Default to chapter number
        return f"Chapter {index + 1}"


# Singleton instance
chapter_split_service = ChapterSplitService()
