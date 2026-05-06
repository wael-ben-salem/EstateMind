import { Box, Card, CardContent, Skeleton, Stack, Typography } from '@mui/material';
import { ReactNode, useEffect, useMemo, useState } from 'react';

function useAnimatedNumber(target: number, durationMs = 900) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    const start = performance.now();
    const from = value;
    const diff = target - from;

    let raf = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(from + diff * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target]);

  return value;
}

export function HeroKPI(props: {
  title: string;
  subtitle: string;
  value: number;
  valueLabel: string;
  loading?: boolean;
  error?: string | null;
  right?: ReactNode;
}) {
  const animated = useAnimatedNumber(props.value);

  const gradient = useMemo(
    () =>
      `radial-gradient(1200px circle at 20% 0%, rgba(59,130,246,0.22), transparent 55%),
       radial-gradient(900px circle at 80% 30%, rgba(16,185,129,0.18), transparent 60%),
       linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255,255,255,0.72))`,
    [],
  );

  return (
    <Card sx={{ position: 'relative', overflow: 'hidden' }}>
      <Box
        sx={{
          position: 'absolute',
          inset: 0,
          background: gradient
        }}
      />
      <CardContent sx={{ position: 'relative' }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ alignItems: { md: 'center' } }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 800 }}>
              {props.subtitle}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 900, mt: 0.25 }}>
              {props.title}
            </Typography>
            <Box sx={{ mt: 1.25 }}>
              {props.loading ? (
                <Skeleton variant="text" width={220} height={48} />
              ) : props.error ? (
                <Typography variant="h6" color="error" sx={{ fontWeight: 800 }}>
                  {props.error}
                </Typography>
              ) : (
                <Stack direction="row" spacing={1} sx={{ alignItems: 'baseline' }}>
                  <Typography variant="h3" sx={{ fontWeight: 950, letterSpacing: -0.5 }}>
                    {animated.toLocaleString('fr-TN')}
                  </Typography>
                  <Typography variant="subtitle1" color="text.secondary" sx={{ fontWeight: 700 }}>
                    {props.valueLabel}
                  </Typography>
                </Stack>
              )}
            </Box>
          </Box>
          {props.right ? <Box>{props.right}</Box> : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

