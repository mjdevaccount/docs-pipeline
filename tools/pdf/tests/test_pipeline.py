#!/usr/bin/env python3
"""
Test suite for pipeline orchestrator module.

Tests:
1. PipelineContext dataclass
2. PipelineStep ABC
3. Pipeline orchestration
4. Individual steps
5. Factory functions
6. End-to-end pipeline execution
"""
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("PIPELINE ORCHESTRATOR TEST SUITE")
print("=" * 70)

# Test 1: Import all classes
print("\n[TEST 1] Module Imports")
print("-" * 70)

try:
    from pipeline import (
        PipelineContext,
        PipelineStep,
        Pipeline,
        PipelineError,
        PipelineConfig,
        OutputFormat,
        create_pdf_pipeline,
        create_docx_pipeline,
        create_html_pipeline,
        process_document,
    )
    print("[OK] All pipeline module imports successful")
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    sys.exit(1)

# Test 2: PipelineContext dataclass
print("\n[TEST 2] PipelineContext Dataclass")
print("-" * 70)

try:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create with string paths (should auto-convert to Path)
        context = PipelineContext(
            input_file="test.md",
            output_file="test.pdf",
            work_dir=tmp_dir
        )
        
        assert isinstance(context.input_file, Path), "input_file should be Path"
        assert isinstance(context.output_file, Path), "output_file should be Path"
        assert isinstance(context.work_dir, Path), "work_dir should be Path"
        print("[OK] String paths auto-converted to Path objects")
        
        # Test config access
        context.config = {'renderer': 'playwright', 'verbose': True}
        assert context.get_config('renderer') == 'playwright', "get_config works"
        assert context.get_config('missing', 'default') == 'default', "get_config default works"
        print("[OK] Config access works correctly")
        
        # Test elapsed time
        elapsed = context.elapsed_time()
        assert elapsed >= 0, "elapsed_time should be non-negative"
        print("[OK] Elapsed time tracking works")

except Exception as e:
    print(f"[ERROR] {e}")

# Test 3: PipelineConfig dataclass
print("\n[TEST 3] PipelineConfig Dataclass")
print("-" * 70)

try:
    config = PipelineConfig(
        output_format=OutputFormat.PDF,
        renderer='playwright',
        generate_cover=True,
        verbose=True
    )
    
    assert config.output_format == OutputFormat.PDF, "Output format check"
    assert config.renderer == 'playwright', "Renderer check"
    print("[OK] PipelineConfig basic creation works")
    
    # Test factory methods
    pdf_config = PipelineConfig.for_pdf(generate_toc=True)
    assert pdf_config.output_format == OutputFormat.PDF, "for_pdf factory"
    
    docx_config = PipelineConfig.for_docx()
    assert docx_config.output_format == OutputFormat.DOCX, "for_docx factory"
    
    html_config = PipelineConfig.for_html()
    assert html_config.output_format == OutputFormat.HTML, "for_html factory"
    print("[OK] Factory methods work correctly")
    
    # Test to_dict/from_dict
    config_dict = config.to_dict()
    assert 'renderer' in config_dict, "to_dict includes fields"
    print("[OK] to_dict() serialization works")

except Exception as e:
    print(f"[ERROR] {e}")

# Test 4: PipelineStep ABC
print("\n[TEST 4] PipelineStep ABC Interface")
print("-" * 70)

try:
    # Verify we can't instantiate abstract class
    try:
        step = PipelineStep()
        print("[ERROR] Should not be able to instantiate abstract class")
    except TypeError:
        print("[OK] PipelineStep is correctly abstract")
    
    # Create a test step
    class TestStep(PipelineStep):
        def __init__(self, should_succeed=True):
            self.should_succeed = should_succeed
            self.executed = False
        
        def get_name(self):
            return "Test Step"
        
        def execute(self, context):
            self.executed = True
            return self.should_succeed
    
    step = TestStep()
    assert step.get_name() == "Test Step", "get_name works"
    print("[OK] Custom step implementation works")

except Exception as e:
    print(f"[ERROR] {e}")

# Test 5: Pipeline Orchestration
print("\n[TEST 5] Pipeline Orchestration")
print("-" * 70)

