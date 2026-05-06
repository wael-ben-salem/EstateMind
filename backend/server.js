const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Database connection - OBLIGATOIRE
const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL ||
    'postgresql://airflow:airflow@postgres:5432/airflow',
});

pool.on('error', (err) => {
  console.error('[DB] Unexpected error on idle client', err);
});

const AIRFLOW_BASE_URL =
  process.env.AIRFLOW_API_URL || 'http://airflow:8080/api/v1';
const AIRFLOW_DAG_ID =
  process.env.AIRFLOW_DAG_ID || 'tayara_ai_agent_pipeline';
const AIRFLOW_USERNAME = process.env.AIRFLOW_USERNAME || 'admin';
const AIRFLOW_PASSWORD = process.env.AIRFLOW_PASSWORD || 'admin';

console.log('[STARTUP] Configuration:', {
  port: PORT,
  db: process.env.DATABASE_URL ? 'Configured' : 'Default',
  airflow: AIRFLOW_BASE_URL,
  dag: AIRFLOW_DAG_ID
});

app.use(cors());
app.use(express.json());

// ============================================
// HEALTH
// ============================================
app.get('/api/health', async (req, res) => {
  try {
    const dbCheck = await pool.query('SELECT 1 AS ok');
    res.json({ 
      status: 'OK', 
      timestamp: new Date().toISOString(),
      database: dbCheck.rows[0].ok === 1 ? 'connected' : 'error'
    });
  } catch (error) {
    res.status(503).json({ status: 'ERROR', database: 'disconnected', error: error.message });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'OK' });
});

// ============================================
// STATS GÉNÉRALES (données réelles)
// ============================================
app.get('/api/scraped-data/stats', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        COUNT(*) AS total_listings,
        COUNT(DISTINCT ville) AS unique_locations,
        COUNT(DISTINCT COALESCE(type_bien_extrait, 'Unknown')) AS property_types,
        ROUND(AVG(price_num)::numeric, 2) AS avg_price,
        ROUND(AVG(superficie_num)::numeric, 2) AS avg_surface,
        ROUND(AVG(price_per_m2)::numeric, 2) AS avg_price_m2,
        MIN(price_num) AS min_price,
        MAX(price_num) AS max_price,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_num) AS median_price
      FROM clean_tayara
      WHERE price_num IS NOT NULL AND price_num > 0
    `);

    const row = result.rows[0];
    
    // Nouvelles annonces aujourd'hui
    const newToday = await pool.query(`
      SELECT COUNT(*) AS count
      FROM clean_tayara
      WHERE date_annonce >= CURRENT_DATE
    `);

    // Nouvelles cette semaine
    const newWeek = await pool.query(`
      SELECT COUNT(*) AS count
      FROM clean_tayara
      WHERE date_annonce >= CURRENT_DATE - INTERVAL '7 days'
    `);

    res.json({
      total_listings: parseInt(row.total_listings || 0),
      totalProperties: parseInt(row.total_listings || 0),
      unique_locations: parseInt(row.unique_locations || 0),
      uniqueLocations: parseInt(row.unique_locations || 0),
      property_types: parseInt(row.property_types || 0),
      propertyTypes: parseInt(row.property_types || 0),
      avg_price: parseFloat(row.avg_price || 0),
      avgPrice: parseFloat(row.avg_price || 0),
      avg_surface: parseFloat(row.avg_surface || 0),
      avgSurface: parseFloat(row.avg_surface || 0),
      avg_price_m2: parseFloat(row.avg_price_m2 || 0),
      avgPriceM2: parseFloat(row.avg_price_m2 || 0),
      min_price: parseFloat(row.min_price || 0),
      minPrice: parseFloat(row.min_price || 0),
      max_price: parseFloat(row.max_price || 0),
      maxPrice: parseFloat(row.max_price || 0),
      median_price: parseFloat(row.median_price || 0),
      medianPrice: parseFloat(row.median_price || 0),
      new_today: parseInt(newToday.rows[0]?.count || 0),
      newToday: parseInt(newToday.rows[0]?.count || 0),
      new_this_week: parseInt(newWeek.rows[0]?.count || 0),
      newThisWeek: parseInt(newWeek.rows[0]?.count || 0)
    });
  } catch (error) {
    console.error('[STATS] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch statistics', details: error.message });
  }
});

// ============================================
// PRIX MOYEN PAR VILLE
// ============================================
app.get('/api/scraped-data/avg-price-city', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        ville AS city, 
        ROUND(AVG(price_num)::numeric, 2) AS avg_price,
        ROUND(AVG(price_per_m2)::numeric, 2) AS avg_price_m2,
        COUNT(*) AS count,
        MIN(price_num) AS min_price,
        MAX(price_num) AS max_price
      FROM clean_tayara
      WHERE ville IS NOT NULL 
        AND price_num IS NOT NULL 
        AND price_num > 0
      GROUP BY ville
      HAVING COUNT(*) >= 5
      ORDER BY avg_price DESC
      LIMIT 20
    `);

    res.json(result.rows.map(row => ({
      city: row.city,
      avg_price: parseFloat(row.avg_price),
      avgPrice: parseFloat(row.avg_price),
      avg_price_m2: parseFloat(row.avg_price_m2),
      avgPriceM2: parseFloat(row.avg_price_m2),
      count: parseInt(row.count),
      min_price: parseFloat(row.min_price),
      minPrice: parseFloat(row.min_price),
      max_price: parseFloat(row.max_price),
      maxPrice: parseFloat(row.max_price)
    })));
  } catch (error) {
    console.error('[AVG PRICE CITY] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch average prices by city', details: error.message });
  }
});

