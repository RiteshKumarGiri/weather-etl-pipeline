# Weather ETL Pipeline

A Python ETL pipeline that pulls live hourly weather forecast data from a public API, computes daily summary statistics, and loads both into PostgreSQL — using an idempotent upsert pattern so the pipeline can be safely re-run any number of times per day without creating duplicate data.

## What It Does

1. **Extract** – Calls the [Open-Meteo](https://open-meteo.com/) forecast API (no API key required) for a given latitude/longitude, requesting hourly temperature data in the local timezone.
2. **Transform**
   - Converts the raw hourly timestamps into proper `datetime` objects
   - Computes daily summary statistics: max, min, and average temperature
   - Produces two datasets: the full hourly readings, and a one-row daily summary
3. **Load** – Writes both datasets into PostgreSQL using an **upsert** pattern:
   - Checks whether data for today's date already exists
   - If it does, deletes the existing rows for that date and inserts the fresh data
   - If not, simply inserts new data
   - This makes the pipeline **idempotent** — running it multiple times in a day updates today's record rather than duplicating it

## Tech Stack

- **Python** – requests for API calls, pandas for transformation
- **PostgreSQL** – data storage (two tables: `weather_hourly`, `weather_daily`)
- **SQLAlchemy + psycopg** – database connectivity, including raw SQL for delete operations
- **python-dotenv** – secure credential management

## Project Structure

```
weather-etl-pipeline/
├── main.py            # ETL pipeline (extract, transform, load)
├── .env                # Database credentials (not committed — see setup)
├── .gitignore
└── README.md
```

## Setup & Usage

**1. Clone the repo**
```bash
git clone https://github.com/RiteshKumarGiri/weather-etl-pipeline.git
cd weather-etl-pipeline
```

**2. Install dependencies**
```bash
pip install pandas requests sqlalchemy psycopg2-binary python-dotenv
```

**3. Create a `.env` file** in the project root:
```
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sales_db
```

**4. Run the pipeline**
```bash
python main.py
```

By default it fetches weather for coordinates set in `main.py` (currently Delhi/NCR area). To use a different location, update the `extract(latitude, longitude)` call.

## Design Notes: Why Upsert Instead of Replace or Append

Two simpler approaches were considered and rejected during development:

- **`if_exists='replace'`** — wipes and reloads the whole table on every run. Simple, but destroys all historical weather data every time the pipeline runs, making it impossible to build a time series.
- **`if_exists='append'`** — keeps adding rows forever. This caused duplicate rows to pile up whenever the pipeline was re-run on the same day (e.g., for testing, or if scheduled to run more than once daily).

The **upsert** approach solves both problems: it preserves historical data across different days, while safely handling same-day re-runs by refreshing (rather than duplicating) that day's record. This mirrors how real-world scheduled data pipelines are typically designed.

## Tables

**`weather_daily`** — one row per calendar date

| Column | Type | Description |
|---|---|---|
| Date | date | The forecast date |
| max_temp | float | Highest hourly temperature that day |
| min_temp | float | Lowest hourly temperature that day |
| avg_temp | float | Average hourly temperature that day |

**`weather_hourly`** — 24 rows per calendar date

| Column | Type | Description |
|---|---|---|
| time | timestamp | Hour of the reading |
| temperature_2m | float | Temperature at 2 meters above ground (°C) |

## Possible Next Steps

- Schedule this pipeline to run automatically (e.g., via Apache Airflow) instead of manual execution
- Add more weather variables (humidity, wind speed, precipitation)
- Support multiple locations in a single run
- Add data validation/alerting if the API returns unexpected values

## Author

Built by Ritesh Kumar Giri as part of a hands-on data engineering learning path, alongside a companion [sales ETL pipeline](https://github.com/RiteshKumarGiri/sales-etl-pipeline) project.
