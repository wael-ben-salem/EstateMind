import { AppBar, Box, IconButton, Toolbar, Typography } from '@mui/material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

export function AppHeader() {
  return (
    <AppBar position="sticky" color="transparent" elevation={0}>
      <Toolbar sx={{ borderBottom: '1px solid', borderColor: 'divider', backdropFilter: 'blur(10px)' }}>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          EstateMind
        </Typography>
        <Box sx={{ flex: 1 }} />
        <IconButton aria-label="account">
          <AccountCircleIcon />
        </IconButton>
      </Toolbar>
    </AppBar>
  );
}

