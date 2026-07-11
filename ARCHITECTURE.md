# Architecture & Design Deep Dive

## System Overview

The Data Quality & Drift Detection Platform is a **modular, event-driven system** that continuously monitors data quality by comparing current datasets against baseline statistics. It detects four classes of data problems: schema changes, distribution drift, data anomalies, and completeness issues.

### High-Level Data Flow

```
User Upload → File Validation → Baseline Extraction → Quality Analysis → Alert Generation → Results Storage → Dashboard Visualization
```

---

## Core Architecture

### 1. Backend Service Layer (FastAPI)

**Technology Choice:** FastAPI + Uvicorn
- **Why:** Async support, auto-generated API docs, type safety via Pydantic
- **Alternative considered:** Flask (too simple), Django (overkill)

**Key Responsibilities:**
- HTTP request routing
- Request validation (Pydantic models)
- Business logic orchestration
- Database transactions

### 2. Service Components (Business Logic)

#### 2.1 Schema Validator
**Purpose:** Detect structural changes in data

**Algorithm:**
```
1. Extract baseline schema on first upload:
   - Column names, data types, nullability
   - Store as JSON in database

2. On subsequent uploads, compare:
   - New columns detected → INFO alert
   - Missing columns detected → CRITICAL alert
   - Type changes (int→string) → WARNING/CRITICAL alert
   - Order changes → INFO alert

3. Severity scoring:
   - Breaking changes (missing columns): 1.0
   - Type changes: 0.7-0.9
   - New columns: 0.1-0.3
```

**Implementation Details:**
- Uses Pandas `dtype` introspection
- Handles nullable columns
- Tracks schema versions for rollback capability

**Edge Cases Handled:**
- Empty dataframes
- Single-row dataframes
- Mixed type columns

---

#### 2.2 Drift Detector
**Purpose:** Detect statistical distribution changes

**Algorithm:**

**For Numerical Features:**
- Compute baseline statistics: mean, std, quantiles
- On new data: compare distributions using approximated Kolmogorov-Smirnov test
- Convert p-value to drift score: `score = min(1.0, -log10(p_value) / 5.0)`
- Interpretation:
  - 0.0-0.3: Normal
  - 0.3-0.7: Warning (significant change)
  - 0.7-1.0: Critical (severe drift)

**For Categorical Features:**
- Store baseline category frequencies
- On new data: compute chi-squared statistic on proportions
- Similar score scaling as KS test

**Why KS/Chi-Squared?**
- KS test is robust to outliers
- Works with different sample sizes
- Well-established statistical foundation
- No assumptions about distribution shape

**Implementation Notes:**
- Simplified implementation (no scipy C extensions to avoid macOS code signing issues)
- Uses numpy for all numerical operations
- Handles sparse categories gracefully with pseudocount (0.5)

**Performance:**
- O(n log n) for sorting (KS test)
- O(c) for chi-squared where c = category count
- Scales linearly with features: O(features × n log n)

---

#### 2.3 Anomaly Detector
**Purpose:** Identify data quality issues within a single dataset

**Components:**

**A. Null Rate Analysis**
- Track missing values per column
- Compare to baseline null rates
- Alert if null rate spikes (>5% change threshold)
- Categorize: nulls vs empty strings vs "NULL" strings

**B. Outlier Detection (IQR Method)**
```
IQR = Q3 - Q1
Lower Bound = Q1 - 1.5 × IQR
Upper Bound = Q3 + 1.5 × IQR
Outliers = values outside [Lower, Upper]
```

**Why IQR over Z-score?**
- Robust to extreme values
- Works well with skewed distributions
- Interpretable business meaning

**Limitation:** Skips boolean columns (quantiles undefined)

**C. Domain Rule Engine**
- Pluggable rules for business logic
- Examples:
  - Negative prices → CRITICAL
  - Future dates → WARNING
  - Invalid phone format → WARNING
- Extensible via custom validators

**Anomaly Score Calculation:**
```
anomaly_score = min(1.0, total_anomalies / (rows × columns))
```

---

#### 2.4 Completeness Checker
**Purpose:** Monitor data availability and freshness

**Metrics:**

**1. Completeness Score**
```
score = non_null_cells / total_cells
```

**2. Record Count Monitoring**
- Track row count over time
- Alert if dropped >10% from baseline
- Useful for detecting pipeline failures

**3. Freshness Check**
- Accepts last_update_timestamp
- Compares to current time
- Thresholds:
  - <24 hours: OK
  - 24-48 hours: WARNING
  - >48 hours: CRITICAL

**4. Coverage Metrics**
- If expected_records provided, calculate coverage %
- Useful for data pipeline SLAs

---

