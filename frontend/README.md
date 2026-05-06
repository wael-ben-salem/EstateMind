# EstateMind Admin Dashboard - Frontend

React-based admin interface for the EstateMind ETL agent platform.

## Features

- **Scraper Management**: Monitor and trigger web scrapers (Tayara, with upcoming integrations)
- **Pipeline Monitor**: Real-time ETL pipeline execution tracking with step-by-step progress
- **Data Analytics**: Visual dashboards showing scraped property data insights
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Architecture

```
frontend/
├── src/
│   ├── components/        # React components
│   │   ├── ScraperManagement/
│   │   ├── DataDashboard/
│   │   └── Layout/
│   ├── context/          # React Context for state management
│   ├── services/         # API service files
│   ├── pages/            # Page components
│   ├── styles/           # Global styles
│   ├── App.jsx
│   └── main.jsx
├── Dockerfile
├── nginx.conf
├── package.json
├── vite.config.js
└── index.html
```

## Setup with Docker

### Prerequisites
- Docker & Docker Compose
- The main docker-compose.yaml must be running (Airflow, PostgreSQL, MinIO)

### Building and Running

1. **Build and start all services:**
   ```bash
   docker-compose up -d --build
   ```

2. **Access the services:**
   - Admin Dashboard: http://localhost
   - Airflow UI: http://localhost:8081
   - Backend API: http://localhost:3001/api

3. **View logs:**
   ```bash
   docker-compose logs -f frontend
   docker-compose logs -f backend
   ```

### Environment Variables

**For Frontend (nginx.conf):**
- `REACT_APP_API_URL`: Backend API URL (default: http://localhost/api)
- `REACT_APP_AIRFLOW_URL`: Airflow API URL (default: http://localhost/airflow/api)

**For Backend (.env):**
- `DATABASE_URL`: PostgreSQL connection string
- `PORT`: Backend server port (default: 3001)
- `NODE_ENV`: Environment (development/production)
- `AIRFLOW_API_URL`: Airflow API endpoint

## Key Components

### 1. **ScraperManagement**
Displays available web scrapers with their status and allows triggering the ETL pipeline.

**Files:**
- `ScraperManagement.jsx` - Main component
- `ScraperCard.jsx` - Individual scraper card
- `TriggerModal.jsx` - Pipeline execution modal

### 2. **DataDashboard**
Shows analytics and visualizations of scraped data from PostgreSQL.

**Files:**
- `DataDashboard.jsx` - Main dashboard
- `LocationChart.jsx` - Location distribution bar chart
- `PropertyTypeChart.jsx` - Property type pie chart
- `PriceDistributionChart.jsx` - Price range line chart

### 3. **Context API**
State management for pipeline and data.

**Files:**
- `PipelineContext.jsx` - Manages ETL pipeline state
- `DataContext.jsx` - Manages scraped data state

### 4. **Services**
API communication layer.

**Files:**
- `airflowService.js` - Airflow REST API calls
- `postgresService.js` - Database queries via backend

## API Endpoints

### Backend API (`/api/`)
- `GET /api/scraped-data/stats` - Get overall statistics
- `GET /api/scraped-data/locations` - Get location distribution
- `GET /api/scraped-data/property-types` - Get property type breakdown
- `GET /api/scraped-data/prices` - Get price distribution

### Airflow API (`/airflow/api/v1/`)
- `POST /dags/tayara_ai_agent_pipeline/dagRuns` - Trigger pipeline
- `GET /dags/tayara_ai_agent_pipeline/dagRuns/{run_id}` - Get run status
- `GET /dags/tayara_ai_agent_pipeline/dagRuns/{run_id}/taskInstances` - Get task details

## Database Requirements

The backend expects a `scraped_properties` table in PostgreSQL with columns:
- `location` (string)
- `property_type` (string)
- `price` (numeric)
- `scraped_at` (timestamp)

Adjust the SQL queries in `backend/server.js` if your schema differs.

## Development

### Local Development (without Docker)

1. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Backend:**
   ```bash
   cd backend
   npm install
   npm run dev
   ```

3. **Update `.env` files** with local URLs (localhost:5173, localhost:3001)

## Troubleshooting

### Frontend won't load
- Check nginx logs: `docker-compose logs frontend`
- Verify Airflow and backend are running: `docker-compose ps`

### API calls failing
- Check backend logs: `docker-compose logs backend`
- Verify database connection: `docker-compose logs backend`
- Check PostgreSQL is running with correct tables

### Pipeline not triggering
- Verify Airflow is running: `docker-compose logs airflow`
- Check Airflow auth credentials in services
- Check DAG exists: http://localhost:8081

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **Ant Design 5** - UI component library
- **Recharts** - Data visualization
- **React Router v6** - Navigation
- **Nginx** - Web server (production)
- **Node.js + Express** - Backend API
- **PostgreSQL** - Database

## Next Steps

1. Create `scraped_properties` table in PostgreSQL
2. Update database queries in `backend/server.js` to match your schema
3. Add Airflow authentication if needed
4. Deploy to production with proper environment variables
