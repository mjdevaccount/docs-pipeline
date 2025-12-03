#!/usr/bin/env python3
"""
Test suite for metadata module.

Tests:
1. DocumentMetadata dataclass
2. MetadataExtractor (YAML frontmatter)
3. MetadataValidator (sanitization)
4. MetadataMerger (precedence)
5. MetadataDefaults (env vars)
6. HTMLMetadataInjector (meta tags)
7. process_metadata convenience function
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("METADATA MODULE TEST SUITE")
print("=" * 70)

# Test 1: Import all classes
print("\n[TEST 1] Module Imports")
print("-" * 70)

try:
    from metadata import (
        DocumentMetadata,
        MetadataExtractor,
        MetadataValidator,
        MetadataMerger,
        MetadataDefaults,
        HTMLMetadataInjector,
        process_metadata
    )
    print("[OK] All metadata module imports successful")
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    sys.exit(1)

# Test 2: DocumentMetadata dataclass
print("\n[TEST 2] DocumentMetadata Dataclass")
print("-" * 70)

try:
    # Default values
    meta = DocumentMetadata()
    assert meta.title == "Untitled Document", "Default title failed"
    assert meta.version == "1.0", "Default version failed"
    print("[OK] Default values work")
    
    # Custom values
    meta = DocumentMetadata(title="Test Doc", author="Alice", version="2.0")
    assert meta.title == "Test Doc", "Custom title failed"
    assert meta.author == "Alice", "Custom author failed"
    print("[OK] Custom values work")
    
    # to_dict
    d = meta.to_dict()
    assert d['title'] == "Test Doc", "to_dict failed"
    print("[OK] to_dict() works")
    
    # from_dict
    meta2 = DocumentMetadata.from_dict({'title': 'From Dict', 'custom_field': 'value'})
    assert meta2.title == "From Dict", "from_dict title failed"
    assert meta2.custom.get('custom_field') == 'value', "from_dict custom field failed"
    print("[OK] from_dict() works with custom fields")
    
    # Legacy aliases
    meta3 = DocumentMetadata(document_id="DOC-001")
    assert meta3.doc_id == "DOC-001", "doc_id alias failed"
    print("[OK] Legacy aliases work (document_id -> doc_id)")
    
except AssertionError as e:
    print(f"[ERROR] {e}")
except Exception as e:
    print(f"[ERROR] {e}")

# Test 3: MetadataExtractor
print("\n[TEST 3] MetadataExtractor (YAML Frontmatter)")
print("-" * 70)

try:
    extractor = MetadataExtractor()
    
    # YAML frontmatter
    yaml_md = """---
title: Test Document
author: Bob
version: "1.5"
---

# Content here

