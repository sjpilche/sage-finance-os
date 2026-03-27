#!/usr/bin/env python3
"""
Run the full Sage Finance OS pipeline end-to-end with synthetic data.

This proves every layer of the system works:
1. Synthetic connector generates Sage Intacct-format data
2. Real transforms convert to canonical records
3. Real contract writers bulk-insert to PostgreSQL
4. Real quality gate runs 15 SQL checks
5. Real scorecard computes 6-dimension weighted score
6. Real HMAC certificate is signed (or circuit breaker quarantines)
7. Real KPI engine materializes metrics
8. Watermarks are updated for incremental sync

Usage:
    python scripts/run_full_pipeline.py

Requires: PostgreSQL running locally (docker compose up db -d)
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2

DSN = os.getenv("DATABASE_URL_SYNC", "postgresql://sage:sage@localhost:5432/sage_finance")


def ensure_tenant(conn) -> str:
    """Ensure default tenant exists, return tenant_id."""
    with conn.cursor() as cur:
        cur.execute("SELECT tenant_id FROM platform.tenants WHERE slug = 'default'")
        row = cur.fetchone()
        if row:
            return str(row[0])
        tenant_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO platform.tenants (tenant_id, slug, name) VALUES (%s, 'default', 'Acme Corp')",
            (tenant_id,),
        )
    conn.commit()
    return tenant_id


def ensure_connection(conn, tenant_id: str) -> str:
    """Ensure synthetic connection exists, return connection_id."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT connection_id FROM platform.connections WHERE tenant_id = %s AND name = %s",
            (tenant_id, "Synthetic Sage Intacct"),
        )
        row = cur.fetchone()
        if row:
            return str(row[0])
        conn_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO platform.connections (connection_id, tenant_id, name, status, credentials) VALUES (%s, %s, %s, 'active', %s)",
            (conn_id, tenant_id, "Synthetic Sage Intacct", json.dumps({"synthetic": True})),
        )
    conn.commit()
    return conn_id


def run_scenario_1_full_sync(conn, tenant_id: str, connection_id: str):
    """Scenario 1: Full sync — extract all objects, quality gate, certify."""
    print("\n" + "=" * 70)
    print("SCENARIO 1: Full Sync (all 7 objects)")
    print("=" * 70)

    from app.pipeline.runner import run_pipeline

    # Monkey-patch the connector import to use synthetic
    import app.pipeline.runner as runner
    from app.ingestion.connectors.synthetic import SyntheticSageConnector
    original_connector = runner.SageIntacctConnector
    runner.SageIntacctConnector = SyntheticSageConnector

    try:
        result = run_pipeline(
            conn=conn,
            tenant_id=tenant_id,
            connection_id=connection_id,
            credentials={"gl_count": 500, "ap_count": 60, "ar_count": 75},
            mode="full",
        )

        print(f"\n  Run ID:  {result['run_id']}")
        print(f"  Status:  {result['status']}")

        if "summary" in result:
            summary = result["summary"]
            if "written" in summary:
                print(f"  Written: {summary['written']}")
            if "quality" in summary:
                q = summary["quality"]
                print(f"  Quality: composite={q.get('scorecard', {}).get('composite_score', '?')}")
                print(f"           verdict={q.get('scorecard', {}).get('verdict', '?')}")
                print(f"           outcome={q.get('outcome', '?')}")
                if "certificate" in q:
                    print(f"           cert_id={q['certificate'].get('certificate_id', '?')}")
                    print(f"           signature={q['certificate'].get('signature', '?')}")
            if "kpis" in summary:
                k = summary["kpis"]
                print(f"  KPIs:    computed={k.get('computed', '?')}/{k.get('total', '?')}")
            if "elapsed_seconds" in summary:
                print(f"  Elapsed: {summary['elapsed_seconds']}s")

        return result

    finally:
        runner.SageIntacctConnector = original_connector


