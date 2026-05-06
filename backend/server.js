const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL ||
    'postgresql://airflow:airflow@postgres:5432/airflow',
});

const AIRFLOW_BASE_URL =
  process.env.AIRFLOW_API_URL || 'http://airflow:8080/api/v1';

const AIRFLOW_DAG_ID =
  process.env.AIRFLOW_DAG_ID || 'tayara_ai_agent_pipeline';

const AIRFLOW_USERNAME = process.env.AIRFLOW_USERNAME || 'admin';
const AIRFLOW_PASSWORD = process.env.AIRFLOW_PASSWORD || 'admin';

// Axios instance with retry logic
const axiosInstance = axios.create({
  timeout: 10000,
});

// Add retry interceptor
axiosInstance.interceptors.response.use(null, async (error) => {
  const config = error.config;
  
  if (!config || !config.retry) {
    config.retry = 0;
  }
  
  config.retry += 1;
  
  if (config.retry <= 3 && (error.message.includes('ECONNREFUSED') || error.message.includes('ETIMEDOUT'))) {
    console.log(`[RETRY] Attempt ${config.retry}/3 for ${config.url}`);
    await new Promise(resolve => setTimeout(resolve, 2000));
    return axiosInstance(config);
  }
  
  return Promise.reject(error);
});

// Log configuration on startup
console.log('[STARTUP] Airflow Config:', {
  baseUrl: AIRFLOW_BASE_URL,
  dagId: AIRFLOW_DAG_ID,
  username: AIRFLOW_USERNAME,
  authenticated: !!AIRFLOW_USERNAME
});

app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ status: 'OK' });
});

app.get('/health/airflow', async (req, res) => {
  try {
    const response = await axiosInstance.get(
      `${AIRFLOW_BASE_URL}/health`,
      {
        auth: {
          username: AIRFLOW_USERNAME,
          password: AIRFLOW_PASSWORD,
        },
      }
    );
    res.json({ status: 'OK', airflow: response.data });
  } catch (error) {
    console.error('[HEALTH] Airflow not ready:', error.message);
    res.status(503).json({ 
      status: 'UNAVAILABLE', 
      error: 'Airflow is not ready yet',
      message: error.message 
    });
  }
});

/* =========================
   SOURCES
========================= */
app.get('/api/etl/sources', (req, res) => {
  res.json([
    {
      id: 'tayara',
      name: 'Tayara',
      description: 'Active source available for scraping.',
      url: 'https://www.tayara.tn',
      locked: false,
    },
    {
      id: 'mubawab',
      name: 'Mubawab',
      description: 'Upcoming source integration.',
      locked: true,
    },
    {
      id: 'tunisie-annonce',
      name: 'Tunisie Annonce',
      description: 'Upcoming source integration.',
      locked: true,
    },
    {
      id: 'facebook-marketplace',
      name: 'Facebook Marketplace',
      description: 'Upcoming source integration.',
      locked: true,
    },
    {
      id: 'real-estate-agencies',
      name: 'Agency Websites',
      description: 'Upcoming source integration.',
      locked: true,
    },
  ]);
});

/* =========================
   AIRFLOW / DAG
========================= */
app.post('/api/etl/trigger', async (req, res) => {
  try {
    console.log('[TRIGGER] Starting DAG trigger request...');
    console.log('[TRIGGER] URL:', `${AIRFLOW_BASE_URL}/dags/${AIRFLOW_DAG_ID}/dagRuns`);
    
    const response = await axiosInstance.post(
      `${AIRFLOW_BASE_URL}/dags/${AIRFLOW_DAG_ID}/dagRuns`,
      { conf: {} },
      {
        headers: { 'Content-Type': 'application/json' },
        auth: {
          username: AIRFLOW_USERNAME,
          password: AIRFLOW_PASSWORD,
        },
      }
    );

    console.log('[TRIGGER] Success! DAG Run ID:', response.data.dag_run_id);
    res.json(response.data);
  } catch (error) {
    console.error('[TRIGGER] Error:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message,
    });
    res.status(500).json({
      error: 'Failed to trigger DAG',
      details: error.response?.data || error.message,
    });
  }
});

app.get('/api/etl/runs/:runId/status', async (req, res) => {
  try {
    const { runId } = req.params;

    const dagRunRes = await axiosInstance.get(
      `${AIRFLOW_BASE_URL}/dags/${AIRFLOW_DAG_ID}/dagRuns/${runId}`,
      {
        auth: {
          username: AIRFLOW_USERNAME,
          password: AIRFLOW_PASSWORD,
        },
      }
    );

    const taskRes = await axiosInstance.get(
      `${AIRFLOW_BASE_URL}/dags/${AIRFLOW_DAG_ID}/dagRuns/${runId}/taskInstances`,
      {
        auth: {
          username: AIRFLOW_USERNAME,
          password: AIRFLOW_PASSWORD,
        },
      }
    );

    res.json({
      state: dagRunRes.data.state,
      run_id: dagRunRes.data.dag_run_id,
      steps: (taskRes.data.task_instances || []).map((task) => ({
        task_id: task.task_id,
        state: task.state,
        start_date: task.start_date,
        end_date: task.end_date,
        duration: task.duration,
      })),
    });
  } catch (error) {
    console.error('DAG status error:', error.response?.data || error.message);
    res.status(500).json({
      error: 'Failed to fetch DAG status',
      details: error.response?.data || error.message,
    });
  }
});