// ============================================
// DISTRIBUTION DES PRIX
// ============================================
app.get('/api/scraped-data/prices', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        CASE
          WHEN price_num < 50000 THEN '<50K'
          WHEN price_num < 100000 THEN '50K-100K'
          WHEN price_num < 200000 THEN '100K-200K'
          WHEN price_num < 300000 THEN '200K-300K'
          WHEN price_num < 500000 THEN '300K-500K'
          WHEN price_num < 1000000 THEN '500K-1M'
          ELSE '>1M'
        END AS range,
        COUNT(*) AS count,
        ROUND(AVG(price_num)::numeric, 2) AS avg_price
      FROM clean_tayara
      WHERE price_num IS NOT NULL AND price_num > 0
      GROUP BY range
      ORDER BY
        CASE range
          WHEN '<50K' THEN 1
          WHEN '50K-100K' THEN 2
          WHEN '100K-200K' THEN 3
          WHEN '200K-300K' THEN 4
          WHEN '300K-500K' THEN 5
          WHEN '500K-1M' THEN 6
          WHEN '>1M' THEN 7
        END
    `);

    res.json(result.rows.map(row => ({
      range: row.range,
      count: parseInt(row.count),
      avg_price: parseFloat(row.avg_price)
    })));
  } catch (error) {
    console.error('[PRICES] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch price distribution', details: error.message });
  }
});

// ============================================
// TYPES DE BIENS
// ============================================
app.get('/api/scraped-data/property-types', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        COALESCE(type_bien_extrait, 'Non spécifié') AS name, 
        COUNT(*) AS value,
        ROUND(AVG(price_num)::numeric, 2) AS avg_price,
        ROUND(AVG(price_per_m2)::numeric, 2) AS avg_price_m2
      FROM clean_tayara
      GROUP BY COALESCE(type_bien_extrait, 'Non spécifié')
      ORDER BY value DESC
    `);

    res.json(result.rows.map(row => ({
      name: row.name,
      value: parseInt(row.value),
      avg_price: parseFloat(row.avg_price || 0),
      avg_price_m2: parseFloat(row.avg_price_m2 || 0)
    })));
  } catch (error) {
    console.error('[PROPERTY TYPES] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch property types', details: error.message });
  }
});

