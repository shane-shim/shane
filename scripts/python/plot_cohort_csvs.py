"""
Plot cohort analysis CSVs produced in analysis/.

Generates:
  - analysis/cohort_retention_heatmap.png
  - analysis/cohort_active_counts_bar.png
  - analysis/cohort_revenue_bar.png

Requires: pandas, seaborn, matplotlib
"""

from __future__ import annotations

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot cohort CSVs from a directory")
    parser.add_argument("--dir", default="analysis", help="Directory containing cohort_retention.csv, cohort_active_counts.csv, cohort_revenue.csv")
    args = parser.parse_args()

    outdir = Path(args.dir)
    retention_csv = outdir / "cohort_retention.csv"
    counts_csv = outdir / "cohort_active_counts.csv"
    revenue_csv = outdir / "cohort_revenue.csv"

    if not (retention_csv.exists() and counts_csv.exists() and revenue_csv.exists()):
        raise SystemExit("Missing CSVs in analysis/. Run the BigQuery step first.")

    # Load CSVs
    ret = pd.read_csv(retention_csv)
    cnt = pd.read_csv(counts_csv)
    rev = pd.read_csv(revenue_csv)

    # Ensure cohort_month is a string or datetime for ordering
    ret["cohort_month"] = pd.to_datetime(ret["cohort_month"]).dt.date
    cnt["cohort_month"] = pd.to_datetime(cnt["cohort_month"]).dt.date
    rev["cohort_month"] = pd.to_datetime(rev["cohort_month"]).dt.date

    # Retention heatmap (%): columns r0,r1,r2 → 0,1,2
    ret_heat = ret.set_index("cohort_month")[[c for c in ret.columns if c.startswith("r")]]
    ret_heat.columns = [int(c[1:]) for c in ret_heat.columns]
    plt.figure(figsize=(6, max(2.5, 0.6 * len(ret_heat))))
    sns.heatmap(ret_heat * 100, annot=True, fmt=".1f", cmap="Blues", cbar_kws={"label": "% Retained"})
    plt.title("Cohort Retention (%)")
    plt.xlabel("Months Since Cohort")
    plt.ylabel("Cohort Month")
    plt.tight_layout()
    plt.savefig(outdir / "cohort_retention_heatmap.png")
    plt.close()

    # Active counts bar: melt m0,m1,m2
    cnt_m = cnt.melt(id_vars=["cohort_month"], var_name="month", value_name="active")
    plt.figure(figsize=(8, 3.5))
    sns.barplot(data=cnt_m, x="cohort_month", y="active", hue="month")
    plt.title("Active Users by Cohort (M0/M1/M2)")
    plt.xlabel("Cohort Month")
    plt.ylabel("Active Users")
    plt.legend(title="Month")
    plt.tight_layout()
    plt.savefig(outdir / "cohort_active_counts_bar.png")
    plt.close()

    # Revenue bar: melt rev0,rev1,rev2
    rev_m = rev.melt(id_vars=["cohort_month"], var_name="month", value_name="revenue")
    plt.figure(figsize=(8, 3.5))
    sns.barplot(data=rev_m, x="cohort_month", y="revenue", hue="month")
    plt.title("Revenue by Cohort (M0/M1/M2)")
    plt.xlabel("Cohort Month")
    plt.ylabel("Revenue")
    plt.legend(title="Month")
    plt.tight_layout()
    plt.savefig(outdir / "cohort_revenue_bar.png")
    plt.close()

    print("Saved:")
    print(f"- {outdir / 'cohort_retention_heatmap.png'}")
    print(f"- {outdir / 'cohort_active_counts_bar.png'}")
    print(f"- {outdir / 'cohort_revenue_bar.png'}")


if __name__ == "__main__":
    main()
