import { Card, CardContent, Stack, Typography } from '@mui/material';
import { ReactNode } from 'react';

export function KpiCard(props: {
  label: string;
  value: string;
  helper?: string;
  icon?: ReactNode;
  trend?: { deltaLabel: string; direction: 'up' | 'down' | 'flat' };
}) {
  const trendColor =
    props.trend?.direction === 'up' ? '#10b981' : props.trend?.direction === 'down' ? '#ef4444' : '#64748b';

  return (
    <Card>
      <CardContent>
        <Stack direction="row" spacing={2} sx={{ alignItems: 'flex-start' }}>
          <Stack spacing={0.75} sx={{ flex: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700, letterSpacing: 0.2 }}>
              {props.label}
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 900 }}>
              {props.value}
            </Typography>
            {props.helper ? (
              <Typography variant="body2" color="text.secondary">
                {props.helper}
              </Typography>
            ) : null}
            {props.trend ? (
              <Typography variant="caption" sx={{ fontWeight: 800, color: trendColor }}>
                {props.trend.deltaLabel}
              </Typography>
            ) : null}
          </Stack>
          {props.icon ? <Stack sx={{ opacity: 0.9 }}>{props.icon}</Stack> : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

