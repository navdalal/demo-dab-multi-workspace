# Databricks notebook source
# MAGIC %md
# MAGIC # elt_job
# MAGIC
# MAGIC Deployed only to ELT via the `elt_only` bundle.
# MAGIC Represents ELT-specific work (e.g. bronze→silver curation, vendor extracts).

# COMMAND ----------

dbutils.widgets.text("workspace_label", "elt")
dbutils.widgets.text("catalog", "dab_demo")
dbutils.widgets.text("schema", "dab_demo_elt")
dbutils.widgets.text("shared_path", "")
dbutils.widgets.text("pipeline_stage", "elt")

workspace_label = dbutils.widgets.get("workspace_label")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
shared_path = dbutils.widgets.get("shared_path")
pipeline_stage = dbutils.widgets.get("pipeline_stage")

# COMMAND ----------

import sys

if shared_path and shared_path not in sys.path:
    sys.path.insert(0, shared_path)

from common_utils import greet, fqn, SHARED_VERSION

print(greet(workspace_label))
print(f"pipeline_stage={pipeline_stage}, shared_utils v{SHARED_VERSION}")

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
table = fqn(catalog, schema, "elt_only_runs")
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {table} (
  workspace_label STRING,
  pipeline_stage STRING,
  bundle STRING,
  run_at TIMESTAMP
)
""")
spark.sql(
    f"INSERT INTO {table} VALUES "
    f"('{workspace_label}', '{pipeline_stage}', 'elt_only', current_timestamp())"
)
display(spark.sql(f"SELECT * FROM {table} ORDER BY run_at DESC LIMIT 5"))
