/**
 * Main layout component with header, navigation, and footer.
 * Includes ad placement containers for future AdSense integration.
 */
import { AppBar, Toolbar, Typography, Container, Box, Link as MuiLink, Drawer, List, ListItem, ListItemText, IconButton, useMediaQuery, useTheme } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';
import MenuIcon from '@mui/icons-material/Menu';

const navItems = [
  { label: 'Dashboard', path: '/' },
  { label: 'Recent Approvals', path: '/approvals' },
  { label: 'Upcoming Events', path: '/events' },
  { label: 'About', path: '/about' },
];

function Layout({ children }) {
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(false);

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Top Banner Ad Placeholder */}
      <Box
        id="ad-top-banner"
        sx={{
          minHeight: '90px',
          backgroundColor: '#f0f0f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid #ddd',
        }}
      >
        {/* AdSense code will be inserted here */}
        <Typography variant="caption" color="text.secondary">
          Advertisement
        </Typography>
      </Box>

      {/* Header / Navigation */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={toggleDrawer}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}

          <Typography
            variant="h6"
            component={Link}
            to="/"
            sx={{
              flexGrow: 1,
              textDecoration: 'none',
              color: 'inherit',
              fontWeight: 700,
            }}
          >
            FDA Drug Approval Tracker
          </Typography>

          {!isMobile && (
            <Box sx={{ display: 'flex', gap: 2 }}>
              {navItems.map((item) => (
                <MuiLink
                  key={item.path}
                  component={Link}
                  to={item.path}
                  sx={{
                    color: 'white',
                    textDecoration: 'none',
                    fontWeight: location.pathname === item.path ? 700 : 400,
                    borderBottom: location.pathname === item.path ? '2px solid white' : 'none',
                    paddingBottom: '4px',
                    '&:hover': {
                      opacity: 0.8,
                    },
                  }}
                >
                  {item.label}
                </MuiLink>
              ))}
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer anchor="left" open={drawerOpen} onClose={toggleDrawer}>
        <List sx={{ width: 250 }}>
          {navItems.map((item) => (
            <ListItem
              button
              key={item.path}
              component={Link}
              to={item.path}
              onClick={toggleDrawer}
              selected={location.pathname === item.path}
            >
              <ListItemText primary={item.label} />
            </ListItem>
          ))}
        </List>
      </Drawer>

      {/* Main Content Area */}
      <Container
        maxWidth="xl"
        sx={{
          flex: 1,
          py: 4,
          display: 'flex',
          gap: 3,
        }}
      >
        {/* Sidebar Ad Placeholder (hidden on mobile) */}
        {!isMobile && (
          <Box
            id="ad-sidebar"
            sx={{
              width: '160px',
              minHeight: '600px',
              backgroundColor: '#f0f0f0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {/* AdSense code will be inserted here */}
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ transform: 'rotate(-90deg)', whiteSpace: 'nowrap' }}
            >
              Advertisement
            </Typography>
          </Box>
        )}

        {/* Main Content */}
        <Box sx={{ flex: 1 }}>
          {children}

          {/* In-Content Ad Placeholder */}
          <Box
            id="ad-in-content"
            sx={{
              minHeight: '250px',
              backgroundColor: '#f0f0f0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mt: 4,
              mb: 2,
            }}
          >
            {/* AdSense code will be inserted here */}
            <Typography variant="caption" color="text.secondary">
              Advertisement
            </Typography>
          </Box>
        </Box>
      </Container>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          backgroundColor: '#1976d2',
          color: 'white',
          py: 3,
          mt: 'auto',
        }}
      >
        <Container maxWidth="xl">
          <Typography variant="body2" align="center" gutterBottom>
            FDA Drug Approval Tracker
          </Typography>
          <Typography variant="caption" align="center" display="block" sx={{ mb: 1 }}>
            Data sourced from publicly available FDA information
          </Typography>
          <Typography variant="caption" align="center" display="block" sx={{ fontStyle: 'italic' }}>
            <strong>Disclaimer:</strong> This site is for informational purposes only and is not
            medical or investment advice. Data accuracy is not guaranteed. This site is not
            affiliated with or endorsed by the U.S. Food and Drug Administration (FDA).
          </Typography>
          <Typography variant="caption" align="center" display="block" sx={{ mt: 2 }}>
            © {new Date().getFullYear()} FDA Drug Approval Tracker
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}

export default Layout;
