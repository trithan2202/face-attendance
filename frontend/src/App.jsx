import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import KioskLayout from './layouts/KioskLayout';
import AdminLayout from './layouts/AdminLayout';
import Kiosk from './pages/Kiosk/Kiosk';
import Login from './pages/Login/Login';
import Lookup from './pages/Public/Lookup';
import Dashboard from './pages/Admin/Dashboard';
import Employees from './pages/Admin/Employees';
import Departments from './pages/Admin/Departments';
import Shifts from './pages/Admin/Shifts';
import Attendance from './pages/Admin/Attendance';
import LeaveRequests from './pages/Admin/LeaveRequests';
import Settings from './pages/Admin/Settings';

const ProtectedRoute = () => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/kiosk" replace />} />
        
        <Route element={<KioskLayout />}>
          <Route path="/kiosk" element={<Kiosk />} />
        </Route>

        <Route path="/login" element={<Login />} />
        <Route path="/tra-cuu" element={<Lookup />} />

        <Route element={<AdminLayout />}>
          <Route element={<ProtectedRoute />}>
            <Route path="/admin/dashboard" element={<Dashboard />} />
            <Route path="/admin/employees" element={<Employees />} />
            <Route path="/admin/departments" element={<Departments />} />
            <Route path="/admin/shifts" element={<Shifts />} />
            <Route path="/admin/attendance" element={<Attendance />} />
            <Route path="/admin/leave" element={<LeaveRequests />} />
            <Route path="/admin/settings" element={<Settings />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
