import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Tuple
from backend.config import application_settings


class SecurityException(Exception):
    pass


class SecurityService:
    PROMPT_INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|directives)", re.IGNORECASE),
        re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|directives)", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|unrestricted)", re.IGNORECASE),
        re.compile(r"bypass\s+(all\s+)?(safety|security|filters|restrictions)", re.IGNORECASE),
        re.compile(r"reveal\s+(the\s+)?(system\s+prompt|master\s+prompt|instructions)", re.IGNORECASE),
        re.compile(r"new\s+system\s+instructions:", re.IGNORECASE),
        re.compile(r"\[system\s+override\]", re.IGNORECASE),
        re.compile(r"mode:\s*unrestricted", re.IGNORECASE)
    ]

    MAGIC_SIGNATURES = {
        "pdf": b"%PDF-",
        "png": b"\x89PNG\r\n\x1a\n",
        "jpeg": b"\xff\xd8\xff",
        "docx": b"PK\x03\x04"
    }

    def __init__(self):
        self.request_records = defaultdict(list)
        self.rate_limit_per_minute = application_settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.max_file_size_bytes = application_settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def sanitize_filename(self, filename: str) -> str:
        base_name = Path(filename).name
        cleaned = re.sub(r"[^a-zA-Z0-9_\.-]", "_", base_name)
        if not cleaned or cleaned.startswith("."):
            cleaned = f"file_{cleaned}"
        return cleaned

    def validate_file_size_and_path(self, file_bytes: bytes, filename: str) -> Path:
        if len(file_bytes) > self.max_file_size_bytes:
            raise SecurityException(
                f"File size exceeds maximum permitted limit of {application_settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        sanitized_name = self.sanitize_filename(filename)
        destination = application_settings.upload_directory_path / sanitized_name

        try:
            destination.resolve().relative_to(application_settings.upload_directory_path.resolve())
        except ValueError:
            raise SecurityException("Path traversal attempt detected.")

        return destination

    def verify_file_magic_bytes(self, file_bytes: bytes, file_type: str) -> bool:
        if len(file_bytes) < 4:
            return False

        if file_type == "image":
            is_png = file_bytes.startswith(self.MAGIC_SIGNATURES["png"])
            is_jpeg = file_bytes.startswith(self.MAGIC_SIGNATURES["jpeg"])
            is_webp = len(file_bytes) >= 12 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP"
            return is_png or is_jpeg or is_webp

        elif file_type == "document":
            is_pdf = file_bytes.startswith(self.MAGIC_SIGNATURES["pdf"])
            is_docx = file_bytes.startswith(self.MAGIC_SIGNATURES["docx"])
            if is_pdf or is_docx:
                return True
            try:
                file_bytes[:1024].decode("utf-8")
                return True
            except UnicodeDecodeError:
                return False

        elif file_type == "audio":
            is_wav = len(file_bytes) >= 12 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WAVE"
            is_mp3 = file_bytes.startswith(b"ID3") or (file_bytes[0] == 0xFF and (file_bytes[1] & 0xE0) == 0xE0)
            is_ogg = file_bytes.startswith(b"OggS")
            is_m4a = len(file_bytes) >= 8 and file_bytes[4:8] == b"ftyp"
            return is_wav or is_mp3 or is_ogg or is_m4a

        return True

    def scan_for_prompt_injection(self, text: str) -> Tuple[bool, str]:
        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if pattern.search(text):
                return True, "Potential prompt injection or instruction override pattern detected."
        return False, ""

    def sanitize_user_input(self, text: str) -> str:
        sanitized = text.replace("\x00", "")
        return sanitized.strip()

    def check_rate_limit(self, client_identifier: str) -> bool:
        current_timestamp = time.time()
        window_start = current_timestamp - 60.0

        timestamps = self.request_records[client_identifier]
        valid_timestamps = [ts for ts in timestamps if ts > window_start]
        valid_timestamps.append(current_timestamp)
        self.request_records[client_identifier] = valid_timestamps

        return len(valid_timestamps) <= self.rate_limit_per_minute


security_service = SecurityService()