#### 2.5 Alert Manager
**Purpose:** Convert quality issues into actionable alerts

**Alert Generation Pipeline:**
```
Quality Results → Severity Classification → Deduplication → Storage → Notification
```

**Severity Assignment:**
- Critical (red): Breaking changes, data loss, high anomaly rates
- Warning (yellow): Mild drift, moderate null rates
- Info (blue): New columns, informational

**Deduplication Strategy:**
- Group similar alerts within time window
- Show "N features drifted" instead of N separate alerts
- Prevents alert fatigue

**Alert Lifecycle:**
- ACTIVE → ACKNOWLEDGED (user marks seen)
- RESOLVED (manually closed)
- Status tracked in database

---

### 3. Database Design (SQLite)

**Schema:**

```sql
datasets
├─ id (PRIMARY KEY)
├─ name
├─ row_count, column_count
├─ baseline_schema (JSON)
├─ baseline_stats (JSON)
└─ created_at, last_analyzed

quality_results
├─ id (PRIMARY KEY)
├─ dataset_id (FOREIGN KEY)
├─ schema_validation (JSON)
├─ drift_analysis (JSON)
├─ anomaly_detection (JSON)
├─ completeness (JSON)
├─ overall_quality_score
└─ created_at

alerts
├─ id (PRIMARY KEY)
├─ dataset_id (FOREIGN KEY)
├─ metric_type
├─ severity (CRITICAL/WARNING/INFO)
├─ message
├─ value, threshold
├─ status (ACTIVE/ACKNOWLEDGED)
└─ created_at, acknowledged_at

metrics_history
├─ id
├─ dataset_id (FOREIGN KEY)
├─ metric_type (e.g., "quality_score", "null_rate")
├─ column_name (optional)
├─ value
└─ created_at
```

**Design Decisions:**
- JSON storage for results (flexible schema evolution)
- Indexed by dataset_id and created_at for fast queries
- metrics_history for trend analysis and time-series visualization

**Normalization:** Denormalized for query speed (pyramid at upload time, query fast)

---

### 4. Frontend Architecture (Streamlit)

**Why Streamlit?**
- Rapid prototyping
- Python-native (same language as backend)
- Built-in state management
- Interactive by default
- No JavaScript needed

**Page Structure:**

```
App (app.py)
├─ pages/
│  ├─ dashboard.py         (KPI cards, alerts summary)
│  ├─ data_explorer.py     (upload, browse datasets)
│  ├─ drift_analysis.py    (distribution changes)
│  ├─ quality_metrics.py   (null rates, completeness)
│  ├─ alerts.py            (alert log, acknowledgment)
│  └─ configure.py         (threshold settings)
└─ API client calls (requests library)
```

**Key Interaction Pattern:**
```
User Action → Streamlit State Update → API Call → Display Results
```

**Performance Considerations:**
- Caching with @st.cache_data for expensive computations
- Pagination for large alert lists
- Real-time updates via browser refresh

---

## Design Decisions & Tradeoffs

### 1. Statistical Tests

**Decision:** Simplified implementations (no scipy C extensions)

**Rationale:**
- macOS code signing issues with scipy
- Approximations sufficient for detecting drift
- Faster deployment

**Tradeoff:**
- Less precise p-values
- Acceptable for categorical detection (binary: drift/no drift)

**Future Improvement:** Use scipy once containerized (Docker handles compilation)

---

### 2. Baseline Strategy

**Decision:** First upload = baseline, subsequent uploads compared against it

**Rationale:**
- Simple, interpretable
- Fast for first analysis
- No training data needed

**Tradeoff:**
- Can't detect day-1 issues
- Requires manual baseline reset for new data regimes

**Alternative Considered:** Sliding window (last 30 days) → Too complex for MVP

---

### 3. Single-Baseline vs Multi-Baseline

**Decision:** Single baseline (one reference point)

**Rationale:**
- Simpler implementation
- Clearer results presentation
- Covers 80% of use cases

**Future:** Multi-baseline for seasonal data, A/B testing

---

### 4. Database Choice

**Decision:** SQLite (embedded)

**Rationale:**
- No server setup
- Portable (single file)
- Sufficient for <1M records

**Scaling Plan:**
```
SQLite (MVP) → PostgreSQL (production) → Data warehouse (enterprise)
```

All queries designed to be DB-agnostic via abstraction layer

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Schema validation | O(columns) | Simple comparison |
| Drift detection | O(features × n log n) | Sorting for KS |
| Anomaly detection | O(features × n) | Single pass for stats |
| Outlier detection | O(n log n) | Quantile calculation |
| **Total Analysis** | **O(n log n)** | Dominated by sorting |

### Space Complexity

