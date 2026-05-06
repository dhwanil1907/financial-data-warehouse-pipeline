# Star Schema ERD

## Tables

- **fact_loans** — central fact table, one row per loan
- **dim_borrower** — borrower profile (state, zip, home ownership, employment, verification)
- **dim_loan_grade** — LC grade/sub_grade (A1–G5)
- **dim_time** — issue month with year, month, quarter
- **dim_purpose** — loan purpose and term combination

## Relationships

- `fact_loans.borrower_id` → `dim_borrower.borrower_id`
- `fact_loans.grade_id` → `dim_loan_grade.grade_id`
- `fact_loans.time_id` → `dim_time.time_id`
- `fact_loans.purpose_id` → `dim_purpose.purpose_id`

## dbdiagram.io Source

Paste into https://dbdiagram.io/d :

<!-- Add dbdiagram.io Table{} block here after DDL is written -->
