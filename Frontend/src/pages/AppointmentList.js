import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  IconButton,
  Tab,
  Tabs,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Divider,
  Chip,
  Paper,
} from '@mui/material';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import AddIcon from '@mui/icons-material/Add';
import EventIcon from '@mui/icons-material/Event';
import VideocamIcon from '@mui/icons-material/Videocam';
import PhoneIcon from '@mui/icons-material/Phone';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import { format, addDays, isSameDay } from 'date-fns';

function AppointmentList() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [tabValue, setTabValue] = useState(0);

  // Mock appointments data
  const appointments = [
    { id: 1, patient: 'John Doe', time: '09:00 AM', duration: '30 min', type: 'In-person', reason: 'Fever, Headache', status: 'Confirmed' },
    { id: 2, patient: 'Jane Smith', time: '10:30 AM', duration: '45 min', type: 'Video', reason: 'Follow-up', status: 'Confirmed' },
    { id: 3, patient: 'Robert Johnson', time: '01:00 PM', duration: '30 min', type: 'In-person', reason: 'Chest Pain', status: 'Confirmed' },
    { id: 4, patient: 'Maria Garcia', time: '03:30 PM', duration: '30 min', type: 'Phone', reason: 'Medication Review', status: 'Confirmed' },
  ];

  // Mock upcoming appointments for the week
  const weekAppointments = [
    ...appointments,
    { id: 5, patient: 'William Brown', time: '11:00 AM', duration: '30 min', type: 'In-person', reason: 'Annual Check-up', status: 'Confirmed', date: addDays(new Date(), 1) },
    { id: 6, patient: 'Emily Davis', time: '02:30 PM', duration: '45 min', type: 'Video', reason: 'Skin Condition', status: 'Confirmed', date: addDays(new Date(), 1) },
    { id: 7, patient: 'Michael Johnson', time: '09:30 AM', duration: '30 min', type: 'In-person', reason: 'Joint Pain', status: 'Confirmed', date: addDays(new Date(), 2) },
    { id: 8, patient: 'Sarah Williams', time: '04:00 PM', duration: '30 min', type: 'Phone', reason: 'Test Results', status: 'Confirmed', date: addDays(new Date(), 3) },
  ];

  const filteredAppointments = tabValue === 0
    ? appointments // Today's appointments
    : weekAppointments.filter(appt => {
        if (tabValue === 1) { // All appointments
          return true;
        } else if (tabValue === 2 && appt.type === 'Video') { // Video appointments
          return true;
        } else if (tabValue === 3 && appt.type === 'Phone') { // Phone appointments
          return true;
        }
        return false;
      });

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const getAppointmentIcon = (type) => {
    switch (type) {
      case 'Video':
        return <VideocamIcon color="primary" />;
      case 'Phone':
        return <PhoneIcon color="secondary" />;
      default:
        return <EventIcon color="action" />;
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Appointments
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />}
          onClick={() => console.log('Add appointment clicked')}
        >
          New Appointment
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DatePicker
                  label="Date"
                  value={selectedDate}
                  onChange={(newDate) => setSelectedDate(newDate)}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />
              </LocalizationProvider>

              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Summary
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Paper elevation={0} sx={{ p: 2, textAlign: 'center', bgcolor: 'background.default' }}>
                      <Typography variant="h4">{appointments.length}</Typography>
                      <Typography variant="body2" color="text.secondary">Today's Appointments</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6}>
                    <Paper elevation={0} sx={{ p: 2, textAlign: 'center', bgcolor: 'background.default' }}>
                      <Typography variant="h4">8</Typography>
                      <Typography variant="body2" color="text.secondary">This Week</Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={handleTabChange} aria-label="appointment tabs">
                <Tab label="Today" />
                <Tab label="All" />
                <Tab label="Video" />
                <Tab label="Phone" />
              </Tabs>
            </Box>
            <List sx={{ bgcolor: 'background.paper' }}>
              {filteredAppointments.map((appointment, index) => (
                <React.Fragment key={appointment.id}>
                  {index > 0 && <Divider variant="inset" component="li" />}
                  <ListItem
                    alignItems="flex-start"
                    secondaryAction={
                      <IconButton edge="end">
                        <MoreHorizIcon />
                      </IconButton>
                    }
                  >
                    <ListItemAvatar>
                      <Avatar>{appointment.patient.charAt(0)}</Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="subtitle1" sx={{ mr: 1 }}>
                            {appointment.patient}
                          </Typography>
                          {getAppointmentIcon(appointment.type)}
                          <Chip 
                            label={appointment.type} 
                            size="small" 
                            sx={{ ml: 1 }}
                            color={appointment.type === 'Video' ? 'primary' : appointment.type === 'Phone' ? 'secondary' : 'default'}
                          />
                        </Box>
                      }
                      secondary={
                        <React.Fragment>
                          <Typography
                            sx={{ display: 'block' }}
                            component="span"
                            variant="body2"
                            color="text.primary"
                          >
                            {appointment.date ? format(appointment.date, 'MMM dd') : format(selectedDate, 'MMM dd')} • {appointment.time} • {appointment.duration}
                          </Typography>
                          <Typography
                            component="span"
                            variant="body2"
                            color="text.secondary"
                          >
                            Reason: {appointment.reason}
                          </Typography>
                        </React.Fragment>
                      }
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default AppointmentList;
