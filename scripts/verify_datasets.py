from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    "Credit Card Fraud": ROOT / "data" / "raw" / "credit_card",
    "PaySim": ROOT / "data" / "raw" / "paysim",
}


def inspect_csvs(name, folder):
    print(f"\n=== {name} ===")
    csv_files = sorted(folder.rglob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in: {folder}")
        return

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, nrows=5)
            row_count = sum(1 for _ in open(csv_file, "r", encoding="utf-8", errors="ignore")) - 1
            print(f"File: {csv_file.name}")
            print(f"Rows (approx): {max(row_count, 0):,}")
            print(f"Columns: {len(df.columns)}")
            print("Column sample:", ", ".join(map(str, df.columns[:12])))
        except Exception as exc:
            print(f"Could not inspect {csv_file}: {exc}")


if __name__ == "__main__":
    for name, folder in DATASETS.items():
        inspect_csvs(name, folder)
