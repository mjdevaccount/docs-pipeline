# 📂 Streaming Architecture - Quick Reference Card

**December 2025 | One-Page Reference**

---

## System Overview

```
🛠️ Control Plane
    ┓━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    │  RT Config, Triggering, Monitoring, Calculations
    │
    │  ⭡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╪
│          ☁️ Orchestration (Coral + Coordinator)
└━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━└
                 │
        ⚡ Stream Processing Loop (100K events/sec, p50: 50ms)
            ┖━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╪
                 │
        🔄 Distribution Hub (1M events/sec)
             ───⮶─────────────────────────────────────────────────────────╪
            │                                                │
    📊 RT Dashboard              💾 Multi-Tier Storage        🌐 External
```

---

## Key Metrics

| Metric | Target | Status |
|--------|--------|--------|
| **Throughput** | 1M events/sec | ✅ |
| **p50 Latency** | <100ms | ✅ |
| **p99 Latency** | <500ms | ✅ |
| **Availability** | 99.95% | ✅ |
| **Data Retention** | 30 days (warm) | ✅ |

---

## Architecture Zones

### 🛠️ Control Plane (Yellow)
- RT Configuration management
- Triggering system
- Monitoring & metrics
- Parameter calculations

### ☁️ Orchestration (Blue)
- Coral Data integration
- Reporting Manager
- Lifecycle management
- Central coordinator

### ⚡ Stream Processing (Purple)
- Event ingestion
- Real-time transformation
- Stateful processing
- Firehose topic distribution

### 🔄 Distribution (Gray)
- Multi-consumer routing
- Load balancing
- Hot-warm-cold tiering
- Delta generation

### 📊 Outputs (Red)
- Real-time dashboard
- External API consumption
- Batch processing
- Event streaming

---

## Data Flows

### Real-Time Path ⚡ (Critical)
```
Config → Orchestrator → Stream Processor → Hub → Dashboard
Latency Budget: 100ms (p50)
Throughput: 1M/sec
```

### Batch Path 📦 (Analytics)
```
Distribution Hub → Delta Generator → External Consumer
Frequency: 1-second batches
Data Type: Change events
```

### Storage Path 💾 (Archive)
```
Hub → Hot Cache (minutes) → Warm Store (days) → Cold Lake (unlimited)
```

---

## Component Details

### Stream Processor
- **Throughput**: 100K events/sec (per instance)
- **Parallelism**: 10 instances × 100K = 1M total
- **Latency**: p50 50ms, p99 200ms
- **State**: In-memory + changelog topic
- **Batching**: 1s tumbling windows

### Distribution Hub
- **Throughput**: 1M events/sec
- **Routing**: Content & key-based
- **Consumers**: 5-20 downstream
- **Buffering**: Multi-tier queue
- **Failover**: Consumer group rebalancing

### Storage Tiers

**Hot (Real-time Cache)**
- Technology: Redis/Memcached
- Retention: 1-24 hours
- Latency: <10ms
- Use Case: Dashboard queries

**Warm (Recent History)**
- Technology: RocksDB/SQLite
- Retention: 3-30 days
- Latency: 100-500ms
- Use Case: Time-series analysis

**Cold (Archive)**
- Technology: S3/ADLS
- Retention: Unlimited
- Latency: Seconds to minutes
- Use Case: Long-term analytics

---

## Mathematical Model

### Throughput
$$T = \sum_{i=1}^{n} C_i = 10 \times 100\text{ K} = 1\text{ M events/sec}$$

### Latency
$$L = L_{\text{ingest}} + L_{\text{process}} + L_{\text{route}} + L_{\text{cache}}$$
$$L = 10 + 50 + 20 + 20 = 100\text{ ms (p50)}$$

### Storage Capacity (Warm Tier)
$$C = 30\text{ days} \times 86,400\text{ s/day} \times 1\text{ M/s} \times 1\text{ KB}$$
$$C \approx 2.6\text{ PB}$$

---

## Configuration Checklist

