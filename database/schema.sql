-- Phase 1 PostgreSQL-ready schema.
-- Flask-SQLAlchemy currently creates the Phase 1 SQLite database automatically.
-- This schema documents the target relational design for PostgreSQL.

CREATE TABLE IF NOT EXISTS users (
    user_id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'VIEWER',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(100) PRIMARY KEY,
    dataset_name VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(50),
    amount NUMERIC(18, 2),
    source_account VARCHAR(150),
    destination_account VARCHAR(150),
    old_balance_source NUMERIC(18, 2),
    new_balance_source NUMERIC(18, 2),
    old_balance_destination NUMERIC(18, 2),
    new_balance_destination NUMERIC(18, 2),
    transaction_timestamp TIMESTAMPTZ,
    is_fraud BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fraud_predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(100) REFERENCES transactions(transaction_id),
    model_name VARCHAR(100) NOT NULL,
    fraud_probability NUMERIC(8, 6),
    risk_score NUMERIC(6, 2),
    risk_level VARCHAR(30),
    prediction VARCHAR(30),
    explanation JSONB,
    predicted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_results (
    model_result_id BIGSERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    dataset_name VARCHAR(100) NOT NULL,
    accuracy NUMERIC(8, 6),
    precision_score NUMERIC(8, 6),
    recall_score NUMERIC(8, 6),
    f1_score NUMERIC(8, 6),
    roc_auc NUMERIC(8, 6),
    pr_auc NUMERIC(8, 6),
    training_seconds NUMERIC(12, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(100) REFERENCES transactions(transaction_id),
    severity VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
