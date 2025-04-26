import React from 'react';
import { Grid, Paper, Typography, Box, Card, CardContent, CardHeader, Divider } from '@mui/material';
import { styled } from '@mui/material/styles';
import PeopleIcon from '@mui/icons-material/People';
import EventIcon from '@mui/icons-material/Event';
import MessageIcon from '@mui/icons-material/Message';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { useNavigate } from 'react-router-dom';

const StatsCard = styled(Card)(({ theme }) => ({
  height: '100%',
  cursor: 'pointer',
  transition: 'transform 0.3s ease, box-shadow 0.3s ease',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.12)',
  },
}));

const IconWrapper = styled(Box)(({ theme, color }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '50%',
  width: 48,
  height: 48,
  backgroundColor: color || theme.palette.primary.main,
  color: 'white',
  marginBottom: theme.spacing(2),
}));

function Dashboard() {
  const navigate = useNavigate();
  
  // Mock data for today's appointments
  const todayAppointments = [
    { time: '09:00 AM', patient: 'John Doe', reason: 'Fever, Headache', status: 'Confirmed' },
    { time: '10:30 AM', patient: 'Jane Smith', reason: 'Follow-up', status: 'Confirmed' },
    { time: '01:00 PM', patient: 'Robert Johnson', reason: 'Chest Pain', status: 'Confirmed' },
    { time: '03:30 PM', patient: 'Maria Garcia', reason: 'Routine Check-up', status: 'Confirmed' },
  ];
  
  // Mock data for recent messages
  const recentMessages = [
    { from: 'Jane Smith', time: '30 min ago', preview: 'I've been feeling better after...' },
    { from: 'Clinic Staff', time: '2 hours ago', preview: 'Meeting scheduled for tomorrow at 9am' },
    { from: 'System', time: '1 day ago', preview: 'New patient assigned to you: Robert Johnson' },
  ];

  return (
    <div>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard onClick={() => navigate('/patients')}>
            <CardContent sx={{ textAlign: 'center' }}>
              <IconWrapper color="#4caf50"}>
                <PeopleIcon />
              </IconWrapper>
              <Typography variant="h4" component="div">
                128
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Patients
              </Typography>
            </CardContent>
          </StatsCard>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard onClick={() => navigate('/appointments')}>
            <CardContent sx={{ textAlign: 'center' }}>
              <IconWrapper color="#2196f3"}>
                <EventIcon />
              </IconWrapper>
              <Typography variant="h4" component="div">
                42
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Appointments This Week
              </Typography>
            </CardContent>
          </StatsCard>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard onClick={() => navigate('/messages')}>
            <CardContent sx={{ textAlign: 'center' }}>
              <IconWrapper color="#ff9800"}>
                <MessageIcon />
              </IconWrapper>
              <Typography variant="h4" component="div">
                12
              </Typography>
              <Typography variant="body2" color="text.secondary">
                New Messages
              </Typography>
            </CardContent>
          </StatsCard>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard>
            <CardContent sx={{ textAlign: 'center' }}>
              <IconWrapper color="#f44336"}>
                <TrendingUpIcon />
              </IconWrapper>
              <Typography variant="h4" component="div">
                85%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Patient Satisfaction
              </Typography>
            </CardContent>
          </StatsCard>
        </Grid>
      </Grid>
      
      {/* Today's Appointments */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Card>
            <CardHeader title="Today's Appointments" />
            <Divider />
            <CardContent>
              {todayAppointments.map((appointment, index) => (
                <React.Fragment key={index}>
                  <Box sx={{ display: 'flex', mb: 2 }}>
                    <Box sx={{ width: '80px' }}>
                      <Typography variant="body2" color="text.secondary">
                        {appointment.time}
                      </Typography>
                    </Box>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="subtitle2">
                        {appointment.patient}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {appointment.reason}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography 
                        variant="body2" 
                        sx={{
                          color: '#4caf50',
                          backgroundColor: 'rgba(76, 175, 80, 0.1)',
                          padding: '2px 8px',
                          borderRadius: '16px'
                        }}
                      >
                        {appointment.status}
                      </Typography>
                    </Box>
                  </Box>
                  {index < todayAppointments.length - 1 && <Divider sx={{ my: 1 }} />}
                </React.Fragment>
              ))}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Recent Messages */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardHeader title="Recent Messages" />
            <Divider />
            <CardContent>
              {recentMessages.map((message, index) => (
                <React.Fragment key={index}>
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="subtitle2">
                        {message.from}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {message.time}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" noWrap>
                      {message.preview}
                    </Typography>
                  </Box>
                  {index < recentMessages.length - 1 && <Divider sx={{ my: 1 }} />}
                </React.Fragment>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
}

export default Dashboard;
