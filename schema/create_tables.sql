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


-- ------------------------------------------------------------
-- Dimension: Loan Grade
-- One row per (grade, sub_grade) combination — max 35 rows
-- ------------------------------------------------------------


-- ------------------------------------------------------------
-- Dimension: Time
-- One row per unique issue month (Lending Club issues monthly)
-- Derived from issue_d parsed as 'Jan-2015' format
-- Adds year, month, quarter
-- ------------------------------------------------------------


-- ------------------------------------------------------------
-- Dimension: Purpose
-- Deduplicates on (purpose, term) — ~30 combinations
-- ------------------------------------------------------------


-- ------------------------------------------------------------
-- Fact: Loans
-- One row per loan. Foreign keys to all four dimensions.
-- int_rate stored as DOUBLE (% stripped in transform step)
-- is_default = TRUE when loan_status = 'Charged Off'
-- ------------------------------------------------------------