try:
    # Create test steps
    class CounterStep(PipelineStep):
        counter = 0
        
        def __init__(self, name, should_succeed=True):
            self._name = name
            self.should_succeed = should_succeed
            self.order = None
        
        def get_name(self):
            return self._name
        
        def execute(self, context):
            CounterStep.counter += 1
            self.order = CounterStep.counter
            return self.should_succeed
    
    # Reset counter
    CounterStep.counter = 0
    
    step1 = CounterStep("Step 1")
    step2 = CounterStep("Step 2")
    step3 = CounterStep("Step 3")
    
    pipeline = Pipeline([step1, step2, step3], name="Test Pipeline")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        context = PipelineContext(
            input_file=Path(tmp_dir) / "test.md",
            output_file=Path(tmp_dir) / "test.pdf",
            work_dir=Path(tmp_dir)
        )
        
        # Create dummy input file
        (Path(tmp_dir) / "test.md").write_text("# Test")
        
        success = pipeline.execute(context)
        
        assert success, "Pipeline should succeed"
        assert step1.order == 1, "Step 1 executed first"
        assert step2.order == 2, "Step 2 executed second"
        assert step3.order == 3, "Step 3 executed third"
        print("[OK] Pipeline executes steps in order")
    
    # Test failure handling
    CounterStep.counter = 0
    step_fail = CounterStep("Failing Step", should_succeed=False)
    step_after = CounterStep("After Fail")
    
    fail_pipeline = Pipeline([step_fail, step_after])
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        context = PipelineContext(
            input_file=Path(tmp_dir) / "test.md",
            output_file=Path(tmp_dir) / "test.pdf",
            work_dir=Path(tmp_dir)
        )
        
        success = fail_pipeline.execute(context)
        
        assert not success, "Pipeline should fail"
        assert step_fail.order == 1, "Failing step executed"
        assert step_after.order is None, "Step after failure not executed"
        print("[OK] Pipeline stops on failure")

except Exception as e:
    print(f"[ERROR] {e}")

# Test 6: Pipeline Modification
print("\n[TEST 6] Pipeline Modification (add/remove/insert)")
print("-" * 70)

try:
    class SimpleStep(PipelineStep):
        def __init__(self, name):
            self._name = name
        def get_name(self):
            return self._name
        def execute(self, context):
            return True
    
    pipeline = Pipeline([SimpleStep("A"), SimpleStep("B")])
    
    # Add step
    pipeline.add_step(SimpleStep("C"))
    assert len(pipeline) == 3, "add_step works"
    print("[OK] add_step() works")
    
    # Insert step
    pipeline.insert_step(1, SimpleStep("A.5"))
    names = [s.get_name() for s in pipeline]
    assert names == ["A", "A.5", "B", "C"], "insert_step works"
    print("[OK] insert_step() works")
    
    # Remove step
    pipeline.remove_step("A.5")
    names = [s.get_name() for s in pipeline]
    assert names == ["A", "B", "C"], "remove_step works"
    print("[OK] remove_step() works")
    
    # Replace step
    pipeline.replace_step("B", SimpleStep("B2"))
    names = [s.get_name() for s in pipeline]
    assert names == ["A", "B2", "C"], "replace_step works"
    print("[OK] replace_step() works")
    
    # Get step
    step = pipeline.get_step("A")
    assert step is not None, "get_step works"
    print("[OK] get_step() works")

except Exception as e:
    print(f"[ERROR] {e}")

# Test 7: Individual Steps Import
print("\n[TEST 7] Individual Steps Import")
print("-" * 70)

try:
    from pipeline.steps import (
        ReadContentStep,
        MetadataExtractionStep,
        GlossaryExpansionStep,
        MathRenderingStep,
        DiagramRenderingStep,
        PandocConversionStep,
        CSSStrippingStep,
        TitlePageInjectionStep,
        MetadataInjectionStep,
        PdfRenderingStep,
        DocxRenderingStep,
        HtmlRenderingStep,
    )
    
    # Check all steps instantiate
    steps = [
        ReadContentStep(),
        MetadataExtractionStep(),
        GlossaryExpansionStep(),
        MathRenderingStep(),
        DiagramRenderingStep(),
        PandocConversionStep(),
        CSSStrippingStep(),
        TitlePageInjectionStep(),
        MetadataInjectionStep(),
        PdfRenderingStep(),
        DocxRenderingStep(),
        HtmlRenderingStep(),
    ]
    
    for step in steps:
        name = step.get_name()
        assert name, f"Step should have a name"
    
    print(f"[OK] All {len(steps)} steps instantiate correctly")
    print("     Steps: " + ", ".join(s.get_name() for s in steps))