// ============================================
// TYPES DE TRANSACTIONS
// ============================================
app.get('/api/scraped-data/transactions', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        COALESCE(transaction_type_final, 'Non spécifié') AS name, 
        COUNT(*) AS value,
        ROUND(AVG(price_num)::numeric, 2) AS avg_price
      FROM clean_tayara
      GROUP BY COALESCE(transaction_type_final, 'Non spécifié')
      ORDER BY value DESC
    `);

    res.json(result.rows.map(row => ({
      name: row.name,
      value: parseInt(row.value),
      avg_price: parseFloat(row.avg_price || 0)
    })));
  } catch (error) {
    console.error('[TRANSACTIONS] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch transactions', details: error.message });
  }
});

// ============================================
// TOP LOCATIONS
// ============================================
app.get('/api/scraped-data/locations', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        ville AS location, 
        COUNT(*) AS count,
        ROUND(AVG(price_num)::numeric, 2) AS avg_price,
        ROUND(AVG(price_per_m2)::numeric, 2) AS avg_price_m2
      FROM clean_tayara
      WHERE ville IS NOT NULL
      GROUP BY ville
      ORDER BY count DESC
      LIMIT 15
    `);

    res.json(result.rows.map(row => ({
      location: row.location,
      count: parseInt(row.count),
      avg_price: parseFloat(row.avg_price || 0),
      avg_price_m2: parseFloat(row.avg_price_m2 || 0)
    })));
  } catch (error) {
    console.error('[LOCATIONS] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch locations', details: error.message });
  }
});

// ============================================
// DONNÉES BRUTES (pour le tableau)
// ============================================
app.get('/api/scraped-data/raw', async (req, res) => {
  try {
    const { limit = 50, offset = 0, ville, type_bien, transaction_type } = req.query;
    
    let query = `
      SELECT 
        id, title, ville, price_num, superficie_num, price_per_m2,
        type_bien_extrait, transaction_type_final, date_annonce,
        description, nb_pieces, nb_salles_bain, etage
      FROM clean_tayara
      WHERE 1=1
    `;
    const params = [];
    let paramCount = 0;

    if (ville) {
      paramCount++;
      query += ` AND LOWER(ville) LIKE LOWER($${paramCount})`;
      params.push(`%${ville}%`);
    }
    if (type_bien) {
      paramCount++;
      query += ` AND LOWER(type_bien_extrait) = LOWER($${paramCount})`;
      params.push(type_bien);
    }
    if (transaction_type) {
      paramCount++;
      query += ` AND LOWER(transaction_type_final) = LOWER($${paramCount})`;
      params.push(transaction_type);
    }

    // Count total
    const countResult = await pool.query(
      `SELECT COUNT(*) FROM (${query}) AS filtered`,
      params
    );
    const total = parseInt(countResult.rows[0].count);

    // Paginated data
    paramCount++;
    query += ` ORDER BY date_annonce DESC NULLS LAST LIMIT $${paramCount}`;
    params.push(parseInt(limit));
    paramCount++;
    query += ` OFFSET $${paramCount}`;
    params.push(parseInt(offset));

    const result = await pool.query(query, params);

    res.json({
      data: result.rows,
      total,
      limit: parseInt(limit),
      offset: parseInt(offset)
    });
  } catch (error) {
    console.error('[RAW DATA] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch raw data', details: error.message });
  }
});

// ============================================
// ANALYTIQUES AVANCÉES
// ============================================
app.get('/api/analytics/market-trends', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        DATE_TRUNC('month', date_annonce) AS month,
        COUNT(*) AS listings,
        ROUND(AVG(price_num)::numeric, 2) AS avg_price,
        ROUND(AVG(price_per_m2)::numeric, 2) AS avg_price_m2,
        ROUND(AVG(superficie_num)::numeric, 2) AS avg_surface
      FROM clean_tayara
      WHERE date_annonce IS NOT NULL
        AND price_num IS NOT NULL
        AND price_num > 0
      GROUP BY DATE_TRUNC('month', date_annonce)
      ORDER BY month DESC
      LIMIT 12
    `);

    res.json(result.rows);
  } catch (error) {
    console.error('[MARKET TRENDS] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch market trends', details: error.message });
  }
});

app.get('/api/analytics/price-by-surface', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        superficie_num AS surface,
        price_num AS price,
        price_per_m2,
        ville AS city,
        type_bien_extrait AS property_type
      FROM clean_tayara
      WHERE superficie_num IS NOT NULL
        AND price_num IS NOT NULL
        AND superficie_num > 0
        AND price_num > 0
        AND superficie_num < 1000
      ORDER BY superficie_num
      LIMIT 1000
    `);

    res.json(result.rows);
  } catch (error) {
    console.error('[PRICE BY SURFACE] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch price by surface', details: error.message });
  }
});

