"""
Document Text Extraction Module
Extracts raw text from PDF and DOCX documents with support for file paths
and file-like objects (e.g., Streamlit UploadedFile, io.BytesIO).
"""

import io
import re
from pathlib import Path
from typing import Union, BinaryIO

import docx
from PyPDF2 import PdfReader


def _clean_extracted_text(text: str) -> str:
    """
    Sanitizes and normalizes extracted raw document text.
    Removes null bytes, excess whitespace, and inconsistent newlines.
    """
    if not text:
        return ""
    # Strip null characters and carriage returns
    text = text.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-breaking spaces
    text = text.replace("\xa0", " ")
    # Normalize multiple horizontal whitespaces to single space
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize more than two consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(file_input: Union[str, Path, BinaryIO, io.BytesIO]) -> str:
    """
    Extracts plain text from a PDF file path or binary stream using PyPDF2.

    Args:
        file_input: File path (str or Path) or binary file stream.

    Returns:
        Extracted text string.
    """
    extracted_pages = []
    
    # Check if file_input is a path or stream
    is_path = isinstance(file_input, (str, Path))
    
    try:
        if is_path:
            reader = PdfReader(str(file_input))
        else:
            # If it's a stream, ensure pointer is at beginning
            if hasattr(file_input, "seek"):
                file_input.seek(0)
            reader = PdfReader(file_input)

        for page_idx, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    extracted_pages.append(page_text)
            except Exception as page_err:
                # Log or handle individual page extraction error
                continue
                
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")

    raw_text = "\n\n".join(extracted_pages)
    return _clean_extracted_text(raw_text)


def extract_text_from_docx(file_input: Union[str, Path, BinaryIO, io.BytesIO]) -> str:
    """
    Extracts plain text from a DOCX file path or binary stream using python-docx.
    Extracts text from paragraphs, tables (crucial for resume skill tables), and headers.

    Args:
        file_input: File path (str or Path) or binary file stream.

    Returns:
        Extracted text string.
    """
    try:
        if not isinstance(file_input, (str, Path)):
            if hasattr(file_input, "seek"):
                file_input.seek(0)
            # python-docx accepts BytesIO directly
            if isinstance(file_input, bytes):
                file_input = io.BytesIO(file_input)
                
        doc = docx.Document(file_input)
        
        text_elements = []

        # 1. Extract from paragraphs
        for para in doc.paragraphs:
            para_text = para.text.strip()
            if para_text:
                text_elements.append(para_text)

        # 2. Extract from tables (many resumes format skills/education in tables)
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                # De-duplicate cell text in case of merged cells
                unique_cells = []
                for cell_text in row_cells:
                    if not unique_cells or cell_text != unique_cells[-1]:
                        unique_cells.append(cell_text)
                if unique_cells:
                    text_elements.append(" | ".join(unique_cells))

        # 3. Extract from section headers
        for section in doc.sections:
            header = section.header
            for header_para in header.paragraphs:
                header_text = header_para.text.strip()
                if header_text and header_text not in text_elements:
                    text_elements.insert(0, header_text)

    except Exception as e:
        raise ValueError(f"Error reading DOCX: {str(e)}")

    raw_text = "\n".join(text_elements)
    return _clean_extracted_text(raw_text)


def extract_text(file_input: Union[str, Path, BinaryIO, io.BytesIO], filename: str = None) -> str:
    """
    Unified entry point to extract text from PDF, DOCX, or plain text files.
    
    Args:
        file_input: File path or file-like object.
        filename: Optional filename hint to determine extension if file_input is a stream.

    Returns:
        Extracted, sanitized text string.
    """
    # Determine extension
    ext = ""
    if filename:
        ext = Path(filename).suffix.lower()
    elif isinstance(file_input, (str, Path)):
        ext = Path(file_input).suffix.lower()
    elif hasattr(file_input, "name"):
        ext = Path(file_input.name).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_input)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_input)
    elif ext in [".txt", ".md"]:
        if isinstance(file_input, (str, Path)):
            with open(file_input, "r", encoding="utf-8", errors="ignore") as f:
                return _clean_extracted_text(f.read())
        else:
            if hasattr(file_input, "seek"):
                file_input.seek(0)
            content = file_input.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
            return _clean_extracted_text(content)
    else:
        # Default fallback attempt: try PDF first, then DOCX, then plain text
        try:
            return extract_text_from_pdf(file_input)
        except Exception:
            try:
                return extract_text_from_docx(file_input)
            except Exception:
                raise ValueError(
                    f"Unsupported or unrecognized file format '{ext}'. "
                    "Please provide a valid PDF (.pdf) or Word document (.docx)."
                )
