-- ============================================================
-- Star Schema DDL — Financial Data Warehouse (Lending Club)
-- ============================================================
-- Run order: dims first, fact last (foreign key dependencies)
-- All tables use CREATE TABLE IF NOT EXISTS for idempotency


-- ------------------------------------------------------------
-- Dimension: Borrower
-- Deduplicates on (addr_state, zip_code, home_ownership,
-- emp_length, verification_status)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_borrower (
    borrower_id INT PRIMARY KEY,
    addr_state VARCHAR(2),
    zip_code VARCHAR(5),
    home_ownership VARCHAR(10),
    emp_length VARCHAR(20),
    verification_status VARCHAR(20),
    UNIQUE (addr_state, zip_code, home_ownership, emp_length, verification_status)
);  


-- ------------------------------------------------------------
-- Dimension: Loan Grade
-- One row per (grade, sub_grade) combination — max 35 rows
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_loan_grade (
    grade_id INT PRIMARY KEY,
    grade VARCHAR(1),
    sub_grade VARCHAR(2),
    UNIQUE (grade, sub_grade)
);


-- ------------------------------------------------------------
-- Dimension: Time
-- One row per unique issue month (Lending Club issues monthly)
-- Derived from issue_d parsed as 'Jan-2015' format
-- Adds year, month, quarter
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_time (
    time_id INT PRIMARY KEY,
    year INT,
    month INT,
    quarter INT,
    UNIQUE (year, month)
);


-- ------------------------------------------------------------
-- Dimension: Purpose
-- Deduplicates on (purpose, term) — ~30 combinations
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_purpose (
    purpose_id INT PRIMARY KEY,
    purpose VARCHAR(50),
    term VARCHAR(10),
    UNIQUE (purpose, term)
);


-- ------------------------------------------------------------
-- Fact: Loans
-- One row per loan. Foreign keys to all four dimensions.
-- int_rate stored as DOUBLE PRECISION (% stripped in transform step)
-- is_default = TRUE when loan_status = 'Charged Off'
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_loans (
    loan_id INT PRIMARY KEY,
    borrower_id INT,
    grade_id INT,
    time_id INT,
    purpose_id INT,
    loan_amnt FLOAT,
    funded_amnt FLOAT,
    int_rate DOUBLE PRECISION,
    installment FLOAT,
    annual_inc FLOAT,
    dti FLOAT,
    total_pymnt FLOAT,
    total_rec_prncp FLOAT,  
    total_rec_int FLOAT,
    recoveries FLOAT,
    is_default BOOLEAN,
    loan_status VARCHAR(64),
    FOREIGN KEY (borrower_id) REFERENCES dim_borrower (borrower_id),
    FOREIGN KEY (grade_id) REFERENCES dim_loan_grade (grade_id),
    FOREIGN KEY (time_id) REFERENCES dim_time (time_id),
    FOREIGN KEY (purpose_id) REFERENCES dim_purpose (purpose_id)
);  
