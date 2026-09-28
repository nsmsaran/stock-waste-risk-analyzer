"""
forecast.py
-----------
Defines DemandForecaster: trains a simple Linear Regression model
per product on historical daily sales, and predicts near-future
demand.
"""

import csv
from collections import defaultdict
import numpy as np
from sklearn.linear_model import LinearRegression


class DemandForecaster:
    def __init__(self, forecast_days=7):
        self.forecast_days = forecast_days
        self.history = {}   # { product_id: [units_day0, units_day1, ...] }

    @classmethod
    def load_history_csv(cls, filepath, forecast_days=7):
        forecaster = cls(forecast_days=forecast_days)
        history = defaultdict(list)
        with open(filepath, newline="") as f:
            reader = csv.DictReader(f)
            rows = sorted(reader, key=lambda r: r["date"])
            for row in rows:
                history[row["product_id"]].append(int(row["units_sold"]))
        forecaster.history = dict(history)
        return forecaster

    def forecast_one(self, daily_sales):
        num_days = len(daily_sales)
        X = np.array(range(num_days)).reshape(-1, 1)
        y = np.array(daily_sales)

        model = LinearRegression()
        model.fit(X, y)

        future_days = np.array(
            range(num_days, num_days + self.forecast_days)
        ).reshape(-1, 1)
        predictions = model.predict(future_days)
        predictions = [max(0, round(p, 1)) for p in predictions]

        slope = model.coef_[0]
        if slope > 0.05:
            trend = "rising"
        elif slope < -0.05:
            trend = "declining"
        else:
            trend = "stable"

        predicted_avg = round(sum(predictions) / len(predictions), 1)
        return predicted_avg, trend

    def forecast_all(self):
        """Returns { product_id: predicted_daily_avg } for every
        product in the loaded history, plus a trend lookup."""
        predicted_averages = {}
        trends = {}
        for product_id, daily_sales in self.history.items():
            avg, trend = self.forecast_one(daily_sales)
            predicted_averages[product_id] = avg
            trends[product_id] = trend
        return predicted_averages, trends
