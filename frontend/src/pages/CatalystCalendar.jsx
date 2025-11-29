/**
 * Catalyst Calendar page
 * Shows upcoming investment catalysts grouped by month
 */
import { useState, useEffect, useCallback } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  Link,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
} from '@mui/material';
import { format, parseISO } from 'date-fns';
import { catalystApi, diseaseAreaApi } from '../services/api';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

function CatalystCalendar() {
  useDocumentTitle('Catalyst Calendar');

  const [catalystsByMonth, setCatalystsByMonth] = useState({});
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter states
  const [diseaseArea, setDiseaseArea] = useState('');
  const [catalystType, setCatalystType] = useState('');
  const [diseaseAreas, setDiseaseAreas] = useState([]);

  const loadDiseaseAreas = useCallback(async () => {
    try {
      const response = await diseaseAreaApi.getDiseaseAreas();
      setDiseaseAreas(response.data);
    } catch (err) {
      console.error('Error loading disease areas:', err);
    }
  }, []);

  const loadCatalysts = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        months: 12,
      };

      if (diseaseArea) params.disease_area = diseaseArea;
      if (catalystType) params.catalyst_type = catalystType;

      const response = await catalystApi.getUpcomingCatalysts(params);
      setCatalystsByMonth(response.data.catalysts_by_month);
      setError(null);
    } catch (err) {
      console.error('Error loading catalysts:', err);
      setError('Failed to load catalysts. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [diseaseArea, catalystType]);

  const loadStats = useCallback(async () => {
    try {
      const response = await catalystApi.getCatalystStats();
      setStats(response.data);
    } catch (err) {
      console.error('Error loading catalyst stats:', err);
    }
  }, []);

  useEffect(() => {
    loadDiseaseAreas();
  }, [loadDiseaseAreas]);

  useEffect(() => {
    loadCatalysts();
  }, [loadCatalysts]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const getCatalystTypeColor = (type) => {
    const colors = {
      'PDUFA Date': 'error',
      'FDA Decision': 'error',
      'AdCom Meeting': 'warning',
      'Top-line Readout': 'primary',
      'Primary Completion': 'info',
      'Conference Presentation': 'default',
    };
    return colors[type] || 'default';
  };

  const getProbabilityColor = (probability) => {
    const colors = {
      'Very High': 'success',
      'High': 'primary',
      'Medium': 'info',
      'Low': 'warning',
      'Very Low': 'error',
    };
    return colors[probability] || 'default';
  };

  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Investment Catalyst Calendar
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track upcoming FDA decisions, clinical trial readouts, and key regulatory events
        </Typography>
      </Box>

      {/* Stats Overview */}
      {stats && (
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <CalendarMonthIcon color="primary" />
                  <Typography variant="h6">Next 3 Months</Typography>
                </Box>
                <Typography variant="h3" color="primary">
                  {stats.next_3_months || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Upcoming catalysts
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <CalendarMonthIcon color="info" />
                  <Typography variant="h6">Next 6 Months</Typography>
                </Box>
                <Typography variant="h3" color="info.main">
                  {stats.next_6_months || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Upcoming catalysts
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <TrendingUpIcon color="success" />
                  <Typography variant="h6">Next 12 Months</Typography>
                </Box>
                <Typography variant="h3" color="success.main">
                  {stats.next_12_months || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Upcoming catalysts
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Catalyst Type</InputLabel>
              <Select
                value={catalystType}
                label="Catalyst Type"
                onChange={(e) => setCatalystType(e.target.value)}
              >
                <MenuItem value="">All Types</MenuItem>
                <MenuItem value="PDUFA Date">PDUFA Date</MenuItem>
                <MenuItem value="FDA Decision">FDA Decision</MenuItem>
                <MenuItem value="AdCom Meeting">AdCom Meeting</MenuItem>
                <MenuItem value="Top-line Readout">Top-line Readout</MenuItem>
                <MenuItem value="Primary Completion">Primary Completion</MenuItem>
                <MenuItem value="Conference Presentation">Conference Presentation</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Disease Area</InputLabel>
              <Select
                value={diseaseArea}
                label="Disease Area"
                onChange={(e) => setDiseaseArea(e.target.value)}
              >
                <MenuItem value="">All Areas</MenuItem>
                {diseaseAreas.map((area) => (
                  <MenuItem key={area} value={area}>
                    {area}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Results */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : (
        <Box>
          {Object.keys(catalystsByMonth).length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                No upcoming catalysts found matching your criteria.
              </Typography>
            </Paper>
          ) : (
            Object.entries(catalystsByMonth)
              .sort((a, b) => a[0].localeCompare(b[0]))
              .map(([month, catalysts]) => (
                <Paper key={month} sx={{ mb: 3, p: 3 }}>
                  <Typography variant="h5" gutterBottom color="primary">
                    {month}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />

                  <Grid container spacing={2}>
                    {catalysts.map((catalyst) => (
                      <Grid item xs={12} key={catalyst.id}>
                        <Card variant="outlined">
                          <CardContent>
                            <Grid container spacing={2} alignItems="center">
                              <Grid item xs={12} sm={2}>
                                <Typography variant="h6" color="text.secondary">
                                  {catalyst.expected_date
                                    ? format(parseISO(catalyst.expected_date), 'MMM d, yyyy')
                                    : 'TBD'}
                                </Typography>
                              </Grid>

                              <Grid item xs={12} sm={7}>
                                <Typography variant="h6" gutterBottom>
                                  {catalyst.title}
                                </Typography>
                                <Typography variant="body2" color="text.secondary" paragraph>
                                  {catalyst.description}
                                </Typography>

                                {catalyst.company && (
                                  <Box display="flex" gap={1} alignItems="center">
                                    <Typography variant="body2" color="text.secondary">
                                      Company:
                                    </Typography>
                                    <Link
                                      component={RouterLink}
                                      to={`/companies/${catalyst.company.id}`}
                                      underline="hover"
                                    >
                                      {catalyst.company.company_name}
                                      {catalyst.company.ticker && ` (${catalyst.company.ticker})`}
                                    </Link>
                                  </Box>
                                )}

                                {catalyst.trial && (
                                  <Box display="flex" gap={1} alignItems="center" mt={1}>
                                    <Typography variant="body2" color="text.secondary">
                                      Trial:
                                    </Typography>
                                    <Link
                                      component={RouterLink}
                                      to={`/trials/${catalyst.trial.id}`}
                                      underline="hover"
                                    >
                                      {catalyst.trial.registry_id}
                                    </Link>
                                  </Box>
                                )}

                                {catalyst.drug && (
                                  <Box display="flex" gap={1} alignItems="center" mt={1}>
                                    <Typography variant="body2" color="text.secondary">
                                      Drug:
                                    </Typography>
                                    <Link
                                      component={RouterLink}
                                      to={`/drugs/${catalyst.drug.id}`}
                                      underline="hover"
                                    >
                                      {catalyst.drug.drug_name}
                                    </Link>
                                  </Box>
                                )}
                              </Grid>

                              <Grid item xs={12} sm={3}>
                                <Box display="flex" flexDirection="column" gap={1}>
                                  <Chip
                                    label={catalyst.catalyst_type}
                                    color={getCatalystTypeColor(catalyst.catalyst_type)}
                                    size="small"
                                  />
                                  {catalyst.probability_band && (
                                    <Chip
                                      label={`${catalyst.probability_band} Probability`}
                                      color={getProbabilityColor(catalyst.probability_band)}
                                      size="small"
                                      variant="outlined"
                                    />
                                  )}
                                </Box>
                              </Grid>
                            </Grid>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Paper>
              ))
          )}
        </Box>
      )}
    </Box>
  );
}

export default CatalystCalendar;
