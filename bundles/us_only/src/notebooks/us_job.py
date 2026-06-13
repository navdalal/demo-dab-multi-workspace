# Databricks notebook source
# MAGIC %md
# MAGIC # us_job
# MAGIC
# MAGIC Deployed only to US1 via the `us_only` bundle.
# MAGIC Represents US-region-specific work (e.g. CCPA reporting, US tax tables).

# COMMAND ----------

dbutils.widgets.text("workspace_label", "us1")
dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "dab_demo_us1")
dbutils.widgets.text("shared_path", "")
dbutils.widgets.text("region", "us-east-1")

workspace_label = dbutils.widgets.get("workspace_label")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
shared_path = dbutils.widgets.get("shared_path")
region = dbutils.widgets.get("region")

# COMMAND ----------

import sys

if shared_path and shared_path not in sys.path:
    sys.path.insert(0, shared_path)

from common_utils import greet, fqn, SHARED_VERSION

print(greet(workspace_label))
print(f"region={region}, shared_utils v{SHARED_VERSION}")

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
table = fqn(catalog, schema, "us_only_runs")
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {table} (
  workspace_label STRING,
  region STRING,
  bundle STRING,
  run_at TIMESTAMP
)
""")
spark.sql(
    f"INSERT INTO {table} VALUES "
    f"('{workspace_label}', '{region}', 'us_only', current_timestamp())"
)
display(spark.sql(f"SELECT * FROM {table} ORDER BY run_at DESC LIMIT 5"))
