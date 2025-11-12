"""
Plot overall repurchase rate in a date window using analysis/repurchase_lifetime_summary.csv.

Repurchase definition: among buyers in the window, share with lifetime orders >= 2
by the end of the window.
"""

from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def main() -> None:
    path = Path("analysis/repurchase_lifetime_summary.csv")
    if not path.exists():
        raise SystemExit("Missing analysis/repurchase_lifetime_summary.csv. Run the BigQuery step.")
    df = pd.read_csv(path)
    buyers = int(df.loc[0, "buyers_in_window"])
    repeat = int(df.loc[0, "repeat_in_window"])
    rate = float(df.loc[0, "repurchase_rate"]) * 100.0
    first = buyers - repeat

    plt.figure(figsize=(5, 3.2))
    plt.bar(["Repeat", "First"], [repeat, first], color=["#2563eb", "#94a3b8"])
    plt.title(f"Repurchase in Window: {rate:.1f}%")
    plt.ylabel("Customers")
    for i, v in enumerate([repeat, first]):
        plt.text(i, v, f"{v:,}", ha="center", va="bottom")
    plt.tight_layout()
    out = Path("analysis/repurchase_window_bar.png")
    plt.savefig(out)
    plt.close()
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()

