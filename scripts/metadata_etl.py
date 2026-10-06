#!/usr/bin/env python3

from pathlib import Path
import pandas as pd
import re

INPUT = Path("/home/sina/bigdata-lab/storage_lab/metadata/metadata_inventory.csv")
OUTPUT = Path("/home/sina/bigdata-lab/storage_lab/metadata/metadata_clean.csv")

SUPPORTED_FORMATS = {
    "csv", "dat", "unl", "json", "orc",
    "txt", "edr", "rec", "parquet"
}


def extract_partition_date(value):
    if not isinstance(value, str):
        return None

    patterns = [
        (r"^\d{4}-\d{2}-\d{2}$", "%Y-%m-%d"),
        (r"^\d{8}$", "%Y%m%d"),
        (r"^\d{4}_\d{2}_\d{2}$", "%Y_%m_%d"),
    ]

    for pattern, fmt in patterns:
        if re.fullmatch(pattern, value):
            try:
                return pd.to_datetime(value, format=fmt)
            except ValueError:
                return None

    return None


def extract_partition_info(parent_path):
    if not isinstance(parent_path, str):
        return None, None, None, False, None

    partition_column = None
    partition_name = None
    partition_pattern = None
    has_hourly_partition = False
    hourly_partition_name = None

    for part in parent_path.split("/"):
        if "=" not in part:
            continue

        key, value = part.split("=", 1)

        if not key or not value:
            continue

        # Date partition
        partition_date = extract_partition_date(value)

        if partition_date is not None:
            partition_column = key
            partition_name = part

            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                partition_pattern = "YYYY-MM-DD"
            elif re.fullmatch(r"\d{8}", value):
                partition_pattern = "YYYYMMDD"
            else:
                partition_pattern = "YYYY_MM_DD"

            # Do not return here.
            # Continue scanning the path for an hourly partition.
            continue

        # Hourly partition
        if (
            re.fullmatch(r"\d{1,2}", value)
            and re.search(r"(^|_)(hour|hr)($|_)", key, re.IGNORECASE)
        ):
            has_hourly_partition = True
            hourly_partition_name = part

    return (
        partition_column,
        partition_name,
        partition_pattern,
        has_hourly_partition,
        hourly_partition_name
    )


def extract_file_format(file_name):
    if not file_name:
        return "unknown"

    name = file_name.lower()

    if name.endswith(".gz"):
        name = name[:-3]

    if "." not in name:
        return "unknown"

    extension = name.rsplit(".", 1)[1]

    return extension if extension in SUPPORTED_FORMATS else "unknown"


def extract_source_table(parent_path):
    parts = Path(parent_path).parts

    try:
        bronze_idx = next(
            i for i, part in enumerate(parts)
            if part.lower() == "bronze"
        )
    except StopIteration:
        return "unknown", "unknown"

    source = (
        parts[bronze_idx + 1]
        if len(parts) > bronze_idx + 1
        else "unknown"
    )

    table = (
        parts[bronze_idx + 2]
        if len(parts) > bronze_idx + 2
        else "unknown"
    )

    return source, table


def clean_metadata():

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT)

    # Basic normalization
    df["ParentPath"] = df["ParentPath"].fillna("").astype(str)
    df["FullPath"] = df["FullPath"].fillna("").astype(str)
    df["Type"] = df["Type"].fillna("").astype(str)

    df["FileSizeBytes"] = (
        pd.to_numeric(df["FileSizeBytes"], errors="coerce")
        .fillna(0)
        .astype("Int64")
    )

    # File name
    df["FileName"] = df["FullPath"].apply(
        lambda x: Path(x).name if x else ""
    )

    # A value containing "=" is not considered a valid file name
    df.loc[
        df["FileName"].str.contains("=", regex=False, na=False),
        "FileName"
    ] = ""

    # File format
    df["FileFormat"] = df["FileName"].apply(extract_file_format)

    # Empty directories
    is_empty_dir = df["Type"].eq("EMPTY_DIRECTORY")

    df["FileCount"] = 1
    df.loc[is_empty_dir, "FileCount"] = 0
    df["FileCount"] = df["FileCount"].astype("Int64")

    df["TotalSizeBytes"] = df["FileSizeBytes"].astype("Int64")

    # Source / table
    source_table = df["ParentPath"].apply(extract_source_table)

    df["Source"] = source_table.apply(lambda x: x[0])
    df["TableName"] = source_table.apply(lambda x: x[1])
    df["LogicalTableName"] = df["TableName"]

    # Zone
    df["Zone"] = "BRONZE"

    # Partition information
    partition_info = df["ParentPath"].apply(
        extract_partition_info
    )

    df["PartitionColumn"] = partition_info.apply(
        lambda x: x[0]
    )

    df["PartitionName"] = partition_info.apply(
        lambda x: x[1]
    )

    df["PartitionPattern"] = partition_info.apply(
        lambda x: x[2]
    )

    df["HasHourlyPartition"] = partition_info.apply(
        lambda x: x[3]
    )

    df["HourlyPartitionName"] = partition_info.apply(
        lambda x: x[4]
    )

    df["IsPartitioned"] = df["PartitionColumn"].notna()

    # IMPORTANT:
    # ModificationDate / ModificationTime come directly
    # from filesystem metadata.
    #
    # We DO NOT replace ModificationDate with partition date here.

    df["ModificationDate"] = df["ModificationDate"].replace(
        {"": pd.NA}
    )

    df["ModificationTime"] = df["ModificationTime"].replace(
        {"": pd.NA}
    )

    date_series = pd.to_datetime(
        df["ModificationDate"],
        errors="coerce"
    )

    # IMPORTANT:
    # Use nullable Int64 to prevent values such as 2026.0

    df["Year"] = date_series.dt.year.astype("Int64")
    df["Month"] = date_series.dt.month.astype("Int64")
    df["Day"] = date_series.dt.day.astype("Int64")

    df["YearMonth"] = date_series.dt.strftime("%Y-%m")

    df.loc[
        date_series.isna(),
        "YearMonth"
    ] = pd.NA

    time_series = pd.to_datetime(
        df["ModificationTime"],
        format="%H:%M:%S",
        errors="coerce"
    )

    df["Hour"] = time_series.dt.hour.astype("Int64")

    # Modification timestamp
    df["ModificationTimestamp"] = pd.NA

    valid_timestamp = (
        date_series.notna()
        & time_series.notna()
    )

    df.loc[valid_timestamp, "ModificationTimestamp"] = (
        date_series[valid_timestamp].dt.strftime("%Y-%m-%d")
        + " "
        + time_series[valid_timestamp].dt.strftime("%H:%M:%S")
    )

    # Final column order
    columns = [
        "Source",
        "Zone",
        "TableName",
        "LogicalTableName",
        "FileName",
        "FileFormat",
        "TotalSizeBytes",
        "FileCount",
        "IsPartitioned",
        "PartitionColumn",
        "PartitionName",
        "PartitionPattern",
        "HasHourlyPartition",
        "HourlyPartitionName",
        "ModificationTimestamp",
        "ModificationDate",
        "ModificationTime",
        "Year",
        "Month",
        "Day",
        "YearMonth",
        "Hour",
        "ParentPath",
        "FullPath",
        "Type"
    ]

    df = df[columns]

    df.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8"
    )

    print("Metadata cleaning completed.")
    print(f"Input : {INPUT}")
    print(f"Output: {OUTPUT}")
    print(f"Rows  : {len(df):,}")


if __name__ == "__main__":
    clean_metadata()