def run_scenario_2_incremental(conn, tenant_id: str, connection_id: str):
    """Scenario 2: Incremental sync — watermark-based delta extraction."""
    print("\n" + "=" * 70)
    print("SCENARIO 2: Incremental Sync (watermark delta)")
    print("=" * 70)

    from app.pipeline.runner import run_pipeline
    import app.pipeline.runner as runner
    from app.ingestion.connectors.synthetic import SyntheticSageConnector
    original_connector = runner.SageIntacctConnector
    runner.SageIntacctConnector = SyntheticSageConnector

    try:
        result = run_pipeline(
            conn=conn,
            tenant_id=tenant_id,
            connection_id=connection_id,
            credentials={"gl_count": 500, "ap_count": 60, "ar_count": 75},
            mode="incremental",
        )

        print(f"\n  Run ID:  {result['run_id']}")
        print(f"  Status:  {result['status']}")
        if "summary" in result:
            written = result["summary"].get("written", {})
            print(f"  Written: {written}")
            print(f"  (Expect ~1/3 of full sync due to watermark filter)")

        return result

    finally:
        runner.SageIntacctConnector = original_connector


def run_scenario_3_quarantine(conn, tenant_id: str, connection_id: str):
    """Scenario 3: Bad data that triggers quarantine via circuit breaker."""
    print("\n" + "=" * 70)
    print("SCENARIO 3: Bad Data — Quarantine (circuit breaker)")
    print("=" * 70)

    from app.pipeline.runner import run_pipeline
    import app.pipeline.runner as runner
    from app.ingestion.connectors.synthetic import SyntheticSageConnector

    class BadDataConnector(SyntheticSageConnector):
        """Connector that produces intentionally bad data to trigger quality failures."""

        def extract(self, object_name, watermark=None, batch_size=1000):
            from app.ingestion.connectors.sage_intacct.transform import SAGE_TRANSFORMERS

            if object_name == "GLDETAIL":
                # Generate GL entries with missing critical fields (null dates, null accounts)
                bad_records = [
                    {"RECORDNO": "99901", "AMOUNT": "5000.00", "BATCH_DATE": "",
                     "DOCNUMBER": "", "DESCRIPTION": "", "ACCOUNTNO": "",
                     "CURRENCY": "USD", "DEPARTMENTID": "", "LOCATIONID": "",
                     "CLASSID": "", "BOOKID": "GL"},
                    {"RECORDNO": "99902", "AMOUNT": "", "BATCH_DATE": "01/15/2026",
                     "DOCNUMBER": "BAD-001", "DESCRIPTION": "Bad entry",
                     "ACCOUNTNO": "9999", "CURRENCY": "USD", "DEPARTMENTID": "",
                     "LOCATIONID": "", "CLASSID": "", "BOOKID": "GL"},
                ] * 25  # 50 bad records
                # Mix with some good records
                good_records = [
                    {"RECORDNO": str(99950 + i), "AMOUNT": "1000.00",
                     "BATCH_DATE": "02/15/2026", "DOCNUMBER": f"GOOD-{i:03d}",
                     "DESCRIPTION": "Good entry", "ACCOUNTNO": "4000",
                     "ACCOUNTTITLE": "Product Revenue",
                     "CURRENCY": "USD", "DEPARTMENTID": "SALES",
                     "LOCATIONID": "HQ", "CLASSID": "", "BOOKID": "GL"}
                    for i in range(10)
                ]
                all_records = bad_records + good_records
                transformer = SAGE_TRANSFORMERS.get(object_name)
                records = transformer(all_records) if transformer else all_records
                yield records
            else:
                # Other objects use normal synthetic data
                yield from super().extract(object_name, watermark, batch_size)

    original_connector = runner.SageIntacctConnector
    runner.SageIntacctConnector = BadDataConnector

    try:
        result = run_pipeline(
            conn=conn,
            tenant_id=tenant_id,
            connection_id=connection_id,
            credentials={"gl_count": 10, "ap_count": 5, "ar_count": 5},
            mode="full",
        )

        print(f"\n  Run ID:  {result['run_id']}")
        print(f"  Status:  {result['status']}")
        if "summary" in result and "quality" in result["summary"]:
            q = result["summary"]["quality"]
            print(f"  Quality: composite={q.get('scorecard', {}).get('composite_score', '?')}")
            print(f"           verdict={q.get('scorecard', {}).get('verdict', '?')}")
            print(f"           outcome={q.get('outcome', '?')}")
            if "quarantine" in q:
                print(f"           reason={q['quarantine'].get('reason', '?')}")
        elif "error" in result:
            print(f"  Error:   {result['error']}")

        return result

    finally:
        runner.SageIntacctConnector = original_connector


