/**
 * Drug Detail page
 * Shows comprehensive information about a specific drug including approval history
 */
import { useState, useEffect, useCallback } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Link,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import { format, parseISO } from 'date-fns';
import { drugApi } from '../services/api';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import DrugSubscriptionButton from '../components/DrugSubscriptionButton';

function DrugDetail() {
  const { id } = useParams();
  const [drug, setDrug] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useDocumentTitle(
    drug ? `${drug.brand_name || drug.drug_name} - FDA Drug Approval Tracker` : 'Drug Details'
  );

  const loadDrugDetail = useCallback(async () => {
    try {
      setLoading(true);
      const response = await drugApi.getDrug(id);
      setDrug(response.data);
      setError(null);
    } catch (err) {
      console.error('Error loading drug detail:', err);
      setError('Failed to load drug information. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadDrugDetail();
  }, [loadDrugDetail]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(parseISO(dateString), 'MMM dd, yyyy');
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !drug) {
    return (
      <Alert severity="error">
        {error || 'Drug not found'}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {drug.brand_name || drug.drug_name}
        </Typography>
        {drug.generic_name && (
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Generic name: {drug.generic_name}
          </Typography>
        )}

        <Grid container spacing={2} sx={{ mt: 2 }}>
          {drug.therapeutic_area && (
            <Grid item>
              <Chip label={`Therapeutic Area: ${drug.therapeutic_area}`} color="primary" />
            </Grid>
          )}
          {drug.route_of_administration && (
            <Grid item>
              <Chip label={`Route: ${drug.route_of_administration}`} variant="outlined" />
            </Grid>
          )}
        </Grid>

        {/* Email Subscription Button */}
        <Box sx={{ mt: 3 }}>
          <DrugSubscriptionButton
            drugId={drug.id}
            drugName={drug.brand_name || drug.drug_name}
          />
        </Box>
      </Paper>

      {/* Drug Information */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Drug Information
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Drug Name
                </Typography>
                <Typography variant="body1">{drug.drug_name}</Typography>
              </Box>

              {drug.brand_name && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Brand Name
                  </Typography>
                  <Typography variant="body1">{drug.brand_name}</Typography>
                </Box>
              )}

              {drug.generic_name && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Generic Name
                  </Typography>
                  <Typography variant="body1">{drug.generic_name}</Typography>
                </Box>
              )}

              {drug.primary_indication && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Primary Indication
                  </Typography>
                  <Typography variant="body1">{drug.primary_indication}</Typography>
                </Box>
              )}

              {drug.therapeutic_area && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Therapeutic Area
                  </Typography>
                  <Typography variant="body1">{drug.therapeutic_area}</Typography>
                </Box>
              )}

              {drug.sponsor && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Sponsor
                  </Typography>
                  <Typography variant="body1">{drug.sponsor.name}</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Approval History */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Approval Summary
              </Typography>
              <Divider sx={{ mb: 2 }} />

              {drug.approvals && drug.approvals.length > 0 ? (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Total Approvals: {drug.approvals.length}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Most Recent: {formatDate(drug.approvals[0]?.approval_date)}
                  </Typography>
                </Box>
              ) : (
                <Typography color="text.secondary">No approvals recorded</Typography>
              )}

              {drug.events && drug.events.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Upcoming Events: {drug.events.length}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Approval History Table */}
      {drug.approvals && drug.approvals.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Approval History
          </Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Approval Date</strong></TableCell>
                  <TableCell><strong>Application Type</strong></TableCell>
                  <TableCell><strong>Application Number</strong></TableCell>
                  <TableCell><strong>FDA Center</strong></TableCell>
                  <TableCell><strong>Indication</strong></TableCell>
                  <TableCell><strong>Links</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {drug.approvals.map((approval) => (
                  <TableRow key={approval.id}>
                    <TableCell>{formatDate(approval.approval_date)}</TableCell>
                    <TableCell>
                      <Chip
                        label={approval.application_type || 'N/A'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {approval.application_number || 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={approval.fda_center || 'N/A'}
                        size="small"
                        color={approval.fda_center === 'CDER' ? 'primary' : 'secondary'}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {approval.indication || 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {approval.fda_page_url && (
                        <Link href={approval.fda_page_url} target="_blank" rel="noopener">
                          FDA Page
                        </Link>
                      )}
                      {approval.label_url && (
                        <>
                          {approval.fda_page_url && ' | '}
                          <Link href={approval.label_url} target="_blank" rel="noopener">
                            Label
                          </Link>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Upcoming Events */}
      {drug.events && drug.events.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Upcoming Events
          </Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Event Date</strong></TableCell>
                  <TableCell><strong>Event Type</strong></TableCell>
                  <TableCell><strong>Description</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {drug.events.map((event) => (
                  <TableRow key={event.id}>
                    <TableCell>{formatDate(event.event_date)}</TableCell>
                    <TableCell>
                      <Chip label={event.event_type} size="small" color="primary" />
                    </TableCell>
                    <TableCell>{event.description || 'N/A'}</TableCell>
                    <TableCell>
                      <Chip label={event.event_status} size="small" variant="outlined" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Back to Approvals */}
      <Box sx={{ mt: 3 }}>
        <Link component={RouterLink} to="/approvals" underline="hover">
          ← Back to Recent Approvals
        </Link>
      </Box>
    </Box>
  );
}

export default DrugDetail;
