from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "raw" / "credit_card"
TARGET.mkdir(parents=True, exist_ok=True)

DATASET = "mlg-ulb/creditcardfraud"

command = [
    "kaggle",
    "datasets",
    "download",
    "-d",
    DATASET,
    "-p",
    str(TARGET),
    "--unzip",
]

print("Downloading Credit Card Fraud Detection dataset...")
print("Kaggle dataset:", DATASET)

try:
    subprocess.run(command, check=True)
except FileNotFoundError:
    print(
        "ERROR: Kaggle CLI was not found. Activate the virtual environment "
        "and install requirements.txt first."
    )
    sys.exit(1)
except subprocess.CalledProcessError as exc:
    print("ERROR: Kaggle download failed.")
    print("Check Kaggle authentication and internet access.")
    sys.exit(exc.returncode)

print(f"Dataset downloaded to: {TARGET}")
