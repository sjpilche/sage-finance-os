# 03 — Analysis Engine

## Findings: 1 CRITICAL, 1 MEDIUM

### CRITICAL: SQL Injection via Dimension Column Interpolation
- **Lens**: Skeptic
- **File**: `app/analysis/profitability.py:38,49`
- **Code**: `COALESCE(g.{dimension}, '(unassigned)')` — f-string interpolation of column name
- **Validation**: Router at `app/api/routers/analysis.py:120-121` validates against whitelist
- **Gap**: Function itself has no validation. Direct callers (scheduler, tests, future code) bypass the router whitelist.
- **Exploit**: `dimension="dimension_1) UNION SELECT credentials FROM platform.connections--"`
- **Fix**: Move whitelist INTO the function:
  ```python
  VALID_DIMS = {"dimension_1", "dimension_2", "dimension_3"}
  if dimension not in VALID_DIMS:
      raise ValueError(f"Invalid dimension: {dimension}")
  ```

### MEDIUM: Same f-string Pattern in variance.py
- **Lens**: Skeptic
- **File**: `app/analysis/variance.py:31-32`
- **Code**: `period_filter = "AND g.fiscal_period = %s" if fiscal_period else ""`
- **Risk**: Low — filter is boolean conditional, not user-controlled. But fragile pattern.
