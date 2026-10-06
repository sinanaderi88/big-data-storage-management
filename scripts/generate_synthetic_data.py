from pathlib import Path
from datetime import date, timedelta, datetime
import random
import csv
import os
import math


# =========================================================
# Configuration
# =========================================================

ROOT = Path("/home/sina/bigdata-lab/storage_lab/bronze")
METADATA_DIR = Path("/home/sina/bigdata-lab/storage_lab/metadata")

random.seed(42)

# Full synthetic history for the public case study
START_DATE = date(2024, 1, 1)
END_DATE = date(2026, 9, 30)


# =========================================================
# Normal file-size patterns
# =========================================================

PATTERNS = {
    "small_file_heavy": (5, 30),
    "healthy": (60, 120),
    "large_file_heavy": (500, 1000),
    "mixed": (10, 150),
}


# =========================================================
# Historical growth behavior
#
# File count and file size intentionally grow at different
# rates. This prevents storage and file-count charts from
# becoming simple copies of each other.
# =========================================================

PATTERN_BEHAVIOR = {
    "small_file_heavy": {
        "file_count_growth": 0.018,
        "file_size_growth": -0.002,
        "seasonality_count": 0.12,
        "seasonality_size": 0.08,
        "noise_count": 0.16,
        "noise_size": 0.20,
    },
    "healthy": {
        "file_count_growth": 0.010,
        "file_size_growth": 0.004,
        "seasonality_count": 0.08,
        "seasonality_size": 0.07,
        "noise_count": 0.12,
        "noise_size": 0.15,
    },
    "large_file_heavy": {
        "file_count_growth": 0.007,
        "file_size_growth": 0.006,
        "seasonality_count": 0.07,
        "seasonality_size": 0.10,
        "noise_count": 0.10,
        "noise_size": 0.18,
    },
    "mixed": {
        "file_count_growth": 0.014,
        "file_size_growth": 0.002,
        "seasonality_count": 0.14,
        "seasonality_size": 0.12,
        "noise_count": 0.18,
        "noise_size": 0.22,
    },
}


def calculate_generation_factors(
    pattern: str,
    table_name: str,
    current_date: date
):
    """Return independent file-count and file-size factors."""

    behavior = PATTERN_BEHAVIOR[pattern]

    months_since_start = (
        (current_date.year - START_DATE.year) * 12
        + (current_date.month - START_DATE.month)
    )

    # Stable table-specific variation.
    # This gives different tables slightly different long-term behavior
    # without adding another configuration block for every table.
    table_seed = sum(ord(char) for char in table_name)
    growth_variation = 1 + ((table_seed % 9) - 4) / 100

    count_growth = (
        1 + behavior["file_count_growth"] * growth_variation
    ) ** months_since_start

    size_growth = (
        1 + behavior["file_size_growth"] * growth_variation
    ) ** months_since_start

    # Table-specific seasonal phase prevents every table from
    # reaching its peak in exactly the same month.
    phase = (table_seed % 12) / 12 * 2 * 3.141592653589793

    count_seasonality = (
        1
        + behavior["seasonality_count"]
        * math.sin(
            ((current_date.month - 1) / 12)
            * 2
            * 3.141592653589793
            + phase
        )
    )

    size_seasonality = (
        1
        + behavior["seasonality_size"]
        * math.sin(
            ((current_date.month - 1) / 12)
            * 2
            * 3.141592653589793
            + phase
            + 0.8
        )
    )

    count_noise = max(
        0.70,
        min(
            1.30,
            random.gauss(
                1.0,
                behavior["noise_count"]
            )
        )
    )

    size_noise = max(
        0.65,
        min(
            1.35,
            random.gauss(
                1.0,
                behavior["noise_size"]
            )
        )
    )

    return (
        count_growth * count_seasonality * count_noise,
        size_growth * size_seasonality * size_noise
    )


# =========================================================
# File formats
#
# The content of the files is NOT generated.
# Files are only metadata carriers.
# =========================================================

