# Databricks notebook source
# MAGIC %md
# MAGIC # shared_helper
# MAGIC
# MAGIC Reusable notebook helper synced into every bundle deploy.
# MAGIC Use `%run ../../../shared/notebooks/shared_helper` from a bundle notebook
# MAGIC to pull in shared setup logic.

# COMMAND ----------

def log_run(spark, catalog, schema, table, workspace_label, bundle):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
    spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table} (
      workspace_label STRING, bundle STRING, run_at TIMESTAMP
    )
    """)
    spark.sql(
        f"INSERT INTO {catalog}.{schema}.{table} VALUES "
        f"('{workspace_label}', '{bundle}', current_timestamp())"
    )