| Component | Space | Notes |
|-----------|-------|-------|
| Baseline schema | O(columns) | ~KB |
| Baseline stats | O(columns) | ~10KB |
| Results JSON | O(columns + features) | ~100KB |
| Entire DB (1000 datasets) | ~1GB | Depends on history retention |

### Benchmark Results (Sample: 15 rows, 7 columns)

```
Time to analyze: < 100ms
Breakdown:
  - File read: 10ms
  - Schema validation: 2ms
  - Drift detection: 15ms
  - Anomaly detection: 30ms
  - Alert generation: 10ms
  - DB storage: 20ms
```

**For 100k rows:**
- Estimated: 5-10 seconds
- Bottleneck: Quantile calculations (O(n log n))

---

## Error Handling Strategy

### Graceful Degradation

```python
# If drift detection fails, continue with other checks
try:
    drift_result = detect_drift(df)
except Exception as e:
    drift_result = {"error": str(e), "drifted_features": []}
    # Continue to anomaly detection
```

### User-Facing Errors

```
Bad Input:
  ❌ "Analysis failed: numpy boolean subtract..."
  ✅ "Unable to analyze column 'is_active' (boolean type). 
      Try removing it or converting to integer (0/1)."
```

### Logging Strategy

- INFO: Analysis started/completed
- WARNING: Unusual data patterns
- ERROR: Exceptions with full traceback
- DEBUG: Detailed step-by-step logs

---

## Security Considerations

### Data Privacy
- No data leaves local machine
- SQLite file stored locally
- No external API calls for analysis

### Input Validation
```python
# All file uploads validated:
- File type (CSV/Parquet)
- File size (<500MB)
- Column count (<1000)
- Row count (<10M)
```

### API Security
- CORS enabled (localhost only in production)
- No authentication (local deployment)
- Input sanitization via Pydantic

---

## Deployment Architecture

### Local Development
```
┌─────────────────────────────────────────┐
│  Docker Compose (dev)                   │
├─────────────────────────────────────────┤
│  Backend (FastAPI) :8000                │
│  Frontend (Streamlit) :8501             │
│  Database (SQLite volume)               │
└─────────────────────────────────────────┘
```

### Production Deployment Options

**Option 1: Cloud Run (Google Cloud)**
```
Docker image → Cloud Run → Cloud SQL (PostgreSQL)
Auto-scaling, serverless
```

**Option 2: Kubernetes**
```
Backend pods + Frontend pods + PostgreSQL + Redis (caching)
High availability, horizontal scaling
```

**Option 3: Traditional VM**
```
EC2/GCP VM → Docker compose → PostgreSQL + volumes
Simpler, more control
```

---

## Future Architecture Improvements

### 1. Async Analysis
```python
# Current: Synchronous
POST /analyze → wait 30s → return results

# Future: Async
POST /analyze → return job_id
GET /jobs/{job_id}/status → polling
WebSocket /jobs/{job_id}/events → streaming
```

### 2. Distributed Processing
- Dask for multi-machine analysis
- Spark for big data (100M+ rows)
- Kafka for streaming data quality

### 3. Machine Learning Integration
- Automl for anomaly detection
- Predictive alerting (predict drift before it happens)
- Root cause analysis (which upstream system broke?)

### 4. Multi-Tenant Support
- Database-per-tenant isolation
- Shared backend resources
- Custom thresholds per tenant

---

## Testing Strategy

### Unit Tests (40% coverage)
- Schema validator edge cases
- Drift detector accuracy
- Anomaly detection correctness

### Integration Tests (30% coverage)
- Full pipeline: upload → analyze → results
- Alert generation end-to-end
- API endpoint behavior

### Performance Tests (10% coverage)
- Time to analyze 100k rows
- Memory usage under load
- Database query speed

### Manual Acceptance Tests (20% coverage)
- Dashboard loads correctly
- Charts render
- User workflows work

---

## Lessons Learned

### 1. Type System Matters
Numpy/Pandas type confusion caused longest debugging session. Solution: Always convert to Python native types for arithmetic.

### 2. Boolean Columns Are Special
Pandas treats booleans as numeric (dtype check passes). Solution: Explicit `is_bool_dtype()` checks.

### 3. Statistical Tests Need Edge Cases
Empty data, single-value columns, NaN-only columns break assumptions. Solution: Defensive checks before every statistical operation.

### 4. Streamlit Import Paths
Relative imports work better than absolute when running via `streamlit run`. Solution: Add project root to `sys.path`.

---

## Conclusion

This architecture balances:
- **Simplicity** for rapid development
- **Scalability** for production growth
- **Correctness** for reliable analysis
- **Debuggability** for maintenance

The modular design allows replacing components (e.g., SQLite → PostgreSQL, Streamlit → React) without affecting others.
