# Quick Start Guide - EstateMind Admin Dashboard with Docker

## 📋 Files Created Summary

### Frontend (React + Vite)
```
frontend/
├── src/
│   ├── components/
│   │   ├── ScraperManagement/    ← Scraper cards & trigger button
│   │   ├── DataDashboard/        ← Analytics & charts
│   │   └── Layout/               ← Header & Sidebar
│   ├── context/
│   │   ├── PipelineContext.jsx   ← Pipeline state
│   │   └── DataContext.jsx       ← Data state
│   ├── services/
│   │   ├── airflowService.js     ← Airflow API calls
│   │   └── postgresService.js    ← DB queries
│   ├── pages/
│   │   └── AdminDashboard.jsx    ← Layout
│   ├── styles/
│   │   ├── index.css             ← Global styles
│   │   └── theme.js              ← Ant Design theme
│   ├── App.jsx                   ← Main app routing
│   └── main.jsx                  ← Entry point
├── Dockerfile                    ← Multi-stage build
├── nginx.conf                    ← Web server config
├── package.json
├── vite.config.js
├── index.html
└── README.md
```

### Backend (Node.js + Express)
```
backend/
├── server.js                     ← Express API server
├── Dockerfile                    ← Node.js Alpine
├── package.json
├── .env.example
└── .gitignore
```

### Configuration
- `docker-compose.yaml` ← Updated with frontend & backend services
- `DOCKER_SETUP.md` ← Complete Docker guide
- `frontend/.env.example` ← Frontend env vars

---

## 🚀 Quick Start (5 minutes)

### Step 1: Create PostgreSQL Volume
```bash
docker volume create etl_postgres-db-volume
```

### Step 2: Build & Start Everything
```bash
docker-compose up -d --build
```

### Step 3: Wait for Services to Start
```bash
# Check status
docker-compose ps

# Wait until all show "Up" status (2-3 minutes)
```

### Step 4: Access Admin Dashboard
Open **http://localhost** in your browser

---

## 📊 What You Get

### Page 1: Scraper Management
- ✅ **Tayara** - Active scraper with stats
- 🔒 **Immobilier.tn, Spadon, Avito, OLX** - Coming soon (locked)
- 🎯 **"Trigger ETL Pipeline" Button**
  - Click to start pipeline
  - Modal shows real-time step execution
  - Watch each task status (queued → running → success/failed)

### Page 2: Data Analytics Dashboard
- 📈 Total Properties count
- 📍 Unique Locations count
- 🏠 Property Types count
- 💰 Average Price
- 📊 Four interactive charts:
  - Properties by location (bar chart)
  - Property types distribution (pie chart)
  - Price distribution (line chart)
  - Summary statistics

---

## 🔧 Key Architecture

```
┌─────────────────────────────────────┐
│  React Admin Dashboard (Port 80)     │
│  ├─ Scraper Management              │
│  ├─ Pipeline Monitor                │
│  └─ Data Analytics                  │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────────┐
    │                 │
    ▼                 ▼
┌─────────────┐  ┌──────────────────┐
│  Nginx      │  │  Backend API     │
│  (Port 80)  │  │  (Port 3001)     │
└─────────────┘  └────────┬─────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │  PostgreSQL    │
                  │  (Port 5432)   │
                  └────────────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ scraped_props  │
                  │ Airflow        │
                  └────────────────┘
```

---

## 📡 How It Works

### Triggering Pipeline
1. Click **"Trigger ETL Pipeline"** button
2. Modal opens showing pipeline steps
3. Frontend calls: `POST /airflow/api/v1/dags/tayara_ai_agent_pipeline/dagRuns`
4. Airflow DAG starts
5. Frontend polls: `GET /airflow/api/v1/dags/tayara_ai_agent_pipeline/dagRuns/{run_id}/taskInstances`
6. Real-time updates show each step status

### Loading Data Analytics
1. Page loads, fetches data
2. Backend API: `GET /api/scraped-data/stats`
3. Returns statistics & chart data
4. Frontend renders with Recharts
5. Refreshes every 30 seconds

---

## 🛠️ Configuration

### Environment Variables

**Frontend** (in docker-compose.yaml):
```env
REACT_APP_API_URL=http://localhost/api
REACT_APP_AIRFLOW_URL=http://localhost/airflow/api
```

**Backend** (in docker-compose.yaml):
```env
DATABASE_URL=postgresql://airflow:airflow@postgres:5432/airflow
AIRFLOW_API_URL=http://airflow:8080/api/v1
```

### Database Table Structure
The backend expects this table:
```sql
CREATE TABLE scraped_properties (
    id SERIAL PRIMARY KEY,
    location VARCHAR(200),
    property_type VARCHAR(100),
    price NUMERIC(15,2),
    scraped_at TIMESTAMP
);
```

---

## 📝 Common Tasks

### View Real-Time Logs
```bash
# Frontend
docker-compose logs -f frontend

# Backend
docker-compose logs -f backend

# All services
docker-compose logs -f
```

### Restart Services
```bash
# All
docker-compose restart

# Specific
docker-compose restart frontend
docker-compose restart backend
```

### Connect to Database
```bash
docker exec -it postgres psql -U airflow -d airflow
```

### Stop Everything
```bash
docker-compose stop
```

### Remove Everything
```bash
docker-compose down    # Keeps volumes
docker-compose down -v # Removes volumes too
```

---

## ⚠️ Troubleshooting

### "Cannot connect to localhost"
- Verify services running: `docker-compose ps`
- Wait 2-3 minutes for startup
- Check: `docker-compose logs frontend`

### "API requests failing"
- Check backend running: `docker-compose logs backend`
- Verify database connection: `docker-compose logs backend`
- Test endpoint: `curl http://localhost:3001/api/scraped-data/stats`

### "Pipeline won't trigger"
- Verify Airflow: `docker-compose logs airflow`
- Check DAG exists in Airflow UI (http://localhost:8081)
- Verify DAG is enabled (toggle switch)

### "Port already in use"
- Find process: `netstat -ano | findstr :80` (Windows)
- Change port in docker-compose.yaml: `ports: - "8080:80"`
- Restart: `docker-compose up -d`

---

## 📚 File Reference

| File | Purpose |
|------|---------|
| `ScraperManagement.jsx` | Main scraper page |
| `TriggerModal.jsx` | Pipeline execution modal |
| `DataDashboard.jsx` | Analytics dashboard |
| `PipelineContext.jsx` | Pipeline state management |
| `DataContext.jsx` | Data state management |
| `airflowService.js` | Airflow API integration |
| `postgresService.js` | Database queries |
| `server.js` | Backend API endpoints |
| `nginx.conf` | Web server routing |
| `docker-compose.yaml` | Service orchestration |

---

## 🎯 Next Steps

1. ✅ Start Docker containers: `docker-compose up -d --build`
2. ✅ Access dashboard: http://localhost
3. ✅ Create database table (see DOCKER_SETUP.md)
4. ✅ Trigger a pipeline run
5. ✅ View data analytics
6. ✅ Add more scrapers (unlock them later)
7. ✅ Deploy to production with env vars

---

## 📞 Support

See `DOCKER_SETUP.md` for detailed documentation and troubleshooting.

---

**Created Components:**
- ✅ 15+ React Components
- ✅ Context API State Management
- ✅ Express.js Backend API
- ✅ Nginx Web Server Config
- ✅ Docker Compose Integration
- ✅ Responsive UI with Ant Design
- ✅ Real-time Pipeline Monitoring
- ✅ Data Analytics Dashboard
