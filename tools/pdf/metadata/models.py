"""
Type-safe metadata model using dataclass.
Provides validation, serialization, and default handling.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class DocumentMetadata:
    """
    Type-safe document metadata with validation and defaults.
    
    Standard Fields (always present):
        title: Document title (extracted from first H1 or frontmatter)
        author: Author name (from frontmatter, env var, or default)
        organization: Organization name (from frontmatter, env var, or default)
        date: Publication date (formatted string, defaults to current month/year)
        version: Document version (defaults to "1.0")
        type: Document type (e.g., "Technical Document", "White Paper")
        classification: Classification level (e.g., "CONFIDENTIAL", empty string allowed)
    
    Optional Enhanced Fields:
        department: Department name (e.g., "Engineering", "Product")
        review_status: Review status (e.g., "Draft", "Final", "Approved")
        doc_id: Document ID or reference number
        document_id: Alias for doc_id (legacy support)
        prepared_for: Recipient or client name
        preparedFor: Alias for prepared_for (camelCase legacy support)
    
    Custom Fields:
        custom: Dict of additional custom fields from frontmatter
    """
    
    # Standard fields (always present, never None)
    title: str = "Untitled Document"
    author: str = "Author Name"
    organization: str = "Organization"
    date: str = field(default_factory=lambda: datetime.now().strftime('%B %Y'))
    version: str = "1.0"
    type: str = "Technical Document"
    classification: str = ""  # Empty string allowed (not all docs are classified)
    
    # Optional enhanced fields (None allowed)
    department: Optional[str] = None
    review_status: Optional[str] = None
    doc_id: Optional[str] = None
    document_id: Optional[str] = None  # Legacy alias for doc_id
    prepared_for: Optional[str] = None
    preparedFor: Optional[str] = None  # Legacy camelCase alias
    
    # Custom fields (catch-all for unknown frontmatter fields)
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Normalize legacy aliases after initialization"""
        # Normalize doc_id aliases
        if self.document_id and not self.doc_id:
            self.doc_id = self.document_id
        elif self.doc_id and not self.document_id:
            self.document_id = self.doc_id
        
        # Normalize prepared_for aliases
        if self.preparedFor and not self.prepared_for:
            self.prepared_for = self.preparedFor
        elif self.prepared_for and not self.preparedFor:
            self.preparedFor = self.prepared_for
    
    def to_dict(self, include_none: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        
        Args:
            include_none: If True, include fields with None values
        
        Returns:
            Dictionary representation
        """
        data = asdict(self)
        if not include_none:
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentMetadata':
        """
        Create DocumentMetadata from dictionary (frontmatter or CLI args).
        Unknown fields go into 'custom' dict.
        
        Args:
            data: Dictionary of metadata fields
        
        Returns:
            DocumentMetadata instance
        """
        # Separate known fields from custom fields
        known_fields = {
            'title', 'author', 'organization', 'date', 'version', 'type', 'classification',
            'department', 'review_status', 'doc_id', 'document_id', 'prepared_for', 'preparedFor'
        }
        
        known_data = {k: v for k, v in data.items() if k in known_fields}
        custom_data = {k: v for k, v in data.items() if k not in known_fields and k != 'custom'}
        
        # Merge existing custom data if present
        if 'custom' in data and isinstance(data['custom'], dict):
            custom_data.update(data['custom'])
        
        return cls(**known_data, custom=custom_data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value by key (supports custom fields).
        
        Args:
            key: Field name
            default: Default value if field not found
        
        Returns:
            Field value or default
        """
        if hasattr(self, key):
            value = getattr(self, key)
            return value if value is not None else default
        return self.custom.get(key, default)

