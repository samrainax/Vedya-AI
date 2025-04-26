import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TablePagination,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import AddIcon from '@mui/icons-material/Add';

function PatientList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Mock patient data
  const patients = [
    { id: 1, name: 'John Doe', age: 45, gender: 'Male', phone: '+91 9876543210', lastVisit: '2023-04-15', condition: 'Hypertension' },
    { id: 2, name: 'Jane Smith', age: 32, gender: 'Female', phone: '+91 9876543211', lastVisit: '2023-04-18', condition: 'Diabetes' },
    { id: 3, name: 'Alice Johnson', age: 28, gender: 'Female', phone: '+91 9876543212', lastVisit: '2023-04-20', condition: 'Pregnancy' },
    { id: 4, name: 'Bob Brown', age: 52, gender: 'Male', phone: '+91 9876543213', lastVisit: '2023-04-10', condition: 'Arthritis' },
    { id: 5, name: 'Emma Wilson', age: 35, gender: 'Female', phone: '+91 9876543214', lastVisit: '2023-04-22', condition: 'Asthma' },
    { id: 6, name: 'Michael Lee', age: 41, gender: 'Male', phone: '+91 9876543215', lastVisit: '2023-04-05', condition: 'Heart Disease' },
    { id: 7, name: 'Sarah Davis', age: 29, gender: 'Female', phone: '+91 9876543216', lastVisit: '2023-04-25', condition: 'Anxiety' },
    { id: 8, name: 'James Miller', age: 38, gender: 'Male', phone: '+91 9876543217', lastVisit: '2023-04-12', condition: 'Back Pain' },
    { id: 9, name: 'Olivia Garcia', age: 24, gender: 'Female', phone: '+91 9876543218', lastVisit: '2023-04-28', condition: 'Allergies' },
    { id: 10, name: 'David Martinez', age: 47, gender: 'Male', phone: '+91 9876543219', lastVisit: '2023-04-08', condition: 'COPD' },
    { id: 11, name: 'Sophia Rodriguez', age: 31, gender: 'Female', phone: '+91 9876543220', lastVisit: '2023-04-17', condition: 'Migraine' },
    { id: 12, name: 'William Hernandez', age: 55, gender: 'Male', phone: '+91 9876543221', lastVisit: '2023-04-03', condition: 'Kidney Disease' },
  ];

  // Filter patients based on search query
  const filteredPatients = patients.filter(patient =>
    patient.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    patient.condition.toLowerCase().includes(searchQuery.toLowerCase()) ||
    patient.phone.includes(searchQuery)
  );

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
    setPage(0); // Reset to first page when searching
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handlePatientClick = (patientId) => {
    navigate(`/patients/${patientId}`);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Patients
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />}
          onClick={() => navigate('/patients/new')}
        >
          Add Patient
        </Button>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                placeholder="Search by name, condition, or phone"
                value={searchQuery}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                variant="outlined"
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={8} sx={{ display: 'flex', justifyContent: { xs: 'flex-start', md: 'flex-end' } }}>
              <Button startIcon={<FilterListIcon />} sx={{ mr: 1 }}>
                Filter
              </Button>
              <Chip label="Recent Patients" color="primary" variant="outlined" sx={{ mr: 1 }} />
              <Chip label="Critical Conditions" color="error" variant="outlined" />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="patients table">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Age</TableCell>
              <TableCell>Gender</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Last Visit</TableCell>
              <TableCell>Condition</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredPatients
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((patient) => (
                <TableRow 
                  key={patient.id} 
                  hover 
                  onClick={() => handlePatientClick(patient.id)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell component="th" scope="row">
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ mr: 2, bgcolor: patient.gender === 'Male' ? 'primary.main' : 'secondary.main' }}>
                        {patient.name.charAt(0)}
                      </Avatar>
                      {patient.name}
                    </Box>
                  </TableCell>
                  <TableCell>{patient.age}</TableCell>
                  <TableCell>{patient.gender}</TableCell>
                  <TableCell>{patient.phone}</TableCell>
                  <TableCell>{patient.lastVisit}</TableCell>
                  <TableCell>
                    <Chip 
                      label={patient.condition} 
                      color={
                        patient.condition === 'Heart Disease' || 
                        patient.condition === 'COPD' || 
                        patient.condition === 'Kidney Disease' ? 'error' : 'default'
                      } 
                      size="small" 
                    />
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredPatients.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>
    </Box>
  );
}

export default PatientList;
