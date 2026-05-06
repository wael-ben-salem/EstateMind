import { Box, Typography } from '@mui/material';

export function AppFooter() {
  return (
    <Box sx={{ px: 3, py: 2, borderTop: '1px solid', borderColor: 'divider' }}>
      <Typography variant="caption" color="text.secondary">
        © {new Date().getFullYear()} EstateMind — Intelligence Immobilière Tunisienne
      </Typography>
    </Box>
  );
}

