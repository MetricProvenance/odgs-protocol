import os
import requests
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import json

def get_github_data(endpoint, token, repo="MetricProvenance/odgs-protocol"):
    url = f"https://api.github.com/repos/{repo}/traffic/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    github_token = os.environ.get("GH_PAT")
    if not github_token:
        print("Missing GH_PAT environment variable")
        exit(1)
        
    repo_name = "MetricProvenance/odgs-protocol"
    
    # 1. Fetch GitHub Data
    print(f"Fetching traffic data for {repo_name}...")
    views_data = get_github_data("views", github_token, repo_name)
    clones_data = get_github_data("clones", github_token, repo_name)
    referrers_data = get_github_data("popular/referrers", github_token, repo_name)
    
    # We only care about the total counts for the current pipeline run to log "today's" snapshot,
    # or we can take the last 14 days and use `bq append` but BigQuery might get duplicates.
    # To avoid duplicates, we will just insert a single row representing the total cumulative past 14 days 
    # OR we can insert yesterday's single day metric by finding it in the array.
    
    # Better approach: find the data for "yesterday" (UTC) in the `views` and `clones` arrays
    yesterday_str = (datetime.utcnow().date() - datetime.timedelta(days=1)).isoformat() + "T00:00:00Z"
    
    view_stats = next((v for v in views_data.get('views', []) if v['timestamp'] == yesterday_str), {"count": 0, "uniques": 0})
    clone_stats = next((c for c in clones_data.get('clones', []) if c['timestamp'] == yesterday_str), {"count": 0, "uniques": 0})
    
    print(f"Yesterday ({yesterday_str.split('T')[0]}) Views: {view_stats['count']} | Clones: {clone_stats['count']}")

    # 2. Authenticate to BigQuery
    gcp_credentials_json = os.environ.get("GCP_SA_KEY")
    if not gcp_credentials_json:
        print("Missing GCP_SA_KEY environment variable")
        exit(1)
        
    credentials = service_account.Credentials.from_service_account_info(json.loads(gcp_credentials_json))
    client = bigquery.Client(project=credentials.project_id, credentials=credentials)
    
    # 3. Insert Traffic Data
    traffic_table_id = f"{credentials.project_id}.github_telemetry.repository_traffic"
    traffic_rows = [
        {
            "timestamp": yesterday_str,
            "repository": repo_name,
            "views_count": view_stats['count'],
            "views_uniques": view_stats['uniques'],
            "clones_count": clone_stats['count'],
            "clones_uniques": clone_stats['uniques']
        }
    ]
    
    errors = client.insert_rows_json(traffic_table_id, traffic_rows)
    if errors == []:
        print("Successfully inserted traffic data into BigQuery.")
    else:
        print("Encountered errors while inserting traffic data:", errors)
        
    # 4. Insert Referrer Data
    referrer_table_id = f"{credentials.project_id}.github_telemetry.repository_referrers"
    referrer_rows = []
    
    # GitHub referrer data doesn't have timestamps, it's just a 14-day rolling window.
    # We will log the snapshot today.
    today_str = datetime.utcnow().isoformat()
    for ref in referrers_data:
        referrer_rows.append({
            "timestamp": today_str,
            "repository": repo_name,
            "referrer": ref['referrer'],
            "count": ref['count'],
            "uniques": ref['uniques']
        })
        
    if referrer_rows:
        errors = client.insert_rows_json(referrer_table_id, referrer_rows)
        if errors == []:
            print("Successfully inserted referrer data into BigQuery.")
        else:
            print("Encountered errors while inserting referrer data:", errors)
    else:
        print("No referrers found.")

if __name__ == "__main__":
    import datetime # Need to import datetime module itself for timedelta
    main()
