-- ============================================================
-- Star Schema DDL — Financial Data Warehouse (Lending Club)
--
-- Layout: four dimension tables + one central fact table.
-- To re-run this script cleanly, tables are dropped and
-- recreated. fact_loans is dropped first because it holds
-- foreign keys into the dimension tables.
-- ============================================================


-- Drop in reverse-dependency order so FK constraints don't block the drops.
DROP TABLE IF EXISTS fact_loans;
DROP TABLE IF EXISTS dim_borrower;
DROP TABLE IF EXISTS dim_loan_grade;
DROP TABLE IF EXISTS dim_time;
DROP TABLE IF EXISTS dim_purpose;


-- ------------------------------------------------------------
-- dim_borrower
-- One row per unique borrower profile. Two loans from the same
-- state/zip/ownership/employment/verification combination share
-- a single borrower_id rather than duplicating the profile.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_borrower (
    borrower_id         INT PRIMARY KEY,
    addr_state          VARCHAR(2),   -- two-letter US state code
    zip_code            VARCHAR(5),
    home_ownership      VARCHAR(10),  -- e.g. RENT, OWN, MORTGAGE
    emp_length          VARCHAR(20),  -- e.g. '10+ years', '< 1 year'
    verification_status VARCHAR(20),  -- e.g. Verified, Not Verified
    UNIQUE (addr_state, zip_code, home_ownership, emp_length, verification_status)
);


-- ------------------------------------------------------------
-- dim_loan_grade
-- One row per (grade, sub_grade) pair — at most 35 rows
-- (grades A–G, each with five sub-grades 1–5).
-- grade_id is an integer surrogate that fact_loans references.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_loan_grade (
    grade_id  INT PRIMARY KEY,
    grade     VARCHAR(1),   -- A through G
    sub_grade VARCHAR(2),   -- A1 through G5
    UNIQUE (grade, sub_grade)
);


-- ------------------------------------------------------------
-- dim_time
-- One row per calendar month in which loans were issued.
-- issue_d values like 'Jan-2015' are parsed into year/month;
-- quarter is derived (1–4). The UNIQUE constraint on (year, month)
-- prevents duplicate months from being inserted.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_time (
    time_id INT PRIMARY KEY,
    year    INT,
    month   INT,            -- 1–12
    quarter INT,            -- 1–4, derived from month
    UNIQUE (year, month)
);


-- ------------------------------------------------------------
-- dim_purpose
-- One row per (purpose, term) combination — roughly 30 pairs.
-- purpose describes why the borrower requested the loan
-- (e.g. debt_consolidation, home_improvement); term is the
-- repayment length (e.g. '36 months', '60 months').
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_purpose (
    purpose_id INT PRIMARY KEY,
    purpose    VARCHAR(50),
    term       VARCHAR(10),
    UNIQUE (purpose, term)
);


-- ------------------------------------------------------------
-- fact_loans
-- Central fact table — one row per individual loan.
--
-- Monetary columns (loan_amnt, funded_amnt, etc.) are in USD.
-- int_rate is stored as a plain decimal (e.g. 0.1299 for 12.99%)
--   — the % symbol is stripped during the transform step.
-- is_default is TRUE when the raw loan_status = 'Charged Off'.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_loans (
    loan_id          INT PRIMARY KEY,
    borrower_id      INT,
    grade_id         INT,
    time_id          INT,
    purpose_id       INT,
    loan_amnt        FLOAT,
    funded_amnt      FLOAT,
    int_rate         DOUBLE PRECISION,
    installment      FLOAT,
    annual_inc       FLOAT,
    dti              FLOAT,
    total_pymnt      FLOAT,
    total_rec_prncp  FLOAT,
    total_rec_int    FLOAT,
    recoveries       FLOAT,
    is_default       BOOLEAN,
    loan_status      VARCHAR(64),
    FOREIGN KEY (borrower_id) REFERENCES dim_borrower (borrower_id),
    FOREIGN KEY (grade_id)    REFERENCES dim_loan_grade (grade_id),
    FOREIGN KEY (time_id)     REFERENCES dim_time (time_id),
    FOREIGN KEY (purpose_id)  REFERENCES dim_purpose (purpose_id)
);