FILE_FORMATS = {
    "customer_profile": "csv",
    "customer_events": "json",
    "customer_history": "csv",
    "customer_scores": "dat",
    "customer_activity": "json",

    "billing_transaction": "dat",
    "billing_summary": "csv",
    "invoice_detail": "dat",
    "payment_history": "csv.gz",
    "payment_events": "json",

    "network_usage": "parquet",
    "network_events": "dat",
    "network_sessions": "json",
    "network_summary": "csv",
    "network_quality": "dat",

    "sales_order": "csv",
    "sales_detail": "dat",
    "sales_summary": "csv",
    "product_sales": "parquet",
    "sales_events": "json",

    "inventory_item": "csv",
    "inventory_movement": "dat",
    "inventory_snapshot": "parquet",
    "warehouse_activity": "json",
    "stock_history": "csv",

    "application_event": "json",
    "application_log": "txt",
    "application_session": "dat",
    "application_usage": "csv",
    "application_summary": "parquet",

    "marketing_event": "json",
    "campaign_activity": "csv",
    "campaign_response": "dat",
    "customer_segment": "csv",
    "marketing_summary": "parquet",

    "service_event": "json",
    "service_request": "dat",
    "service_history": "csv",
    "service_usage": "parquet",
    "service_summary": "csv",

    "analytics_event": "json",
    "analytics_daily": "csv",
    "analytics_summary": "parquet",
    "metric_history": "dat",
    "metric_snapshot": "csv",

    "operations_event": "json",
    "operations_log": "txt",
    "operations_daily": "csv",
    "operations_summary": "parquet",
    "operations_history": "dat",
}


# =========================================================
# Table configuration
#
# "anomaly" describes the injected behavior only.
# It is NEVER reflected in the file name.
# =========================================================

TABLE_CONFIG = {

    "customer_profile": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "customer_events": {
        "pattern": "small_file_heavy",
        "anomaly": "small_file_spike",
    },

    "customer_history": {
        "pattern": "large_file_heavy",
        "anomaly": "large_file",
    },

    "customer_scores": {
        "pattern": "mixed",
        "anomaly": None,
    },

    "customer_activity": {
        "pattern": "small_file_heavy",
        "anomaly": "file_count_spike",
    },

    "billing_transaction": {
        "pattern": "small_file_heavy",
        "anomaly": "small_file_spike",
    },

    "billing_summary": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "invoice_detail": {
        "pattern": "large_file_heavy",
        "anomaly": "large_file",
    },

    "payment_history": {
        "pattern": "mixed",
        "anomaly": None,
    },

    "payment_events": {
        "pattern": "small_file_heavy",
        "anomaly": "file_count_spike",
    },

    "network_usage": {
        "pattern": "large_file_heavy",
        "anomaly": "large_file",
    },

    "network_events": {
        "pattern": "small_file_heavy",
        "anomaly": "small_file_spike",
    },

    "network_sessions": {
        "pattern": "small_file_heavy",
        "anomaly": "file_count_spike",
    },

    "network_summary": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "network_quality": {
        "pattern": "mixed",
        "anomaly": None,
    },

    "sales_order": {
        "pattern": "small_file_heavy",
        "anomaly": "storage_growth",
    },

    "sales_detail": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "sales_summary": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "product_sales": {
        "pattern": "large_file_heavy",
        "anomaly": None,
    },

    "sales_events": {
        "pattern": "small_file_heavy",
        "anomaly": "small_file_spike",
    },

    "inventory_item": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "inventory_movement": {
        "pattern": "small_file_heavy",
        "anomaly": "file_count_spike",
    },

    "inventory_snapshot": {
        "pattern": "large_file_heavy",
        "anomaly": None,
    },

    "warehouse_activity": {
        "pattern": "small_file_heavy",
        "anomaly": "small_file_spike",
    },

    "stock_history": {
        "pattern": "mixed",
        "anomaly": None,
    },

    "application_event": {
        "pattern": "small_file_heavy",
        "anomaly": "file_count_spike",
    },

    "application_log": {
        "pattern": "small_file_heavy",
        "anomaly": "small_file_spike",
    },

    "application_session": {
        "pattern": "mixed",
        "anomaly": None,
    },

    "application_usage": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "application_summary": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "marketing_event": {
        "pattern": "small_file_heavy",
        "anomaly": "small_file_spike",
    },

    "campaign_activity": {
        "pattern": "mixed",
        "anomaly": None,
    },

    "campaign_response": {
        "pattern": "small_file_heavy",
        "anomaly": "file_count_spike",
    },

    "customer_segment": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "marketing_summary": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "service_event": {
        "pattern": "small_file_heavy",
        "anomaly": "file_count_spike",
    },

    "service_request": {
        "pattern": "mixed",
        "anomaly": None,
    },

    "service_history": {
        "pattern": "large_file_heavy",
        "anomaly": "large_file",
    },

    "service_usage": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "service_summary": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "analytics_event": {
        "pattern": "small_file_heavy",
        "anomaly": "small_file_spike",
    },

    "analytics_daily": {
        "pattern": "healthy",
        "anomaly": "storage_growth",
    },

    "analytics_summary": {
        "pattern": "large_file_heavy",
        "anomaly": None,
    },

    "metric_history": {
        "pattern": "mixed",
        "anomaly": None,
    },

    "metric_snapshot": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "operations_event": {
        "pattern": "small_file_heavy",
        "anomaly": "file_count_spike",
    },

    "operations_log": {
        "pattern": "small_file_heavy",
        "anomaly": "small_file_spike",
    },

    "operations_daily": {
        "pattern": "healthy",
        "anomaly": None,
    },

    "operations_summary": {
        "pattern": "large_file_heavy",
        "anomaly": "large_file",
    },

    "operations_history": {
        "pattern": "mixed",
        "anomaly": None,
    },
}


