/**
 * Drug Subscription Button Component
 * Allows users to subscribe to email notifications for a specific drug
 */
import { useState, useEffect, useCallback } from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Box,
} from '@mui/material';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import NotificationsOffIcon from '@mui/icons-material/NotificationsOff';
import { subscriptionApi } from '../services/api';

function DrugSubscriptionButton({ drugId, drugName }) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  // Get stored email from localStorage
  useEffect(() => {
    const storedEmail = localStorage.getItem('subscriberEmail');
    if (storedEmail) {
      setEmail(storedEmail);
      checkSubscriptionStatus(storedEmail);
    }
  }, [checkSubscriptionStatus]);

  const checkSubscriptionStatus = useCallback(async (emailToCheck) => {
    try {
      const response = await subscriptionApi.checkSubscriptionStatus(drugId, emailToCheck);
      setIsSubscribed(response.data.subscribed);
    } catch (err) {
      console.error('Error checking subscription status:', err);
    }
  }, [drugId]);

  const handleOpen = () => {
    setOpen(true);
    setMessage(null);
    setError(null);
  };

  const handleClose = () => {
    setOpen(false);
    setMessage(null);
    setError(null);
  };

  const handleSubscribe = async () => {
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      // First, ensure user is subscribed to the system
      const subscribeResponse = await subscriptionApi.subscribe(email);

      if (!subscribeResponse.data.subscribed) {
        // User needs to verify their email first
        setMessage(subscribeResponse.data.message);
        localStorage.setItem('subscriberEmail', email);
        setLoading(false);
        return;
      }

      // Subscribe to this specific drug
      const drugSubResponse = await subscriptionApi.subscribeToDrug(drugId, email);

      if (drugSubResponse.data.success) {
        setMessage(drugSubResponse.data.message);
        setIsSubscribed(true);
        localStorage.setItem('subscriberEmail', email);

        // Close dialog after 2 seconds
        setTimeout(() => {
          handleClose();
        }, 2000);
      }
    } catch (err) {
      console.error('Subscription error:', err);
      setError(
        err.response?.data?.detail ||
        'Failed to subscribe. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleUnsubscribe = async () => {
    if (!email) {
      setError('Please enter your email address');
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const response = await subscriptionApi.unsubscribeFromDrug(drugId, email);

      if (response.data.success) {
        setMessage('Successfully unsubscribed from ' + drugName);
        setIsSubscribed(false);

        // Close dialog after 2 seconds
        setTimeout(() => {
          handleClose();
        }, 2000);
      }
    } catch (err) {
      console.error('Unsubscribe error:', err);
      setError(
        err.response?.data?.detail ||
        'Failed to unsubscribe. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        variant={isSubscribed ? "outlined" : "contained"}
        color={isSubscribed ? "secondary" : "primary"}
        startIcon={isSubscribed ? <NotificationsOffIcon /> : <NotificationsActiveIcon />}
        onClick={handleOpen}
        size="large"
      >
        {isSubscribed ? 'Unsubscribe' : 'Get Email Updates'}
      </Button>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {isSubscribed ? `Unsubscribe from ${drugName}` : `Subscribe to ${drugName} Updates`}
        </DialogTitle>
        <DialogContent>
          {!isSubscribed ? (
            <>
              <Typography variant="body1" paragraph>
                Get email notifications when:
              </Typography>
              <Typography component="ul" variant="body2">
                <li>New FDA approvals are announced</li>
                <li>PDUFA dates or advisory committee meetings are scheduled</li>
                <li>Upcoming events are approaching (configurable reminders)</li>
              </Typography>
              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  label="Email Address"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  placeholder="your.email@example.com"
                  variant="outlined"
                />
              </Box>
            </>
          ) : (
            <>
              <Typography variant="body1" paragraph>
                Are you sure you want to unsubscribe from email updates for {drugName}?
              </Typography>
              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  label="Email Address"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  variant="outlined"
                />
              </Box>
            </>
          )}

          {message && (
            <Alert severity="success" sx={{ mt: 2 }}>
              {message}
            </Alert>
          )}

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          {!isSubscribed ? (
            <Button
              onClick={handleSubscribe}
              variant="contained"
              color="primary"
              disabled={loading}
              startIcon={loading && <CircularProgress size={20} />}
            >
              {loading ? 'Subscribing...' : 'Subscribe'}
            </Button>
          ) : (
            <Button
              onClick={handleUnsubscribe}
              variant="contained"
              color="secondary"
              disabled={loading}
              startIcon={loading && <CircularProgress size={20} />}
            >
              {loading ? 'Unsubscribing...' : 'Unsubscribe'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </>
  );
}

export default DrugSubscriptionButton;
