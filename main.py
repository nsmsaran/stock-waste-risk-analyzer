"""
main.py
-------
The full pipeline, start to finish:
  1. Load inventory data
  2. Load sales history and forecast future demand (ML)
  3. Apply forecasts onto the inventory
  4. Generate the final, ranked priority report
  5. Export it as a CSV deliverable

Run this one file to see the entire project work end to end.
"""

from inventory import Inventory
from forecast import DemandForecaster

INVENTORY_FILE = "inventory_data.csv"
SALES_HISTORY_FILE = "sales_history.csv"
FINAL_REPORT_FILE = "final_priority_report.csv"


def main():
    print("Loading inventory...")
    inventory = Inventory.load_from_csv(INVENTORY_FILE)
    print(f"  {len(inventory.products)} products loaded.\n")

    print("Training demand forecast models...")
    forecaster = DemandForecaster.load_history_csv(SALES_HISTORY_FILE, forecast_days=7)
    predicted_averages, trends = forecaster.forecast_all()
    inventory.apply_forecast(predicted_averages)
    print(f"  Forecasts generated for {len(predicted_averages)} products.\n")

    print("=" * 75)
    print("FINAL PRIORITY ACTION LIST (highest risk first)")
    print("=" * 75)
    report = inventory.priority_report()
    for row in report:
        trend = trends.get(row["product_id"], "n/a")
        print(f"[{row['priority_score']:>3}] {row['product_name']:<22} "
              f"stock:{row['stock_quantity']:<5} "
              f"days_left:{row['days_of_stock_remaining']:<6} "
              f"trend:{trend:<10} | {row['reason']}")

    total_loss = inventory.total_potential_waste_cost()
    print(f"\nTotal potential waste cost (near-expiry stock): Rs {total_loss:,.2f}")

    inventory.export_report(FINAL_REPORT_FILE)


if __name__ == "__main__":
    main()
