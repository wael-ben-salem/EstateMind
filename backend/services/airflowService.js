const axios = require("axios");

const DAG_ID = "tayara_ai_agent_pipeline";

function client() {
  return axios.create({
    baseURL: process.env.AIRFLOW_API_URL || "http://localhost:8081/api/v1",
    auth: {
      username: process.env.AIRFLOW_USER || "airflow",
      password: process.env.AIRFLOW_PASSWORD || "airflow",
    },
    timeout: 10000,
  });
}

async function getDagRuns(limit = 30) {
  const { data } = await client().get(
    `/dags/${DAG_ID}/dagRuns?limit=${limit}&order_by=-start_date`
  );
  return data;
}

async function triggerDag() {
  const { data } = await client().post(`/dags/${DAG_ID}/dagRuns`, {
    conf: {},
  });
  return data;
}

async function getTaskInstances(runId) {
  const { data } = await client().get(
    `/dags/${DAG_ID}/dagRuns/${runId}/taskInstances`
  );
  return data;
}

async function getTaskLogs(runId, taskId) {
  const { data } = await client().get(
    `/dags/${DAG_ID}/dagRuns/${runId}/taskInstances/${taskId}/logs/1`
  );
  return data;
}

async function getPipelineStatus() {
  try {
    const runs = await getDagRuns(1);
    const latest = runs.dag_runs?.[0] || null;
    return {
      is_running: latest?.state === "running",
      last_run: latest?.start_date || null,
      next_run: null,
      current_step: latest?.state || "unknown",
      last_run_id: latest?.dag_run_id || null,
    };
  } catch {
    return { is_running: false, last_run: null, next_run: null, current_step: "airflow_unreachable" };
  }
}

module.exports = { getDagRuns, triggerDag, getTaskInstances, getTaskLogs, getPipelineStatus };
