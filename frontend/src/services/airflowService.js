const API_BASE_URL = '/api/etl';

export const airflowService = {
  getSources: async () => {
    const response = await fetch(`${API_BASE_URL}/sources`);
    if (!response.ok) throw new Error('Failed to fetch sources');
    return await response.json();
  },

  triggerPipeline: async () => {
    const response = await fetch(`${API_BASE_URL}/trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('[SERVICE] Trigger error:', errorData);
      throw new Error(errorData.details || errorData.error || 'Failed to trigger pipeline');
    }
    return await response.json();
  },

  getPipelineStatus: async (dagRunId) => {
    const response = await fetch(`${API_BASE_URL}/runs/${dagRunId}/status`);
    if (!response.ok) throw new Error('Failed to fetch pipeline status');
    return await response.json();
  },
};