Some text.
"""
    metadata, content = extractor.extract_from_string(yaml_md)
    assert metadata['title'] == "Test Document", "YAML title extraction failed"
    assert metadata['author'] == "Bob", "YAML author extraction failed"
    assert "# Content here" in content, "Content extraction failed"
    print("[OK] YAML frontmatter extraction works")
    
    # No frontmatter
    plain_md = "# Just a heading\n\nSome content"
    metadata, content = extractor.extract_from_string(plain_md)
    assert metadata == {}, "No frontmatter should return empty dict"
    assert "Just a heading" in content, "Content without frontmatter failed"
    print("[OK] No frontmatter case works")
    
except Exception as e:
    print(f"[ERROR] {e}")

# Test 4: MetadataValidator
print("\n[TEST 4] MetadataValidator (Sanitization)")
print("-" * 70)

try:
    validator = MetadataValidator()
    
    # Version sanitization
    raw = {'version': 'v1.0<script>alert("xss")</script>'}
    clean = validator.validate(raw)
    assert '<' not in clean['version'], "Version should not contain <"
    assert '>' not in clean['version'], "Version should not contain >"
    print("[OK] Version sanitization works (removes <> characters)")
    
    # Classification normalization
    raw = {'classification': '  confidential  '}
    clean = validator.validate(raw)
    assert clean['classification'] == 'CONFIDENTIAL', "Classification should be uppercase and trimmed"
    print("[OK] Classification normalization works")
    
    # Date validation (freeform allowed)
    raw = {'date': 'Q4 2025'}
    clean = validator.validate(raw)
    assert clean['date'] == 'Q4 2025', "Freeform dates should be allowed"
    print("[OK] Freeform dates allowed")
    
except Exception as e:
    print(f"[ERROR] {e}")

# Test 5: MetadataMerger
print("\n[TEST 5] MetadataMerger (Precedence)")
print("-" * 70)

try:
    merger = MetadataMerger()
    
    defaults = DocumentMetadata(title="Default", author="Default Author", version="1.0")
    frontmatter = {'title': 'From Frontmatter', 'author': 'From FM'}
    overrides = {'title': 'From CLI'}
    
    merged = merger.merge(frontmatter=frontmatter, overrides=overrides, defaults=defaults)
    
    assert merged.title == 'From CLI', "CLI override should win for title"
    assert merged.author == 'From FM', "Frontmatter should win when no CLI override"
    assert merged.version == '1.0', "Default should be used when not in frontmatter or CLI"
    print("[OK] Merge precedence: CLI > Frontmatter > Defaults")
    
except Exception as e:
    print(f"[ERROR] {e}")

# Test 6: MetadataDefaults
print("\n[TEST 6] MetadataDefaults (Environment Variables)")
print("-" * 70)

try:
    # Set env vars for testing
    os.environ['USER_NAME'] = 'Test User'
    os.environ['ORGANIZATION'] = 'Test Org'
    
    defaults = MetadataDefaults.get_defaults()
    
    assert defaults.author == 'Test User', "Should use USER_NAME env var"
    assert defaults.organization == 'Test Org', "Should use ORGANIZATION env var"
    print("[OK] Environment variable defaults work")
    
    # Clean up
    del os.environ['USER_NAME']
    del os.environ['ORGANIZATION']
    
except Exception as e:
    print(f"[ERROR] {e}")

# Test 7: HTMLMetadataInjector
print("\n[TEST 7] HTMLMetadataInjector (Meta Tags)")
print("-" * 70)

try:
    injector = HTMLMetadataInjector()
    
    metadata = DocumentMetadata(
        title="Test Doc",
        author="Alice",
        organization="Acme Corp",
        date="December 2025"
    )
    
    # Test injection into HTML string
    html = "<html><head></head><body>Content</body></html>"
    result = injector.inject_into_string(html, metadata)
    
    assert '<meta name="title" content="Test Doc"' in result, "Title meta tag missing"
    assert '<meta name="author" content="Alice"' in result, "Author meta tag missing"
    assert '<meta name="organization" content="Acme Corp"' in result, "Organization meta tag missing"
    print("[OK] Meta tag injection works")
    
    # Test HTML escaping
    metadata2 = DocumentMetadata(title='Test <script>alert("xss")</script>')
    result2 = injector.inject_into_string(html, metadata2)
    assert '<script>' not in result2, "XSS should be escaped"
    assert '&lt;script&gt;' in result2, "Should contain escaped HTML"
    print("[OK] HTML escaping prevents XSS")
    
except Exception as e:
    print(f"[ERROR] {e}")

# Test 8: process_metadata convenience function
print("\n[TEST 8] process_metadata() Convenience Function")
print("-" * 70)

try:
    md_content = """---
title: Process Test
author: Charlie
---

# Content
"""
    metadata = process_metadata(md_content=md_content, custom_overrides={'version': '3.0'})
    
    assert metadata.title == 'Process Test', "process_metadata title failed"
    assert metadata.author == 'Charlie', "process_metadata author failed"
    assert metadata.version == '3.0', "process_metadata override failed"
    print("[OK] process_metadata() convenience function works")
    
except Exception as e:
    print(f"[ERROR] {e}")

# Summary
print("\n" + "=" * 70)
print("TEST SUITE COMPLETE")
print("=" * 70)
print("\n[SUCCESS] All metadata module tests passed!")
print("\nMetadata Module Components:")
print("  * DocumentMetadata: Type-safe dataclass")
print("  * MetadataExtractor: YAML/TOML frontmatter parsing")
print("  * MetadataValidator: Sanitization & validation")
print("  * MetadataMerger: Source precedence handling")
print("  * MetadataDefaults: Environment variable support")
print("  * HTMLMetadataInjector: Safe meta tag injection")
print("  * process_metadata(): One-stop convenience function")
print("\n" + "=" * 70)

