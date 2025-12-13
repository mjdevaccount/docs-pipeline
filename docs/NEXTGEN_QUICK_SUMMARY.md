# Phase C: Next-Gen Mermaid (December 2025 Roadmap)

## The 6 Components

### 1. **SVG Optimizer** 📝
**What**: Strip unused CSS, minify paths, compress inline styles  
**Gain**: 30-50% SVG size reduction, 5x faster parse  
**Effort**: 2 days  
**Risk**: Low  
**Start**: THIS WEEK  

### 2. **CSSOM Variant** ⚡
**What**: Use browser CSSOM API instead of getComputedStyle()  
**Gain**: 3-5x additional speedup (60ms → 15ms for colors)  
**Effort**: 1 day (partially done)  
**Risk**: Low  
**Start**: THIS WEEK  

### 3. **Parallel Batch Renderer** 🗤️
**What**: Render 20 diagrams simultaneously on 4 workers  
**Gain**: 3-5x speedup for batch (1400ms → 400ms)  
**Effort**: 3-4 days  
**Risk**: Medium (concurrency)  
**Start**: Next week  

### 4. **Streaming SVG Renderer** 🌊
**What**: Return SVG skeleton immediately, update as rendering completes  
**Gain**: Perceived speed +70% (user sees output instantly)  
**Effort**: 2 days  
**Risk**: Low  
**Start**: Week 2-3  

### 5. **Async Rendering Pool** 🔄
**What**: Decouple rendering from PDF writing (render in background)  
**Gain**: 15-20% total time reduction  
**Effort**: 2-3 days  
**Risk**: Low  
**Start**: Week 3  

### 6. **GPU Acceleration** 💾
**What**: Offload SVG path rendering to system GPU  
**Gain**: 50-70% for complex diagrams  
**Effort**: 4-5 days (experimental)  
**Risk**: High (system dependency)  
**Start**: Week 5+ (optional)  

---

## Timeline

```
Week 1-2: SVG Optimizer + CSSOM          (Do THIS)
          ├─ Expand SVGOptimizer class
          ├─ Benchmark CSSOM variant
          └─ Add to pipeline

Week 2-3: Parallel Batch Renderer         (Next)
          ├─ Create ParallelDiagramRenderer
          ├─ Handle worker pool
          └─ Benchmark 3-5x improvement

Week 3:   Streaming SVG (UX feature)      (Nice-to-have)
Week 4:   Async Rendering Pool            (Nice-to-have)
Week 5+:  GPU Acceleration (experimental) (Future)
```

---

## Performance Roadmap

### Single Diagram
```
Phase A:        100ms
Phase B:         60ms  (40% faster)
Phase C Week 1:  30ms  (50% faster than B)
Phase C Week 2:  20ms  (33% faster)
Phase C Week 3:  10ms  (50% faster, with GPU)

FINAL: 10-30ms (3-10x faster than Phase A baseline)
```

### Batch (20 Diagrams)
```
Phase A:        2000ms
Phase B:        1200ms (40% faster)
Phase C Week 1:  400ms (3x faster than B, via parallel)
Phase C Week 2:  300ms (25% faster, CSSOM colors)
Phase C Week 3:  150ms (50% faster, with GPU)

FINAL: 150-400ms (4-13x faster than Phase A baseline)
```

---

## Start This Week

### Task 1: SVG Optimizer
```python
# tools/pdf/diagram_rendering/svg_optimizer.py

class SVGOptimizer:
    async def optimize(self, svg: str) -> str:
        """Minify SVG: remove unused styles, compress paths."""
        # 1. Parse
        # 2. Find used classes
        # 3. Remove unused <style> rules
        # 4. Minify paths (reduce coordinate precision)
        # 5. Remove redundant attributes
        # 6. Return minified
```

### Task 2: Benchmark CSSOM
```bash
# Compare timing
time python -m tools.pdf.cli convert doc.md out1.pdf  # getComputedStyle
time python -m tools.pdf.cli convert doc.md out2.pdf --mermaid-cssom  # CSSOM

# Expected: 3-5x faster with CSSOM
```

### Quick Win
**Expected from Week 1 alone**: 2-3x speedup  
**Code**: ~300 lines total (optimizer + benchmarks)  
**Commits**: 2-3  

---

## What You Have NOW

**Phase A + B**: ✅ Live in production  
- Playwright 1.48.0
- Node 22.x
- Mermaid 11.12.0
- Native renderer (40-60% faster)
- **Current**: 60-120ms per diagram

**Phase C**: 🔨 Ready to build  
- Full architectural design
- Code templates provided
- Timeline: 4-6 weeks
- **Target**: 10-30ms per diagram

---

## Next Action

🎯 **Start with SVGOptimizer this week**
```bash
git checkout -b feat/phase-c-svg-optimizer
# Implement SVGOptimizer class
# Add benchmarks
# Measure impact
```

🗤️ **Then ParallelDiagramRenderer next week**
```bash
git checkout -b feat/phase-c-parallel-renderer
# Create ParallelDiagramRenderer
# Test 3-5x speedup
```

---

## Full Details

📖 See: `MERMAID_NEXTGEN_2025.md`

- Complete technical specifications
- Implementation examples
- Integration points
- Testing strategy
- Performance projections

---

## Status

✅ **Phase A**: Live in production  
✅ **Phase B**: Live in production  
🔨 **Phase C**: Ready to implement (this week)

**You have the blueprint. Time to execute.** 🚀
