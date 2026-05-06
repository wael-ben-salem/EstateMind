import { Alert, Box, Typography } from '@mui/material';
import mapboxgl from 'mapbox-gl';
import { useEffect, useRef } from 'react';

export function GeographicInsights() {
  const token = import.meta.env.VITE_MAPBOX_TOKEN;
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!token) return;
    if (!ref.current) return;

    mapboxgl.accessToken = token;
    const map = new mapboxgl.Map({
      container: ref.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [10.1658, 36.8065],
      zoom: 5.3
    });

    map.addControl(new mapboxgl.NavigationControl(), 'top-right');

    return () => map.remove();
  }, [token]);

  if (!token) {
    return (
      <Alert severity="info">
        <Typography variant="body2" sx={{ fontWeight: 700 }}>
          Carte désactivée.
        </Typography>
        <Typography variant="body2">
          Ajoute `VITE_MAPBOX_TOKEN` (frontend) pour activer Mapbox. En attendant, tu peux tester toute la plateforme
          sans la carte.
        </Typography>
      </Alert>
    );
  }

  return <Box ref={ref} sx={{ height: 420, borderRadius: 2, overflow: 'hidden' }} />;
}

