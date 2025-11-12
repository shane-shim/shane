"""
BigQuery Cohort Analysis (Last 3 Cohorts, Monthly)

This script queries a BigQuery orders table and produces a cohort analysis
for cohorts defined by a customer's first order month, restricted to the
most recent 3 cohorts (current month and previous two). It outputs:
  - Active user counts pivot (cohort x month offset)
  - Retention rate pivot (percentage)
  - Revenue pivot (sum)
  - A retention heatmap PNG

Usage (example):
  python scripts/python/bq_cohort_analysis.py \
    --project inductive-folio-324208 \
    --dataset purelevy \
    --table cafe24_order \
    --customer-id-col member_id \
    --timestamp-col order_date \
    --amount-col paid_price \
    --status-col order_status \
    --status-allowlist PAYMENT_COMPLETE,DELIVERED

Authentication:
  - Set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON, or
  - Use gcloud auth application-default login

Outputs (default):
  - analysis/cohort_active_counts.csv
  - analysis/cohort_retention.csv
  - analysis/cohort_revenue.csv
  - analysis/cohort_retention_heatmap.png

Dependencies:
  pip install google-cloud-bigquery pandas seaborn matplotlib
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns


def _quote_ident(ident: str) -> str:
    """Backtick-quote a BigQuery identifier (column/table)."""
    ident = ident.strip().strip("`")
    return f"`{ident}`"


def build_sql(
    project: str,
    dataset: str,
    table: str,
    customer_col: str,
    ts_col: str,
    amount_col: str,
    status_col: Optional[str] = None,
    status_allowlist: Optional[List[str]] = None,
) -> str:
    full_table = f"{project}.{dataset}.{table}"

    c_customer = _quote_ident(customer_col)
    c_ts = _quote_ident(ts_col)
    c_amount = _quote_ident(amount_col)
    where_clauses: List[str] = []

    # Basic sanity: exclude NULL ids/dates
    where_clauses.append(f"{c_customer} IS NOT NULL")
    where_clauses.append(f"{c_ts} IS NOT NULL")

    if status_col and status_allowlist:
        c_status = _quote_ident(status_col)
        # Sanitize values and make them lowercase for case-insensitive match
        sanitized = [v.replace("'", "").strip() for v in status_allowlist]
        lowered = [s.lower() for s in sanitized]
        rhs = ",".join([f"'{s}'" for s in lowered])
        where_clauses.append(
            f"LOWER(CAST({c_status} AS STRING)) IN ({rhs})"
        )

    where_sql = " AND ".join(where_clauses)

    # Three most recent cohorts: current month and previous two
    sql = f"""
    WITH base AS (
      SELECT
        CAST({c_customer} AS STRING) AS customer_id,
        DATE({c_ts}) AS order_date,
        SAFE_CAST({c_amount} AS NUMERIC) AS amount
      FROM `{full_table}`
      WHERE {where_sql}
    ),
    cohorts AS (
      SELECT customer_id, DATE_TRUNC(MIN(order_date), MONTH) AS cohort_month
      FROM base
      GROUP BY 1
    ),
    last3_cohorts AS (
      SELECT * FROM cohorts
      WHERE cohort_month >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH), MONTH)
    ),
    joined AS (
      SELECT b.customer_id,
             b.order_date,
             DATE_TRUNC(b.order_date, MONTH) AS activity_month,
             l.cohort_month,
             b.amount
      FROM base b
      JOIN last3_cohorts l USING(customer_id)
    ),
    activity AS (
      SELECT
        cohort_month,
        activity_month,
        DATE_DIFF(activity_month, cohort_month, MONTH) AS months_since_cohort,
        customer_id,
        SUM(amount) AS revenue
      FROM joined
      GROUP BY 1,2,3,4
    ),
    cohort_sizes AS (
      SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
      FROM last3_cohorts
      GROUP BY 1
    )
    SELECT
      a.cohort_month,
      a.months_since_cohort,
      a.customer_id,
      a.revenue,
      s.cohort_size
    FROM activity a
    JOIN cohort_sizes s USING (cohort_month)
    WHERE a.months_since_cohort BETWEEN 0 AND 2
    ORDER BY cohort_month, months_since_cohort, customer_id
    """
    return sql


def run_query(sql: str, project: str) -> pd.DataFrame:
    client = bigquery.Client(project=project)
    job = client.query(sql)
    df = job.result().to_dataframe()
    return df


def compute_pivots(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Ensure proper dtypes
    df = df.copy()
    df["cohort_month"] = pd.to_datetime(df["cohort_month"]).dt.date
    df["months_since_cohort"] = df["months_since_cohort"].astype(int)

    # Active users per cell
    counts = (
        df.groupby(["cohort_month", "months_since_cohort"])  # type: ignore
        ["customer_id"].nunique()
        .unstack(fill_value=0)
    )

    # Cohort sizes (distinct customers per cohort)
    cohort_sizes = (
        df[["cohort_month", "cohort_size"]]
        .drop_duplicates()
        .set_index("cohort_month")["cohort_size"]
    )

    # Retention = active / cohort_size
    retention = counts.div(cohort_sizes, axis=0).fillna(0.0)

    # Revenue per cell
    revenue = (
        df.groupby(["cohort_month", "months_since_cohort"])  # type: ignore
        ["revenue"].sum()
        .unstack(fill_value=0.0)
    )

    # Order columns 0,1,2 if present
    cols = [c for c in [0, 1, 2] if c in counts.columns]
    if cols:
        counts = counts.reindex(columns=cols, fill_value=0)
        retention = retention.reindex(columns=cols, fill_value=0.0)
        revenue = revenue.reindex(columns=cols, fill_value=0.0)

    return counts, retention, revenue


def save_outputs(outdir: Path, counts: pd.DataFrame, retention: pd.DataFrame, revenue: pd.DataFrame) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    counts.to_csv(outdir / "cohort_active_counts.csv", index=True)
    retention.to_csv(outdir / "cohort_retention.csv", index=True)
    revenue.to_csv(outdir / "cohort_revenue.csv", index=True)

    # Heatmap for retention
    plt.figure(figsize=(8, max(3, 0.5 * len(retention))))
    sns.heatmap(retention * 100, annot=True, fmt=".0f", cmap="Blues", cbar_kws={"label": "% Retained"})
    plt.title("Cohort Retention (Last 3 Cohorts)")
    plt.xlabel("Months Since Cohort")
    plt.ylabel("Cohort Month")
    heatmap_path = outdir / "cohort_retention_heatmap.png"
    plt.tight_layout()
    plt.savefig(heatmap_path)
    plt.close()
    return heatmap_path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="BigQuery cohort analysis (last 3 monthly cohorts)")
    p.add_argument("--project", default="inductive-folio-324208")
    p.add_argument("--dataset", default="purelevy")
    p.add_argument("--table", default="cafe24_order")
    p.add_argument("--customer-id-col", default="member_id", help="Customer identifier column name")
    p.add_argument("--timestamp-col", default="order_date", help="Order timestamp/date column name")
    p.add_argument("--amount-col", default="paid_price", help="Order amount/revenue column name")
    p.add_argument("--status-col", default=None, help="Optional status column for filtering paid/complete orders")
    p.add_argument(
        "--status-allowlist",
        default=None,
        help="Comma-separated allowed status values (e.g., PAYMENT_COMPLETE,DELIVERED)",
    )
    p.add_argument("--outdir", default="analysis", help="Output directory for CSVs and heatmap")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    allowlist = None
    if args.status_allowlist:
        allowlist = [x.strip() for x in args.status_allowlist.split(",") if x.strip()]

    sql = build_sql(
        project=args.project,
        dataset=args.dataset,
        table=args.table,
        customer_col=args.customer_id_col,
        ts_col=args.timestamp_col,
        amount_col=args.amount_col,
        status_col=args.status_col,
        status_allowlist=allowlist,
    )

    print("Running BigQuery cohort query...\n")
    try:
        df = run_query(sql, project=args.project)
    except Exception as e:
        print("[ERROR] Query failed. Check column names and permissions.")
        print(e)
        raise SystemExit(2)

    if df.empty:
        print("No data returned. Check filters, column mapping, and date coverage.")
        return

    counts, retention, revenue = compute_pivots(df)

    outdir = Path(args.outdir)
    heatmap_path = save_outputs(outdir, counts, retention, revenue)

    print("\nOutputs:")
    print(f"- Active counts CSV: {outdir / 'cohort_active_counts.csv'}")
    print(f"- Retention CSV:    {outdir / 'cohort_retention.csv'}")
    print(f"- Revenue CSV:      {outdir / 'cohort_revenue.csv'}")
    print(f"- Heatmap PNG:      {heatmap_path}")

    # Quick preview
    print("\nRetention preview (%):")
    preview = (retention * 100).round(1)
    with pd.option_context('display.width', 120, 'display.max_columns', None):
        print(preview.tail(5))


if __name__ == "__main__":
    main()
