from pathlib import Path
from datetime import date, timedelta

ROOT = Path("/home/sina/bigdata-lab/storage_lab/bronze")

sources = {
    "source_01": ["customer_profile", "customer_events", "customer_history", "customer_scores", "customer_activity"],
    "source_02": ["billing_transaction", "billing_summary", "invoice_detail", "payment_history", "payment_events"],
    "source_03": ["network_usage", "network_events", "network_sessions", "network_summary", "network_quality"],
    "source_04": ["sales_order", "sales_detail", "sales_summary", "product_sales", "sales_events"],
    "source_05": ["inventory_item", "inventory_movement", "inventory_snapshot", "warehouse_activity", "stock_history"],
    "source_06": ["application_event", "application_log", "application_session", "application_usage", "application_summary"],
    "source_07": ["marketing_event", "campaign_activity", "campaign_response", "customer_segment", "marketing_summary"],
    "source_08": ["service_event", "service_request", "service_history", "service_usage", "service_summary"],
    "source_09": ["analytics_event", "analytics_daily", "analytics_summary", "metric_history", "metric_snapshot"],
    "source_10": ["operations_event", "operations_log", "operations_daily", "operations_summary", "operations_history"],
}

daily_tables = {
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

hourly_tables = {
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

start_date = date(2024, 1, 1)
end_date = date(2026, 9, 30)

current = start_date

while current <= end_date:

    date_value = current.isoformat()

    for source, tables in sources.items():

        for table in tables:

            table_path = ROOT / source / table

            if table in hourly_tables:

                for hour in range(24):
                    partition = (
                        table_path
                        / f"event_date={date_value}"
                        / f"hour={hour:02d}"
                    )
                    partition.mkdir(parents=True, exist_ok=True)

            elif table in daily_tables:

                partition = (
                    table_path
                    / f"event_date={date_value}"
                )
                partition.mkdir(parents=True, exist_ok=True)

            else:
                table_path.mkdir(parents=True, exist_ok=True)

    current += timedelta(days=1)

print("Directory structure created successfully.")
