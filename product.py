"""
product.py
----------
Defines the Product class: one single product, and everything it
knows about its own risk of becoming waste.
"""

from datetime import datetime


class Product:
    def __init__(self, product_id, product_name, category,
                 stock_quantity, units_sold_last_30_days,
                 expiry_date, cost_per_unit):
        self.product_id = product_id
        self.product_name = product_name
        self.category = category
        self.stock_quantity = int(stock_quantity)
        self.units_sold_last_30_days = int(units_sold_last_30_days)
        self.expiry_date = expiry_date if isinstance(expiry_date, datetime) \
            else datetime.strptime(expiry_date, "%Y-%m-%d")
        self.cost_per_unit = float(cost_per_unit)

        # Set later by the forecaster (Day 4/5). Falls back to the
        # simple historical average until a forecast is applied.
        self.predicted_daily_demand = None

    def historical_daily_rate(self):
        return self.units_sold_last_30_days / 30

    def effective_daily_demand(self):
        """Use the ML-predicted demand if available, otherwise fall
        back to the plain historical average."""
        if self.predicted_daily_demand is not None:
            return self.predicted_daily_demand
        return self.historical_daily_rate()

    def stock_to_sales_ratio(self):
        if self.units_sold_last_30_days > 0:
            return self.stock_quantity / self.units_sold_last_30_days
        return float("inf")

    def is_slow_mover(self, threshold=1.5):
        return self.stock_to_sales_ratio() > threshold

    def days_until_expiry(self, today=None):
        today = today or datetime.now()
        return (self.expiry_date - today).days

    def is_near_expiry(self, warning_days=7, today=None):
        days_left = self.days_until_expiry(today)
        return 0 <= days_left <= warning_days

    def days_of_stock_remaining(self):
        rate = self.effective_daily_demand()
        if rate > 0:
            return round(self.stock_quantity / rate, 1)
        return float("inf")

    def potential_waste_cost(self):
        return self.stock_quantity * self.cost_per_unit

    def priority_score(self, today=None):
        score = 0
        reasons = []

        if self.is_slow_mover():
            score += 40
            reasons.append("slow-moving")

        if self.is_near_expiry(today=today):
            days_left = self.days_until_expiry(today)
            score += (7 - days_left) * 10 + 10
            reasons.append(f"expires in {days_left}d")

        # New signal enabled by forecasting: if demand is predicted
        # to rise sharply, low stock becomes urgent for a DIFFERENT
        # reason (stockout risk, not waste risk).
        if self.predicted_daily_demand is not None:
            if self.predicted_daily_demand > self.historical_daily_rate() * 1.3:
                if self.days_of_stock_remaining() < 14:
                    score += 25
                    reasons.append("demand rising, stock may run out")

        return score, ", ".join(reasons)

    def __repr__(self):
        return f"Product({self.product_name!r}, stock={self.stock_quantity})"