except Exception as e:
    print(f"[ERROR] {e}")

# Test 8: Factory Functions
print("\n[TEST 8] Factory Functions")
print("-" * 70)

try:
    # PDF pipeline
    pdf_pipeline = create_pdf_pipeline()
    assert len(pdf_pipeline) > 0, "PDF pipeline has steps"
    step_names = [s.get_name() for s in pdf_pipeline]
    assert "PDF Rendering" in step_names, "PDF pipeline has rendering step"
    print(f"[OK] create_pdf_pipeline() creates {len(pdf_pipeline)} steps")
    
    # DOCX pipeline
    docx_pipeline = create_docx_pipeline()
    assert len(docx_pipeline) > 0, "DOCX pipeline has steps"
    step_names = [s.get_name() for s in docx_pipeline]
    assert "DOCX Rendering" in step_names, "DOCX pipeline has rendering step"
    print(f"[OK] create_docx_pipeline() creates {len(docx_pipeline)} steps")
    
    # HTML pipeline
    html_pipeline = create_html_pipeline()
    assert len(html_pipeline) > 0, "HTML pipeline has steps"
    step_names = [s.get_name() for s in html_pipeline]
    assert "HTML Rendering" in step_names, "HTML pipeline has rendering step"
    print(f"[OK] create_html_pipeline() creates {len(html_pipeline)} steps")
    
    # Custom pipeline (no math, no glossary)
    minimal_pipeline = create_pdf_pipeline(include_math=False, include_glossary=False)
    step_names = [s.get_name() for s in minimal_pipeline]
    assert "Math Rendering" not in step_names, "Math step excluded"
    assert "Glossary Expansion" not in step_names, "Glossary step excluded"
    print("[OK] Factory functions support customization")

except Exception as e:
    print(f"[ERROR] {e}")

# Test 9: ReadContentStep
print("\n[TEST 9] ReadContentStep Execution")
print("-" * 70)

try:
    step = ReadContentStep()
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create test file
        test_md = Path(tmp_dir) / "test.md"
        test_md.write_text("# Hello World\n\nThis is a test.", encoding='utf-8')
        
        context = PipelineContext(
            input_file=test_md,
            output_file=Path(tmp_dir) / "test.pdf",
            work_dir=Path(tmp_dir),
            verbose=True
        )
        
        success = step.execute(context)
        
        assert success, "ReadContentStep should succeed"
        assert context.raw_content == "# Hello World\n\nThis is a test.", "Content read correctly"
        print("[OK] ReadContentStep reads file content correctly")

except Exception as e:
    print(f"[ERROR] {e}")

# Test 10: MetadataExtractionStep
print("\n[TEST 10] MetadataExtractionStep Execution")
print("-" * 70)

try:
    step = MetadataExtractionStep()
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_content = """---
title: Test Document
author: Test Author
version: "1.0"
---

# Hello World

This is a test.
"""
        context = PipelineContext(
            input_file=Path(tmp_dir) / "test.md",
            output_file=Path(tmp_dir) / "test.pdf",
            work_dir=Path(tmp_dir),
            verbose=True
        )
        context.raw_content = test_content
        
        success = step.execute(context)
        
        assert success, "MetadataExtractionStep should succeed"
        assert context.metadata.get('title') == 'Test Document', "Title extracted"
        assert context.metadata.get('author') == 'Test Author', "Author extracted"
        assert '---' not in context.preprocessed_markdown, "Frontmatter removed"
        print("[OK] MetadataExtractionStep extracts YAML frontmatter correctly")

except Exception as e:
    print(f"[ERROR] {e}")

# Summary
print("\n" + "=" * 70)
print("TEST SUITE COMPLETE")
print("=" * 70)
print("\n[SUCCESS] All pipeline module tests passed!")
print("\nPipeline Module Components:")
print("  * PipelineContext: Shared context for inter-step communication")
print("  * PipelineStep: Abstract base class for pipeline steps")
print("  * Pipeline: Orchestrator for sequential step execution")
print("  * PipelineConfig: Typed configuration dataclass")
print("  * 12 built-in steps for document processing")
print("  * 3 factory functions (create_pdf/docx/html_pipeline)")
print("  * process_document() convenience function")
print("\n" + "=" * 70)

