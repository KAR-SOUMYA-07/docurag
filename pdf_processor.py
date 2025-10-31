"""
PDF and Document Processor
Extracts text from various document formats: PDF, TXT, DOCX, DOC
"""

import os
from typing import Optional, List
import PyPDF2
from docx import Document

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text.strip()
    except Exception as e:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                text = file.read()
            return text.strip()
        except:
            print(f"Error extracting text from TXT: {e}")
            return ""

def process_document(file_path: str) -> Optional[str]:
    """
    Process document and extract text based on file extension
    Supports: .pdf, .txt, .docx, .doc
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext == '.txt':
        return extract_text_from_txt(file_path)
    elif file_ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    else:
        print(f"Unsupported file format: {file_ext}")
        return None

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to split
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
    
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        # Try to break at sentence or word boundary
        if end < text_length:
            # Look for sentence end
            for i in range(end, start + overlap, -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
            else:
                # Look for word boundary
                for i in range(end, start + overlap, -1):
                    if text[i].isspace():
                        end = i
                        break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks

if __name__ == '__main__':
    # Test the processor
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"Processing: {file_path}")
        text = process_document(file_path)
        if text:
            print(f"\nExtracted {len(text)} characters")
            print(f"First 500 characters:\n{text[:500]}")
            
            chunks = chunk_text(text)
            print(f"\nCreated {len(chunks)} chunks")
        else:
            print("Failed to extract text")
