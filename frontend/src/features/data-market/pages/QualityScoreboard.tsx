import { Box, Card, CardContent, Grid, LinearProgress, Stack, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';
import { useQuery } from '@tanstack/react-query';
import { estateMindApi } from '@/shared/api/estateMindApi';

function scoreFromStats(stats: { avgPrice: number; totalProperties: number; uniqueLocations: number }) {
  // MVP heuristic: just to render a meaningful UI without new endpoints.
  const a = Math.min(100, Math.round((stats.uniqueLocations / Math.max(1, stats.totalProperties)) * 6000));
  const b = stats.avgPrice > 0 ? 30 : 0;
  return Math.min(100, Math.max(0, Math.round((a + b) / 2)));
}

export function QualityScoreboard() {
  const q = useQuery({ queryKey: ['stats'], queryFn: estateMindApi.stats, refetchInterval: 30_000 });

  const score = q.data ? scoreFromStats(q.data) : 0;

  return (
    <Box>
      <PageHeader
        title="Data Quality Command Center"
        subtitle="Qualité: complétude, fraîcheur, anomalies, outliers, et corrections (MVP)."
      />

      <Grid container spacing={2}>
        <Grid item xs={12} lg={5}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 900 }}>
                Quality Score
              </Typography>
              {q.isLoading ? <LinearProgress sx={{ mt: 2 }} /> : null}
              {q.isError ? (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Backend indisponible. On affiche un score par défaut.
                </Typography>
              ) : null}

              <Stack spacing={1} sx={{ mt: 2 }}>
                <Typography variant="h3" sx={{ fontWeight: 950 }}>
                  {score}/100
                </Typography>
                <LinearProgress variant="determinate" value={score} sx={{ height: 10, borderRadius: 99 }} />
                <Typography variant="body2" color="text.secondary">
                  MVP: score heuristique basé sur les stats disponibles. À remplacer par des métriques validator/ETL.
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={7}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 900 }}>
                Matrice de complétion (à brancher)
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                On branchera cette vue sur les ratios de complétude (`missing_*_ratio`, `geo_fill_ratio`, etc.) produits
                par `agent/validator.py` et exposés via API.
              </Typography>
              <Box sx={{ mt: 2, p: 2, borderRadius: 2, border: '1px dashed', borderColor: 'divider' }}>
                <Typography variant="caption" color="text.secondary">
                  Placeholder UI.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