### Control Plane
- [ ] RT Config store initialized
- [ ] Triggering rules defined
- [ ] Monitoring metrics configured
- [ ] Alert thresholds set

### Processing
- [ ] Stream processors: 10 instances
- [ ] Batch size: 10K events
- [ ] Window: 1s tumbling
- [ ] Parallelism: 10

### Storage
- [ ] Hot cache: Redis cluster
- [ ] Warm store: RocksDB shards
- [ ] Cold lake: S3/ADLS bucket
- [ ] Retention policies set

### Monitoring
- [ ] Throughput tracking (target: 1M/sec)
- [ ] Latency percentiles (p50, p95, p99)
- [ ] Queue depth monitoring
- [ ] Cache hit ratio (target: >95%)
- [ ] Error rate alerts (threshold: >0.1%)

---

## Performance Tuning

### Increase Throughput
1. Add processor instances (horizontal scale)
2. Increase batch size (trade-off: latency)
3. Enable parallelism (more executor threads)
4. Optimize network (reduce serialization overhead)

### Reduce Latency
1. Reduce batch window (trade-off: throughput)
2. Optimize processing logic (remove bottlenecks)
3. Upgrade cache tier (faster hardware)
4. Reduce network hops (co-locate services)

### Optimize Storage
1. Enable compression (reduce disk usage)
2. Partition by time (faster queries)
3. Archive cold data (reduce warm tier size)
4. Use tiering (hot/warm/cold separation)

---

## Scaling Rules

| Metric | Threshold | Action |
|--------|-----------|--------|
| **Latency p99** | >1s | Add processors |
| **Queue Depth** | >100K | Increase batch size |
| **Cache Hit Ratio** | <90% | Increase cache size |
| **Error Rate** | >0.1% | Investigate errors |
| **Warm Tier Storage** | >80% | Archive to cold |
| **CPU Usage** | >80% | Horizontal scale |
| **Memory Usage** | >85% | Increase instance size |

---

## Deployment Checklist

- [ ] All 4 diagram types rendered and validated
- [ ] PDF generated with correct CSS profile
- [ ] Performance metrics documented
- [ ] LaTeX equations rendering correctly
- [ ] SVGs optimized (<20KB each)
- [ ] Configuration examples provided
- [ ] SLA targets defined
- [ ] Monitoring strategy documented
- [ ] Scaling guidelines defined
- [ ] Document version tracked (v1.0)

---

## Quick Commands

### Render Documentation
```bash
python tools/pdf/convert_final.py \
    docs/STREAMING_ARCHITECTURE_COMPLETE.md \
    output/streaming-arch.pdf \
    --profile tech-whitepaper
```

### Validate Diagrams
```bash
python tools/pdf/diagram_rendering/validator.py \
    docs/STREAMING_ARCHITECTURE_COMPLETE.md
```

### Test All Profiles
```bash
./scripts/render-all-profiles.sh \
    docs/STREAMING_ARCHITECTURE_COMPLETE.md \
    output/
```

### Enable Caching
```bash
export DIAGRAM_CACHE=/tmp/diagram-cache
python tools/pdf/convert_final.py \
    docs/STREAMING_ARCHITECTURE_COMPLETE.md \
    output/streaming-arch.pdf
```

---

## Files Reference

| File | Purpose |
|------|----------|
| `STREAMING_ARCHITECTURE_COMPLETE.md` | Main specification with all 4 diagram types |
| `STREAMING_ARCHITECTURE_DIAGRAM_IMPROVEMENTS.md` | Enhanced Mermaid design guide |
| `RENDERING_GUIDE.md` | Complete rendering and optimization guide |
| `QUICK_REFERENCE.md` | This file - one-page reference |

---

## Contact & Support

**Documentation**: See `docs/` folder in `mjdevaccount/docs-pipeline`
**Issues**: GitHub Issues in docs-pipeline repository
**Latest Updates**: December 2025

---

**Status**: ✅ Production Ready | **Version**: 1.0 | **Last Updated**: December 12, 2025
