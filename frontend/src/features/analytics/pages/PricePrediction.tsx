import { Box, Button, Card, CardContent, Grid, Stack, TextField, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';
import { useMemo, useState } from 'react';
import { formatCurrencyTND } from '@/shared/utils/format';

type FormState = {
  superficie_finale: number;
  nbr_chambres_final: number;
  nbr_sdb_final: number;
  image_count: number;
  ville: string;
  location_finale: string;
  usage_extrait: string;
  type_bien_extrait: string;
};

export function PricePrediction() {
  const [form, setForm] = useState<FormState>({
    superficie_finale: 120,
    nbr_chambres_final: 3,
    nbr_sdb_final: 2,
    image_count: 6,
    ville: 'TUNIS',
    location_finale: 'TUNIS',
    usage_extrait: 'habitation',
    type_bien_extrait: 'appartement'
  });

  // MVP: prédiction mock (frontend only). À brancher sur POST /api/v1/analytics/predict-price.
  const predicted = useMemo(() => {
    const base = 1200 * form.superficie_finale;
    const rooms = form.nbr_chambres_final * 15000;
    const baths = form.nbr_sdb_final * 8000;
    const images = form.image_count * 1200;
    return Math.max(25000, base + rooms + baths + images);
  }, [form]);

  return (
    <Box>
      <PageHeader
        title="Price Prediction"
        subtitle="Suite de prédiction (MVP frontend): formulaire, estimation et explication."
      />

      <Grid container spacing={2}>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 900 }}>
                Caractéristiques du bien
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Remplis les champs. La prédiction temps réel sera branchée sur le microservice ML plus tard.
              </Typography>

              <Stack spacing={2}>
                <TextField
                  label="Surface (m²)"
                  type="number"
                  value={form.superficie_finale}
                  onChange={(e) => setForm((s) => ({ ...s, superficie_finale: Number(e.target.value) }))}
                />
                <Stack direction="row" spacing={2}>
                  <TextField
                    label="Chambres"
                    type="number"
                    fullWidth
                    value={form.nbr_chambres_final}
                    onChange={(e) => setForm((s) => ({ ...s, nbr_chambres_final: Number(e.target.value) }))}
                  />
                  <TextField
                    label="Salles de bain"
                    type="number"
                    fullWidth
                    value={form.nbr_sdb_final}
                    onChange={(e) => setForm((s) => ({ ...s, nbr_sdb_final: Number(e.target.value) }))}
                  />
                </Stack>
                <TextField
                  label="Nombre d’images"
                  type="number"
                  value={form.image_count}
                  onChange={(e) => setForm((s) => ({ ...s, image_count: Number(e.target.value) }))}
                />
                <Stack direction="row" spacing={2}>
                  <TextField
                    label="Ville"
                    fullWidth
                    value={form.ville}
                    onChange={(e) => setForm((s) => ({ ...s, ville: e.target.value }))}
                  />
                  <TextField
                    label="Localisation finale"
                    fullWidth
                    value={form.location_finale}
                    onChange={(e) => setForm((s) => ({ ...s, location_finale: e.target.value }))}
                  />
                </Stack>
                <Stack direction="row" spacing={2}>
                  <TextField
                    label="Usage"
                    fullWidth
                    value={form.usage_extrait}
                    onChange={(e) => setForm((s) => ({ ...s, usage_extrait: e.target.value }))}
                  />
                  <TextField
                    label="Type de bien"
                    fullWidth
                    value={form.type_bien_extrait}
                    onChange={(e) => setForm((s) => ({ ...s, type_bien_extrait: e.target.value }))}
                  />
                </Stack>

                <Button variant="contained" disabled>
                  Lancer une prédiction via API (à brancher)
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={6}>
          <Stack spacing={2}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 900 }}>
                  Prix estimé (MVP)
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 950, mt: 1 }}>
                  {formatCurrencyTND(predicted)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Intervalle de confiance, SHAP, comparables et ROI seront ajoutés quand le backend ML sera prêt.
                </Typography>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 900 }}>
                  Facteurs d’influence (mock)
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  Surface: +45% • Localisation: +30% • État: +15% • Étage: +5% • Parking: +5%
                </Typography>
              </CardContent>
            </Card>
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
}

