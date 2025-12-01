#!/bin/bash
set -e

echo "📚 Generating example PDFs..."
echo ""

# Create output directory
mkdir -p docs/examples/generated

# Example 1: SOLID Implementation
if [ -f "docs/development/pdf-solid-implementation.md" ]; then
    echo "📄 Generating: SOLID Implementation Analysis..."
    python -m tools.pdf.convert_final \
        docs/development/pdf-solid-implementation.md \
        docs/examples/generated/solid-implementation.pdf
    echo "   ✅ Generated: solid-implementation.pdf"
else
    echo "   ⚠️  Source not found: docs/development/pdf-solid-implementation.md"
fi

# Example 2: Structurizr Evaluation
if [ -f "docs/development/structurizr-solid-evaluation.md" ]; then
    echo "📄 Generating: Structurizr Architecture Evaluation..."
    python -m tools.pdf.convert_final \
        docs/development/structurizr-solid-evaluation.md \
        docs/examples/generated/structurizr-evaluation.pdf
    echo "   ✅ Generated: structurizr-evaluation.pdf"
else
    echo "   ⚠️  Source not found: docs/development/structurizr-solid-evaluation.md"
fi

# Example 3: PDF Setup Guide
if [ -f "tools/pdf/docs/PDF_GENERATION_SETUP.md" ]; then
    echo "📄 Generating: PDF Generation Setup Guide..."
    python -m tools.pdf.convert_final \
        tools/pdf/docs/PDF_GENERATION_SETUP.md \
        docs/examples/generated/pdf-setup-guide.pdf
    echo "   ✅ Generated: pdf-setup-guide.pdf"
else
    echo "   ⚠️  Source not found: tools/pdf/docs/PDF_GENERATION_SETUP.md"
fi

echo ""
echo "✅ Example generation complete!"
echo "📁 Examples saved to: docs/examples/generated/"
echo ""

ls -lh docs/examples/generated/