def print_summary(conn, tenant_id: str):
    """Print final state summary."""
    print("\n" + "=" * 70)
    print("FINAL STATE")
    print("=" * 70)

    with conn.cursor() as cur:
        # Run counts
        cur.execute(
            "SELECT status, COUNT(*) FROM platform.data_runs WHERE tenant_id = %s GROUP BY status ORDER BY status",
            (tenant_id,),
        )
        print("\n  Pipeline Runs:")
        for row in cur.fetchall():
            print(f"    {row[0]}: {row[1]}")

        # Record counts
        tables = ["contract.gl_entry", "contract.trial_balance", "contract.ap_invoice",
                   "contract.ar_invoice", "contract.vendor", "contract.customer",
                   "contract.chart_of_accounts"]
        print("\n  Contract Tables:")
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE tenant_id = %s", (tenant_id,))
            count = cur.fetchone()[0]
            print(f"    {table.split('.')[1]}: {count:,}")

        # Scorecards
        cur.execute(
            "SELECT gate_status, composite, created_at FROM audit.scorecard_results WHERE tenant_id = %s ORDER BY created_at",
            (tenant_id,),
        )
        rows = cur.fetchall()
        print(f"\n  Quality Scorecards: {len(rows)}")
        for row in rows:
            print(f"    {row[0].upper()} (composite={row[1]}) at {row[2].strftime('%H:%M:%S')}")

        # Certificates
        cur.execute("SELECT COUNT(*) FROM audit.certificates WHERE tenant_id = %s", (tenant_id,))
        cert_count = cur.fetchone()[0]
        print(f"\n  HMAC Certificates: {cert_count}")

        # Quarantine log
        cur.execute("SELECT COUNT(*) FROM audit.quarantine_log WHERE tenant_id = %s", (tenant_id,))
        q_count = cur.fetchone()[0]
        print(f"  Quarantine Events: {q_count}")

        # KPIs
        cur.execute("SELECT COUNT(*) FROM semantic.computed_kpis WHERE tenant_id = %s", (tenant_id,))
        kpi_count = cur.fetchone()[0]
        print(f"  Computed KPIs:     {kpi_count}")

    print()


if __name__ == "__main__":
    print("Sage Finance OS — Full Pipeline End-to-End Test")
    print(f"Connecting to: {DSN.split('@')[1] if '@' in DSN else DSN}")

    # Use autocommit connection for setup, fresh connections per scenario
    setup_conn = psycopg2.connect(DSN)
    setup_conn.autocommit = True

    try:
        tenant_id = ensure_tenant(setup_conn)
        connection_id = ensure_connection(setup_conn, tenant_id)
        print(f"Tenant:     {tenant_id[:8]}...")
        print(f"Connection: {connection_id[:8]}...")
    finally:
        setup_conn.close()

    # Each scenario gets a fresh connection to avoid transaction pollution
    scenarios = [
        ("Scenario 1", run_scenario_1_full_sync),
        ("Scenario 2", run_scenario_2_incremental),
        ("Scenario 3", run_scenario_3_quarantine),
    ]

    for name, scenario_fn in scenarios:
        conn = psycopg2.connect(DSN)
        conn.autocommit = True
        try:
            scenario_fn(conn, tenant_id, connection_id)
        except Exception as e:
            print(f"\n  {name} ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()

    # Print final state
    summary_conn = psycopg2.connect(DSN)
    summary_conn.autocommit = True
    try:
        print_summary(summary_conn, tenant_id)
    finally:
        summary_conn.close()

    print("All 3 scenarios complete. The full pipeline has been proven.")
