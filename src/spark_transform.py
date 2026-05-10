"""
PySpark aggregation layer — reads the raw Lending Club CSV and writes Parquet.

Public API:
    create_spark_session(app_name)     local[*] SparkSession
    compute_default_rate_by_grade(df)  grade, default_rate (0–1)
    compute_avg_loan_by_year(df)       issue_year, avg_loan_amount
    write_parquet(df, path)            overwrite Parquet at path
    run_spark_pipeline(csv, out_dir)   raw_loans + analytics Parquet folders
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def create_spark_session(app_name: str = "financial-dw") -> SparkSession:
    """Return a SparkSession in local mode suitable for laptop-sized runs."""
    return (
        SparkSession.builder.master("local[*]")
        .appName(app_name)
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )


def _read_loans_csv(spark: SparkSession, csv_path: str) -> DataFrame:
    """Read Lending Club CSV and keep only real loan rows (numeric ``id``)."""
    raw = spark.read.option("header", True).option("inferSchema", False).csv(csv_path)
    id_num = F.col("id").cast("long")
    df = raw.withColumn("_id_num", id_num).filter(F.col("_id_num").isNotNull()).drop("_id_num")
    return (
        df.withColumn("loan_amnt", F.col("loan_amnt").cast("double"))
        .withColumn("funded_amnt", F.col("funded_amnt").cast("double"))
        .withColumn("is_default", F.col("loan_status") == F.lit("Charged Off"))
    )


def compute_default_rate_by_grade(df: DataFrame) -> DataFrame:
    """Group by LC letter grade; default_rate = share of Charged Off loans."""
    return (
        df.groupBy("grade")
        .agg(F.avg(F.col("is_default").cast("double")).alias("default_rate"))
        .orderBy(F.desc("default_rate"))
    )


def compute_avg_loan_by_year(df: DataFrame) -> DataFrame:
    """Parse ``issue_d`` (Jan-2015) into calendar year; average ``loan_amnt``."""
    # Prefix day so Java time parser accepts MMM-yyyy reliably.
    issue_ts = F.to_timestamp(F.concat(F.lit("01-"), F.col("issue_d")), "dd-MMM-yyyy")
    return (
        df.withColumn("issue_year", F.year(issue_ts))
        .filter(F.col("issue_year").isNotNull())
        .groupBy("issue_year")
        .agg(F.avg("loan_amnt").alias("avg_loan_amount"))
        .orderBy("issue_year")
    )


def write_parquet(df: DataFrame, path: str) -> None:
    """Write ``df`` to Parquet (overwrite). Creates a directory of part files."""
    df.write.mode("overwrite").parquet(path)


def run_spark_pipeline(csv_path: str, output_dir: str) -> None:
    """Write ``raw_loans``, ``default_rate_by_grade``, and ``avg_loan_by_year`` Parquet trees."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    spark = create_spark_session()
    try:
        loans = _read_loans_csv(spark, csv_path)
        write_parquet(loans, str(out / "raw_loans"))
        write_parquet(compute_default_rate_by_grade(loans), str(out / "default_rate_by_grade"))
        write_parquet(compute_avg_loan_by_year(loans), str(out / "avg_loan_by_year"))
    finally:
        spark.stop()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Spark: CSV → Parquet aggregates.")
    parser.add_argument("--csv", required=True, help="Path to Lending Club CSV")
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory for Parquet output (default: data/processed)",
    )
    args = parser.parse_args(argv)
    if not Path(args.csv).is_file():
        print(f"Error: CSV not found: {args.csv}", file=sys.stderr)
        return 1
    run_spark_pipeline(args.csv, args.output_dir)
    print(f"Parquet written under {args.output_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
