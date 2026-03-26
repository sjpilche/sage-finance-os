"""
quality.checks
==============
SQL-based data quality checks for contract tables.

Each check returns a dict with: check_name, object_name, passed, severity, details.
Checks are grouped by object and run against the data for a specific run_id.

These are simpler and faster than Great Expectations — suitable for V1.
GE suites can be layered on top in Phase 3b if needed.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def run_all_checks(conn, tenant_id: str, run_id: str, write_counts: dict) -> dict:
    """
    Run all quality checks for a completed pipeline run.

    Parameters
    ----------
    conn:          psycopg2 connection.
    tenant_id:     Tenant UUID.
    run_id:        Run UUID.
    write_counts:  {object_name: row_count} from contract writers.

    Returns
    -------
    dict with: results (per-object list), total, passed, failed,
               critical_failures, pass_rate.
    """
    results: dict[str, list[dict]] = {}
    total = 0
    passed = 0
    failed = 0
    critical_failures = 0

    # Run checks for each object that was written
    check_map = {
        "gl_entry": _checks_gl_entry,
        "trial_balance": _checks_trial_balance,
        "ap_invoice": _checks_ap_invoice,
        "ar_invoice": _checks_ar_invoice,
        "chart_of_accounts": _checks_chart_of_accounts,
        "vendor": _checks_vendor,
        "customer": _checks_customer,
    }

    for obj_name, count in write_counts.items():
        if count == 0:
            continue
        checker = check_map.get(obj_name)
        if checker is None:
            continue

        obj_results = checker(conn, tenant_id, run_id)
        results[obj_name] = obj_results

        for r in obj_results:
            total += 1
            if r["passed"]:
                passed += 1
            else:
                failed += 1
                if r["severity"] == "critical":
                    critical_failures += 1

    # Persist results to platform.dq_results
    _persist_results(conn, tenant_id, run_id, results)

    pass_rate = passed / total if total > 0 else 1.0

    summary = {
        "results": results,
        "total": total,
        "passed": passed,
        "failed": failed,
        "critical_failures": critical_failures,
        "pass_rate": round(pass_rate, 4),
        "objects_checked": list(results.keys()),
    }

    log.info(
        "quality: run=%s total=%d passed=%d failed=%d critical=%d rate=%.1f%%",
        run_id, total, passed, failed, critical_failures, pass_rate * 100,
    )

    return summary


# -- GL Entry checks -----------------------------------------------------------


def _checks_gl_entry(conn, tenant_id: str, run_id: str) -> list[dict]:
    checks = []

    with conn.cursor() as cur:
        # 1. No null posting_date (critical)
        cur.execute(
            "SELECT count(*) FROM contract.gl_entry WHERE run_id = %s AND posting_date IS NULL",
            (run_id,),
        )
        null_dates = cur.fetchone()[0]
        checks.append({
            "check_name": "gl_posting_date_not_null",
            "object_name": "gl_entry",
            "passed": null_dates == 0,
            "severity": "critical",
            "details": {"null_count": null_dates},
        })

        # 2. No null account_number (critical)
        cur.execute(
            "SELECT count(*) FROM contract.gl_entry WHERE run_id = %s AND (account_number IS NULL OR account_number = '')",
            (run_id,),
        )
        null_accts = cur.fetchone()[0]
        checks.append({
            "check_name": "gl_account_number_not_null",
            "object_name": "gl_entry",
            "passed": null_accts == 0,
            "severity": "critical",
            "details": {"null_count": null_accts},
        })

        # 3. Debits = Credits balance check (warning — may not balance per run)
        cur.execute(
            "SELECT COALESCE(SUM(debit_amount), 0), COALESCE(SUM(credit_amount), 0) "
            "FROM contract.gl_entry WHERE run_id = %s",
            (run_id,),
        )
        total_debit, total_credit = cur.fetchone()
        imbalance = abs(float(total_debit) - float(total_credit))
        checks.append({
            "check_name": "gl_debit_credit_balance",
            "object_name": "gl_entry",
            "passed": imbalance < 0.01,
            "severity": "warning",
            "details": {"total_debit": float(total_debit), "total_credit": float(total_credit), "imbalance": imbalance},
        })

        # 4. Row count > 0 (critical)
        cur.execute("SELECT count(*) FROM contract.gl_entry WHERE run_id = %s", (run_id,))
        count = cur.fetchone()[0]
        checks.append({
            "check_name": "gl_row_count_positive",
            "object_name": "gl_entry",
            "passed": count > 0,
            "severity": "critical",
            "details": {"row_count": count},
        })

        # 5. Completeness: description field (warning)
        cur.execute(
            "SELECT count(*) FROM contract.gl_entry WHERE run_id = %s AND (description IS NULL OR description = '')",
            (run_id,),
        )
        null_desc = cur.fetchone()[0]
        total = max(count, 1)
        completeness = round((1 - null_desc / total) * 100, 1)
        checks.append({
            "check_name": "gl_description_completeness",
            "object_name": "gl_entry",
            "passed": completeness >= 50.0,
            "severity": "warning",
            "details": {"null_count": null_desc, "completeness_pct": completeness},
        })

    return checks


# -- Trial Balance checks ------------------------------------------------------


def _checks_trial_balance(conn, tenant_id: str, run_id: str) -> list[dict]:
    checks = []

    with conn.cursor() as cur:
        # 1. TB balance: sum(debits) ≈ sum(credits)
        cur.execute(
            "SELECT COALESCE(SUM(total_debits), 0), COALESCE(SUM(total_credits), 0) "
            "FROM contract.trial_balance WHERE run_id = %s",
            (run_id,),
        )
        debits, credits = cur.fetchone()
        imbalance = abs(float(debits) - float(credits))
        checks.append({
            "check_name": "tb_debit_credit_balance",
            "object_name": "trial_balance",
            "passed": imbalance < 0.01,
            "severity": "critical",
            "details": {"total_debits": float(debits), "total_credits": float(credits), "imbalance": imbalance},
        })

        # 2. No null account_number
        cur.execute(
            "SELECT count(*) FROM contract.trial_balance WHERE run_id = %s AND (account_number IS NULL OR account_number = '')",
            (run_id,),
        )
        nulls = cur.fetchone()[0]
        checks.append({
            "check_name": "tb_account_number_not_null",
            "object_name": "trial_balance",
            "passed": nulls == 0,
            "severity": "critical",
            "details": {"null_count": nulls},
        })

    return checks


# -- AP Invoice checks ---------------------------------------------------------


def _checks_ap_invoice(conn, tenant_id: str, run_id: str) -> list[dict]:
    checks = []

    with conn.cursor() as cur:
        # 1. No null vendor_code
        cur.execute(
            "SELECT count(*) FROM contract.ap_invoice WHERE run_id = %s AND (vendor_code IS NULL OR vendor_code = '')",
            (run_id,),
        )
        nulls = cur.fetchone()[0]
        checks.append({
            "check_name": "ap_vendor_code_not_null",
            "object_name": "ap_invoice",
            "passed": nulls == 0,
            "severity": "critical",
            "details": {"null_count": nulls},
        })

        # 2. Valid status values
        cur.execute(
            "SELECT count(*) FROM contract.ap_invoice WHERE run_id = %s AND status NOT IN ('open', 'partial', 'paid', 'void')",
            (run_id,),
        )
        invalid = cur.fetchone()[0]
        checks.append({
            "check_name": "ap_valid_status_enum",
            "object_name": "ap_invoice",
            "passed": invalid == 0,
            "severity": "warning",
            "details": {"invalid_count": invalid},
        })

        # 3. Balance = total - paid
        cur.execute(
            "SELECT count(*) FROM contract.ap_invoice WHERE run_id = %s AND ABS(balance - (total_amount - paid_amount)) > 0.01",
            (run_id,),
        )
        mismatched = cur.fetchone()[0]
        checks.append({
            "check_name": "ap_balance_consistency",
            "object_name": "ap_invoice",
            "passed": mismatched == 0,
            "severity": "warning",
            "details": {"mismatched_count": mismatched},
        })

    return checks


# -- AR Invoice checks ---------------------------------------------------------


def _checks_ar_invoice(conn, tenant_id: str, run_id: str) -> list[dict]:
    checks = []

    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM contract.ar_invoice WHERE run_id = %s AND (customer_code IS NULL OR customer_code = '')",
            (run_id,),
        )
        nulls = cur.fetchone()[0]
        checks.append({
            "check_name": "ar_customer_code_not_null",
            "object_name": "ar_invoice",
            "passed": nulls == 0,
            "severity": "critical",
            "details": {"null_count": nulls},
        })

        cur.execute(
            "SELECT count(*) FROM contract.ar_invoice WHERE run_id = %s AND status NOT IN ('open', 'partial', 'paid', 'void')",
            (run_id,),
        )
        invalid = cur.fetchone()[0]
        checks.append({
            "check_name": "ar_valid_status_enum",
            "object_name": "ar_invoice",
            "passed": invalid == 0,
            "severity": "warning",
            "details": {"invalid_count": invalid},
        })

    return checks


# -- Chart of Accounts checks --------------------------------------------------


def _checks_chart_of_accounts(conn, tenant_id: str, run_id: str) -> list[dict]:
    checks = []

    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM contract.chart_of_accounts WHERE run_id = %s AND (account_type IS NULL OR account_type = '')",
            (run_id,),
        )
        nulls = cur.fetchone()[0]
        checks.append({
            "check_name": "coa_account_type_not_null",
            "object_name": "chart_of_accounts",
            "passed": nulls == 0,
            "severity": "critical",
            "details": {"null_count": nulls},
        })

    return checks


# -- Vendor checks -------------------------------------------------------------


def _checks_vendor(conn, tenant_id: str, run_id: str) -> list[dict]:
    checks = []
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM contract.vendor WHERE run_id = %s AND (vendor_name IS NULL OR vendor_name = '')",
            (run_id,),
        )
        nulls = cur.fetchone()[0]
        checks.append({
            "check_name": "vendor_name_completeness",
            "object_name": "vendor",
            "passed": nulls == 0,
            "severity": "warning",
            "details": {"null_count": nulls},
        })
    return checks


# -- Customer checks -----------------------------------------------------------


def _checks_customer(conn, tenant_id: str, run_id: str) -> list[dict]:
    checks = []
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM contract.customer WHERE run_id = %s AND (customer_name IS NULL OR customer_name = '')",
            (run_id,),
        )
        nulls = cur.fetchone()[0]
        checks.append({
            "check_name": "customer_name_completeness",
            "object_name": "customer",
            "passed": nulls == 0,
            "severity": "warning",
            "details": {"null_count": nulls},
        })
    return checks


# -- Persistence ---------------------------------------------------------------


def _persist_results(conn, tenant_id: str, run_id: str, results: dict[str, list[dict]]) -> None:
    """Write all DQ results to platform.dq_results."""
    import json
    with conn.cursor() as cur:
        for obj_name, checks in results.items():
            for check in checks:
                cur.execute(
                    """
                    INSERT INTO platform.dq_results
                        (run_id, tenant_id, object_name, check_name, passed, severity, details)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        run_id, tenant_id, check["object_name"],
                        check["check_name"], check["passed"],
                        check["severity"], json.dumps(check.get("details", {})),
                    ),
                )
    conn.commit()
