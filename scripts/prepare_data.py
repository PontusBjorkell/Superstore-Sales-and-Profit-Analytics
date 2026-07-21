"""Prepare the Superstore analytical dataset."""

from __future__ import annotations

from superstore_analytics.config import (
    DATA_QUALITY_REPORT_PATH,
    PROCESSED_DATA_PATH,
    RAW_DATA_PATH,
    create_output_directories,
)
from superstore_analytics.data import (
    clean_superstore_data,
    create_data_quality_summary,
    load_raw_data,
    save_processed_data,
)


def main() -> None:
    """Run the complete data preparation workflow."""

    create_output_directories()

    print("=" * 72)
    print("SUPERSTORE DATA PREPARATION")
    print("=" * 72)

    print(f"\nLoading raw data from:\n{RAW_DATA_PATH}")
    raw_df = load_raw_data(RAW_DATA_PATH)

    print(f"Raw shape: {raw_df.shape[0]:,} rows × {raw_df.shape[1]} columns")

    print("\nValidating, cleaning, and engineering analytical features...")
    clean_df = clean_superstore_data(raw_df)

    save_processed_data(clean_df, PROCESSED_DATA_PATH)

    quality_summary = create_data_quality_summary(raw_df, clean_df)
    DATA_QUALITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    quality_summary.to_csv(DATA_QUALITY_REPORT_PATH, index=False)

    print(f"\nProcessed data saved to:\n{PROCESSED_DATA_PATH}")
    print(f"\nData-quality report saved to:\n{DATA_QUALITY_REPORT_PATH}")

    total_sales = clean_df["sales"].sum()
    total_profit = clean_df["profit"].sum()
    profit_margin = total_profit / total_sales if total_sales else 0

    print("\nPreparation summary")
    print("-" * 72)
    print(f"Rows:              {len(clean_df):,}")
    print(f"Columns:           {clean_df.shape[1]}")
    print(f"Orders:            {clean_df['order_id'].nunique():,}")
    print(f"Customers:         {clean_df['customer_id'].nunique():,}")
    print(f"Products:          {clean_df['product_id'].nunique():,}")
    print(f"Order period:      {clean_df['order_date'].min().date()} "
          f"to {clean_df['order_date'].max().date()}")
    print(f"Total sales:       ${total_sales:,.2f}")
    print(f"Total profit:      ${total_profit:,.2f}")
    print(f"Profit margin:     {profit_margin:.2%}")
    print(f"Loss-making lines: {clean_df['is_loss'].sum():,}")
    print("=" * 72)


if __name__ == "__main__":
    main()