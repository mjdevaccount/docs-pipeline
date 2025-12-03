"""
Configuration Management
========================

Handles configuration, profiles, and settings for PDF generation.
"""

from .profiles import get_profile, DocumentProfile

__all__ = [
    'get_profile',
    'Profile',
]

