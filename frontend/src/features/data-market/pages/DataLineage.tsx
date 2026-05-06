import { Box, Card, CardContent, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';

export function DataLineage() {
  return (
    <Box>
      <PageHeader title="Data Lineage" subtitle="Lineage: raw → enrich → located → clean → analytics (MVP)." />
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            MVP: page placeholder. On branchera la lineage réelle via Airflow metadata + événements pipeline.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

