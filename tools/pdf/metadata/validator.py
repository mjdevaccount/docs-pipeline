"""
Validate and sanitize metadata to prevent PDF generation errors.
"""
import re
from datetime import datetime
from typing import Dict, Any


class MetadataValidator:
    """
    Validate and sanitize metadata fields.
    
    Responsibilities:
    - Remove dangerous characters (e.g., <> in version field)
    - Validate date formats
    - Normalize classification strings
    - Ensure string encoding
    - Prevent XSS in HTML metadata injection
    
    Example:
        validator = MetadataValidator()
        safe_metadata = validator.validate(raw_metadata)
    """
    
    # Characters that can break PDF metadata
    UNSAFE_CHARS_PATTERN = r'[<>]'
    
    # Common date formats to try
    DATE_FORMATS = ['%B %Y', '%Y-%m-%d', '%m/%d/%Y', '%d %B %Y', '%Y-%m', '%B %d, %Y']
    
    def validate(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize all metadata fields.
        
        Args:
            metadata: Raw metadata dictionary
        
        Returns:
            Sanitized metadata dictionary
        """
        if not metadata:
            return {}
        
        validated = metadata.copy()
        
        # Sanitize version field
        if 'version' in validated and validated['version']:
            validated['version'] = self._sanitize_version(validated['version'])
        
        # Validate date format
        if 'date' in validated and validated['date']:
            validated['date'] = self._sanitize_date(validated['date'])
        
        # Normalize classification
        if 'classification' in validated and validated['classification']:
            validated['classification'] = self._normalize_classification(validated['classification'])
        
        # Sanitize string fields
        string_fields = [
            'title', 'author', 'organization', 'type', 'department',
            'review_status', 'doc_id', 'document_id', 'prepared_for', 'preparedFor'
        ]
        for field in string_fields:
            if field in validated and validated[field]:
                validated[field] = self._sanitize_string(validated[field])
        
        return validated
    
    def _sanitize_version(self, version: Any) -> str:
        """
        Remove characters that could break PDF metadata.
        Example: "v1.0<test>" -> "v1.0test"
        """
        version_str = str(version)
        return re.sub(self.UNSAFE_CHARS_PATTERN, '', version_str)
    
    def _sanitize_date(self, date: Any) -> str:
        """
        Validate date format and allow freeform dates.
        Try to parse common formats but don't fail if unparseable.
        """
        date_str = str(date)
        
        # Try to parse common formats (validates structure)
        for fmt in self.DATE_FORMATS:
            try:
                datetime.strptime(date_str, fmt)
                return date_str  # Valid format
            except ValueError:
                continue
        
        # Allow freeform dates (e.g., "Q4 2025", "Winter 2024")
        return date_str
    
    def _normalize_classification(self, classification: Any) -> str:
        """
        Normalize classification string (uppercase, trimmed).
        Example: "confidential  " -> "CONFIDENTIAL"
        """
        return str(classification).strip().upper()
    
    def _sanitize_string(self, value: Any) -> str:
        """
        Ensure proper string encoding and remove control characters.
        Prevents XSS in HTML meta tags.
        """
        value_str = str(value).strip()
        
        # Remove control characters (except newline/tab)
        value_str = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', value_str)
        
        return value_str

