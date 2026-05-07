# Star Schema ERD — Financial Data Warehouse (Lending Club)

## Normalization Notes

The schema is a classic star schema: one central fact table surrounded by four
dimension tables. Normalization decisions:

- **dim_borrower** deduplicates on the five-column natural key
  `(addr_state, zip_code, home_ownership, emp_length, verification_status)`.
  This captures borrower *segments*, not individual identities, keeping cardinality low.
- **dim_loan_grade** holds at most 35 rows — one per (grade A–G) × (sub-grade 1–5)
  combination. `grade_id` is an integer surrogate rather than using the string
  sub-grade as a key.
- **dim_time** stores one row per calendar month. `quarter` is a derived column
  (not a natural key attribute) so the UNIQUE constraint is on `(year, month)` only.
- **dim_purpose** deduplicates on `(purpose, term)` — roughly 30 combinations.
  Keeping `term` here avoids adding it to `fact_loans`, reducing row width.
- **fact_loans** carries every per-loan numeric measure plus the four FK surrogates.
  `is_default` is a pre-computed boolean (TRUE when `loan_status = 'Charged Off'`)
  to avoid string comparisons in every analytic query.

## Relationships

```
fact_loans.borrower_id  →  dim_borrower.borrower_id
fact_loans.grade_id     →  dim_loan_grade.grade_id
fact_loans.time_id      →  dim_time.time_id
fact_loans.purpose_id   →  dim_purpose.purpose_id
```

## dbdiagram.io Source

Paste at https://dbdiagram.io/d to render the ERD:

```
Table dim_borrower {
  borrower_id         int [pk]
  addr_state          varchar(2)
  zip_code            varchar(5)
  home_ownership      varchar(10)
  emp_length          varchar(20)
  verification_status varchar(20)

  indexes {
    (addr_state, zip_code, home_ownership, emp_length, verification_status) [unique]
  }
}

Table dim_loan_grade {
  grade_id  int [pk]
  grade     varchar(1)
  sub_grade varchar(2)

  indexes {
    (grade, sub_grade) [unique]
  }
}

Table dim_time {
  time_id int [pk]
  year    int
  month   int
  quarter int

  indexes {
    (year, month) [unique]
  }
}

Table dim_purpose {
  purpose_id int [pk]
  purpose    varchar(50)
  term       varchar(10)

  indexes {
    (purpose, term) [unique]
  }
}

Table fact_loans {
  loan_id         int [pk]
  borrower_id     int [ref: > dim_borrower.borrower_id]
  grade_id        int [ref: > dim_loan_grade.grade_id]
  time_id         int [ref: > dim_time.time_id]
  purpose_id      int [ref: > dim_purpose.purpose_id]
  loan_amnt       float
  funded_amnt     float
  int_rate        float
  installment     float
  annual_inc      float
  dti             float
  total_pymnt     float
  total_rec_prncp float
  total_rec_int   float
  recoveries      float
  is_default      boolean
  loan_status     varchar(64)
}
```
