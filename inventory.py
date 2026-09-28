"""
inventory.py
------------
Defines the Inventory class: holds every Product, and handles
fleet-wide jobs -- loading data, ranking risk, applying forecasts,
and exporting the final report.
"""

import csv
from product import Product


class Inventory:
    def __init__(self):
        self.products = []

    @classmethod
    def load_from_csv(cls, filepath):
        inventory = cls()
        with open(filepath, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory.products.append(Product(
                    product_id=row["product_id"],
                    product_name=row["product_name"],
                    category=row["category"],
                    stock_quantity=row["stock_quantity"],
                    units_sold_last_30_days=row["units_sold_last_30_days"],
                    expiry_date=row["expiry_date"],
                    cost_per_unit=row["cost_per_unit"],
                ))
        return inventory

    def get_product(self, product_id):
        for p in self.products:
            if p.product_id == product_id:
                return p
        return None

    def apply_forecast(self, forecast_by_product_id):
        """
        forecast_by_product_id: { product_id: predicted_daily_avg }
        Pushes each ML prediction onto its matching Product.
        """
        for product_id, predicted_avg in forecast_by_product_id.items():
            product = self.get_product(product_id)
            if product:
                product.predicted_daily_demand = predicted_avg

    def slow_movers(self, threshold=1.5):
        return [p for p in self.products if p.is_slow_mover(threshold)]

    def near_expiry_items(self, warning_days=7, today=None):
        return [p for p in self.products if p.is_near_expiry(warning_days, today)]

    def total_potential_waste_cost(self, today=None):
        return sum(p.potential_waste_cost() for p in self.near_expiry_items(today=today))

    def priority_report(self, today=None):
        rows = []
        for p in self.products:
            score, reason = p.priority_score(today=today)
            if score > 0:
                rows.append({
                    "product_id": p.product_id,
                    "product_name": p.product_name,
                    "stock_quantity": p.stock_quantity,
                    "days_of_stock_remaining": p.days_of_stock_remaining(),
                    "priority_score": score,
                    "reason": reason,
                })
        rows.sort(key=lambda r: -r["priority_score"])
        return rows

    def export_report(self, filepath, today=None):
        rows = self.priority_report(today=today)
        if not rows:
            print("No priority items to export.")
            return
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"Report exported to {filepath}")