# =========================================================
# Synthetic ingestion hour per table
#
# IMPORTANT:
#
# This is NOT the partition hour.
# This is NOT the script execution time.
#
# It represents the synthetic ingestion/load hour
# used for Peak Load analysis.
# =========================================================

TABLE_INGESTION_HOUR = {

    "customer_profile": 8,
    "customer_events": 9,
    "customer_history": 10,
    "customer_scores": 11,
    "customer_activity": 13,

    "billing_transaction": 13,
    "billing_summary": 14,
    "invoice_detail": 15,
    "payment_history": 16,
    "payment_events": 17,

    "network_usage": 8,
    "network_events": 9,
    "network_sessions": 10,
    "network_summary": 13,
    "network_quality": 14,

    "sales_order": 13,
    "sales_detail": 15,
    "sales_summary": 16,
    "product_sales": 17,
    "sales_events": 18,

    "inventory_item": 8,
    "inventory_movement": 9,
    "inventory_snapshot": 10,
    "warehouse_activity": 13,
    "stock_history": 14,

    "application_event": 15,
    "application_log": 16,
    "application_session": 17,
    "application_usage": 18,
    "application_summary": 19,

    "marketing_event": 9,
    "campaign_activity": 10,
    "campaign_response": 13,
    "customer_segment": 14,
    "marketing_summary": 15,

    "service_event": 16,
    "service_request": 17,
    "service_history": 18,
    "service_usage": 19,
    "service_summary": 20,

    "analytics_event": 10,
    "analytics_daily": 13,
    "analytics_summary": 14,
    "metric_history": 15,
    "metric_snapshot": 16,

    "operations_event": 17,
    "operations_log": 18,
    "operations_daily": 19,
    "operations_summary": 20,
    "operations_history": 21,
}


# =========================================================
# Partition behavior
# =========================================================

HOURLY_TABLES = {
    "customer_events",
    "customer_activity",
    "billing_transaction",
    "payment_events",
    "network_events",
    "network_sessions",
    "sales_order",
    "application_event",
    "application_log",
    "marketing_event",
    "service_event",
    "analytics_event",
    "operations_event",
}


DAILY_TABLES = {
    "customer_profile",
    "customer_history",
    "billing_summary",
    "network_summary",
    "sales_summary",
    "inventory_snapshot",
    "application_summary",
    "marketing_summary",
    "service_summary",
    "analytics_daily",
    "operations_daily",
}


# =========================================================
# Ground truth
#
# Used only for internal validation of the later analysis.
# Do NOT publish this file in the public repository.
# =========================================================

GROUND_TRUTH = []


