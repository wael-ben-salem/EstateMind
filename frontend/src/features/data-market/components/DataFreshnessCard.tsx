import { Card, CardContent, Typography } from '@mui/material';

export function DataFreshnessCard() {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle2" sx={{ fontWeight: 900 }}>
          Freshness
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          MVP: brancher sur un endpoint qui expose l’âge de `TayaraDataDetailed.json` (agent/state_reader.py) ou des
          métadonnées DB.
        </Typography>
      </CardContent>
    </Card>
  );
}

