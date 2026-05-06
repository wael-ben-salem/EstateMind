import { Box, Chip, Stack, Typography } from '@mui/material';
import { useMemo } from 'react';
import { usePipelineStore } from '@/features/pipeline/state/pipelineStore';

function computeHealth(score: number) {
  if (score >= 80) return { label: 'Healthy', color: 'success' as const };
  if (score >= 50) return { label: 'Degraded', color: 'warning' as const };
  return { label: 'At risk', color: 'error' as const };
}

export function PipelineHealthGauge() {
  const { lastRunState, lastRunScore } = usePipelineStore();
  const health = useMemo(() => computeHealth(lastRunScore), [lastRunScore]);

  return (
    <Stack spacing={1} sx={{ minWidth: 220 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'flex-end' }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
          Pipeline health
        </Typography>
        <Chip size="small" label={health.label} color={health.color} />
      </Stack>

      <Box
        sx={{
          height: 10,
          width: 220,
          borderRadius: 999,
          backgroundColor: 'rgba(15,23,42,0.08)',
          overflow: 'hidden',
          ml: 'auto'
        }}
      >
        <Box
          sx={{
            height: '100%',
            width: `${Math.max(0, Math.min(100, lastRunScore))}%`,
            backgroundColor:
              health.color === 'success' ? '#10b981' : health.color === 'warning' ? '#f59e0b' : '#ef4444'
          }}
        />
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'right' }}>
        Dernier run: {lastRunState || 'n/a'} — score {lastRunScore}/100
      </Typography>
    </Stack>
  );
}