// ============================================
// AIRFLOW / ETL ENDPOINTS
// ============================================
app.get('/api/etl/sources', (req, res) => {
  res.json([
    { id: 'tayara', name: 'Tayara', description: 'Active source', url: 'https://www.tayara.tn', locked: false },
    { id: 'mubawab', name: 'Mubawab', description: 'Coming soon', locked: true },
    { id: 'tunisie-annonce', name: 'Tunisie Annonce', description: 'Coming soon', locked: true },
  ]);
});

app.post('/api/etl/trigger', async (req, res) => {
  try {
    const response = await axios.post(
      `${AIRFLOW_BASE_URL}/dags/${AIRFLOW_DAG_ID}/dagRuns`,
      { conf: {} },
      {
        headers: { 'Content-Type': 'application/json' },
        auth: { username: AIRFLOW_USERNAME, password: AIRFLOW_PASSWORD },
        timeout: 10000
      }
    );
    res.json(response.data);
  } catch (error) {
    console.error('[TRIGGER] Error:', error.message);
    res.status(500).json({ error: 'Failed to trigger DAG', details: error.message });
  }
});

app.get('/api/etl/runs/:runId/status', async (req, res) => {
  try {
    const { runId } = req.params;
    const [dagRunRes, taskRes] = await Promise.all([
      axios.get(`${AIRFLOW_BASE_URL}/dags/${AIRFLOW_DAG_ID}/dagRuns/${runId}`, {
        auth: { username: AIRFLOW_USERNAME, password: AIRFLOW_PASSWORD }
      }),
      axios.get(`${AIRFLOW_BASE_URL}/dags/${AIRFLOW_DAG_ID}/dagRuns/${runId}/taskInstances`, {
        auth: { username: AIRFLOW_USERNAME, password: AIRFLOW_PASSWORD }
      })
    ]);

    res.json({
      state: dagRunRes.data.state,
      run_id: dagRunRes.data.dag_run_id,
      steps: (taskRes.data.task_instances || []).map(task => ({
        task_id: task.task_id,
        state: task.state,
        start_date: task.start_date,
        end_date: task.end_date,
        duration: task.duration
      }))
    });
  } catch (error) {
    console.error('[RUN STATUS] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch run status', details: error.message });
  }
});

// ============================================
// QUALITÉ DES DONNÉES
// ============================================
app.get('/api/quality/report', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT
        COUNT(*) AS total_records,
        COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END) * 100.0 / COUNT(*) AS title_completeness,
        COUNT(CASE WHEN price_num IS NOT NULL AND price_num > 0 THEN 1 END) * 100.0 / COUNT(*) AS price_completeness,
        COUNT(CASE WHEN ville IS NOT NULL AND ville != '' THEN 1 END) * 100.0 / COUNT(*) AS city_completeness,
        COUNT(CASE WHEN superficie_num IS NOT NULL AND superficie_num > 0 THEN 1 END) * 100.0 / COUNT(*) AS surface_completeness,
        COUNT(CASE WHEN type_bien_extrait IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) AS type_completeness,
        COUNT(CASE WHEN price_per_m2 IS NOT NULL AND price_per_m2 > 0 THEN 1 END) * 100.0 / COUNT(*) AS price_m2_completeness
      FROM clean_tayara
    `);

    res.json(result.rows[0]);
  } catch (error) {
    console.error('[QUALITY] Error:', error.message);
    res.status(500).json({ error: 'Failed to fetch quality report', details: error.message });
  }
});

// ============================================
// START SERVER
// ============================================
app.listen(PORT, () => {
  console.log(`✅ Backend server running on http://localhost:${PORT}`);
  console.log(`📊 API endpoints:`);
  console.log(`   GET /api/health`);
  console.log(`   GET /api/scraped-data/stats`);
  console.log(`   GET /api/scraped-data/avg-price-city`);
  console.log(`   GET /api/scraped-data/prices`);
  console.log(`   GET /api/scraped-data/property-types`);
  console.log(`   GET /api/scraped-data/transactions`);
  console.log(`   GET /api/scraped-data/locations`);
  console.log(`   GET /api/scraped-data/raw`);
  console.log(`   GET /api/analytics/market-trends`);
  console.log(`   GET /api/analytics/price-by-surface`);
  console.log(`   GET /api/quality/report`);
  console.log(`   POST /api/etl/trigger`);
});

process.on('SIGTERM', async () => {
  console.log('Shutting down...');
  await pool.end();
  process.exit(0);
});