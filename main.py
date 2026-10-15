import os
import json
from datetime import datetime
import pytz
import requests
import pandas as pd
from google.cloud import storage, bigquery

# Environment Variables (Terraform ကတဆင့် ဝင်လာမည့် တန်ဖိုးများ)
PROJECT_ID = os.environ.get("PROJECT_ID", "crypto-price-live-dashboard")
BUCKET_NAME = f"{PROJECT_ID}-crypto-raw"
DATASET_ID = "raw"  # Terraform မှာ သတ်မှတ်ထားသည့် dataset_id "raw"
TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.coin_markets_raw"

yangon_tz = pytz.timezone("Asia/Yangon")

# CoinGecko API URLs (USD ဖြင့် Market Data ဆွဲရန် နှင့် USD/THB ဈေးနှုန်းများအတွက်)
url_market = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=3&page=1&sparkline=false"
url_prices = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether&vs_currencies=usd,thb"

def fetch_and_save_crypto():
    now = datetime.now(yangon_tz)
    snapshot_at = now.strftime("%Y-%m-%d %H:%M:%S")
    ingested_at = snapshot_at
    file_timestamp = now.strftime("%Y%m%d_%H%M%S")

    print(f"Fetching crypto data at {snapshot_at} (Yangon Time)...")

    # API နှစ်ခုစလုံးကို ခေါ်ယူခြင်း
    res_market = requests.get(url_market)
    res_prices = requests.get(url_prices)

    if res_market.status_code != 200 or res_prices.status_code != 200:
        print(f"Error fetching data from API. Market status: {res_market.status_code}, Prices status: {res_prices.status_code}")
        return

    coins_market = res_market.json()
    prices_data = res_prices.json()
    
    records = []

    for coin in coins_market:
        coin_id = coin.get("id")
        coin_prices = prices_data.get(coin_id, {})

        record = {
            "snapshot_at": snapshot_at,
            "ingested_at": ingested_at,
            "coin_id": coin_id,
            "symbol": coin.get("symbol"),
            "name": coin.get("name"),
            "current_price_usd": coin_prices.get("usd"),
            "current_price_thb": coin_prices.get("thb"),
            "market_cap": coin.get("market_cap"),
            "market_cap_rank": coin.get("market_cap_rank"),
            "total_volume": coin.get("total_volume"),
            "high_24h": coin.get("high_24h"),
            "low_24h": coin.get("low_24h"),
            "price_change_percentage_24h": coin.get("price_change_percentage_24h"),
            "circulating_supply": coin.get("circulating_supply"),
            "last_updated": coin.get("last_updated")
        }
        records.append(record)

    # 1. GCS Bucket ထဲသို့ Raw JSON ဖိုင်ပုံစံဖြင့် တင်ခြင်း (Backup)
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_name = f"raw_data/{file_timestamp}.json"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(
            data=json.dumps(records),
            content_type='application/json'
        )
        print(f"Successfully uploaded raw data to GCS: gs://{BUCKET_NAME}/{blob_name}")
    except Exception as e:
        print(f"Error uploading to GCS: {e}")

    # 2. BigQuery Table (raw.coin_markets_raw) ထဲသို့ ဒေတာထည့်သွင်းခြင်း
    try:
        bq_client = bigquery.Client()
        df = pd.DataFrame(records)
        
        # Timestamp field များကို Pandas datetime သို့ ပြောင်းရန်
        df["snapshot_at"] = pd.to_datetime(df["snapshot_at"])
        df["ingested_at"] = pd.to_datetime(df["ingested_at"])
        if "last_updated" in df.columns:
            df["last_updated"] = pd.to_datetime(df["last_updated"])

        job = bq_client.load_table_from_dataframe(df, TABLE_ID)
        job.result()  # ပြီးဆုံးသည်အထိ စောင့်ရန်
        print(f"Successfully inserted {len(records)} rows into BigQuery table: {TABLE_ID}")
    except Exception as e:
        print(f"Error inserting data into BigQuery: {e}")

if __name__ == "__main__":
    fetch_and_save_crypto()