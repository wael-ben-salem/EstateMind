import { useMemo } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Box,
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import HubIcon from '@mui/icons-material/Hub';
import InsightsIcon from '@mui/icons-material/Insights';
import VerifiedIcon from '@mui/icons-material/Verified';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';

type NavItem = {
  label: string;
  to: string;
  icon: JSX.Element;
};

const drawerWidth = 280;

export function Sidebar() {
  const location = useLocation();

  const nav = useMemo<NavItem[]>(
    () => [
      { label: 'Executive Dashboard', to: '/dashboard/executive', icon: <DashboardIcon /> },
      { label: 'Operational Dashboard', to: '/dashboard/operational', icon: <DashboardIcon /> },
      { label: 'Pipeline Orchestrator', to: '/pipeline', icon: <AccountTreeIcon /> },
      { label: 'Data Catalog', to: '/data/catalog', icon: <HubIcon /> },
      { label: 'Data Lineage', to: '/data/lineage', icon: <HubIcon /> },
      { label: 'Quality Command Center', to: '/data/quality', icon: <VerifiedIcon /> },
      { label: 'Market Intelligence', to: '/analytics/market', icon: <InsightsIcon /> },
      { label: 'Price Prediction', to: '/analytics/predict', icon: <InsightsIcon /> },
      { label: 'Admin / System Health', to: '/admin/health', icon: <AdminPanelSettingsIcon /> }
    ],
    []
  );

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          borderRight: '1px solid',
          borderColor: 'divider'
        }
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 800 }}>
          EstateMind
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Real estate intelligence suite
        </Typography>
      </Box>
      <Divider />
      <List dense sx={{ py: 1 }}>
        {nav.map((item) => (
          <ListItem key={item.to} disablePadding>
            <ListItemButton
              component={NavLink}
              to={item.to}
              selected={location.pathname === item.to}
              sx={{
                '&.active': { backgroundColor: 'action.selected' },
                borderRadius: 1,
                mx: 1,
                my: 0.25
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} primaryTypographyProps={{ fontSize: 13 }} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}