# =========================================================
# Create one physical file
#
# IMPORTANT:
# No file content is written.
# Only the file size is created.
#
# ModificationTime is explicitly controlled and therefore
# does NOT depend on the actual execution time of the script.
# =========================================================

def create_file(
    path: Path,
    size_mb: int,
    modification_time: datetime
):

    size_bytes = size_mb * 1024 * 1024

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(path, "wb") as f:
        f.truncate(size_bytes)

    # -----------------------------------------------------
    # Explicitly set ModificationTime.
    # This prevents the actual generator execution time
    # from becoming the file modification time.
    # -----------------------------------------------------

    timestamp = modification_time.timestamp()

    os.utime(
        path,
        (timestamp, timestamp)
    )


# =========================================================
# Generate synthetic ModificationTime
# =========================================================

def generate_modification_time(
    modification_date: date,
    ingestion_hour: int
) -> datetime:

    return datetime(
        modification_date.year,
        modification_date.month,
        modification_date.day,
        ingestion_hour,
        random.randint(0, 59),
        random.randint(0, 59)
    )


# =========================================================
# Normal file generation
# =========================================================

def create_normal_files(
    partition_path: Path,
    pattern: str,
    table_name: str,
    modification_date: date,
    ingestion_hour: int
):

    min_mb, max_mb = PATTERNS[pattern]

    if pattern == "small_file_heavy":
        base_file_count = random.randint(8, 15)
        max_file_count = 40

    elif pattern == "healthy":
        base_file_count = random.randint(2, 5)
        max_file_count = 12

    elif pattern == "large_file_heavy":
        base_file_count = random.randint(1, 2)
        max_file_count = 8

    else:
        base_file_count = random.randint(3, 7)
        max_file_count = 25

    count_factor, size_factor = calculate_generation_factors(
        pattern,
        table_name,
        modification_date
    )

    file_count = max(
        1,
        min(
            max_file_count,
            round(base_file_count * count_factor)
        )
    )

    extension = FILE_FORMATS.get(
        table_name,
        "dat"
    )

    for i in range(1, file_count + 1):

        # File size has its own trend, seasonality and noise.
        # It is intentionally independent from file-count noise.
        file_size_noise = random.uniform(0.82, 1.18)

        generated_min = max(
            1,
            round(min_mb * size_factor * file_size_noise)
        )

        generated_max = max(
            generated_min,
            round(max_mb * size_factor * file_size_noise)
        )

        size_mb = random.randint(
            generated_min,
            generated_max
        )

        file_name = (
            f"{table_name}_"
            f"{i:05d}."
            f"{extension}"
        )

        modification_time = generate_modification_time(
            modification_date,
            ingestion_hour
        )

        create_file(
            partition_path / file_name,
            size_mb,
            modification_time
        )


# =========================================================
# Inject intentional abnormal behavior
#
# IMPORTANT:
# File names remain completely normal.
# =========================================================

def create_abnormal_files(
    partition_path: Path,
    table_name: str,
    anomaly_type: str,
    modification_date: date,
    ingestion_hour: int
):

    extension = FILE_FORMATS.get(
        table_name,
        "dat"
    )

    def create_abnormal_file(
        file_name,
        size_mb
    ):

        modification_time = generate_modification_time(
            modification_date,
            ingestion_hour
        )

        create_file(
            partition_path / file_name,
            size_mb,
            modification_time
        )

    # -----------------------------------------------------
    # Extremely large file
    # -----------------------------------------------------

    if anomaly_type == "large_file":

        create_abnormal_file(
            f"{table_name}_extra_01.{extension}",
            2048
        )

    # -----------------------------------------------------
    # Extremely small files
    # -----------------------------------------------------

    elif anomaly_type == "small_file_spike":

        for i in range(1, 31):

            create_abnormal_file(
                f"{table_name}_extra_{i:03d}.{extension}",
                random.randint(1, 5)
            )

    # -----------------------------------------------------
    # Huge number of files
    # -----------------------------------------------------

    elif anomaly_type == "file_count_spike":

        for i in range(1, 101):

            create_abnormal_file(
                f"{table_name}_extra_{i:03d}.{extension}",
                random.randint(5, 10)
            )

    # -----------------------------------------------------
    # Storage growth
    # -----------------------------------------------------

    elif anomaly_type == "storage_growth":

        for i in range(1, 16):

            create_abnormal_file(
                f"{table_name}_extra_{i:03d}.{extension}",
                random.randint(150, 300)
            )


