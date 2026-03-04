import os
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import json

def main():
    # 1. Authenticate to BigQuery
    gcp_credentials_json = os.environ.get("GCP_SA_KEY")
    if not gcp_credentials_json:
        print("Missing GCP_SA_KEY environment variable")
        exit(1)
        
    credentials = service_account.Credentials.from_service_account_info(json.loads(gcp_credentials_json))
    client = bigquery.Client(project=credentials.project_id, credentials=credentials)
    
    # Yesterday's date for the partition
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    yesterday_str = yesterday.isoformat()
    yesterday_timestamp = yesterday_str + " 00:00:00 UTC" # Start of day

    print(f"Querying PyPI downloads for {yesterday_str}...")

    # Set up the query to aggregate downloads for our packages
    query = f"""
    SELECT
      TIMESTAMP("{yesterday_timestamp}") as timestamp,
      file.project as project,
      file.version as version,
      country_code,
      details.installer.name as installer_name,
      details.installer.version as installer_version,
      details.system.name as system,
      COUNT(*) as download_count
    FROM
      `bigquery-public-data.pypi.file_downloads`
    WHERE
      DATE(timestamp) = "{yesterday_str}"
      AND file.project IN ('odgs', 'odgs-protocol', 'odgs-engine')
    GROUP BY
      timestamp, project, version, country_code, installer_name, installer_version, system
    """

    # Run the query. It will scan only yesterday's partition for the requested packages.
    query_job = client.query(query)
    results = query_job.result()
    
    rows_to_insert = []
    for row in results:
        rows_to_insert.append({
            "timestamp": row["timestamp"].isoformat(),
            "project": row["project"],
            "version": row["version"],
            "country_code": row["country_code"],
            "installer_name": row["installer_name"],
            "installer_version": row["installer_version"],
            "system": row["system"],
            "download_count": row["download_count"]
        })

    if not rows_to_insert:
        print("No downloads found for the specified packages yesterday.")
        return

    print(f"Found {len(rows_to_insert)} aggregated rows. Inserting into github_telemetry.pypi_downloads...")

    # Insert into our private telemetry table
    table_id = f"{credentials.project_id}.github_telemetry.pypi_downloads"
    errors = client.insert_rows_json(table_id, rows_to_insert)
    
    if errors == []:
        print("Successfully inserted PyPI download data into BigQuery.")
    else:
        print("Encountered errors while inserting PyPI data:", errors)

if __name__ == "__main__":
    main()
