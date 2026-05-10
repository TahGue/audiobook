from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ArabicProcessRequest(BaseModel):
    text: str
    add_diacritics: bool = True


class ArabicProcessResponse(BaseModel):
    processed_text: str
    original_text: str
    diacritics_added: bool


@router.post("/process/", response_model=ArabicProcessResponse)
async def process_arabic_text(request: ArabicProcessRequest):
    """
    Process Arabic text to add diacritics (tachkil) and improve readability.
    """
    try:
        from mishkal.tashkeel import TashkeelClass
        
        # Initialize Mishkal tashkeel
        tashkeel = TashkeelClass()
        
        processed_text = request.text
        
        # Add diacritics if requested
        if request.add_diacritics:
            # Mishkal can add diacritics to Arabic text
            processed_text = tashkeel.tashkeel(request.text)
        
        return ArabicProcessResponse(
            processed_text=processed_text,
            original_text=request.text,
            diacritics_added=request.add_diacritics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arabic text processing failed: {str(e)}")


@router.post("/diacritize/", response_model=ArabicProcessResponse)
async def diacritize_text(request: ArabicProcessRequest):
    """
    Add diacritics (tachkil) to Arabic text.
    Processes text in chunks if it's too long.
    """
    try:
        from mishkal.tashkeel import TashkeelClass
        
        tashkeel = TashkeelClass()
        text = request.text
        
        # Process in chunks if text is long (mishkal can be slow on large texts)
        max_chunk_size = 500  # characters
        
        if len(text) <= max_chunk_size:
            diacritized_text = tashkeel.tashkeel(text)
        else:
            # Split by lines first to preserve structure
            lines = text.split('\n')
            result_lines = []
            
            for line in lines:
                if len(line) <= max_chunk_size:
                    # Process short lines directly
                    if line.strip():
                        result_lines.append(tashkeel.tashkeel(line))
                    else:
                        result_lines.append(line)
                else:
                    # Split long lines by sentences (periods)
                    sentences = line.split('.')
                    result_sentences = []
                    
                    for sentence in sentences:
                        if sentence.strip():
                            result_sentences.append(tashkeel.tashkeel(sentence))
                    
                    result_lines.append('.'.join(result_sentences))
            
            diacritized_text = '\n'.join(result_lines)
        
        return ArabicProcessResponse(
            processed_text=diacritized_text,
            original_text=request.text,
            diacritics_added=True
        )
    except Exception as e:
        import traceback
        print(f"Diacritization error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Diacritization failed: {str(e)}")
