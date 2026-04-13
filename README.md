# Tayara ETL Pipeline with Intelligent Agent

A sophisticated ETL pipeline for Tayara.tn real estate data with intelligent validation, decision-making, and reporting.

## Architecture

```
tayara-etl-agent/
├── docker-compose.yaml          # Docker services orchestration
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── airflow/
│   ├── Dockerfile               # Airflow image
│   └── dags/
│       └── tayara_etl_dag.py     # Airflow DAG definition
├── spark/
│   ├── Dockerfile               # Spark image
│   ├── jobs/
│   │   └── tayara_etl.py         # Spark data processing job
│   └── data/
│       └── TayaraDataDetailed.json   # Input dataset
├── scraper/
│   ├── scrape_tayara.py          # Web scraper for Tayara.tn
│   └── raw/                      # Raw scraped data storage
├── agent/
│   ├── run_agent.py              # Main agent orchestrator
│   ├── validator.py              # Data quality validator
│   ├── decision_engine.py         # Intelligent decision maker
│   └── reporter.py               # Report generator
└── reports/                      # Generated reports directory
```

## Components

### 1. **Scraper** (`scraper/scrape_tayara.py`)
- Scrapes real estate listings from Tayara.tn
- Saves raw data to JSON files
- Configurable page limits and retry logic

### 2. **Agent** (`agent/`)
- **run_agent.py**: Main orchestrator that coordinates the entire pipeline
- **validator.py**: Validates data quality, completeness, and integrity
- **decision_engine.py**: Makes intelligent decisions (proceed, skip, retry, alert)
- **reporter.py**: Generates JSON and HTML execution reports

### 3. **Spark ETL** (`spark/jobs/tayara_etl.py`)
- Cleans and transforms raw data
- Removes duplicates and handles missing values
- Calculates derived metrics (price_per_m2)
- Writes cleaned data to PostgreSQL

### 4. **Airflow** (`airflow/dags/tayara_etl_dag.py`)
- Orchestrates the pipeline as a scheduled DAG
- Integrates with the agent for decision-making
- Monitors task execution and status

## Services

- **PostgreSQL 15**: Data warehouse (port 5432)
- **Apache Airflow 3.1.0**: Workflow orchestration (port 8081)
- **Apache Spark 3.5.8**: Distributed data processing

## Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.8+ (for local agent testing)

### Setup

1. Clone the repository:
```bash
cd tayara-etl-agent
```

2. Install Python dependencies (optional, for local testing):
```bash
pip install -r requirements.txt
```

3. Start services:
```bash
docker compose up -d
```

4. Wait for Airflow to initialize (~30 seconds):
```bash
docker logs etl-airflow-1 | grep "Airflow is ready"
```

## Usage

### Option 1: Run via Airflow UI

1. Access Airflow at `http://localhost:8081`
2. Login with default credentials: `admin` / `admin`
3. Find `tayara_etl_pipeline` DAG
4. Click **Trigger DAG**
5. Monitor task execution in the UI

### Option 2: Run Agent Directly

```bash
# Inside the container
docker exec -it etl-airflow-1 bash
cd /opt/airflow
python -m agent.run_agent

# Or with scraper first
python scraper/scrape_tayara.py
python -m agent.run_agent
```

### Option 3: Run Spark Job Directly

```bash
docker exec spark-etl python /opt/spark_app/jobs/tayara_etl.py
```

## Data Flow

```
Raw Data (JSON)
    ↓
Scraper (optional source)
    ↓
Agent Validator
    ↓
Decision Engine
    ├─→ PROCEED → Spark ETL Job
    ├─→ RETRY → Retry with backoff
    ├─→ SKIP → Skip processing
    └─→ ALERT → Manual intervention needed
    ↓
Spark Job
    ↓
Clean Data Transformation
    ↓
PostgreSQL Storage
    ├─→ clean_tayara (cleaned records)
    └─→ agg_price_by_location (aggregated statistics)
    ↓
Reporter
    ├─→ JSON Report
    └─→ HTML Report
```

## Database Tables

### clean_tayara
Cleaned and deduplicated real estate listings
- **Fields**: id, title, location, transaction_type, price_num, superficie_num, price_per_m2, etc.
- **Records**: ~10,000

### agg_price_by_location
Aggregated market statistics grouped by location and transaction type
- **Fields**: location, transaction_type, avg_price, avg_superficie, avg_price_per_m2
- **Records**: By unique location/transaction combinations

## Configuration

### Agent Thresholds (`agent/decision_engine.py`)
```python
thresholds = {
    'min_data_count': 100,        # Minimum records required
    'min_completeness': 0.8,      # 80% field completeness
    'max_duplicates': 10,         # Max allowed duplicates
    'max_retry_count': 3          # Max retry attempts
}
```

### PostgreSQL Connection
- **Host**: `postgres` (Docker) or `localhost` (local)
- **Port**: 5432
- **User**: airflow
- **Password**: airflow
- **Database**: airflow

## Monitoring & Reporting

### View Execution Reports
```bash
# List all reports
ls -la reports/

# View JSON report
cat reports/execution_report_*.json

# Open HTML report in browser
open reports/execution_report_*.html
```

### Check Data in PostgreSQL
```bash
# Connect to PostgreSQL
docker exec -it etl-postgres-1 psql -U airflow -d airflow

# Query clean data
SELECT COUNT(*) FROM clean_tayara;
SELECT * FROM clean_tayara LIMIT 10;

# Query aggregated data
SELECT * FROM agg_price_by_location;
```

## Development

### Adding Custom Validation Rules

Edit `agent/validator.py`:
```python
def validate_custom_field(self, data):
    # Add your validation logic
    pass
```

### Adding Decision Rules

Edit `agent/decision_engine.py`:
```python
def make_decision(self, validation_report, retry_count=0):
    # Add your decision logic
    pass
```

### Customizing Reports

Edit `agent/reporter.py`:
```python
def _generate_html(self, report):
    # Customize HTML template
    pass
```

## Troubleshooting

### Pipeline not starting
```bash
# Check Airflow logs
docker logs etl-airflow-1

# Check Spark logs
docker logs spark-etl
```

### Data not in database
```bash
# Verify PostgreSQL connection
docker exec etl-postgres-1 psql -U airflow -d airflow -c "SELECT 1"

# Check tables exist
docker exec etl-postgres-1 psql -U airflow -d airflow -c "\dt"
```

### Out of memory errors
Increase Docker memory limits in `docker-compose.yaml`:
```yaml
services:
  spark:
    environment:
      SPARK_DRIVER_MEMORY: 2g
      SPARK_EXECUTOR_MEMORY: 2g
```

## Performance

- **Data Processing**: ~36 seconds for 10,000 records
- **Scraping**: Configurable (depends on page count and internet speed)
- **Validation**: <1 second
- **Decision Making**: <1 second
- **Reporting**: <2 seconds

## License

MIT License

## Support

For issues or questions, check the logs or review the agent's decision reports in the `reports/` directory.
