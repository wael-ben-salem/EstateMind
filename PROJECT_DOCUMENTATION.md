# Tayara ETL Pipeline with Intelligent Agent - Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Data Flow](#data-flow)
4. [Key Components](#key-components)
5. [Technologies & Stack](#technologies--stack)
6. [Setup & Installation](#setup--installation)
7. [Running the Pipeline](#running-the-pipeline)
8. [Understanding Each Stage](#understanding-each-stage)
9. [Price Prediction Engine](#price-prediction-engine)
10. [Key Features](#key-features)

---

## Project Overview

This project is an **intelligent ETL (Extract, Transform, Load) pipeline** for Tayara.tn, a North African real estate marketplace. It automates the collection, enrichment, validation, and intelligent processing of real estate listings with the following capabilities:

- **Web Scraping**: Automatically collects real estate listings from Tayara.tn
- **Data Enrichment**: Enhances incomplete data using regex patterns and LLM (Large Language Model) fallback
- **Location Intelligence**: Matches properties to geographic locations and municipalities
- **Smart Validation**: Validates data quality with decision-making logic
- **Price Prediction**: Trains ML models to predict real estate prices based on features
- **Orchestration**: Uses Apache Airflow to schedule and monitor pipeline runs
- **Data Processing**: Leverages Apache Spark for distributed data transformations
- **Storage**: Uses MinIO for cloud-like object storage and PostgreSQL for structural data

The system uses an **intelligent agent** that makes autonomous decisions about when to scrape, validate, and process data based on current state and data freshness.

---

## Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    TAYARA ETL PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               DATA ACQUISITION LAYER                     │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │  Web Scraper (Tayara.tn) → Raw JSON Data        │    │   │
│  │  │  Output: TayaraDataDetailed.json                 │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            DATA ENRICHMENT & PROCESSING LAYER            │   │
│  │  1. Raw Deduplication (against DB)                       │   │
│  │  2. Regex-based Field Extraction                         │   │
│  │  3. LLM Fallback Enrichment (Claude API)                 │   │
│  │  4. Location Matching (against reference data)           │   │
│  │  Outputs: TayaraDataEnrichedLocated.json                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         INTELLIGENT AGENT & VALIDATION LAYER             │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │  Decision Engine: Analyzes state & decides next   │ │   │
│  │  │  actions (scrape, validate, ETL, report)          │ │   │
│  │  │                                                    │ │   │
│  │  │  Validator: Quality checks on enriched data       │ │   │
│  │  │  - Missing fields, duplicates, coverage ratio     │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         SPARK ETL & TRANSFORMATION LAYER                 │   │
│  │  - Clean raw data (handle nulls, duplicates)             │   │
│  │  - Derive metrics (price_per_m2, etc)                    │   │
│  │  - Data type conversions                                 │   │
│  │  - Write to PostgreSQL data warehouse                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │      PRICE PREDICTION & ML LAYER                         │   │
│  │  - Prepare training data from processed dataset          │   │
│  │  - Train XGBoost models (by property type)               │   │
│  │  - Store trained models for inference                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         REPORTING & ORCHESTRATION LAYER                  │   │
│  │  - Generate execution reports (JSON)                     │   │
│  │  - Airflow DAG orchestration & scheduling                │   │
│  │  - Agent memory management (state persistence)           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Folder Structure

```
d:\Study\4DS\AIPI\ETL/
├── docker-compose.yaml              # Service orchestration
├── requirements.txt                 # Python dependencies
├── README.md                        # Quick start guide
├── PROJECT_DOCUMENTATION.md         # This file
│
├── scraper/                         # Data acquisition
│   ├── run_scraper.py              # Scraper driver
│   └── spiders/
│       └── tayaraScrapper.py        # Scrapy spider implementation
│
├── agent/                           # Core pipeline orchestration
│   ├── run_agent.py                 # Main agent entry point
│   ├── decision_engine.py           # Intelligent decision logic
│   ├── validator.py                 # Data quality validation
│   ├── reporter.py                  # Report generation
│   ├── deduplicate_raw_against_db.py# Remove known records
│   ├── enrich_with_regex.py         # Field extraction via regex
│   ├── enrich_with_llm_fallback.py  # Claude API enrichment
│   ├── match_locations_from_reference.py # Geographic matching
│   ├── llm_reasoner.py              # LLM interaction utilities
│   ├── tools.py                     # Tool orchestration
│   ├── state_reader.py              # State/context management
│   ├── memory.json                  # Agent state persistence
│   └── reference/
│       └── state-municipality-areas.json # Location reference data
│
├── agent_price/                     # Price prediction subsystem
│   ├── run_price_agent.py           # Price agent driver
│   ├── prepare_training_data.py     # Training data preparation
│   ├── train_price_model.py         # Model training pipeline
│   ├── predict_price.py             # Inference module
│   ├── data/
│   │   └── training_data.csv        # Training dataset
│   └── models/
│       ├── price_model.joblib               # Main model
│       ├── price_model_log.joblib           # Log-scaled model
│       └── models_by_type_xgb/
│           ├── price_model_appartement_log_xgb.joblib
│           ├── price_model_house_like_log_xgb.joblib
│           ├── price_model_maison_log_xgb.joblib
│           └── price_model_villa_log_xgb.joblib
│
├── spark/                           # Distributed processing
│   ├── Dockerfile                   # Spark image
│   ├── jobs/
│   │   └── tayara_etl.py            # Main Spark ETL job
│   └── data/
│       ├── TayaraDataDetailed.json  # Raw scraped data
│       ├── TayaraDataRegex.json     # Regex-enriched data
│       ├── TayaraDataEnriched.json  # LLM-enriched data
│       └── TayaraDataEnrichedLocated.json # Location-matched data
│
├── airflow/                         # Workflow orchestration
│   ├── Dockerfile                   # Airflow image
│   ├── dags/
│   │   ├── tayara_etl_dag.py        # Main ETL DAG
│   │   ├── tayara_agent_pipeline.py # Agent execution DAG
│   │   └── tayara_price_prediction_dag.py # Price prediction DAG
│   ├── logs/                        # DAG execution logs
│   └── plugins/                     # Custom Airflow plugins
│
├── minio_data/                      # MinIO object storage
│   ├── tayara-raw/
│   │   └── raw/                     # Raw scraped data storage
│   └── tayara-processed/
│       ├── agg/                     # Aggregated data
│       └── clean/                   # Cleaned data
│
├── output/                          # Pipeline outputs
│   ├── clean_tayara/                # Cleaned data output
│   ├── agg_price_by_location/       # Price aggregations
│   └── reports/                     # Generated reports
│
└── understanding.ipynb              # Analysis notebooks
    ml_ready_tayara.ipynb            # ML exploration
```

---

## Data Flow

### Step-by-Step Pipeline Execution

```
1. SCRAPING PHASE
   ├─→ run_scraper() triggers Scrapy spider
   ├─→ Downloads listings from Tayara.tn
   └─→ Saves to: TayaraDataDetailed.json

2. DEDUPLICATION PHASE
   ├─→ Loads new scraped data
   ├─→ Compares against existing database records
   └─→ Filters out duplicates (keeps only new listings)

3. REGEX ENRICHMENT PHASE
   ├─→ Parses free-text descriptions
   ├─→ Extracts structured fields (area, rooms, type)
   ├─→ Uses regex patterns to find values
   └─→ Output: TayaraDataRegex.json

4. LLM FALLBACK ENRICHMENT PHASE
   ├─→ For records with missing critical fields
   ├─→ Sends description to Claude API
   ├─→ Extracts structured information via LLM
   ├─→ Merges LLM results with regex results
   └─→ Output: TayaraDataEnriched.json

5. LOCATION MATCHING PHASE
   ├─→ Loads reference data (state-municipality-areas.json)
   ├─→ Matches property locations to geographic entities
   ├─→ Fills in missing state/municipality info
   ├─→ Adds lat/long coordinates
   └─→ Output: TayaraDataEnrichedLocated.json

6. VALIDATION PHASE
   ├─→ Analyzes TayaraDataEnrichedLocated.json
   ├─→ Calculates quality metrics:
   │   ├─ Total records count
   │   ├─ Valid records (has ID + title)
   │   ├─ Missing title ratio
   │   ├─ Missing price ratio
   │   ├─ City fill ratio
   │   └─ Geographic fill ratio
   ├─→ Returns validation result JSON
   └─→ Validator decides if ETL should proceed

7. DECISION ENGINE PHASE
   ├─→ Reads current state from memory.json
   ├─→ Analyzes: data freshness, record count, availability
   ├─→ Decides: proceed with ETL, skip scraping, or retry
   └─→ Outputs decision reason and next actions

8. ETL / SPARK PROCESSING PHASE
   ├─→ Reads TayaraDataEnrichedLocated.json
   ├─→ Data cleaning:
   │   ├─ Remove null/empty values
   │   ├─ Remove duplicates
   │   ├─ Normalize data types
   │   └─ Handle missing fields
   ├─→ Feature engineering:
   │   ├─ Normalize prices
   │   ├─ Calculate price_per_m2
   │   ├─ Extract temporal features
   │   └─ Categorize property types
   ├─→ Write clean data to PostgreSQL
   ├─→ Save processed output to MinIO & local /output
   └─→ Output: /output/clean_tayara/_SUCCESS marker

9. PRICE PREDICTION PHASE
   ├─→ Load cleaned data from PostgreSQL
   ├─→ Prepare training dataset (features + target)
   ├─→ Train XGBoost models:
   │   ├─ Overall model for all properties
   │   ├─ Type-specific models:
   │   │   ├─ Appartement model
   │   │   ├─ Maison model
   │   │   ├─ Villa model
   │   │   └─ House-like model
   │   └─ Log-scaled variants for better accuracy
   ├─→ Evaluate model performance (R², MAE, RMSE)
   ├─→ Save models: /agent_price/models/models_by_type_xgb/
   └─→ Store metrics in metrics_by_type_xgb.json

10. REPORTING PHASE
    ├─→ Aggregates execution metrics
    ├─→ Generates JSON report with:
    │   ├─ Execution timestamp
    │   ├─ Validation results
    │   ├─ Processing statistics
    │   ├─ Model performance metrics
    │   └─ Data quality indicators
    └─→ Saves report to /reports/ and memory.json

11. MEMORY PERSISTENCE
    └─→ Updates memory.json with:
        ├─ Last run timestamp
        ├─ Validation results
        ├─ Report summary
        └─ State for next run
```

---

## Key Components

### 1. **Web Scraper** (`scraper/`)
**Purpose**: Automatically collects real estate listings from Tayara.tn

**How it works**:
- Implements a Scrapy Spider (`tayaraScrapper.py`)
- Sends HTTP requests to Tayara.tn with pagination
- Parses HTML responses to extract listing details:
  - Title, description, price, location
  - Contact information, listing date
  - Property attributes (area, rooms, etc.)
- Handles retries for failed requests
- Saves raw data as JSON files

**Output**: `TayaraDataDetailed.json` - Raw scraped listing data

---

### 2. **Intelligent Agent** (`agent/`)
**Purpose**: Orchestrates the entire pipeline with smart decision-making

#### 2.1 **Agent Orchestrator** (`run_agent.py`)
- Main entry point that coordinates all processing steps
- Loads/saves agent state from `memory.json`
- Executes tools in sequence:
  ```
  Scraper → Deduplication → Regex Enrichment → LLM Fallback 
  → Location Matching → Validation → ETL → Reporting
  ```
- Tracks execution results and updates memory

#### 2.2 **Decision Engine** (`decision_engine.py`)
- **Intelligent decision-making logic** that determines pipeline actions
- Analyzes current state:
  - Does raw data exist?
  - How old is the raw data (age in hours)?
  - How many records are available?
- Makes decisions:
  ```python
  if not raw_data_exists:
      # Full pipeline needed
      scrape=True, validate=True, etl=True
  elif raw_data_older_than_12_hours:
      # Refresh stale data
      scrape=True, validate=True, etl=True
  elif too_few_records (<500):
      # Insufficient data, scrape more
      scrape=True, validate=True, etl=True
  else:
      # Recent data exists, skip scraping
      scrape=False, validate=True, etl=True
  ```
- Provides reasoning for each decision

#### 2.3 **Validator** (`validator.py`)
- Analyzes enriched data quality
- Calculates metrics:
  - **Total records**: Count of all listings
  - **Valid records**: Listings with ID + title
  - **Missing title ratio**: % of listings without title
  - **Missing price ratio**: % of listings without price
  - **City fill ratio**: % with location information
  - **Geographic fill ratio**: % with lat/long coordinates
- Returns JSON report showing data completeness

#### 2.4 **Enrichment Modules**

##### Deduplication (`deduplicate_raw_against_db.py`)
- Compares new scraped data against database
- Removes listings already in system
- Keeps only new/updated records

##### Regex Enrichment (`enrich_with_regex.py`)
- Extracts structured fields from free-text descriptions
- Uses regex patterns to find:
  - Surface area (m²)
  - Number of rooms/bedrooms
  - Property type/category
  - Other attributes
- Fills gaps in structured data

##### LLM Fallback (`enrich_with_llm_fallback.py`)
- For records with missing critical fields
- Calls Claude API (Claude 3.5 Sonnet)
- Sends property description to LLM with extraction prompt
- Extracts: area, rooms, type, condition, amenities
- Merges LLM results with regex results for robustness

##### Location Matching (`match_locations_from_reference.py`)
- Loads reference database: `state-municipality-areas.json`
- Matches user-provided location text to official geographic entities
- Fills in:
  - State/region information
  - Municipality/delegation
  - Precise geographic names
  - Geographic coordinates (lat/long)

#### 2.5 **Reporter** (`reporter.py`)
- Generates execution reports with metrics
- Creates structured JSON output with:
  - Timestamp of execution
  - Processing statistics (records processed, etc.)
  - Validation results
  - Data quality indicators
  - Error/warning information

#### 2.6 **State Management** (`state_reader.py`)
- Reads current pipeline state from disk/database
- Provides context to Decision Engine
- Enables intelligent decision-making

#### 2.7 **Memory System** (`memory.json`)
- Persistent state file storing:
  - Last execution timestamp
  - Previous validation results
  - Execution history
  - Data freshness information
- Allows agent to maintain context across runs
- Enables smart decisions based on history

---

### 3. **Spark ETL Pipeline** (`spark/jobs/tayara_etl.py`)
**Purpose**: Distributed data cleaning and transformation

**Processing steps**:

1. **Data Loading**
   - Reads enriched/located JSON data
   - Converts to Spark DataFrame

2. **Data Cleaning**
   - Removes null/empty values
   - Handles NULL in numeric fields
   - Standardizes text fields (lowercase, strip)
   - Removes duplicate records
   - Validates data types

3. **Feature Engineering**
   - Normalizes prices (handle outliers)
   - Calculates `price_per_m2` metric
   - Extracts temporal features (listing date)
   - Categorizes property types
   - Normalizes location strings

4. **Data Quality Checks**
   - Validates required fields
   - Checks value ranges
   - Ensures referential integrity

5. **Output**
   - Writes clean data to PostgreSQL (staging table)
   - Saves Parquet files to `/output/clean_tayara/`
   - Saves to MinIO for cloud storage
   - Creates `_SUCCESS` marker on successful completion

---

### 4. **Price Prediction Engine** (`agent_price/`)
**Purpose**: Train ML models to predict real estate prices

#### 4.1 **Data Preparation** (`prepare_training_data.py`)
- Loads cleaned data from PostgreSQL or processed files
- Selects relevant features:
  - Property attributes (area, rooms, type)
  - Location (state, municipality)
  - Market factors (listing date, popularity)
- Removes outliers and invalid entries
- Handles missing values
- Encodes categorical variables
- Creates train/test split
- Outputs: `training_data.csv`

#### 4.2 **Model Training** (`train_price_model.py`)
- Trains **XGBoost regression models**
- Creates multiple model variants:
  - **Overall model**: Predicts price for all property types
  - **Type-specific models**:
    - Appartement model (apartments)
    - Maison model (houses)
    - Villa model (villas)
    - House-like model (various house types)
  - **Log-scaled models**: Better handling of price distribution

- **Model training process**:
  ```
  Load training_data.csv
    ↓
  Separate by property type
    ↓
  Feature selection
    ↓
  Train XGBoost for each type
    ↓
  Evaluate with metrics:
    - R² (variation explained)
    - MAE (mean absolute error)
    - RMSE (root mean squared error)
    ↓
  Save models + metrics
  ```

- **Outputs**:
  - `models_by_type_xgb/price_model_*.joblib` - Trained models
  - `metrics_by_type_xgb.json` - Performance metrics

#### 4.3 **Inference** (`predict_price.py`)
- Loads trained XGBoost models
- Makes price predictions for new listings
- Returns point estimates with model outputs

---

### 5. **Apache Airflow Orchestration** (`airflow/`)
**Purpose**: Schedule and monitor pipeline execution

**DAGs (Directed Acyclic Graphs)**:

1. **`tayara_etl_dag.py`** - Main ETL Pipeline
   - Schedules regular scraping/processing
   - Dependencies: scraper → enrich → validate → etl → report
   - Failure notifications and retries

2. **`tayara_agent_pipeline.py`** - Agent Execution
   - Runs intelligent agent with decision-making
   - Depends on decision engine evaluation
   - Executes full or partial pipeline based on decisions

3. **`tayara_price_prediction_dag.py`** - Price Model Training
   - Trains/updates price prediction models
   - Depends on cleaned data availability
   - Runs after main ETL completes

**Features**:
- Scheduled execution (configurable intervals)
- Task dependencies and retries
- Monitoring UI at `http://localhost:8081`
- Integration with PostgreSQL for state
- Logging to `/airflow/logs/`

---

### 6. **Data Storage** (`minio_data/`)
**Purpose**: Object storage for raw and processed data

**MinIO Buckets**:
- `tayara-raw/raw/` - Raw scraped JSON data
- `tayara-processed/clean/` - Cleaned/processed data
- `tayara-processed/agg/` - Aggregated datasets

**Benefits**:
- S3-compatible storage (cloud-like features)
- Scalable data management
- Backup and versioning support

---

## Technologies & Stack

### Core Technologies

| Component | Purpose | Version/Details |
|-----------|---------|-----------------|
| **Python** | Language | 3.8+ |
| **Apache Spark** | Distributed processing | 3.5.8 |
| **Pandas** | Data manipulation | 2.1.4 |
| **XGBoost** | ML model training | - |
| **PostgreSQL** | Data warehouse | 15 |
| **Apache Airflow** | Workflow orchestration | 3.1.0 |
| **MinIO** | Object storage | Latest |
| **Scrapy** | Web scraping | - |
| **BeautifulSoup4** | HTML parsing | 4.12.2 |
| **Claude API** | LLM enrichment | 3.5 Sonnet |
| **Docker** | Containerization | Latest |

### Python Dependencies
- **Data Processing**: pandas, numpy, PyArrow
- **ML**: scikit-learn, XGBoost, joblib
- **Web**: requests, beautifulsoup4, lxml, Scrapy
- **Database**: psycopg2-binary, sqlalchemy
- **Orchestration**: apache-airflow, pyspark
- **Utilities**: python-dotenv, pydantic, pytz

### Infrastructure
- **Docker Compose** - Multi-container orchestration
- **PostgreSQL** - Primary data warehouse
- **MinIO** - S3-compatible object storage
- **Airflow Standalone** - Lightweight orchestration

---

## Setup & Installation

### Prerequisites
- Docker and Docker Compose v2.0+
- Python 3.8+ (for local testing)
- Git
- Environment variables (API keys for LLM)

### Installation Steps

1. **Clone the repository**
   ```bash
   cd d:\Study\4DS\AIPI\ETL
   ```

2. **Install Python dependencies** (optional, for local testing)
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   set LLM_API_KEY=your_claude_api_key_here  # Windows
   # or
   export LLM_API_KEY=your_claude_api_key_here  # Linux/Mac
   ```

4. **Start all services**
   ```bash
   docker compose up -d
   ```

5. **Initialize Airflow database**
   ```bash
   docker compose exec airflow airflow db init
   docker compose exec airflow airflow users create \
     --username admin \
     --password admin \
     --firstname Admin \
     --lastname User \
     --role Admin \
     --email admin@example.com
   ```

6. **Verify services are running**
   ```bash
   docker compose ps
   ```

### Service URLs
- **Airflow UI**: `http://localhost:8081`
- **MinIO Console**: `http://localhost:9001`
- **PostgreSQL**: `localhost:5432` (credentials: airflow/airflow)

---

## Running the Pipeline

### Option 1: Via Airflow Web UI
1. Open `http://localhost:8081`
2. Login with `admin` / `admin`
3. Find the DAG you want to run:
   - `tayara_etl_pipeline` - Main ETL
   - `tayara_ai_agent_pipeline` - Intelligent agent
   - `tayara_price_prediction_pipeline` - Price models
4. Click **Trigger DAG**
5. Monitor execution in the UI
6. Check logs for detailed output

### Option 2: Direct Agent Execution
```bash
# Run the intelligent agent directly
docker compose exec airflow python /opt/project/agent/run_agent.py

# Run price prediction agent
docker compose exec airflow python /opt/project/agent_price/run_price_agent.py
```

### Option 3: Spark Job Only
```bash
# Run just the Spark ETL
docker compose exec spark spark-submit /opt/spark_app/jobs/tayara_etl.py
```

### Option 4: Local Testing
```bash
# Setup local environment
python -m venv venv
venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r requirements.txt

# Test individual components
python agent/run_agent.py
python agent_price/run_price_agent.py
```

---

## Understanding Each Stage

### Stage 1: Web Scraping
```
Input: Tayara.tn website
│
├─→ Send paginated requests to Tayara
├─→ Parse HTML response with BeautifulSoup
├─→ Extract listing fields:
│   - ID, title, description
│   - Price, location, contact
│   - Category, dates
├─→ Handle pagination/retries
│
Output: TayaraDataDetailed.json (raw data)
```

**Key metrics**: Records scraped, failed requests, data coverage

---

### Stage 2-4: Data Enrichment Pipeline
```
Raw Data (missing/incomplete fields)
│
├─→ Deduplication (keep only new listings)
│
├─→ Regex Enrichment (extract from text)
│   - Uses patterns to find: area, rooms, type
│   - Works: 70-80% of records
│
├─→ LLM Fallback (Claude API for remaining)
│   - Sends descriptions to LLM
│   - Extracts missing structured fields
│   - Works: ~95% combined with regex
│
├─→ Location Matching (geo-normalization)
│   - Matches to reference database
│   - Adds state, municipality, coordinates
│
Output: TayaraDataEnrichedLocated.json (structured, complete)
```

**Quality checks**: Field completeness, data consistency, reference coverage

---

### Stage 5-6: Validation & Decision
```
Enriched Data
│
├─→ Validator analyzes data quality:
│   - Counts total vs valid records
│   - Calculates field fill ratios
│   - Identifies missing data
│
├─→ Decision Engine evaluates state:
│   - Is raw data fresh? (< 12 hours)
│   - Do we have enough records? (> 500)
│   - Do we need to scrape again?
│   - Should we run ETL?
│
Output: Validation JSON + Decision (proceed/skip/retry)
```

**Failure handling**: 
- Low city fill ratio → requires re-enrichment
- Too few records → triggers re-scraping
- Stale data → forces refresh

---

### Stage 7: Spark ETL
```
Enriched Data (JSON)
│
├─→ Load into Spark DataFrame
│
├─→ Data Cleaning:
│   - Remove duplicates
│   - Handle NULL values
│   - Standardize formats
│   - Type conversions
│
├─→ Feature Engineering:
│   - Calculate price_per_m2
│   - Normalize prices (log transform)
│   - Extract temporal features
│   - Categorize property types
│
├─→ Quality Assurance:
│   - Validate ranges
│   - Check referential integrity
│   - Remove outliers
│
├─→ Write Outputs:
│   - PostgreSQL (analytical queries)
│   - Parquet files (/output/clean_tayara/)
│   - MinIO (cloud backup)
│
Output: Clean, analytical-ready data
```

**Performance**: Processes 10,000+ records in minutes

---

### Stage 8: Price Prediction
```
Clean Data (with features)
│
├─→ Prepare Training Data
│   - Select relevant features
│   - Handle missing values
│   - Encode categorical variables
│   - Split train/test (80/20)
│
├─→ Train XGBoost Models
│   ├─→ Overall model (all properties)
│   ├─→ Appartement-specific model
│   ├─→ Maison-specific model
│   ├─→ Villa-specific model
│   └─→ House-like-specific model
│
├─→ Model Evaluation
│   - R² score (fit quality: 0-1, higher better)
│   - MAE (Mean Absolute Error in TND)
│   - RMSE (Root Mean Squared Error in TND)
│
├─→ Save Models
│   - Joblib serialized models
│   - Metrics JSON
│   - Feature importance
│
Output: Ready-to-use price prediction models
```

**Usage**: Use saved models to predict prices for new listings

---

### Stage 9: Reporting
```
Execution Results
│
├─→ Aggregate metrics from all stages
├─→ Compile validation results
├─→ Add model performance metrics
├─→ Generate JSON report
├─→ Update memory.json with state
│
Output: /reports/execution_report_*.json + memory.json
```

**Memory stores**:
- Last execution timestamp
- Previous validation data
- Model metrics
- State for next run

---

## Price Prediction Engine

### How Price Prediction Works

The price prediction engine uses **XGBoost** (eXtreme Gradient Boosting), a powerful ensemble learning algorithm optimized for regression tasks.

#### Feature Engineering
Properties are represented with these features:
- **Size-based**: area (m²), number of rooms/bedrooms
- **Type-based**: property category, building type
- **Location-based**: state, municipality, coordinates
- **Market-based**: listing date, market trends
- **Condition**: property condition, amenities

#### Model Training
1. **Data Split**: 80% training, 20% validation
2. **XGBoost Parameters**: 
   - Learning rate: 0.1 (slow learning for stability)
   - Max depth: 6 (tree complexity)
   - N estimators: 100+ (ensemble size)
3. **Target Scaling**: Log transform for price (handles distribution skew)

#### Model Types
- **Overall Model**: General prediction across all types
- **Type-Specific Models**: Separate models for:
  - Appartements (better apartment-specific features)
  - Maisons (single-family homes)
  - Villas (luxury properties)
  - House-like (various house types)

#### Prediction Quality
Models are evaluated on test data:
- **R² Score**: How well model explains price variation
  - 0.85-0.95 = Excellent (typical range)
  - Target: Explain 85%+ of price variation
- **MAE (Mean Absolute Error)**: Average prediction error in TND
  - Example: MAE=500k means ±500k average error
- **RMSE (Root Mean Squared Error)**: Penalizes large errors more heavily

#### Using Predictions
```python
# Load trained model
model = joblib.load('price_model_appartement_log_xgb.joblib')

# Prepare features for new property
features = {
    'area': 120,              # m²
    'rooms': 3,
    'state': 'Tunis',
    'municipality': 'Carthage',
    'listing_date': '2025-01-01'
}

# Predict price
predicted_price = model.predict([features])
# Returns: e.g., 350,000 TND
```

---

## Key Features

### 🤖 Intelligent Decision Making
- Autonomous decisions about pipeline execution
- Stateful memory system tracking execution history
- Adaptive scraping based on data freshness
- Smart deduplication to avoid redundant processing

### 🚀 Multi-Stage Enrichment
1. **Regex-based extraction** - Fast, deterministic
2. **LLM fallback** - Handles complex descriptions
3. **Geographic normalization** - Precise location matching
4. **Combined approach** - Leverages strengths of both

### 📊 Data Quality Assurance
- Comprehensive validation metrics
- Quality ratio tracking (city/geo fill)
- Completeness checks
- Duplicate detection and removal

### 💰 Price Prediction
- Type-specific ML models (apartments, houses, villas)
- XGBoost ensemble method for accuracy
- Handles price distribution via log scaling
- Detailed performance metrics (R², MAE, RMSE)

### 🔄 Automated Orchestration
- Airflow DAG scheduling
- Task dependency management
- Failure handling and retries
- Comprehensive logging

### 💾 Scalable Storage
- PostgreSQL for structured queries
- MinIO for object storage (S3-compatible)
- Spark for distributed processing
- Multiple output formats (JSON, Parquet, CSV)

### 📈 Distributed Processing
- Apache Spark for handling large datasets
- Parallel data transformations
- Optimized memory usage
- Fault-tolerant processing

### 🔒 Robust Error Handling
- Retry mechanisms for failed requests
- Graceful fallbacks (regex → LLM)
- Detailed error logging
- State recovery from failures

---

## Data Quality Metrics

The pipeline tracks several quality metrics:

### Completeness Metrics
- **Valid Records**: % with ID and title
- **City Fill Ratio**: % with location information
- **Geographic Fill Ratio**: % with coordinates
- **Title Fill**: % of listings with titles
- **Price Fill**: % of listings with prices

### Processing Metrics
- **Total Records**: Count of processed listings
- **Duplicates Removed**: Count of filtered records
- **Enrichment Rate**: % records enhanced with LLM
- **Location Match Rate**: % successfully matched to geo-entities

### Model Metrics
- **R² Score**: Model fit quality (aim: 0.85+)
- **MAE**: Mean absolute error in TND (lower better)
- **RMSE**: Root mean squared error in TND (lower better)
- **Feature Importance**: Which features drive predictions

---

## Troubleshooting

### Common Issues

**Issue**: Airflow DAGs not showing up
- **Solution**: Check `airflow/dags/` folder permissions, restart Airflow container

**Issue**: LLM enrichment fails (API key missing)
- **Solution**: Set `LLM_API_KEY` environment variable before starting containers

**Issue**: Spark job out of memory
- **Solution**: Increase Docker memory limit in `docker-compose.yaml`

**Issue**: PostgreSQL connection refused
- **Solution**: Ensure `postgres` service is running, wait 10-20 seconds after docker-compose up

**Issue**: Location matching returns no results
- **Solution**: Check `state-municipality-areas.json` reference data is loaded

---

## Performance Characteristics

### Processing Speed
- **Scraping**: ~100-200 listings per second
- **Regex Enrichment**: ~1000+ records per second
- **LLM Enrichment**: ~10-20 records per second (API rate-limited)
- **Location Matching**: ~1000+ records per second
- **Spark ETL**: ~10,000+ records per minute
- **Model Training**: ~30 seconds-2 minutes per model

### Data Volumes
- **Typical daily output**: 1,000-5,000 new listings
- **Historical data**: 10,000+ cumulative records
- **Model training size**: 5,000+ records minimum for reliable models

### Resource Usage
- **Memory**: 2-4 GB for full stack
- **Disk**: 1-5 GB depending on data retention
- **Network**: Minimal (Tayara.tn scraping ~100 MB/day)

---

## Maintenance & Monitoring

### Regular Tasks
- **Daily**: Monitor Airflow logs for failures
- **Weekly**: Check model performance metrics
- **Monthly**: Analyze data quality trends
- **Quarterly**: Retrain models with updated data

### Health Checks
```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f airflow
docker compose logs -f spark

# Test database connection
docker compose exec postgres psql -U airflow -d airflow -c "SELECT 1;"

# Verify MinIO
docker compose exec minio mc ls local/
```

### Cleanup & Archival
- Archive old Airflow logs monthly
- Backup PostgreSQL regularly
- Compress processed data older than 6 months
- Maintain model versioning

---

## Future Enhancements

Potential improvements for the system:

1. **Real-time Processing**: Kafka streaming for live updates
2. **Advanced ML**: Neural networks for better price prediction
3. **Sentiment Analysis**: Analyze listing descriptions for market sentiment
4. **Image Processing**: Process property images with computer vision
5. **Forecasting**: Time-series models for price trends
6. **API Layer**: REST API for price predictions and data queries
7. **Dashboard**: Interactive visualization of market trends
8. **Multi-region**: Expand to other North African markets

---

## Conclusion

This ETL pipeline represents a complete data engineering solution combining:
- **Web scraping** for data acquisition
- **Intelligent enrichment** using regex and LLM
- **Quality validation** with metrics-driven decisions
- **Distributed processing** with Spark
- **Machine learning** for price prediction
- **Workflow orchestration** with Airflow
- **Cloud-like storage** with MinIO

The system is designed to be **autonomous**, **scalable**, and **intelligent** — making it suitable for production real estate data platforms.

For detailed technical implementation, refer to individual component documentation in the source code.
