import { Box, Card, CardContent, Grid, Stack, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';
import { PriceByCityChart } from '@/features/analytics/visuals/PriceByCityChart';
import { PriceDistributionChart } from '@/features/analytics/visuals/PriceDistributionChart';
import { GeographicInsights } from '@/features/analytics/visuals/GeographicInsights';

export function MarketIntelligence() {
  return (
    <Box>
      <PageHeader
        title="Market Intelligence"
        subtitle="Analyse avancée: cartes, tendances, heatmaps et comparaisons."
      />

      <Grid container spacing={2}>
        <Grid item xs={12} lg={7}>
          <Card>
            <CardContent>
              <Stack spacing={0.5} sx={{ mb: 1 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 900 }}>
                  Carte (Tunisie) — densité & prix
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Si `VITE_MAPBOX_TOKEN` est défini, la carte Mapbox s’active.
                </Typography>
              </Stack>
              <GeographicInsights />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={5}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 900, mb: 1 }}>
                Prix moyen par ville (Top 10)
              </Typography>
              <PriceByCityChart />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mt: 0 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 900, mb: 1 }}>
                Distribution des prix
              </Typography>
              <PriceDistributionChart />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

