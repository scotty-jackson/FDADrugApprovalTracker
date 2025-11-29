/**
 * Clinical Trials Explorer page
 * Shows paginated, searchable, and filterable list of clinical trials
 */
import { useState, useEffect, useCallback } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  CircularProgress,
  Alert,
  Chip,
  Link,
  Button,
} from '@mui/material';
import { format } from 'date-fns';
import { trialsApi, diseaseAreaApi } from '../services/api';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

function TrialsExplorer() {
  useDocumentTitle('Clinical Trials Explorer');

  const [trials, setTrials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalCount, setTotalCount] = useState(0);

  // Filter states
  const [search, setSearch] = useState('');
  const [phase, setPhase] = useState('');
  const [status, setStatus] = useState('');
  const [diseaseArea, setDiseaseArea] = useState('');
  const [diseaseAreas, setDiseaseAreas] = useState([]);

  // Pagination states
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);

  useEffect(() => {
    loadDiseaseAreas();
  }, []);

  useEffect(() => {
    loadTrials();
  }, [loadTrials]);

  const loadDiseaseAreas = async () => {
    try {
      const response = await diseaseAreaApi.getDiseaseAreas();
      setDiseaseAreas(response.data);
    } catch (err) {
      console.error('Error loading disease areas:', err);
    }
  };

  const loadTrials = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page: page + 1, // API uses 1-based pagination
        page_size: pageSize,
      };

      if (search) params.search = search;
      if (phase) params.phase = phase;
      if (status) params.status = status;
      if (diseaseArea) params.disease_area = diseaseArea;

      const response = await trialsApi.getTrials(params);
      setTrials(response.data.items);
      setTotalCount(response.data.total);
      setError(null);
    } catch (err) {
      console.error('Error loading trials:', err);
      setError('Failed to load clinical trials. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [diseaseArea, page, pageSize, phase, search, status]);

  const handleSearchChange = (event) => {
    setSearch(event.target.value);
    setPage(0); // Reset to first page on search
  };

  const handleClearFilters = () => {
    setSearch('');
    setPhase('');
    setStatus('');
    setDiseaseArea('');
    setPage(0);
  };

  const getPhaseColor = (trialPhase) => {
    const colors = {
      'Early Phase 1': 'info',
      'Phase 1': 'info',
      'Phase 2': 'primary',
      'Phase 3': 'warning',
      'Phase 4': 'success',
    };
    return colors[trialPhase] || 'default';
  };

  const getStatusColor = (trialStatus) => {
    const colors = {
      'Recruiting': 'success',
      'Active, not recruiting': 'primary',
      'Completed': 'default',
      'Terminated': 'error',
      'Suspended': 'warning',
      'Withdrawn': 'error',
    };
    return colors[trialStatus] || 'default';
  };

  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Clinical Trials Explorer
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Search and explore clinical trials from ClinicalTrials.gov
        </Typography>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search trials"
              placeholder="Search by title, intervention, or NCT number..."
              value={search}
              onChange={handleSearchChange}
              variant="outlined"
            />
          </Grid>

          <Grid item xs={12} sm={4} md={2}>
            <FormControl fullWidth>
              <InputLabel>Phase</InputLabel>
              <Select
                value={phase}
                label="Phase"
                onChange={(e) => {
                  setPhase(e.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="">All Phases</MenuItem>
                <MenuItem value="Early Phase 1">Early Phase 1</MenuItem>
                <MenuItem value="Phase 1">Phase 1</MenuItem>
                <MenuItem value="Phase 2">Phase 2</MenuItem>
                <MenuItem value="Phase 3">Phase 3</MenuItem>
                <MenuItem value="Phase 4">Phase 4</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={4} md={2}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={status}
                label="Status"
                onChange={(e) => {
                  setStatus(e.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="Recruiting">Recruiting</MenuItem>
                <MenuItem value="Active, not recruiting">Active, not recruiting</MenuItem>
                <MenuItem value="Completed">Completed</MenuItem>
                <MenuItem value="Terminated">Terminated</MenuItem>
                <MenuItem value="Suspended">Suspended</MenuItem>
                <MenuItem value="Withdrawn">Withdrawn</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={4} md={2}>
            <FormControl fullWidth>
              <InputLabel>Disease Area</InputLabel>
              <Select
                value={diseaseArea}
                label="Disease Area"
                onChange={(e) => {
                  setDiseaseArea(e.target.value);
                  setPage(0);
                }}
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

          <Grid item xs={12} display="flex" justifyContent="flex-end">
            <Button onClick={handleClearFilters} variant="outlined">
              Clear Filters
            </Button>
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
        <>
          <Paper>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Trial ID</strong></TableCell>
                    <TableCell><strong>Title</strong></TableCell>
                    <TableCell><strong>Phase</strong></TableCell>
                    <TableCell><strong>Status</strong></TableCell>
                    <TableCell><strong>Sponsor</strong></TableCell>
                    <TableCell><strong>Start Date</strong></TableCell>
                    <TableCell><strong>Completion Date</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {trials.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        <Typography variant="body2" color="text.secondary" py={4}>
                          No trials found matching your criteria.
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
                              color={getPhaseColor(trial.phase)}
                              size="small"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          {trial.status && (
                            <Chip
                              label={trial.status}
                              color={getStatusColor(trial.status)}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {trial.sponsor?.name || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {trial.start_date
                            ? format(new Date(trial.start_date), 'MMM d, yyyy')
                            : 'N/A'}
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
            <TablePagination
              component="div"
              count={totalCount}
              page={page}
              onPageChange={(event, newPage) => setPage(newPage)}
              rowsPerPage={pageSize}
              onRowsPerPageChange={(event) => {
                setPageSize(parseInt(event.target.value, 10));
                setPage(0);
              }}
              rowsPerPageOptions={[10, 20, 50, 100]}
            />
          </Paper>
        </>
      )}
    </Box>
  );
}

export default TrialsExplorer;
