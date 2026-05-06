import { Box, Card, CardContent, Grid, Stack, Typography } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TimelineIcon from '@mui/icons-material/Timeline';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

import { PageHeader } from '@/shared/ui/PageHeader';
import { HeroKPI } from '@/features/dashboard/components/HeroKPI';
import { KpiCard } from '@/shared/ui/KpiCard';
import { formatCurrencyTND, formatNumber } from '@/shared/utils/format';
import { useExecutiveSummary } from '@/features/dashboard/queries/useExecutiveSummary';
import { PipelineHealthGauge } from '@/features/pipeline/components/PipelineHealthGauge';
import { TopExpensiveLocations } from '@/features/analytics/components/TopExpensiveLocations';
import { WaterfallDataFlow } from '@/features/analytics/components/WaterfallDataFlow';

export function ExecutiveDashboard() {
  const summary = useExecutiveSummary();

  return (
    <Box>
      <PageHeader
        title="Executive Dashboard"
        subtitle="Vue exécutive: KPIs, santé pipeline, marché et qualité des données."
      />

      <HeroKPI
        title="Marché immobilier — Vue synthèse"
        subtitle="Key stats (live)"
        value={summary.data?.totalProperties ?? 0}
        valueLabel="annonces analysées"
        loading={summary.isLoading}
        error={summary.isError ? 'Impossible de charger les stats (backend indisponible).' : null}
        right={<PipelineHealthGauge />}
      />

      <Grid container spacing={2} sx={{ mt: 1 }}>
        <Grid item xs={12} md={3}>
          <KpiCard
            label="Total annonces"
            value={formatNumber(summary.data?.totalProperties ?? 0)}
            helper="Source: clean_tayara"
            icon={<TimelineIcon />}
            trend={{ deltaLabel: '+2.1% vs mois dernier', direction: 'up' }}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <KpiCard
            label="Localisations uniques"
            value={formatNumber(summary.data?.uniqueLocations ?? 0)}
            helper="Top villes + quartiers"
            icon={<TrendingUpIcon />}
            trend={{ deltaLabel: '+0.4% vs mois dernier', direction: 'up' }}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <KpiCard
            label="Types de biens"
            value={formatNumber(summary.data?.propertyTypes ?? 0)}
            helper="Taxonomie extraite"
            icon={<CheckCircleIcon />}
            trend={{ deltaLabel: 'stable', direction: 'flat' }}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <KpiCard
            label="Prix moyen"
            value={formatCurrencyTND(summary.data?.avgPrice ?? 0)}
            helper="Filtré: price_num NOT NULL"
            icon={<TrendingUpIcon />}
            trend={{ deltaLabel: '-1.2% vs mois dernier', direction: 'down' }}
          />
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mt: 0 }}>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="subtitle1" sx={{ fontWeight: 800 }}>
                  Top 5 zones les plus chères
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Basé sur la table agrégée `agg_price_by_location`.
                </Typography>
              </Stack>
              <Box sx={{ mt: 2 }}>
                <TopExpensiveLocations />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="subtitle1" sx={{ fontWeight: 800 }}>
                  Waterfall: flux de données (pipeline)
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Vue prescriptive: où se perd la donnée (scrape → enrich → ETL).
                </Typography>
              </Stack>
              <Box sx={{ mt: 2 }}>
                <WaterfallDataFlow />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

