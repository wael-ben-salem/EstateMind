import { Card, CardContent, Typography } from '@mui/material';

export function ErrorRateCard() {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle2" sx={{ fontWeight: 900 }}>
          Error rate
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          MVP: calculer via logs Airflow (tasks failed) et exposer via API. UI prête pour afficher une série temporelle.
        </Typography>
      </CardContent>
    </Card>
  );
}

