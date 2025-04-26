import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  Divider,
  Avatar,
  Switch,
  FormControlLabel,
  IconButton,
  Alert,
  Snackbar,
  InputAdornment,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import EventNoteIcon from '@mui/icons-material/EventNote';
import WatchLaterIcon from '@mui/icons-material/WatchLater';
import NotificationsIcon from '@mui/icons-material/Notifications';
import LanguageIcon from '@mui/icons-material/Language';
import SecurityIcon from '@mui/icons-material/Security';
import WhatsAppIcon from '@mui/icons-material/WhatsApp';

function Profile() {
  // Mock doctor data
  const [doctor, setDoctor] = useState({
    name: 'Dr. Sarah Johnson',
    email: 'sarah.johnson@example.com',
    phone: '+91 9876543210',
    specialization: 'Cardiology',
    licenseNumber: 'MED12345',
    experience: '12',
    bio: 'Cardiologist with over 12 years of experience in treating heart conditions and specializing in preventive cardiology.',
    language: 'English, Hindi',
    location: 'Mumbai, Maharashtra',
    availability: {
      monday: '9:00 AM - 5:00 PM',
      tuesday: '9:00 AM - 5:00 PM',
      wednesday: '9:00 AM - 5:00 PM',
      thursday: '9:00 AM - 5:00 PM',
      friday: '9:00 AM - 5:00 PM',
      saturday: '9:00 AM - 1:00 PM',
      sunday: 'Closed',
    },
    whatsappEnabled: true,
    notificationsEnabled: true,
  });

  const [editing, setEditing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success',
  });

  const handleEditToggle = () => {
    setEditing(!editing);
    // Reset password fields when cancelling edit
    if (editing) {
      setPassword('');
      setConfirmPassword('');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setDoctor({
      ...doctor,
      [name]: value,
    });
  };

  const handleSwitchChange = (e) => {
    const { name, checked } = e.target;
    setDoctor({
      ...doctor,
      [name]: checked,
    });
  };

  const handleSave = () => {
    // Validate password if trying to change it
    if (password && password !== confirmPassword) {
      setSnackbar({
        open: true,
        message: 'Passwords do not match!',
        severity: 'error',
      });
      return;
    }

    // In a real app, you would save the changes to the backend here
    setSnackbar({
      open: true,
      message: 'Profile updated successfully!',
      severity: 'success',
    });
    setEditing(false);
  };

  const handleSnackbarClose = () => {
    setSnackbar({
      ...snackbar,
      open: false,
    });
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          My Profile
        </Typography>
        <Button
          variant={editing ? 'outlined' : 'contained'}
          startIcon={editing ? <CancelIcon /> : <EditIcon />}
          onClick={handleEditToggle}
          color={editing ? 'error' : 'primary'}
        >
          {editing ? 'Cancel' : 'Edit Profile'}
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Personal Information */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
              <Avatar
                src="/avatar.jpg"
                sx={{ width: 120, height: 120, mb: 2 }}
              />
              <Typography variant="h5" component="div" gutterBottom>
                {doctor.name}
              </Typography>
              <Typography color="text.secondary" gutterBottom>
                {doctor.specialization}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                License: {doctor.licenseNumber}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {doctor.experience} years of experience
              </Typography>

              {editing && (
                <Button
                  variant="outlined"
                  component="label"
                  sx={{ mt: 2 }}
                >
                  Change Photo
                  <input
                    type="file"
                    hidden
                    accept="image/*"
                  />
                </Button>
              )}
            </CardContent>
          </Card>

          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Settings
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <WhatsAppIcon />
                  </ListItemIcon>
                  <ListItemText primary="WhatsApp Integration" secondary="Enable WhatsApp for patient communications" />
                  <Switch
                    edge="end"
                    checked={doctor.whatsappEnabled}
                    onChange={handleSwitchChange}
                    name="whatsappEnabled"
                    disabled={!editing}
                  />
                </ListItem>
                
                <ListItem>
                  <ListItemIcon>
                    <NotificationsIcon />
                  </ListItemIcon>
                  <ListItemText primary="Notifications" secondary="Receive notifications for new appointments" />
                  <Switch
                    edge="end"
                    checked={doctor.notificationsEnabled}
                    onChange={handleSwitchChange}
                    name="notificationsEnabled"
                    disabled={!editing}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Profile Details */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Personal Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Full Name"
                    name="name"
                    value={doctor.name}
                    onChange={handleInputChange}
                    margin="normal"
                    disabled={!editing}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Specialization"
                    name="specialization"
                    value={doctor.specialization}
                    onChange={handleInputChange}
                    margin="normal"
                    disabled={!editing}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Email"
                    name="email"
                    value={doctor.email}
                    onChange={handleInputChange}
                    margin="normal"
                    disabled={!editing}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Phone"
                    name="phone"
                    value={doctor.phone}
                    onChange={handleInputChange}
                    margin="normal"
                    disabled={!editing}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="License Number"
                    name="licenseNumber"
                    value={doctor.licenseNumber}
                    onChange={handleInputChange}
                    margin="normal"
                    disabled={!editing}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Years of Experience"
                    name="experience"
                    type="number"
                    value={doctor.experience}
                    onChange={handleInputChange}
                    margin="normal"
                    disabled={!editing}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Bio"
                    name="bio"
                    value={doctor.bio}
                    onChange={handleInputChange}
                    margin="normal"
                    multiline
                    rows={4}
                    disabled={!editing}
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              {/* Location and Availability */}
              <Typography variant="h6" gutterBottom>
                Location & Availability
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Location"
                    name="location"
                    value={doctor.location}
                    onChange={handleInputChange}
                    margin="normal"
                    disabled={!editing}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                    Weekly Availability
                  </Typography>
                  <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
                    <Grid container spacing={2}>
                      {Object.entries(doctor.availability).map(([day, hours]) => (
                        <Grid item xs={12} sm={6} md={4} key={day}>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            <WatchLaterIcon sx={{ mr: 1, color: 'text.secondary' }} />
                            <Typography variant="subtitle2" sx={{ textTransform: 'capitalize' }}>
                              {day}
                            </Typography>
                          </Box>
                          {editing ? (
                            <TextField
                              fullWidth
                              size="small"
                              name={`availability.${day}`}
                              value={hours}
                              onChange={(e) => {
                                setDoctor({
                                  ...doctor,
                                  availability: {
                                    ...doctor.availability,
                                    [day]: e.target.value
                                  }
                                });
                              }}
                            />
                          ) : (
                            <Typography variant="body2">{hours}</Typography>
                          )}
                        </Grid>
                      ))}
                    </Grid>
                  </Paper>
                </Grid>
              </Grid>

              {editing && (
                <React.Fragment>
                  <Divider sx={{ my: 3 }} />
                  
                  {/* Change Password */}
                  <Typography variant="h6" gutterBottom>
                    Change Password
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="New Password"
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        margin="normal"
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowPassword(!showPassword)}
                                edge="end"
                              >
                                {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Confirm New Password"
                        type={showPassword ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        margin="normal"
                      />
                    </Grid>
                  </Grid>
                </React.Fragment>
              )}

              {editing && (
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={handleSave}
                  >
                    Save Changes
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar open={snackbar.open} autoHideDuration={6000} onClose={handleSnackbarClose}>
        <Alert onClose={handleSnackbarClose} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default Profile;
