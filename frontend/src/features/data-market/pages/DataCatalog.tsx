import { Box, Card, CardContent, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';

export function DataCatalog() {
  return (
    <Box>
      <PageHeader title="Data Catalog" subtitle="Catalogue des datasets, schémas, propriétaires et SLAs (MVP)." />
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            MVP: page placeholder. On affichera les tables (clean_tayara, clean_tayara_analytics, agg_price_by_location),
            leurs colonnes, et la qualité associée.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

