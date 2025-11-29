/**
 * Company Dashboard page
 * Shows company pipeline overview with trials by phase, drugs, and upcoming catalysts
 */
import { useState, useEffect, useCallback } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';
import { companyApi } from '../services/api';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import BusinessIcon from '@mui/icons-material/Business';
import ScienceIcon from '@mui/icons-material/Science';
import MedicationIcon from '@mui/icons-material/Medication';
import EventIcon from '@mui/icons-material/Event';

function CompanyDashboard() {
  const { id } = useParams();
  useDocumentTitle('Company Pipeline Dashboard');

  const [stats, setStats] = useState(null);
  const [trials, setTrials] = useState([]);
  const [drugs, setDrugs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);

  const loadCompanyData = useCallback(async () => {
    try {
      setLoading(true);

      // Load company stats
      const statsResponse = await companyApi.getCompanyStats(id);
      setStats(statsResponse.data);

      // Load company trials
      const trialsResponse = await companyApi.getCompanyTrials(id);
      setTrials(trialsResponse.data);

      // Load company drugs
      const drugsResponse = await companyApi.getCompanyDrugs(id);
      setDrugs(drugsResponse.data);

      setError(null);
    } catch (err) {
      console.error('Error loading company data:', err);
      setError('Failed to load company data. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadCompanyData();
  }, [loadCompanyData]);

  const getPhaseColor = (phase) => {
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#00C49F'];
    const phases = ['Early Phase 1', 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4'];
    const index = phases.indexOf(phase);
    return colors[index] !== undefined ? colors[index] : '#8884d8';
  };

  const getPhaseChipColor = (phase) => {
    const colors = {
      'Early Phase 1': 'info',
      'Phase 1': 'info',
      'Phase 2': 'primary',
      'Phase 3': 'warning',
      'Phase 4': 'success',
    };
    return colors[phase] || 'default';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!stats) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        Company not found.
      </Alert>
    );
  }

  // Prepare data for charts
  const phaseData = Object.entries(stats.trials_by_phase || {}).map(([phase, count]) => ({
    name: phase,
    value: count,
    fill: getPhaseColor(phase),
  }));

  return (
    <Box>
      {/* Header */}
      <Box mb={4}>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <BusinessIcon sx={{ fontSize: 40 }} color="primary" />
          <Box>
            <Typography variant="h4" component="h1">
              {stats.company_name || 'Company Pipeline Dashboard'}
            </Typography>
            {stats.ticker && (
              <Typography variant="h6" color="text.secondary">
                {stats.ticker}
              </Typography>
            )}
          </Box>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Comprehensive pipeline overview including trials, drugs, and upcoming catalysts
        </Typography>
      </Box>

      {/* Overview Stats */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <ScienceIcon color="primary" />
                <Typography variant="h6">Total Trials</Typography>
              </Box>
              <Typography variant="h3" color="primary">
                {stats.total_trials || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <MedicationIcon color="info" />
                <Typography variant="h6">Total Drugs</Typography>
              </Box>
              <Typography variant="h3" color="info.main">
                {stats.total_drugs || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <EventIcon color="success" />
                <Typography variant="h6">Approvals</Typography>
              </Box>
              <Typography variant="h3" color="success.main">
                {stats.total_approvals || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <EventIcon color="error" />
                <Typography variant="h6">Upcoming Catalysts</Typography>
              </Box>
              <Typography variant="h3" color="error.main">
                {stats.upcoming_catalysts_count || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Trials by Phase
            </Typography>
            {phaseData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={phaseData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={80}
                    dataKey="value"
                  >
                    {phaseData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Typography variant="body2" color="text.secondary" align="center" py={4}>
                No trial data available
              </Typography>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Disease Area Distribution
            </Typography>
            {stats.active_disease_areas && stats.active_disease_areas.length > 0 ? (
              <Box>
                {stats.active_disease_areas.slice(0, 5).map((area, index) => (
                  <Box key={index} mb={1}>
                    <Box display="flex" justifyContent="space-between" mb={0.5}>
                      <Typography variant="body2">{area.disease_area}</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {area.count}
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        width: '100%',
                        height: 8,
                        backgroundColor: '#e0e0e0',
                        borderRadius: 4,
                      }}
                    >
                      <Box
                        sx={{
                          width: `${(area.count / stats.total_trials) * 100}%`,
                          height: '100%',
                          backgroundColor: 'primary.main',
                          borderRadius: 4,
                        }}
                      />
                    </Box>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary" align="center" py={4}>
                No disease area data available
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Tabs for Trials and Drugs */}
      <Paper>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label={`Clinical Trials (${trials.length})`} />
          <Tab label={`Drugs (${drugs.length})`} />
        </Tabs>

        {activeTab === 0 && (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Trial ID</strong></TableCell>
                  <TableCell><strong>Title</strong></TableCell>
                  <TableCell><strong>Phase</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Completion Date</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {trials.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      <Typography variant="body2" color="text.secondary" py={4}>
                        No trials found for this company.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  trials.map((trial) => (
                    <TableRow key={trial.id} hover>
                      <TableCell>
                        <Link
                          component={RouterLink}
                          to={`/trials/${trial.id}`}
                          underline="hover"
                          color="primary"
                        >
                          {trial.registry_id}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 400 }}>
                          {trial.title}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {trial.phase && (
                          <Chip
                            label={trial.phase}
                            color={getPhaseChipColor(trial.phase)}
                            size="small"
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{trial.status || 'N/A'}</Typography>
                      </TableCell>
                      <TableCell>
                        {trial.primary_completion_date
                          ? format(new Date(trial.primary_completion_date), 'MMM d, yyyy')
                          : 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {activeTab === 1 && (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Drug Name</strong></TableCell>
                  <TableCell><strong>Brand Name</strong></TableCell>
                  <TableCell><strong>Therapeutic Area</strong></TableCell>
                  <TableCell><strong>Indication</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {drugs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      <Typography variant="body2" color="text.secondary" py={4}>
                        No drugs found for this company.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  drugs.map((drug) => (
                    <TableRow key={drug.id} hover>
                      <TableCell>
                        <Link
                          component={RouterLink}
                          to={`/drugs/${drug.id}`}
                          underline="hover"
                          color="primary"
                        >
                          {drug.drug_name}
                        </Link>
                      </TableCell>
                      <TableCell>{drug.brand_name || 'N/A'}</TableCell>
                      <TableCell>{drug.therapeutic_area || 'N/A'}</TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 400 }}>
                          {drug.primary_indication || 'N/A'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  );
}

export default CompanyDashboard;
