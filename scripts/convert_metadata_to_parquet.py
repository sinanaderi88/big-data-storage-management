import pandas as pd

INPUT_FILE = "/home/sina/bigdata-lab/storage_lab/metadata/metadata_clean.csv"
OUTPUT_FILE = "/home/sina/bigdata-lab/storage_lab/metadata/metadata_clean.parquet"


def convert_to_parquet():
    df = pd.read_csv(INPUT_FILE)

    df.to_parquet(
        OUTPUT_FILE,
        engine="pyarrow",
        index=False
    )

    print(f"Parquet created: {OUTPUT_FILE}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")


if __name__ == "__main__":
    convert_to_parquet()
