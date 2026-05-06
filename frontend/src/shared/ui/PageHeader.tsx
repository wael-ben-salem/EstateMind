import { Box, Breadcrumbs, Chip, Link, Stack, Typography } from '@mui/material';
import { ReactNode } from 'react';

export function PageHeader(props: {
  title: string;
  subtitle?: string;
  right?: ReactNode;
  statusPill?: { label: string; color?: 'default' | 'primary' | 'success' | 'warning' | 'error' };
}) {
  return (
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2, alignItems: { md: 'center' } }}>
      <Box sx={{ flex: 1 }}>
        <Breadcrumbs sx={{ mb: 0.75 }}>
          <Link underline="hover" color="inherit" href="/">
            EstateMind
          </Link>
          <Typography color="text.secondary">{props.title}</Typography>
        </Breadcrumbs>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <Typography variant="h5" sx={{ fontWeight: 800 }}>
            {props.title}
          </Typography>
          {props.statusPill ? (
            <Chip size="small" label={props.statusPill.label} color={props.statusPill.color || 'default'} />
          ) : null}
        </Stack>
        {props.subtitle ? (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {props.subtitle}
          </Typography>
        ) : null}
      </Box>
      {props.right ? <Box>{props.right}</Box> : null}
    </Stack>
  );
}

