# 🐳 Docker Installation & Running Guide

Complete step-by-step guide to install and run EstateMind Admin Platform with Docker.

---

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 10/11, macOS, or Linux
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 5GB free space
- **Ports**: 80, 3001, 5432, 8081, 9000, 9001 (must be available)

### Install Docker

#### Windows 10/11
1. Download: [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Install and restart computer
3. Run PowerShell and verify:
   ```bash
   docker --version
   docker-compose --version
   ```

#### macOS
1. Download: [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. Install and start
3. Verify:
   ```bash
   docker --version
   docker-compose --version
   ```

#### Linux (Ubuntu)
```bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo usermod -aG docker $USER

# Verify
docker --version
docker-compose --version
```

---

## 🔧 Step-by-Step Installation

### Step 1: Verify Your Project Structure

Navigate to your project directory:
```bash
cd d:\Study\4DS\AIPI\EstateMindFinale\EstateMind
# or on Mac/Linux:
cd ~/path/to/EstateMind
```

Verify you have these folders:
```
✓ frontend/        (newly created)
✓ backend/         (newly created)
✓ airflow/
✓ spark/
✓ scraper/
✓ agent/
✓ agent_price/
✓ docker-compose.yaml (updated)
```

List contents to confirm:
```bash
# Windows PowerShell
ls

# Mac/Linux
ls -la
```

### Step 2: Create Required Docker Volume

```bash
docker volume create etl_postgres-db-volume
```

Verify it was created:
```bash
docker volume ls | grep etl_postgres
```

Expected output:
```
DRIVER    NAME
local     etl_postgres-db-volume
```

### Step 3: Build All Services

From project root directory:

```bash
docker-compose build
```

This will take 5-10 minutes the first time. It builds:
- ✅ Frontend (React + Nginx)
- ✅ Backend (Node.js)
- ✅ Airflow (unchanged)
- ✅ Spark (unchanged)

Watch for:
```
Building airflow
Building spark
Building backend
Building frontend

Successfully built xxx
Successfully tagged xxx
```

### Step 4: Start All Services

```bash
docker-compose up -d
```

The `-d` flag runs in background. Output should show:
```
Creating postgres ... done
Creating spark ... done
Creating airflow ... done
Creating minio ... done
Creating minio-init ... done
Creating backend ... done
Creating estateMind-frontend ... done
```

### Step 5: Wait for Services to Start

Wait 2-3 minutes for all services to fully initialize. Check status:

```bash
docker-compose ps
```

Keep running this command until ALL containers show `Up` status:

```
CONTAINER ID  IMAGE                  STATUS              PORTS
xxx           postgres:15            Up 2 minutes        0.0.0.0:5432->5432/tcp
xxx           airflow:latest         Up 1 minute         0.0.0.0:8081->8080/tcp
xxx           spark:latest           Up 2 minutes
xxx           minio:latest           Up 2 minutes        0.0.0.0:9000->9000/tcp, 9001/tcp
xxx           backend:latest         Up 30 seconds       0.0.0.0:3001->3001/tcp
xxx           frontend:latest        Up 20 seconds       0.0.0.0:80->80/tcp
```

⏳ **If any show "Restarting"**: Wait another minute, then recheck

### Step 6: Access the Dashboard

Open your browser and go to:

**http://localhost**

You should see:
- ✅ Logo: "🏠 EstateMind Admin"
- ✅ Left sidebar with menu items
- ✅ Scraper Management page with cards
- ✅ "Trigger ETL Pipeline" button

### Step 7: Create Database Table

The backend needs a database table. Connect to PostgreSQL:

```bash
docker exec -it postgres psql -U airflow -d airflow
```

You'll see the `airflow=#` prompt. Run:

```sql
CREATE TABLE IF NOT EXISTS scraped_properties (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500),
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

Exit PostgreSQL:
```sql
\q
```

### Step 8: Insert Sample Data (Optional)

While still connected to PostgreSQL (or run step 7 again), insert test data:

```sql
INSERT INTO scraped_properties 
(title, location, price, property_type, bedrooms, bathrooms, area) 
VALUES
('Villa Moderne Tunis', 'Tunis', 150000, 'Villa', 4, 3, 250),
('Appartement Sfax', 'Sfax', 45000, 'Apartment', 2, 1, 85),
('Maison Sousse', 'Sousse', 65000, 'House', 3, 2, 150),
('Studio Ariana', 'Ariana', 25000, 'Studio', 1, 1, 35),
('Appartement Monastir', 'Monastir', 38000, 'Apartment', 2, 1, 75),
('Villa Tunis 2', 'Tunis', 180000, 'Villa', 5, 4, 300),
('Maison Sfax', 'Sfax', 72000, 'House', 3, 2, 160),
('Appartement Sousse', 'Sousse', 52000, 'Apartment', 2, 1, 90);
```

Exit:
```sql
\q
```

### Step 9: Verify Everything Works

#### Test Backend API
```bash
curl http://localhost:3001/api/scraped-data/stats
```

Expected response:
```json
{
  "totalProperties": 8,
  "uniqueLocations": 5,
  "propertyTypes": 4,
  "avgPrice": 82125,
  "locationData": [...],
  "propertyTypeData": [...],
  "priceData": [...]
}
```

#### Test Frontend
Refresh browser at http://localhost and you should see:
- ✅ Statistics cards with data
- ✅ Charts showing data
- ✅ Location chart with bars
- ✅ Property types pie chart
- ✅ Price distribution line chart

---

## 🎯 First Time Testing

### Test 1: Scraper Management Page

1. Go to **http://localhost**
2. You should be on "Scraper Management" page
3. See cards:
   - ✅ **Tayara** (Active) - with properties count
   - 🔒 **Immobilier.tn** (Coming Soon)
   - 🔒 **Spadon** (Coming Soon)
   - 🔒 **Avito** (Coming Soon)
   - 🔒 **OLX** (Coming Soon)
4. Click **"Trigger ETL Pipeline"** button
5. Modal opens showing "Start Pipeline" button
6. Click it (should attempt to trigger Airflow DAG)
7. See real-time step execution with Timeline

### Test 2: Data Analytics Page

1. Click **"Data Analytics"** in sidebar
2. See statistics:
   - Total Properties: 8
   - Unique Locations: 5
   - Property Types: 4
   - Avg Price: 82,125
3. See 3 charts:
   - Bar chart of locations
   - Pie chart of property types
   - Line chart of price distribution
4. Sidebar toggle works smoothly

---

## 🔍 Monitoring & Debugging

### View Real-Time Logs

**All services:**
```bash
docker-compose logs -f
```

**Specific service:**
```bash
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f airflow
docker-compose logs -f postgres
```

**Last 50 lines:**
```bash
docker-compose logs --tail=50 backend
```

### Check Service Status

```bash
docker-compose ps
```

### Restart a Service

```bash
docker-compose restart frontend
docker-compose restart backend
```

### Rebuild a Service

```bash
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

---

## 🛑 Stopping & Cleanup

### Stop All Services (Keep Data)

```bash
docker-compose stop
```

Restart later with:
```bash
docker-compose start
```

### Stop and Remove (Keeps Volumes/Data)

```bash
docker-compose down
```

Restart with:
```bash
docker-compose up -d
```

### Full Reset (Remove Everything)

⚠️ **This deletes all data!**

```bash
docker-compose down -v
```

Then recreate volume:
```bash
docker volume create etl_postgres-db-volume
docker-compose up -d --build
```

---

## 🔧 Troubleshooting

### Issue: "Cannot connect to Docker daemon"

**Windows/Mac:**
- Open Docker Desktop application
- Wait for status to show "Running"
- Try again

**Linux:**
```bash
sudo systemctl start docker
```

### Issue: "Port 80 already in use"

Find what's using it:
```bash
# Windows
netstat -ano | findstr :80

# Mac/Linux
lsof -i :80
```

Kill the process or change port in docker-compose.yaml:
```yaml
frontend:
  ...
  ports:
    - "8080:80"  # Changed from 80:80
```

Then restart:
```bash
docker-compose restart frontend
```

Access at: **http://localhost:8080**

### Issue: Frontend shows blank page / 404

```bash
# Check logs
docker-compose logs frontend

# Rebuild
docker-compose build --no-cache frontend
docker-compose up -d frontend

# Wait 1 minute, then refresh browser
```

### Issue: "Cannot GET /api/..."

Backend API issue:
```bash
# Check backend
docker-compose logs backend

# Restart
docker-compose restart backend

# Test directly
curl http://localhost:3001/api/scraped-data/stats
```

### Issue: Database error "relation does not exist"

Table not created:
```bash
docker exec -it postgres psql -U airflow -d airflow

# Create table (see Step 7 above)
CREATE TABLE IF NOT EXISTS scraped_properties ...
```

### Issue: "Connection refused" on 3001

Backend not running:
```bash
docker-compose ps backend

# Should show "Up" status
# If not:
docker-compose logs backend
docker-compose restart backend
```

### Issue: Nothing works after `docker-compose up`

Full reset:
```bash
# Stop everything
docker-compose down -v

# Create volume fresh
docker volume create etl_postgres-db-volume

# Full rebuild
docker-compose build --no-cache

# Start fresh
docker-compose up -d

# Wait 3 minutes
docker-compose ps

# All should show "Up"
```

---

## 📊 Performance Tips

### Docker Resources (Windows/Mac)

1. Open Docker Desktop
2. Click Settings ⚙️
3. **Resources** tab
4. Allocate:
   - **Memory**: 4GB minimum (8GB recommended)
   - **CPUs**: 2+ cores
5. Click **Apply & Restart**

### First Run Takes Time

Expected timeline:
- `docker-compose build`: 5-10 minutes
- `docker-compose up -d`: 2-3 minutes
- First database query: 5-10 seconds
- Subsequent queries: < 1 second

### Optimize Images

After first run:
```bash
# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Check disk usage
docker system df
```

---

## ✅ Success Checklist

- [ ] Docker installed and running
- [ ] Volume created: `etl_postgres-db-volume`
- [ ] `docker-compose build` completed
- [ ] `docker-compose up -d` completed
- [ ] All containers showing "Up" in `docker-compose ps`
- [ ] http://localhost loads dashboard
- [ ] Scraper Management page visible
- [ ] Data Analytics page has statistics and charts
- [ ] Database table created
- [ ] Backend API responds to requests
- [ ] Can trigger ETL pipeline (or see error)

---

## 🚀 Next Steps After Installation

1. ✅ Verify everything works (see Testing section)
2. Add real scrapers to the Tayara scraper
3. Configure Airflow DAG scheduling
4. Connect real data pipeline
5. Add authentication to admin dashboard
6. Deploy to production servers

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Start all | `docker-compose up -d` |
| Stop all | `docker-compose stop` |
| View logs | `docker-compose logs -f` |
| Check status | `docker-compose ps` |
| Restart service | `docker-compose restart frontend` |
| Full rebuild | `docker-compose down -v && docker volume create etl_postgres-db-volume && docker-compose up -d --build` |
| Connect to DB | `docker exec -it postgres psql -U airflow -d airflow` |
| Shell in frontend | `docker exec -it estateMind-frontend /bin/sh` |
| Test backend | `curl http://localhost:3001/api/scraped-data/stats` |

---

## 📚 Additional Resources

- [Docker Docs](https://docs.docker.com/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Airflow Docs](https://airflow.apache.org/)

---

**You're all set! 🎉**

Your EstateMind Admin Dashboard is now ready to use!
