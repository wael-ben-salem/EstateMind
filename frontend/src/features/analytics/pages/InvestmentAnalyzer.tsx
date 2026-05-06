import { Box, Card, CardContent, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';

export function InvestmentAnalyzer() {
  return (
    <Box>
      <PageHeader title="Investment Analyzer" subtitle="Analyse ROI locatif, projections, recommandations (à venir)." />
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            MVP: page placeholder. On branchera les calculs ROI et les comparables quand les endpoints analytics seront
            disponibles.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

