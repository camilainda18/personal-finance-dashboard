import pandas as pd
import sqlite3
from pathlib import Path

DB_NAME = "finance.db"
DATA_DIR = Path("Monthly Data")

EXPECTED_COLUMNS = [
    "transaction_id",
    "date",
    "account_name",
    "category_name",
    "type",
    "amount",
    "description"
]

def main():
    csv_files = list(DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError("No CSV files found in the /data folder")

    df_list = []

    for file in csv_files:
        print(f"Loading {file.name}...")
        temp = pd.read_csv(file)

            # Handle case where all data is in a single column
        if len(temp.columns) == 1:
            temp = temp[temp.columns[0]].str.split(",", expand=True)
            temp.columns = EXPECTED_COLUMNS

        if list(temp.columns) != EXPECTED_COLUMNS:
            raise ValueError(f"Column mismatch in {file.name}")

        df_list.append(temp)

    # Combine all months
    df = pd.concat(df_list, ignore_index=True)

    # Clean data
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    for col in ["account_name", "category_name", "type", "description"]:
        df[col] = df[col].astype(str).str.strip()

    # Build normalized tables
    accounts = df[["account_name"]].drop_duplicates().reset_index(drop=True)
    accounts["account_id"] = accounts.index + 1

    categories = df[["category_name"]].drop_duplicates().reset_index(drop=True)
    categories["category_id"] = categories.index + 1

    df = df.merge(accounts, on="account_name")
    df = df.merge(categories, on="category_name")

    transactions = df[
        [
            "transaction_id",
            "date",
            "type",
            "amount",
            "description",
            "account_id",
            "category_id",
        ]
    ]

    conn = sqlite3.connect(DB_NAME)

    accounts.to_sql("Accounts", conn, if_exists="replace", index=False)
    categories.to_sql("Categories", conn, if_exists="replace", index=False)
    transactions.to_sql("Transactions", conn, if_exists="replace", index=False)

    conn.close()

    print("Multi month database built from CSV files")

if __name__ == "__main__":
    main()
