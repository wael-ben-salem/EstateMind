# Docker Setup Guide for EstateMind Admin Platform

Complete step-by-step guide to build and run the entire EstateMind admin platform using Docker.

## Project Structure

```
EstateMind/
├── docker-compose.yaml          # Main orchestration file
├── airflow/                      # Airflow DAGs and Dockerfile
├── spark/                        # Spark jobs and Dockerfile
├── frontend/                     # React admin dashboard
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── backend/                      # Node.js API server
│   ├── Dockerfile
│   ├── server.js
│   └── package.json
└── scraper/                      # Web scraper
```

## Prerequisites

- **Docker**: v20.10+
- **Docker Compose**: v2.0+
- **Git**: For version control
- **Ports available**: 80, 3001, 5432, 8081, 9000, 9001

## Step 1: Prepare the Project

### 1.1 Clone/Setup the Project

```bash
# Navigate to your project directory
cd d:\Study\4DS\AIPI\EstateMindFinale\EstateMind

# List current files to verify structure
dir
```

You should see:
- `docker-compose.yaml` ✓
- `frontend/` folder (new)
- `backend/` folder (new)
- `airflow/` folder ✓
- Other folders...

### 1.2 Initialize Docker Volume

```bash
# Create the persistent PostgreSQL volume
docker volume create etl_postgres-db-volume

# Verify the volume was created
docker volume ls | grep etl_postgres
```

## Step 2: Build and Start Services

### 2.1 Build All Services

```bash
# From project root, build all services
docker-compose build

# This will build:
# - Frontend (React + Nginx)
# - Backend (Node.js Express)
# - Airflow DAGs
# - Spark jobs
```

**Expected output:**
```
Building airflow
Building spark
Building backend
Building frontend
```

### 2.2 Start All Services

```bash
# Start all services in the background
docker-compose up -d

# Watch the startup process (optional)
docker-compose logs -f

# Press Ctrl+C to stop watching logs
```

**Expected output:**
```
Creating postgres ... done
Creating airflow ... done
Creating spark ... done
Creating minio ... done
Creating minio-init ... done
Creating backend ... done
Creating estateMind-frontend ... done
```

### 2.3 Verify All Services are Running

```bash
# Check status of all containers
docker-compose ps

# Expected output:
# CONTAINER ID  IMAGE              STATUS              PORTS
# xxx           airflow:latest     Up 2 minutes        0.0.0.0:8081->8080/tcp
# xxx           postgres:15        Up 2 minutes        0.0.0.0:5432->5432/tcp
# xxx           backend:latest     Up 1 minute         0.0.0.0:3001->3001/tcp
# xxx           frontend:latest    Up 1 minute         0.0.0.0:80->80/tcp
```

## Step 3: Access Services

Once all services are running, access them at:

| Service | URL | Purpose |
|---------|-----|---------|
| **Admin Dashboard** | http://localhost | React admin UI |
| **Airflow UI** | http://localhost:8081 | ETL pipeline management |
| **Backend API** | http://localhost:3001 | Data API (debugging) |
| **MinIO Console** | http://localhost:9001 | Object storage management |
| **Database** | localhost:5432 | PostgreSQL (pgAdmin recommended) |

### Accessing Admin Dashboard

1. Open browser to **http://localhost**
2. You should see:
   - **Scraper Management page** with:
     - Tayara (Active) card
     - 4 "Coming Soon" locked scrapers
     - **"Trigger ETL Pipeline"** button
   - Navigation sidebar with:
     - Scraper Management
     - Data Analytics

3. Click **"Trigger ETL Pipeline"** button
   - A modal will open
   - Shows real-time pipeline execution steps
   - Displays each task status (running, success, failed)

4. Click **"Data Analytics"** in sidebar
   - Shows scraped data statistics
   - Displays location distribution chart
   - Shows property types pie chart
   - Displays price distribution line chart

## Step 4: Database Setup

The backend expects a `scraped_properties` table. Create it:

### 4.1 Connect to PostgreSQL

```bash
# Option 1: Using Docker exec
docker exec -it postgres psql -U airflow -d airflow

# Option 2: Using any PostgreSQL client
# Host: localhost
# Port: 5432
# Username: airflow
# Password: airflow
# Database: airflow
```

### 4.2 Create Table (if not exists)

```sql
CREATE TABLE IF NOT EXISTS scraped_properties (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) UNIQUE,
    title VARCHAR(500),
    location VARCHAR(200),
    price NUMERIC(15,2),
    property_type VARCHAR(100),
    bedrooms INTEGER,
    bathrooms INTEGER,
    area NUMERIC(10,2),
    description TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_location ON scraped_properties(location);
CREATE INDEX idx_price ON scraped_properties(price);
CREATE INDEX idx_property_type ON scraped_properties(property_type);
CREATE INDEX idx_scraped_at ON scraped_properties(scraped_at);
```

### 4.3 Exit PostgreSQL

```sql
\q
```

## Step 5: Insert Sample Data (Optional)

