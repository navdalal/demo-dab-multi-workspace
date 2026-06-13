# Databricks notebook source
# MAGIC %md
# MAGIC # common_job
# MAGIC
# MAGIC Deployed everywhere via the `common_jobs` bundle (UAT, US1, ELT).
# MAGIC Demonstrates shared-code propagation + per-workspace parameterization.

# COMMAND ----------

dbutils.widgets.text("workspace_label", "unknown")
dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "dab_demo")
dbutils.widgets.text("shared_path", "")

workspace_label = dbutils.widgets.get("workspace_label")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
shared_path = dbutils.widgets.get("shared_path")

# COMMAND ----------

import sys

if shared_path and shared_path not in sys.path:
    sys.path.insert(0, shared_path)

from common_utils import greet, fqn, SHARED_VERSION

print(greet(workspace_label))
print(f"shared_utils version = {SHARED_VERSION}")

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
table = fqn(catalog, schema, "common_runs")
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {table} (
  workspace_label STRING,
  shared_version STRING,
  bundle STRING,
  run_at TIMESTAMP
)
""")
spark.sql(
    f"INSERT INTO {table} VALUES "
    f"('{workspace_label}', '{SHARED_VERSION}', 'common_jobs', current_timestamp())"
)
display(spark.sql(f"SELECT * FROM {table} ORDER BY run_at DESC LIMIT 5"))
