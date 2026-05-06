import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';

import { AppHeader } from '@/app/layout/Header';
import { Sidebar } from '@/app/layout/Sidebar';
import { AppFooter } from '@/app/layout/Footer';

export function MainLayout() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Sidebar />
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <AppHeader />
        <Box component="main" sx={{ flex: 1, px: { xs: 2, md: 3 }, py: 2 }}>
          <Outlet />
        </Box>
        <AppFooter />
      </Box>
    </Box>
  );
}