# =========================================================
# Create partition data
# =========================================================

def create_partition_data(
    partition_path: Path,
    table_name: str,
    pattern: str,
    anomaly_type: str | None,
    inject_anomaly: bool,
    source_name: str,
    date_value: str,
    modification_date: date,
    ingestion_hour: int
):

    partition_path.mkdir(
        parents=True,
        exist_ok=True
    )

    create_normal_files(
        partition_path,
        pattern,
        table_name,
        modification_date,
        ingestion_hour
    )

    if anomaly_type and inject_anomaly:

        create_abnormal_files(
            partition_path,
            table_name,
            anomaly_type,
            modification_date,
            ingestion_hour
        )

        # Internal validation record
        GROUND_TRUTH.append({
            "source": source_name,
            "table": table_name,
            "date": date_value,
            "anomaly_type": anomaly_type,
            "partition": str(partition_path),
        })


# =========================================================
# Main generator
# =========================================================

def main():

    current = START_DATE

    while current <= END_DATE:

        date_value = current.isoformat()

        for source_path in ROOT.iterdir():

            if not source_path.is_dir():
                continue

            source_name = source_path.name

            for table_path in source_path.iterdir():

                if not table_path.is_dir():
                    continue

                table = table_path.name

                config = TABLE_CONFIG.get(table)

                if not config:
                    continue

                pattern = config["pattern"]
                anomaly = config["anomaly"]

                # -------------------------------------------------
                # Synthetic ingestion hour for this table.
                #
                # This is independent from the actual script
                # execution time and from partition hour.
                # -------------------------------------------------

                ingestion_hour = TABLE_INGESTION_HOUR[table]

                # -------------------------------------------------
                # Anomaly is injected on selected dates.
                #
                # This is intentionally NOT visible in file names.
                # -------------------------------------------------

                inject_anomaly = (
                    current.day == 1
                    or current.day == 15
                )

                # -------------------------------------------------
                # Hourly tables
                # -------------------------------------------------

                if table in HOURLY_TABLES:

                    for hour in range(24):

                        partition_path = (
                            table_path
                            / f"event_date={date_value}"
                            / f"hour={hour:02d}"
                        )

                        # Only noon receives the abnormal behavior.
                        # This remains independent from the
                        # synthetic ingestion hour.
                        hour_anomaly = (
                            inject_anomaly
                            and hour == 12
                        )

                        create_partition_data(
                            partition_path,
                            table,
                            pattern,
                            anomaly,
                            hour_anomaly,
                            source_name,
                            date_value,
                            current,
                            ingestion_hour
                        )

                # -------------------------------------------------
                # Daily tables
                # -------------------------------------------------

                elif table in DAILY_TABLES:

                    partition_path = (
                        table_path
                        / f"event_date={date_value}"
                    )

                    create_partition_data(
                        partition_path,
                        table,
                        pattern,
                        anomaly,
                        inject_anomaly,
                        source_name,
                        date_value,
                        current,
                        ingestion_hour
                    )

                # -------------------------------------------------
                # Non-partitioned tables
                # -------------------------------------------------

                else:

                    create_partition_data(
                        table_path,
                        table,
                        pattern,
                        anomaly,
                        False,
                        source_name,
                        date_value,
                        current,
                        ingestion_hour
                    )

        current += timedelta(days=1)

    # =========================================================
    # Save internal ground truth
    # =========================================================

    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    ground_truth_file = (
        METADATA_DIR /
        "generator_ground_truth.csv"
    )

    with open(
        ground_truth_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source",
                "table",
                "date",
                "anomaly_type",
                "partition",
            ]
        )

        writer.writeheader()
        writer.writerows(GROUND_TRUTH)

    print(
        "Synthetic storage metadata environment "
        "created successfully."
    )

    print(
        f"Date range: "
        f"{START_DATE} -> {END_DATE}"
    )

    print(
        f"Ground truth: "
        f"{ground_truth_file}"
    )


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":
    main()
