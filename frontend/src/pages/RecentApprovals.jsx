/**
 * Recent Approvals page
 * Shows paginated, searchable, and filterable list of FDA drug approvals
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
import { approvalApi, drugApi } from '../services/api';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

function RecentApprovals() {
  useDocumentTitle('Recent FDA Drug Approvals');

  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalCount, setTotalCount] = useState(0);

  // Filter states
  const [search, setSearch] = useState('');
  const [fdaCenter, setFdaCenter] = useState('');
  const [applicationType, setApplicationType] = useState('');
  const [therapeuticArea, setTherapeuticArea] = useState('');
  const [therapeuticAreas, setTherapeuticAreas] = useState([]);

  // Pagination states
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);

  useEffect(() => {
    loadTherapeuticAreas();
  }, []);

  useEffect(() => {
    loadApprovals();
  }, [loadApprovals]);

  const loadTherapeuticAreas = async () => {
    try {
      const response = await drugApi.getTherapeuticAreas();
      setTherapeuticAreas(response.data);
    } catch (err) {
      console.error('Error loading therapeutic areas:', err);
    }
  };

  const loadApprovals = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page: page + 1, // API uses 1-based pagination
        page_size: pageSize,
      };

      if (search) params.search = search;
      if (fdaCenter) params.fda_center = fdaCenter;
      if (applicationType) params.application_type = applicationType;
      if (therapeuticArea) params.therapeutic_area = therapeuticArea;

      const response = await approvalApi.getApprovals(params);
      setApprovals(response.data.items);
      setTotalCount(response.data.total);
      setError(null);
    } catch (err) {
      console.error('Error loading approvals:', err);
      setError('Failed to load approvals. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [applicationType, fdaCenter, page, pageSize, search, therapeuticArea]);

  const handleSearchChange = (event) => {
    setSearch(event.target.value);
    setPage(0); // Reset to first page on search
  };

  const handleClearFilters = () => {
    setSearch('');
    setFdaCenter('');
    setApplicationType('');
    setTherapeuticArea('');
    setPage(0);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'MMM dd, yyyy');
    } catch {
      return dateString;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Recent FDA Drug Approvals
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Search and filter FDA drug approvals by therapeutic area, sponsor, and more
      </Typography>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="Search"
              placeholder="Drug name or application #"
              value={search}
              onChange={handleSearchChange}
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>FDA Center</InputLabel>
              <Select
                value={fdaCenter}
                label="FDA Center"
                onChange={(e) => {
                  setFdaCenter(e.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="CDER">CDER</MenuItem>
                <MenuItem value="CBER">CBER</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Application Type</InputLabel>
              <Select
                value={applicationType}
                label="Application Type"
                onChange={(e) => {
                  setApplicationType(e.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="NDA">NDA</MenuItem>
                <MenuItem value="BLA">BLA</MenuItem>
                <MenuItem value="sNDA">sNDA</MenuItem>
                <MenuItem value="sBLA">sBLA</MenuItem>
                <MenuItem value="ANDA">ANDA</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Therapeutic Area</InputLabel>
              <Select
                value={therapeuticArea}
                label="Therapeutic Area"
                onChange={(e) => {
                  setTherapeuticArea(e.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="">All</MenuItem>
                {therapeuticAreas.map((area) => (
                  <MenuItem key={area} value={area}>
                    {area}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button variant="outlined" fullWidth onClick={handleClearFilters}>
              Clear Filters
            </Button>
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
                  <TableCell><strong>Drug Name</strong></TableCell>
                  <TableCell><strong>Sponsor</strong></TableCell>
                  <TableCell><strong>Approval Date</strong></TableCell>
                  <TableCell><strong>Application</strong></TableCell>
                  <TableCell><strong>Center</strong></TableCell>
                  <TableCell><strong>Therapeutic Area</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {approvals.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography color="text.secondary" py={2}>
                        No approvals found matching your filters
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  approvals.map((approval) => (
                    <TableRow key={approval.id} hover>
                      <TableCell>
                        <Link
                          component={RouterLink}
                          to={`/drugs/${approval.drug.id}`}
                          underline="hover"
                        >
                          {approval.drug.brand_name || approval.drug.drug_name}
                        </Link>
                        {approval.drug.generic_name && (
                          <Typography variant="caption" display="block" color="text.secondary">
                            {approval.drug.generic_name}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{approval.drug.sponsor?.name || 'N/A'}</TableCell>
                      <TableCell>{formatDate(approval.approval_date)}</TableCell>
                      <TableCell>
                        <Chip
                          label={`${approval.application_type || 'N/A'} ${approval.application_number || ''}`}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={approval.fda_center || 'N/A'}
                          size="small"
                          color={approval.fda_center === 'CDER' ? 'primary' : 'secondary'}
                        />
                      </TableCell>
                      <TableCell>{approval.drug.therapeutic_area || 'N/A'}</TableCell>
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
        </>
      )}
    </Box>
  );
}

export default RecentApprovals;
