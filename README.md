# Crypto Prices Pipeline

A micro-batch data pipeline on Google Cloud that pulls cryptocurrency prices from the CoinGecko API every 15 minutes, stores the raw data, and prepares analytics-ready tables in BigQuery for dashboarding.

> **Note:** Infrastructure is provisioned with Terraform and kept in a private repository. Available on request.

## Architecture

```
Cloud Scheduler (every 15 min)
        |
        v
Cloud Run Job (Python ingestion container)
        |
        |--> CoinGecko API  (fetch prices)
        |
        v
Cloud Storage (raw JSON)
        |
        v
BigQuery
  |-- raw        (landed data)
  |-- analytics  (cleaned, query-ready tables)
        |
        v
Looker Studio dashboard (planned)
```

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python |
| Packaging | Docker, Artifact Registry |
| Compute | Cloud Run Jobs |
| Orchestration | Cloud Scheduler |
| Raw storage | Google Cloud Storage |
| Warehouse | BigQuery |
| Infrastructure as Code | Terraform (private repo) |
| Visualization | Looker Studio (planned) |

## Project Structure

```
crypto-prices-pipeline/
|-- main.py             # Ingestion logic
|-- Dockerfile          # Container image for Cloud Run
|-- requirements.txt    # Python dependencies
|-- LICENSE
|-- README.md
```

## How It Works

1. **Cloud Scheduler** triggers the Cloud Run job every 15 minutes.
2. **`main.py`** calls the CoinGecko API for the configured coins (currently 3) and receives current price data.
3. The raw response is written to a **GCS bucket**, so the original data is always kept.
4. Data is loaded into the BigQuery **`raw`** dataset, then shaped into the **`analytics`** dataset for reporting.

## Design Decisions

- **Micro-batch over true streaming.** Prices only change meaningfully every few minutes, and the CoinGecko API is request-based, so a 15-minute schedule gives near-real-time freshness at a fraction of the cost of Kafka or Pub/Sub.
- **Cloud Run Jobs over a VM.** The job runs for seconds and then stops, so you pay only for execution time. No server to patch or keep running.
- **Raw layer in GCS.** Keeping the untouched API response allows reprocessing if transformation logic changes.
- **Separate `raw` and `analytics` datasets.** Clear boundary between landed data and business-ready data.
- **Terraform for everything.** The environment can be rebuilt reproducibly, with no manual console clicks.
- **Kept MVP-minimal.** No dbt or heavy orchestration for now. Added only when complexity justifies it.

## Configuration

| Variable | Description | Default |
|---|---|---|
| `COIN_COUNT` | Number of coins to fetch | `3` |

Credentials are never stored in this repository. The job authenticates through a service account attached to the Cloud Run job.

## Running Locally

```bash
pip install -r requirements.txt
python main.py
```

Or with Docker:

```bash
docker build -t crypto-prices-pipeline .
docker run crypto-prices-pipeline
```

## Roadmap

- [ ] Looker Studio dashboard on the `analytics` dataset
- [ ] Data quality checks
- [ ] Alerting on failed runs
- [ ] Expand the list of tracked coins

## License

All rights reserved. This code is public for viewing and evaluation only.

## Author

**Zaw Myo Htet**, Data Engineer
