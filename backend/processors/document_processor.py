import hashlib
import re
from pathlib import Path
from typing import List
from docx import Document
from pypdf import PdfReader


class DocumentProcessor:
    def compute_file_hash(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as stream:
            while chunk := stream.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def extract_text(self, file_path: Path, mime_type: str) -> str:
        extension = file_path.suffix.lower()

        if extension == ".pdf" or "pdf" in mime_type:
            return self._extract_pdf_text(file_path)
        elif extension == ".docx" or "wordprocessingml" in mime_type:
            return self._extract_docx_text(file_path)
        else:
            return self._extract_plain_text(file_path)

    def _extract_pdf_text(self, file_path: Path) -> str:
        reader = PdfReader(str(file_path))
        extracted_pages = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text)
        return "\n\n".join(extracted_pages)

    def _extract_docx_text(self, file_path: Path) -> str:
        document = Document(str(file_path))
        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    def _extract_plain_text(self, file_path: Path) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as stream:
                return stream.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as stream:
                return stream.read()

    def preprocess_text(self, raw_text: str) -> str:
        cleaned = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 700,
        chunk_overlap: int = 100
    ) -> List[str]:
        cleaned_text = self.preprocess_text(text)
        if not cleaned_text:
            return []

        if len(cleaned_text) <= chunk_size:
            return [cleaned_text]

        chunks = []
        start_index = 0
        text_length = len(cleaned_text)

        while start_index < text_length:
            end_index = start_index + chunk_size
            if end_index >= text_length:
                chunk = cleaned_text[start_index:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            split_position = cleaned_text.rfind("\n\n", start_index, end_index)
            if split_position == -1:
                split_position = cleaned_text.rfind("\n", start_index, end_index)
            if split_position == -1:
                split_position = cleaned_text.rfind(". ", start_index, end_index)
                if split_position != -1:
                    split_position += 1
            if split_position == -1 or split_position <= start_index:
                split_position = cleaned_text.rfind(" ", start_index, end_index)

            if split_position == -1 or split_position <= start_index:
                split_position = end_index

            chunk = cleaned_text[start_index:split_position].strip()
            if chunk:
                chunks.append(chunk)

            start_index = max(split_position - chunk_overlap, start_index + 1)

        return chunks


document_processor = DocumentProcessor()
