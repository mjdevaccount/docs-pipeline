"""
Default metadata values with environment variable support.
"""
import os
from datetime import datetime
from .models import DocumentMetadata


class MetadataDefaults:
    """
    Provide default metadata values with environment variable support.
    
    Supported environment variables:
    - USER_NAME: Default author name
    - ORGANIZATION: Default organization name
    - AUTHOR_EMAIL: Author email (optional)
    - DEPARTMENT: Department name (optional)
    
    Example:
        defaults = MetadataDefaults()
        metadata = defaults.get_defaults()
    """
    
    @staticmethod
    def get_defaults() -> DocumentMetadata:
        """
        Get default metadata with environment variable fallbacks.
        
        Returns:
            DocumentMetadata with defaults applied
        """
        return DocumentMetadata(
            title="Untitled Document",  # Will be extracted from H1
            author=os.environ.get('USER_NAME', 'Author Name'),
            organization=os.environ.get('ORGANIZATION', 'Organization'),
            date=datetime.now().strftime('%B %Y'),
            version='1.0',
            type='Technical Document',
            classification='',  # Not all documents are classified
            department=os.environ.get('DEPARTMENT'),  # Optional
        )
    
    @staticmethod
    def get_env_overrides() -> dict:
        """
        Get environment variable overrides for metadata.
        
        Returns:
            Dictionary of env var overrides
        """
        overrides = {}
        
        if 'USER_NAME' in os.environ:
            overrides['author'] = os.environ['USER_NAME']
        
        if 'ORGANIZATION' in os.environ:
            overrides['organization'] = os.environ['ORGANIZATION']
        
        if 'DEPARTMENT' in os.environ:
            overrides['department'] = os.environ['DEPARTMENT']
        
        if 'AUTHOR_EMAIL' in os.environ:
            overrides['author_email'] = os.environ['AUTHOR_EMAIL']
        
        return overrides