```bash
# Create a script file: insert_sample_data.sql
cat > insert_sample_data.sql << 'EOF'
INSERT INTO scraped_properties (title, location, price, property_type, bedrooms, bathrooms, area, description) VALUES
('Beautiful Villa in Tunis', 'Tunis', 125000, 'Villa', 4, 3, 250.50, 'Spacious villa with garden'),
('Apartment in Sfax', 'Sfax', 45000, 'Apartment', 2, 1, 85.00, 'Modern apartment'),
('House in Sousse', 'Sousse', 65000, 'House', 3, 2, 150.00, 'Family house'),
('Studio in Ariana', 'Ariana', 25000, 'Studio', 1, 1, 35.00, 'Cozy studio apartment'),
('Apartment in Monastir', 'Monastir', 35000, 'Apartment', 2, 1, 75.00, 'Beach apartment');
EOF

# Run the script
docker exec -i postgres psql -U airflow -d airflow < insert_sample_data.sql
```

## Step 6: Verify Backend API

Test the backend API endpoints:

```bash
# Get statistics
curl http://localhost:3001/api/scraped-data/stats

# Get locations
curl http://localhost:3001/api/scraped-data/locations

# Get property types
curl http://localhost:3001/api/scraped-data/property-types

# Get price distribution
curl http://localhost:3001/api/scraped-data/prices
```

## Common Docker Commands

### Viewing Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs frontend
docker-compose logs backend
docker-compose logs airflow

# Follow logs in real-time
docker-compose logs -f frontend

# Last 50 lines
docker-compose logs --tail=50 backend
```

### Managing Containers

```bash
# Stop all services
docker-compose stop

# Start all services
docker-compose start

# Restart specific service
docker-compose restart frontend

# Remove all containers (careful!)
docker-compose down

# Remove everything including volumes (careful!)
docker-compose down -v
```

### Rebuilding Services

```bash
# Rebuild frontend only
docker-compose build frontend

# Rebuild and restart
docker-compose up -d --build frontend

# Rebuild everything
docker-compose up -d --build
```

### Executing Commands in Containers

```bash
# Open bash in frontend
docker exec -it estateMind-frontend /bin/sh

# Run npm command in backend
docker exec estateMind-backend npm list

# Run SQL in database
docker exec -i postgres psql -U airflow -d airflow < query.sql
```

## Troubleshooting

### Issue: Port 80 Already in Use

```bash
# Find what's using port 80
# Windows:
netstat -ano | findstr :80

# Stop the service or change frontend port in docker-compose.yaml:
# Change: ports: - "80:80"
# To: ports: - "8080:80"  (then access at http://localhost:8080)
```

### Issue: Frontend Blank Page / 404

```bash
# Check frontend logs
docker-compose logs frontend

# Verify build was successful
docker-compose build --no-cache frontend

# Restart frontend
docker-compose restart frontend
```

### Issue: Backend API Errors

```bash
# Check backend logs
docker-compose logs backend

# Verify database connection
docker exec estateMind-backend npm run dev

# Check if database is running
docker-compose ps postgres
```

### Issue: Database Connection Failed

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify volume exists
docker volume ls | grep etl_postgres

# Recreate volume if needed
docker volume rm etl_postgres-db-volume
docker volume create etl_postgres-db-volume
docker-compose restart postgres
```

### Issue: Airflow DAG Not Running

```bash
# Check Airflow logs
docker-compose logs airflow

# Access Airflow UI: http://localhost:8081
# Verify DAG exists: Search "tayara_ai_agent_pipeline"
# Check DAG is enabled (toggle switch)
```

## Performance Tips

1. **Docker Desktop Settings** (Windows/Mac):
   - Allocate at least 4GB RAM
   - Allocate 2+ CPU cores

2. **First Run**: May take 5-10 minutes for services to start

3. **Production**: Use `.env` file for sensitive credentials

## Security Notes

⚠️ **For Development Only**

Current credentials (should be changed for production):
- PostgreSQL: `airflow:airflow`
- Airflow: Default credentials (check Airflow docs)
- MinIO: `minioadmin:minioadmin`

For production, update:
1. `docker-compose.yaml` environment variables
2. `.env` file for sensitive data
3. Database passwords
4. API authentication

## Next Steps

1. ✅ Verify all services running (`docker-compose ps`)
2. ✅ Access admin dashboard (http://localhost)
3. ✅ Create scraped_properties table in PostgreSQL
4. ✅ Insert sample data or run actual scrapers
5. ✅ Trigger ETL pipeline from dashboard
6. ✅ Monitor real-time execution
7. ✅ View data analytics dashboard

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Express.js API Guide](https://expressjs.com/)
- [React Documentation](https://react.dev/)

## Support

If you encounter issues:

1. Check logs: `docker-compose logs [service]`
2. Verify ports available: `netstat -ano` (Windows) or `lsof -i` (Mac/Linux)
3. Ensure volumes created: `docker volume ls`
4. Rebuild if needed: `docker-compose build --no-cache`
5. Check docker-compose.yaml syntax: `docker-compose config`
