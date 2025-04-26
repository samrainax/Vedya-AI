import React from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Grid,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  Avatar,
  Tab,
  Tabs,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import LocalPhoneIcon from '@mui/icons-material/LocalPhone';
import WhatsAppIcon from '@mui/icons-material/WhatsApp';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import EventNoteIcon from '@mui/icons-material/EventNote';

function PatientDetail() {
  const { id } = useParams();
  const [tabValue, setTabValue] = React.useState(0);

  // Mock patient data (in a real app, you would fetch this based on the ID)
  const patient = {
    id: parseInt(id),
    name: 'John Doe',
    age: 45,
    gender: 'Male',
    phone: '+91 9876543210',
    whatsapp: '+91 9876543210',
    email: 'john.doe@example.com',
    address: '123 Main St, Mumbai, Maharashtra 400001',
    bloodGroup: 'O+',
    height: '175 cm',
    weight: '72 kg',
    allergies: ['Penicillin', 'Peanuts'],
    chronicConditions: ['Hypertension', 'Type 2 Diabetes'],
    medications: [
      { name: 'Lisinopril', dosage: '10mg', frequency: 'Once daily', purpose: 'Blood pressure' },
      { name: 'Metformin', dosage: '500mg', frequency: 'Twice daily', purpose: 'Diabetes' },
    ],
    appointments: [
      { date: '2023-04-15', reason: 'Regular check-up', notes: 'Blood pressure elevated. Adjusted medication.' },
      { date: '2023-02-10', reason: 'Flu symptoms', notes: 'Prescribed antibiotics for 5 days.' },
      { date: '2022-11-25', reason: 'Annual physical', notes: 'All vitals normal. Recommended diet changes.' },
    ],
    tests: [
      { date: '2023-04-15', name: 'Blood Pressure', result: '140/90 mmHg', status: 'High' },
      { date: '2023-04-15', name: 'Blood Glucose', result: '140 mg/dL', status: 'High' },
      { date: '2023-02-10', name: 'Complete Blood Count', result: 'Normal', status: 'Normal' },
      { date: '2022-11-25', name: 'Cholesterol Panel', result: 'LDL: 130 mg/dL', status: 'Borderline' },
    ],
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Patient Details
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<EventNoteIcon />}
            sx={{ mr: 2 }}
          >
            Schedule Appointment
          </Button>
          <Button 
            variant="contained" 
            startIcon={<EditIcon />}
          >
            Edit Profile
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Patient Basic Info */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
              <Avatar 
                sx={{ width: 100, height: 100, mb: 2, bgcolor: 'primary.main', fontSize: '2.5rem' }}
              >
                {patient.name.charAt(0)}
              </Avatar>
              <Typography variant="h5" component="div" gutterBottom>
                {patient.name}
              </Typography>
              <Typography color="text.secondary" gutterBottom>
                {patient.age} years • {patient.gender} • {patient.bloodGroup}
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <IconButton color="primary" aria-label="call patient">
                  <LocalPhoneIcon />
                </IconButton>
                <IconButton color="secondary" aria-label="whatsapp patient">
                  <WhatsAppIcon />
                </IconButton>
              </Box>
              
              <Divider sx={{ width: '100%', my: 2 }} />
              
              <List sx={{ width: '100%' }}>
                <ListItem>
                  <ListItemText primary="Phone" secondary={patient.phone} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="WhatsApp" secondary={patient.whatsapp} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Email" secondary={patient.email} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Address" secondary={patient.address} />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Patient Detailed Info */}
        <Grid item xs={12} md={8}>
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={handleTabChange} aria-label="patient details tabs">
                <Tab label="Medical History" />
                <Tab label="Appointments" />
                <Tab label="Test Results" />
                <Tab label="Medications" />
              </Tabs>
            </Box>
            
            {/* Medical History Tab */}
            {tabValue === 0 && (
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>Vital Statistics</Typography>
                    <List>
                      <ListItem>
                        <ListItemText primary="Height" secondary={patient.height} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Weight" secondary={patient.weight} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Blood Group" secondary={patient.bloodGroup} />
                      </ListItem>
                    </List>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>Allergies</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {patient.allergies.map((allergy, index) => (
                        <Chip key={index} label={allergy} color="error" />
                      ))}
                    </Box>
                    
                    <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Chronic Conditions</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {patient.chronicConditions.map((condition, index) => (
                        <Chip key={index} label={condition} color="primary" />
                      ))}
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            )}
            
            {/* Appointments Tab */}
            {tabValue === 1 && (
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
                  <Button startIcon={<FileDownloadIcon />} variant="outlined">
                    Export History
                  </Button>
                </Box>
                <TableContainer component={Paper} elevation={0}>
                  <Table sx={{ minWidth: 650 }} aria-label="appointments table">
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Reason</TableCell>
                        <TableCell>Notes</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {patient.appointments.map((appointment, index) => (
                        <TableRow key={index}>
                          <TableCell component="th" scope="row">
                            {appointment.date}
                          </TableCell>
                          <TableCell>{appointment.reason}</TableCell>
                          <TableCell>{appointment.notes}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            )}
            
            {/* Test Results Tab */}
            {tabValue === 2 && (
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
                  <Button startIcon={<FileDownloadIcon />} variant="outlined">
                    Download Reports
                  </Button>
                </Box>
                <TableContainer component={Paper} elevation={0}>
                  <Table sx={{ minWidth: 650 }} aria-label="test results table">
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Test</TableCell>
                        <TableCell>Result</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {patient.tests.map((test, index) => (
                        <TableRow key={index}>
                          <TableCell component="th" scope="row">
                            {test.date}
                          </TableCell>
                          <TableCell>{test.name}</TableCell>
                          <TableCell>{test.result}</TableCell>
                          <TableCell>
                            <Chip 
                              label={test.status} 
                              color={
                                test.status === 'Normal' ? 'success' :
                                test.status === 'Borderline' ? 'warning' : 'error'
                              } 
                              size="small" 
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            )}
            
            {/* Medications Tab */}
            {tabValue === 3 && (
              <CardContent>
                <Typography variant="h6" gutterBottom>Current Medications</Typography>
                <TableContainer component={Paper} elevation={0}>
                  <Table sx={{ minWidth: 650 }} aria-label="medications table">
                    <TableHead>
                      <TableRow>
                        <TableCell>Medication</TableCell>
                        <TableCell>Dosage</TableCell>
                        <TableCell>Frequency</TableCell>
                        <TableCell>Purpose</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {patient.medications.map((medication, index) => (
                        <TableRow key={index}>
                          <TableCell component="th" scope="row">
                            {medication.name}
                          </TableCell>
                          <TableCell>{medication.dosage}</TableCell>
                          <TableCell>{medication.frequency}</TableCell>
                          <TableCell>{medication.purpose}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            )}
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default PatientDetail;
