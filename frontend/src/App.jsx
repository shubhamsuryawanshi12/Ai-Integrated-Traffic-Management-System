import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import MockDataViewer from './pages/MockDataViewer';
import ParkingPage from './pages/ParkingPage';
import EnforcementDashboard from './pages/EnforcementDashboard';
import CitizenPWA from './pages/CitizenPWA';

// Driver Pages
import ParkingDetailPage from './pages/user/ParkingDetailPage';
import BookingConfirmPage from './pages/user/BookingConfirmPage';
import BookingSuccessPage from './pages/user/BookingSuccessPage';
import MyBookingsPage from './pages/user/MyBookingsPage';

// Owner Pages
import AddParkingPage from './pages/owner/AddParkingPage';
import OwnerParkingsPage from './pages/owner/OwnerParkingsPage';
import OwnerBookingsPage from './pages/owner/OwnerBookingsPage';
import OwnerEarningsPage from './pages/owner/OwnerEarningsPage';

// Admin Pages
import AdminApprovalsPage from './pages/admin/AdminApprovalsPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import CommissionPage from './pages/admin/CommissionPage';
import AdminRevenuePage from './pages/admin/AdminRevenuePage';

import { AuthProvider } from './context/AuthContext';
import { CssBaseline } from '@mui/material';
import { ThemeProvider } from './context/ThemeContext';

function App() {
    return (
        <AuthProvider>
            <ThemeProvider>
                <CssBaseline />
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/enforcement" element={<EnforcementDashboard />} />
                    <Route path="/citizen" element={<CitizenPWA />} />
                    <Route path="/parking" element={<ParkingPage />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/mock-data" element={<MockDataViewer />} />

                    {/* Driver Routes */}
                    <Route path="/parking/:zoneId" element={<ParkingDetailPage />} />
                    <Route path="/parking/booking/:bookingId/confirm" element={<BookingConfirmPage />} />
                    <Route path="/parking/booking/:bookingId/success" element={<BookingSuccessPage />} />
                    <Route path="/parking/my-bookings" element={<MyBookingsPage />} />

                    {/* Owner Routes */}
                    <Route path="/owner/add-parking" element={<AddParkingPage />} />
                    <Route path="/owner/my-parkings" element={<OwnerParkingsPage />} />
                    <Route path="/owner/bookings" element={<OwnerBookingsPage />} />
                    <Route path="/owner/earnings" element={<OwnerEarningsPage />} />

                    {/* Admin Routes */}
                    <Route path="/admin/parking/approvals" element={<AdminApprovalsPage />} />
                    <Route path="/admin/users" element={<AdminUsersPage />} />
                    <Route path="/admin/commission" element={<CommissionPage />} />
                    <Route path="/admin/revenue" element={<AdminRevenuePage />} />
                </Routes>
            </ThemeProvider>
        </AuthProvider>
    );
}

export default App;
