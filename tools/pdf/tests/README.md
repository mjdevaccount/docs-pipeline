# Front Matter Scaling Test Suite

This test suite validates that the PDF generation system correctly accounts for front matter (cover page and table of contents) when calculating available space for diagram scaling.

## Test Suites

### 1. Unit Tests (`test_scaling_with_frontmatter.py`)
Validates the core logic of front matter accounting:
- **Test 1**: Scaling without front matter (baseline)
- **Test 2**: Scaling with cover page and TOC
- **Test 3**: Page break reset logic

**Run:** `python tests/test_scaling_with_frontmatter.py`

### 2. Validation Tests (`test_scaling_validation.py`)
Programmatically validates measurement accuracy:
- Content above heading measurement
- Available height calculation
- Scaling factor validation
- Consistency checks

**Run:** `python tests/test_scaling_validation.py`

### 3. Visual Tests (`test_scaling_visual_validation.py`)
Generates actual PDFs for manual review:
- PDF without front matter
- PDF with front matter (cover + TOC)
- Comparison guide

**Run:** `python tests/test_scaling_visual_validation.py`

**Output:** PDFs are generated in `tests/test_outputs/`

## Running All Tests

Run the complete test suite:

```bash
python tests/run_all_tests.py
```

This runs all three test suites and provides a comprehensive summary.

## What Gets Tested

### Front Matter Accounting
- Cover page and TOC are detected as page-break elements
- Content measurement resets after page breaks
- Available height accounts for content after TOC

### Scaling Decisions
- Scale factors are reasonable (0.2x - 1.0x)
- Available heights are not artificially low (>= 400px)
- Diagrams are scaled appropriately based on available space

### Page Break Logic
- Page breaks reset cumulative height counters
- Content after page breaks starts fresh
- Natural page flow is accounted for

## Expected Results

When all tests pass, you should see:

```
FINAL TEST SUMMARY
  Unit            [OK]
  Validation      [OK]
  Visual          [OK]
  Total: 3/3 test suites passed
```

## Manual Validation

After running visual tests, review the generated PDFs:

1. **test_no_frontmatter.pdf**: Should show diagrams scaled based on full page height
2. **test_with_frontmatter.pdf**: Should show:
   - Cover page first
   - TOC second
   - Diagrams scaled accounting for content after TOC
   - No diagrams cut off or overlapping

## Architecture

The test suite validates the following architectural components:

1. **DOM Analyzer** (`dom_analyzer.py`): Measures content and calculates available space
2. **Layout Transformer** (`layout_transformer.py`): Computes scaling decisions
3. **Pipeline** (`pipeline.py`): Orchestrates the PDF generation process

## Key Fixes Validated

1. ✅ Analysis happens AFTER cover/TOC injection
2. ✅ Page breaks reset cumulative height counters
3. ✅ Content above heading is measured from last page break
4. ✅ Available height accounts for natural page flow
5. ✅ Scaling factors are reasonable and consistent

## Iterative Development

The test suite enables iterative development:

1. Make changes to scaling logic
2. Run tests: `python tests/run_all_tests.py`
3. Review failures and fix issues
4. Repeat until all tests pass
5. Validate with real documents

This ensures the scaling logic works correctly before deploying to production.

