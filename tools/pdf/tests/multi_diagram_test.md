---
title: Multi-Diagram Test Document
author: Matt Jeffcoat
organization: [Organization Name]
date: November 2025
---

# Multi-Diagram Test Document

This document contains three large diagrams to test the scaling logic across multiple diagrams.

## Introduction

This test document validates that the PDF generation pipeline correctly scales multiple large diagrams within a single document, accounting for front matter (cover page and table of contents).

## Background

The project documentation system provides comprehensive orchestration capabilities. This document includes three key architectural diagrams that demonstrate different aspects of the system.

---

## Architecture Overview (Phase 0)

The project documentation architecture consists of multiple layers working together to provide unified job tracking and orchestration.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'12px'}}}%%
graph TB
    subgraph External["External Systems"]
        User["User<br/>[Person]"]
        MarketAPI["Market Data API<br/>[External System]"]
        TradeSB["Trade Service Bus<br/>[External System]"]
    end
    
    subgraph Portal["Portal Layer"]
        PortalUI["Web Portal<br/>Angular/React<br/>User interface"]
        PortalFunc["Portal Function<br/>Azure Function<br/>Validates requests"]
    end
    
    subgraph Manager["Project Documentation"]
        API["Heartbeat API<br/>HTTP<br/>Receives heartbeats"]
        Registry["Job Registry<br/>In-Memory + SQL<br/>Tracks jobs"]
        Processor["Processor<br/>Background Service<br/>Detects timeouts"]
        CacheReg["Cache Registry<br/>Redis Tracking<br/>Coordinates cache"]
    end
    
    subgraph Execution["Execution Layer"]
        TradeFunc["Trade Handler<br/>Azure Function<br/>Processes trade events"]
        Batch["Azure Batch<br/>Batch Service<br/>Executes workloads"]
    end
    
    subgraph Data["Data Layer"]
        SQL["SQL Database<br/>Azure SQL<br/>Persists data"]
        Redis["Redis Cache<br/>Azure Cache<br/>Market data cache"]
    end
    
    User -->|Requests report| PortalUI
    PortalUI -->|Submits| PortalFunc
    PortalFunc -->|Registers job| Manager
    Manager -->|Launches job| Batch
    Batch -->|Heartbeat 15s| Manager
    Batch -->|Fetches prices| MarketAPI
    Batch -->|Caches data| Redis
    Batch -->|Writes results| SQL
    TradeSB -->|Trade events| TradeFunc
    TradeFunc -->|Registers baseline job| Manager
    TradeFunc -->|Writes baseline| SQL
    
    style User fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style PortalUI fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style PortalFunc fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style Manager fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
    style API fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style Registry fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style Processor fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style CacheReg fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style Batch fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style TradeFunc fill:#ffe0b2,stroke:#f57c00,stroke-width:2px
    style SQL fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style Redis fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style MarketAPI fill:#999999,stroke:#6b6b6b,stroke-width:2px
    style TradeSB fill:#999999,stroke:#6b6b6b,stroke-width:2px
    style External fill:#f5f5f5,stroke:#757575,stroke-width:1px
    style Portal fill:#fff9e6,stroke:#f57c00,stroke-width:1px
    style Manager fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style Execution fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px
    style Data fill:#e1f5fe,stroke:#01579b,stroke-width:1px
```

---

## Job Execution Flow

The job execution flow demonstrates the sequence of interactions between components during a typical report generation.

```mermaid
%%{init: {'theme':'base'}}%%
sequenceDiagram
    actor User
    participant Portal
    participant Function as Portal Function
    participant Manager as Project Documentation
    participant Batch as Azure Batch
    participant API as Market Data API
    participant DB as SQL Database
    
    User->>Portal: Click "Run Report"
    Portal->>Function: POST /api/reports
    Function->>DB: Check ReportExecutionLog
    Function->>Manager: Register job
    Manager->>DB: Create ReportingJob
    Manager->>Batch: Launch job
    loop Every 15 seconds
        Batch->>Manager: Heartbeat (progress %)
        Manager->>DB: Update LastHeartbeat
    end
    Batch->>API: Fetch market data
    Batch->>DB: Write valuation results
    Batch->>Manager: Heartbeat (Status: Completed)
    Manager->>DB: Mark job complete
    Manager->>Portal: Job complete notification
    Portal->>User: Show "View Report"
```

---

## Failure Detection and Recovery

The failure detection and recovery mechanism ensures system resilience through automatic timeout detection and recovery classification.

```mermaid
%%{init: {'theme':'base'}}%%
stateDiagram-v2
    [*] --> Created: User submits report
    Created --> Queued: Job registered
    Queued --> Processing: Batch node assigned
    Processing --> Processing: Heartbeat received<br/>(every 15s)
    Processing --> Completed: All tasks done
    Processing --> Failed: Error reported
    Processing --> TimedOut: No heartbeat (60s)
    Failed --> Analyzing: Classify failure
    TimedOut --> Analyzing: Classify failure
    Analyzing --> Retrying: Recoverable<br/>(network, transient)
    Analyzing --> PermanentFailure: Non-recoverable<br/>(data error, config)
    Retrying --> Queued: Resubmit job
    Retrying --> PermanentFailure: Max retries exceeded (3)
    Completed --> [*]: Success
    PermanentFailure --> [*]: Alert operations
```

---

## Conclusion

This test document validates that all three diagrams are properly scaled and positioned within the PDF, accounting for front matter and page boundaries.

