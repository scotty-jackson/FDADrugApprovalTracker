/**
 * Trial Detail page
 * Displays full information about a specific clinical trial including timeline, sponsor, and study design.
 */
import { useState, useEffect } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Divider,
  Link,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
} from '@mui/material';
import { format, parseISO } from 'date-fns';
import { trialsApi } from '../services/api';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  try {
    return format(parseISO(dateString), 'MMM dd, yyyy');
  } catch (error) {
    return dateString;
  }
}

function getPhaseChipColor(phase) {
  const colors = {
    'Early Phase 1': 'info',
    'Phase 1': 'info',
    'Phase 2': 'primary',
    'Phase 3': 'warning',
    'Phase 4': 'success',
  };
  return colors[phase] || 'default';
}

function getStatusChipColor(status) {
  const colors = {
    Recruiting: 'success',
    'Active, not recruiting': 'primary',
    Completed: 'default',
    Terminated: 'error',
    Suspended: 'warning',
    Withdrawn: 'error',
  };
  return colors[status] || 'default';
}

function buildRegistryUrl(trial) {
  if (!trial) return null;
  if (trial.registry_url) {
    return trial.registry_url;
  }

  const registryName = (trial.registry || '').toLowerCase();
  if (!trial.registry_id) {
    return null;
  }

  if (registryName === 'clinicaltrials.gov') {
    return `https://clinicaltrials.gov/study/${trial.registry_id}`;
  }

  if (registryName === 'euctr') {
    return `https://www.clinicaltrialsregister.eu/ctr-search/trial/${trial.registry_id}`;
  }

  return null;
}

function InfoRow({ label, value }) {
  return (
    <Box display="flex" justifyContent="space-between" py={0.5}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" fontWeight={600} sx={{ ml: 2 }}>
        {value || 'N/A'}
      </Typography>
    </Box>
  );
}

function TrialDetail() {
  const { id } = useParams();
  const [trial, setTrial] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useDocumentTitle(
    trial ? `${trial.registry_id || 'Trial'} - Clinical Trial Details` : 'Trial Details'
  );

  useEffect(() => {
    const loadTrial = async () => {
      try {
        setLoading(true);
        const response = await trialsApi.getTrial(id);
        setTrial(response.data);
        setError(null);
      } catch (err) {
        console.error('Error loading trial detail:', err);
        setError('Failed to load trial information. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    loadTrial();
  }, [id]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !trial) {
    return <Alert severity="error">{error || 'Trial not found'}</Alert>;
  }

  const registryUrl = buildRegistryUrl(trial);
  const hasConditions = trial.conditions && trial.conditions.length > 0;
  const hasInterventions = trial.interventions && trial.interventions.length > 0;
  const hasOutcomes = trial.outcomes && trial.outcomes.length > 0;
  const hasResults = Boolean(trial.results);

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="overline" color="text.secondary">
          {trial.registry || 'Clinical Trial'}
        </Typography>
        <Typography variant="h4" gutterBottom>
          {trial.title}
        </Typography>

        <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
          {trial.registry_id && (
            <Chip label={`ID: ${trial.registry_id}`} color="primary" />
          )}
          {trial.phase && (
            <Chip label={trial.phase} color={getPhaseChipColor(trial.phase)} />
          )}
          {trial.status && (
            <Chip label={trial.status} color={getStatusChipColor(trial.status)} variant="outlined" />
          )}
          {trial.study_type && (
            <Chip label={trial.study_type} variant="outlined" />
          )}
          {trial.location_summary && (
            <Chip label={trial.location_summary} variant="outlined" />
          )}
        </Box>

        {registryUrl && (
          <Box mb={2}>
            <Button component="a" href={registryUrl} target="_blank" rel="noopener" variant="contained">
              View Registry Entry
            </Button>
          </Box>
        )}

        {trial.brief_summary && (
          <Typography variant="body1" color="text.secondary">
            {trial.brief_summary}
          </Typography>
        )}
      </Paper>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Trial Timeline & Overview
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <InfoRow label="Start Date" value={formatDate(trial.start_date)} />
              <InfoRow label="Primary Completion" value={formatDate(trial.primary_completion_date)} />
              <InfoRow label="Study Completion" value={formatDate(trial.completion_date)} />
              <InfoRow label="Study Type" value={trial.study_type} />
              <InfoRow label="Location" value={trial.location_summary} />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Current Status
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <InfoRow label="Phase" value={trial.phase || 'Unknown'} />
              <InfoRow label="Recruitment Status" value={trial.status || 'Unknown'} />
              <InfoRow label="Registry" value={trial.registry} />
            </CardContent>
          </Card>

          {trial.sponsor && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Lead Sponsor
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  {trial.sponsor.name}
                </Typography>
                {trial.sponsor.notes && (
                  <Typography variant="body2" color="text.secondary">
                    {trial.sponsor.notes}
                  </Typography>
                )}
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {hasConditions && (
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Conditions Studied
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Box display="flex" flexWrap="wrap" gap={1}>
            {trial.conditions.map((condition) => (
              <Chip
                key={condition.id}
                label={
                  condition.disease_area
                    ? `${condition.condition_name} (${condition.disease_area})`
                    : condition.condition_name
                }
                variant="outlined"
              />
            ))}
          </Box>
        </Paper>
      )}

      {hasInterventions && (
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Interventions
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            {trial.interventions.map((intervention) => (
              <Grid item xs={12} md={6} key={intervention.id}>
                <Box sx={{ p: 2, borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="subtitle1" fontWeight={600}>
                    {intervention.intervention_name}
                  </Typography>
                  {intervention.intervention_type && (
                    <Typography variant="body2" color="text.secondary">
                      {intervention.intervention_type}
                    </Typography>
                  )}
                  {intervention.description && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {intervention.description}
                    </Typography>
                  )}
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {hasOutcomes && (
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Outcome Measures
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Type</strong></TableCell>
                  <TableCell><strong>Measure</strong></TableCell>
                  <TableCell><strong>Time Frame</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {trial.outcomes.map((outcome) => (
                  <TableRow key={outcome.id}>
                    <TableCell>
                      <Chip label={outcome.outcome_type} size="small" color="primary" />
                    </TableCell>
                    <TableCell>{outcome.measure}</TableCell>
                    <TableCell>{outcome.time_frame || 'N/A'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {hasResults && (
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Results & Readouts
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
            <Chip
              label={trial.results.results_available ? 'Results Posted' : 'Results Pending'}
              color={trial.results.results_available ? 'success' : 'default'}
            />
            {typeof trial.results.reported_success_flag === 'boolean' && (
              <Chip
                label={trial.results.reported_success_flag ? 'Met Primary Endpoint' : 'Did Not Meet Endpoint'}
                color={trial.results.reported_success_flag ? 'success' : 'error'}
                variant="outlined"
              />
            )}
          </Box>

          {trial.results.primary_outcome_summary && (
            <Typography variant="body1" sx={{ mb: 2 }}>
              {trial.results.primary_outcome_summary}
            </Typography>
          )}

          {trial.results.results_url && (
            <Link href={trial.results.results_url} target="_blank" rel="noopener">
              View Complete Results
            </Link>
          )}
        </Paper>
      )}

      <Box sx={{ mt: 3 }}>
        <Link component={RouterLink} to="/trials" underline="hover">
          <- Back to Trials Explorer
        </Link>
      </Box>
    </Box>
  );
}

export default TrialDetail;




