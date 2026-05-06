import { Box, Card, CardContent, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';

export function ConfigurationHub() {
  return (
    <Box>
      <PageHeader title="Configuration Hub" subtitle="Centralisation config (sources, alerting, tokens, RBAC)." />
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            MVP: page placeholder. On branchera quand le backend aura `/api/v1/alerts/config` etc.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

