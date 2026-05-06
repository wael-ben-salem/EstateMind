import { Alert, Box, Button, Card, CardContent, CircularProgress, Stack, Typography } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { useEffect, useMemo, useState } from 'react';

import { estateMindApi, PipelineStatus } from '@/shared/api/estateMindApi';
import { PageHeader } from '@/shared/ui/PageHeader';
import { usePipelineStore } from '@/features/pipeline/state/pipelineStore';
import { sleep } from '@/shared/utils/sleep';

function scoreFromStatus(status: PipelineStatus) {
  const steps = status.steps || [];
  if (steps.length === 0) return 50;
  const ok = steps.filter((s) => s.state === 'success').length;
  const failed = steps.filter((s) => s.state === 'failed').length;
  const base = Math.round((ok / steps.length) * 100);
  return Math.max(0, Math.min(100, base - failed * 10));
}

export function PipelineRunPanel() {
  const store = usePipelineStore();
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pill = useMemo(() => {
    if (!status) return undefined;
    if (status.state === 'success') return { label: 'success', color: 'success' as const };
    if (status.state === 'failed') return { label: 'failed', color: 'error' as const };
    return { label: status.state, color: 'warning' as const };
  }, [status]);

  async function trigger() {
    setError(null);
    setRunning(true);
    setStatus(null);
    try {
      const res = await estateMindApi.triggerPipeline();
      store.setLastRun({ runId: res.dag_run_id, state: res.state || 'queued', score: 50 });
      await poll(res.dag_run_id);
    } catch (e: any) {
      setError(e?.message || 'Trigger failed');
      setRunning(false);
    }
  }

  async function poll(runId: string) {
    for (;;) {
      const s = await estateMindApi.pipelineStatus(runId);
      setStatus(s);
      store.setLastRun({ runId, state: s.state, score: scoreFromStatus(s) });

      if (s.state === 'success' || s.state === 'failed') {
        setRunning(false);
        break;
      }
      await sleep(3000);
    }
  }

  useEffect(() => {
    // keep last known run on reload if desired (future: persisted store)
  }, []);

  return (
    <Card>
      <CardContent>
        <PageHeader
          title="Pipeline Monitor"
          subtitle="Trigger + suivi step-by-step (API existante: /api/etl/*)."
          statusPill={pill}
          right={
            <Button
              variant="contained"
              startIcon={running ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon />}
              onClick={trigger}
              disabled={running}
            >
              {running ? 'Running…' : 'Trigger pipeline'}
            </Button>
          }
        />

        {error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : null}

        {!status ? (
          <Box sx={{ py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              Aucun run sélectionné. Clique sur “Trigger pipeline”.
            </Typography>
          </Box>
        ) : (
          <Stack spacing={1.25}>
            {(status.steps || []).map((step) => (
              <Box
                key={step.task_id}
                sx={{
                  p: 1.25,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 2,
                  backgroundColor: 'background.paper'
                }}
              >
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ fontWeight: 800 }}>
                    {step.task_id}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                    {step.state || 'unknown'} {step.duration ? `• ${Math.round(step.duration)}s` : ''}
                  </Typography>
                </Stack>
              </Box>
            ))}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}

