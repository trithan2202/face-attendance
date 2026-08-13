import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import KioskLayout from './layouts/KioskLayout';
import AdminLayout from './layouts/AdminLayout';
import Kiosk from './pages/Kiosk/Kiosk';
import Login from './pages/Login/Login';
import Dashboard from './pages/Admin/Dashboard';
import Employees from './pages/Admin/Employees';
import Shifts from './pages/Admin/Shifts';
import Attendance from './pages/Admin/Attendance';

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

        <Route element={<AdminLayout />}>
          <Route element={<ProtectedRoute />}>
            <Route path="/admin/dashboard" element={<Dashboard />} />
            <Route path="/admin/employees" element={<Employees />} />
            <Route path="/admin/shifts" element={<Shifts />} />
            <Route path="/admin/attendance" element={<Attendance />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
