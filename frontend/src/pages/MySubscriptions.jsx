/**
 * My Subscriptions Page
 * Allows users to manage their drug subscriptions and email preferences
 */
import { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  CircularProgress,
  Divider,
  FormControlLabel,
  Switch,
  Slider,
  Grid,
  Link,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';
import { subscriptionApi } from '../services/api';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

function MySubscriptions() {
  useDocumentTitle('My Subscriptions - FDA Drug Approval Tracker');

  const [email, setEmail] = useState('');
  const [subscriptions, setSubscriptions] = useState([]);
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  // Load email from localStorage
  useEffect(() => {
    const storedEmail = localStorage.getItem('subscriberEmail');
    if (storedEmail) {
      setEmail(storedEmail);
      loadData(storedEmail);
    }
  }, []);

  const loadData = async (emailToUse) => {
    if (!emailToUse) return;

    setLoading(true);
    setError(null);

    try {
      // Load subscriptions and preferences in parallel
      const [subsResponse, prefsResponse] = await Promise.all([
        subscriptionApi.getMySubscriptions(emailToUse),
        subscriptionApi.getPreferences(emailToUse)
      ]);

      setSubscriptions(subsResponse.data);
      setPreferences(prefsResponse.data);
    } catch (err) {
      console.error('Error loading data:', err);
      setError(
        err.response?.status === 404
          ? 'No subscription found for this email address'
          : 'Failed to load subscriptions'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSubscriptions = () => {
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    localStorage.setItem('subscriberEmail', email);
    loadData(email);
  };

  const handleUnsubscribeFromDrug = async (drugId, drugName) => {
    if (!window.confirm(`Unsubscribe from ${drugName}?`)) {
      return;
    }

    try {
      await subscriptionApi.unsubscribeFromDrug(drugId, email);
      setMessage(`Unsubscribed from ${drugName}`);
      // Reload subscriptions
      loadData(email);
    } catch (err) {
      setError('Failed to unsubscribe');
    }
  };

  const handleSavePreferences = async () => {
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const updates = {
        notify_new_approvals: preferences.notify_new_approvals,
        notify_new_events: preferences.notify_new_events,
        notify_event_reminders: preferences.notify_event_reminders,
        notify_event_updates: preferences.notify_event_updates,
        reminder_days_before: preferences.reminder_days_before,
        digest_mode: preferences.digest_mode,
      };

      await subscriptionApi.updatePreferences(email, updates);
      setMessage('Preferences saved successfully');
    } catch (err) {
      setError('Failed to save preferences');
    } finally {
      setLoading(false);
    }
  };

  const handleUnsubscribeAll = async () => {
    if (!window.confirm(
      'Are you sure you want to unsubscribe from ALL notifications? This will deactivate your subscription.'
    )) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await subscriptionApi.unsubscribeAll(email);
      setMessage('Successfully unsubscribed from all notifications');
      setSubscriptions([]);
      setPreferences(null);
      localStorage.removeItem('subscriberEmail');
      setEmail('');
    } catch (err) {
      setError('Failed to unsubscribe');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        My Subscriptions
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Manage your drug subscriptions and email notification preferences
      </Typography>

      {/* Email Input */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Enter Your Email
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your.email@example.com"
            disabled={loading}
          />
          <Button
            variant="contained"
            onClick={handleLoadSubscriptions}
            disabled={loading}
            sx={{ minWidth: '150px' }}
          >
            {loading ? <CircularProgress size={24} /> : 'Load'}
          </Button>
        </Box>
      </Paper>

      {/* Messages */}
      {message && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Drug Subscriptions */}
      {subscriptions && subscriptions.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Your Drug Subscriptions ({subscriptions.length})
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <List>
            {subscriptions.map((sub) => (
              <ListItem key={sub.id}>
                <ListItemText
                  primary={
                    <Link component={RouterLink} to={`/drugs/${sub.drug_id}`} underline="hover">
                      {sub.drug_name}
                    </Link>
                  }
                  secondary={`Subscribed on ${new Date(sub.created_at).toLocaleDateString()}`}
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    aria-label="unsubscribe"
                    onClick={() => handleUnsubscribeFromDrug(sub.drug_id, sub.drug_name)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* Notification Preferences */}
      {preferences && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Notification Preferences
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.notify_new_approvals}
                    onChange={(e) => setPreferences({
                      ...preferences,
                      notify_new_approvals: e.target.checked
                    })}
                  />
                }
                label="Notify me about new approvals"
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.notify_new_events}
                    onChange={(e) => setPreferences({
                      ...preferences,
                      notify_new_events: e.target.checked
                    })}
                  />
                }
                label="Notify me about new events (PDUFA dates, AdCom meetings)"
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.notify_event_reminders}
                    onChange={(e) => setPreferences({
                      ...preferences,
                      notify_event_reminders: e.target.checked
                    })}
                  />
                }
                label="Send event reminders"
              />
            </Grid>

            {preferences.notify_event_reminders && (
              <Grid item xs={12}>
                <Typography gutterBottom>
                  Send reminders {preferences.reminder_days_before} days before events
                </Typography>
                <Slider
                  value={preferences.reminder_days_before}
                  onChange={(e, value) => setPreferences({
                    ...preferences,
                    reminder_days_before: value
                  })}
                  min={1}
                  max={30}
                  marks
                  valueLabelDisplay="auto"
                />
              </Grid>
            )}

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.notify_event_updates}
                    onChange={(e) => setPreferences({
                      ...preferences,
                      notify_event_updates: e.target.checked
                    })}
                  />
                }
                label="Notify me about event status changes (delayed, cancelled)"
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.digest_mode}
                    onChange={(e) => setPreferences({
                      ...preferences,
                      digest_mode: e.target.checked
                    })}
                  />
                }
                label="Digest mode (receive daily summary instead of instant notifications)"
              />
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSavePreferences}
                  disabled={loading}
                >
                  Save Preferences
                </Button>

                <Button
                  variant="outlined"
                  color="error"
                  onClick={handleUnsubscribeAll}
                  disabled={loading}
                >
                  Unsubscribe from All
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* No Data */}
      {!loading && email && !preferences && !error && (
        <Alert severity="info">
          No subscription found for this email. Subscribe to drugs to get started!
        </Alert>
      )}
    </Box>
  );
}

export default MySubscriptions;