/* =========================
   ANALYTICS
========================= */

// Summary cards
app.get('/api/scraped-data/stats', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        COUNT(*) AS total_properties,
        COUNT(DISTINCT ville) AS unique_locations,
        COUNT(DISTINCT COALESCE(type_bien_extrait, 'Unknown')) AS property_types,
        ROUND(AVG(price_num)::numeric, 2) AS avg_price
      FROM clean_tayara
      WHERE price_num IS NOT NULL
    `);

    const row = result.rows[0];

    res.json({
      totalProperties: parseInt(row.total_properties || 0, 10),
      uniqueLocations: parseInt(row.unique_locations || 0, 10),
      propertyTypes: parseInt(row.property_types || 0, 10),
      avgPrice: parseFloat(row.avg_price || 0),
    });
  } catch (error) {
    console.error('Stats error:', error);
    res.status(500).json({ error: 'Failed to fetch statistics' });
  }
});

// By city
app.get('/api/scraped-data/locations', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT ville AS location, COUNT(*) AS count
      FROM clean_tayara
      WHERE ville IS NOT NULL
      GROUP BY ville
      ORDER BY count DESC
      LIMIT 10
    `);

    res.json(
      result.rows.map((row) => ({
        location: row.location,
        count: parseInt(row.count, 10),
      }))
    );
  } catch (error) {
    console.error('Locations error:', error);
    res.status(500).json({ error: 'Failed to fetch locations' });
  }
});

// By property type
app.get('/api/scraped-data/property-types', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT COALESCE(type_bien_extrait, 'Unknown') AS name, COUNT(*) AS value
      FROM clean_tayara
      GROUP BY COALESCE(type_bien_extrait, 'Unknown')
      ORDER BY value DESC
    `);

    res.json(
      result.rows.map((row) => ({
        name: row.name,
        value: parseInt(row.value, 10),
      }))
    );
  } catch (error) {
    console.error('Property types error:', error);
    res.status(500).json({ error: 'Failed to fetch property types' });
  }
});

// By transaction type
app.get('/api/scraped-data/transactions', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT COALESCE(transaction_type_final, 'Unknown') AS name, COUNT(*) AS value
      FROM clean_tayara
      GROUP BY COALESCE(transaction_type_final, 'Unknown')
      ORDER BY value DESC
    `);

    res.json(
      result.rows.map((row) => ({
        name: row.name,
        value: parseInt(row.value, 10),
      }))
    );
  } catch (error) {
    console.error('Transactions error:', error);
    res.status(500).json({ error: 'Failed to fetch transaction types' });
  }
});

// Price distribution
app.get('/api/scraped-data/prices', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        CASE
          WHEN price_num < 100000 THEN '<100K'
          WHEN price_num < 300000 THEN '100K-300K'
          WHEN price_num < 600000 THEN '300K-600K'
          WHEN price_num < 1000000 THEN '600K-1M'
          ELSE '>1M'
        END AS range,
        COUNT(*) AS count
      FROM clean_tayara
      WHERE price_num IS NOT NULL
      GROUP BY range
      ORDER BY
        CASE range
          WHEN '<100K' THEN 1
          WHEN '100K-300K' THEN 2
          WHEN '300K-600K' THEN 3
          WHEN '600K-1M' THEN 4
          WHEN '>1M' THEN 5
        END
    `);

    res.json(
      result.rows.map((row) => ({
        range: row.range,
        count: parseInt(row.count, 10),
      }))
    );
  } catch (error) {
    console.error('Prices error:', error);
    res.status(500).json({ error: 'Failed to fetch price distribution' });
  }
});

// Average price by city
app.get('/api/scraped-data/avg-price-city', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT ville AS city, ROUND(AVG(price_num)::numeric, 2) AS avg_price
      FROM clean_tayara
      WHERE ville IS NOT NULL AND price_num IS NOT NULL
      GROUP BY ville
      ORDER BY avg_price DESC
      LIMIT 10
    `);

    res.json(
      result.rows.map((row) => ({
        city: row.city,
        avgPrice: parseFloat(row.avg_price),
      }))
    );
  } catch (error) {
    console.error('Avg price by city error:', error);
    res.status(500).json({ error: 'Failed to fetch average price by city' });
  }
});

app.listen(PORT, () => {
  console.log(`Backend server running on port ${PORT}`);
});

process.on('SIGTERM', async () => {
  await pool.end();
  process.exit(0);
});