import { Box, Card, CardContent, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';

export function CustomDashboardBuilder() {
  return (
    <Box>
      <PageHeader
        title="Custom Dashboard Builder"
        subtitle="Builder de dashboards (MVP): à connecter aux widgets et au data catalog."
      />
      <Card>
        <CardContent>
          <Typography variant="body1" sx={{ fontWeight: 700 }}>
            À venir
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Cette page servira à composer des dashboards (drag/drop) avec des widgets KPI, charts, et filtres,
            puis sauvegarder les layouts côté backend.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

