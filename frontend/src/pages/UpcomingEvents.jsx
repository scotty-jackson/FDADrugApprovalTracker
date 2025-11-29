/**
 * Upcoming Events page
 * Shows PDUFA dates, advisory committee meetings, and other FDA events
 */
import { useState, useEffect, useCallback } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
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
  Card,
  CardContent,
} from '@mui/material';
import EventIcon from '@mui/icons-material/Event';
import { format, parseISO, differenceInDays } from 'date-fns';
import { eventApi } from '../services/api';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

function UpcomingEvents() {
  useDocumentTitle('Upcoming FDA Events & PDUFA Calendar');

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalCount, setTotalCount] = useState(0);

  // Filter states
  const [eventType, setEventType] = useState('');
  const [eventStatus, setEventStatus] = useState('SCHEDULED');
  const [daysAhead, setDaysAhead] = useState(90);

  // Pagination states
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  const loadEvents = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page: page + 1,
        page_size: pageSize,
        days: daysAhead,
      };

      if (eventType) params.event_type = eventType;
      if (eventStatus) params.event_status = eventStatus;

      const response = await eventApi.getUpcomingEvents(params);
      setEvents(response.data.items);
      setTotalCount(response.data.total);
      setError(null);
    } catch (err) {
      console.error('Error loading events:', err);
      setError('Failed to load events. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [daysAhead, eventStatus, eventType, page, pageSize]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(parseISO(dateString), 'MMM dd, yyyy');
    } catch {
      return dateString;
    }
  };

  const getDaysUntil = (dateString) => {
    if (!dateString) return null;
    try {
      const eventDate = parseISO(dateString);
      const today = new Date();
      return differenceInDays(eventDate, today);
    } catch {
      return null;
    }
  };

  const getEventTypeColor = (type) => {
    const colors = {
      PDUFA: 'primary',
      ADCOM: 'secondary',
      DECISION: 'success',
      FILING_ACCEPTANCE: 'info',
      OTHER: 'default',
    };
    return colors[type] || 'default';
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upcoming FDA Events
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Track PDUFA dates, advisory committee meetings, and other regulatory milestones
      </Typography>

      {/* Summary Card */}
      <Card sx={{ mb: 3, backgroundColor: '#e3f2fd' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={1}>
            <EventIcon color="primary" />
            <Typography variant="h6">
              {totalCount} upcoming events in the next {daysAhead} days
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Event Type</InputLabel>
              <Select
                value={eventType}
                label="Event Type"
                onChange={(e) => {
                  setEventType(e.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="">All Types</MenuItem>
                <MenuItem value="PDUFA">PDUFA Date</MenuItem>
                <MenuItem value="ADCOM">Advisory Committee</MenuItem>
                <MenuItem value="DECISION">Decision</MenuItem>
                <MenuItem value="FILING_ACCEPTANCE">Filing Acceptance</MenuItem>
                <MenuItem value="OTHER">Other</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={eventStatus}
                label="Status"
                onChange={(e) => {
                  setEventStatus(e.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="SCHEDULED">Scheduled</MenuItem>
                <MenuItem value="COMPLETED">Completed</MenuItem>
                <MenuItem value="DELAYED">Delayed</MenuItem>
                <MenuItem value="CANCELLED">Cancelled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Time Range</InputLabel>
              <Select
                value={daysAhead}
                label="Time Range"
                onChange={(e) => {
                  setDaysAhead(e.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value={30}>Next 30 days</MenuItem>
                <MenuItem value={60}>Next 60 days</MenuItem>
                <MenuItem value={90}>Next 90 days</MenuItem>
                <MenuItem value={180}>Next 6 months</MenuItem>
                <MenuItem value={365}>Next 12 months</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Results */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Event Date</strong></TableCell>
                  <TableCell><strong>Days Until</strong></TableCell>
                  <TableCell><strong>Drug</strong></TableCell>
                  <TableCell><strong>Event Type</strong></TableCell>
                  <TableCell><strong>Description</strong></TableCell>
                  <TableCell><strong>Application #</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {events.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography color="text.secondary" py={2}>
                        No upcoming events found
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  events.map((event) => {
                    const daysUntil = getDaysUntil(event.event_date);
                    return (
                      <TableRow key={event.id} hover>
                        <TableCell>
                          <strong>{formatDate(event.event_date)}</strong>
                        </TableCell>
                        <TableCell>
                          {daysUntil !== null && (
                            <Chip
                              label={`${daysUntil} days`}
                              size="small"
                              color={daysUntil <= 7 ? 'error' : daysUntil <= 30 ? 'warning' : 'default'}
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          {event.drug ? (
                            <Link
                              component={RouterLink}
                              to={`/drugs/${event.drug.id}`}
                              underline="hover"
                            >
                              {event.drug.brand_name || event.drug.drug_name}
                            </Link>
                          ) : (
                            'N/A'
                          )}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={event.event_type}
                            size="small"
                            color={getEventTypeColor(event.event_type)}
                          />
                        </TableCell>
                        <TableCell>{event.description || 'N/A'}</TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {event.application_number || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={event.event_status}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                      </TableRow>
                    );
                  })
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
            rowsPerPageOptions={[10, 20, 50]}
          />
        </>
      )}
    </Box>
  );
}

export default UpcomingEvents;
