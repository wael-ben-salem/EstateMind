import { Box, Card, CardContent, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';

export function AuditTrail() {
  return (
    <Box>
      <PageHeader title="Audit Trail" subtitle="Journal d’audit (RBAC, actions pipeline, exports, etc.)." />
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            MVP: page placeholder. On branchera quand le backend aura `/api/v1/admin/audit`.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

