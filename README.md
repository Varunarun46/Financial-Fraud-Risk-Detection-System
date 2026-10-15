# Financial Data Analytics and Fraud Risk Prediction System

## Phase 1 — Project Foundation

This is the foundation for the MCA final-year major project:

**Financial Data Analytics and Fraud Risk Prediction System**

Phase 1 provides:

- Modular Flask backend
- REST API health endpoint
- Environment-based configuration
- PostgreSQL-ready SQLAlchemy setup
- Kaggle dataset download scripts
- Dataset directory structure
- Basic database schema
- Logging
- Testing foundation
- Windows setup instructions

## Planned technology stack

- Python 3.11+
- Flask
- Flask-CORS
- SQLAlchemy / Flask-SQLAlchemy
- PostgreSQL
- Pandas / NumPy
- Scikit-learn
- XGBoost / LightGBM
- TensorFlow / Keras
- SHAP
- Matplotlib / Seaborn / Plotly
- Power BI

## Phase 1 datasets

1. Credit Card Fraud Detection (ULB)
2. PaySim

IEEE-CIS can be added later because of its much larger size and more complex schema.

## Project structure

```text
financial-fraud-risk-system/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   └── routes/
├── data/
│   ├── raw/
│   │   ├── credit_card/
│   │   └── paysim/
│   ├── processed/
│   └── sample/
├── database/
│   └── schema.sql
├── scripts/
│   ├── download_credit_card.py
│   ├── download_paysim.py
│   └── verify_datasets.py
├── tests/
├── logs/
├── notebooks/
├── models/
├── reports/
├── powerbi/
├── .env.example
├── .gitignore
├── requirements.txt
└── run.py
```

## Windows setup

Open PowerShell in the project directory.

### 1. Create virtual environment

```powershell
py -3.11 -m venv .venv
```

### 2. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Create environment file

```powershell
Copy-Item .env.example .env
```

For Phase 1, the application can run using SQLite by default. PostgreSQL can be configured later by changing `DATABASE_URL`.

### 6. Start Flask

```powershell
python run.py
```

Open:

```text
http://127.0.0.1:5000/
```

Health endpoint:

```text
http://127.0.0.1:5000/api/health
```

## Kaggle authentication

The download scripts support the modern Kaggle CLI/API workflow.

Install the Kaggle package through `requirements.txt`.

Then authenticate using one of the supported Kaggle credential methods.

A common Windows setup is:

```powershell
kaggle auth login
```

Follow Kaggle's authentication instructions.

Then run:

```powershell
python scripts/download_credit_card.py
python scripts/download_paysim.py
```

The scripts do not hard-code private credentials.

## Dataset verification

After downloading:

```powershell
python scripts/verify_datasets.py
```

The script checks whether expected CSV files are present and reports basic row/column information.

## Testing

Run:

```powershell
python -m pytest
```

## Important

Do not commit:

- `.env`
- Kaggle credentials
- database passwords
- raw datasets if their redistribution is restricted
- trained model binaries unless intentionally versioned

The `.gitignore` already excludes common sensitive/generated files.
