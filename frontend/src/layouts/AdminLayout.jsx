import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, Building2, CalendarDays, ClipboardList, CalendarOff, Settings as SettingsIcon, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { ToastProvider } from '../components/ui/Toast';
import logo from '../assets/logo_ACACY.png';

const AdminLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/admin/dashboard', icon: LayoutDashboard, label: 'Tổng quan' },
    { to: '/admin/employees', icon: Users, label: 'Nhân viên' },
    { to: '/admin/departments', icon: Building2, label: 'Phòng ban' },
    { to: '/admin/shifts', icon: CalendarDays, label: 'Ca làm' },
    { to: '/admin/attendance', icon: ClipboardList, label: 'Chấm công' },
    { to: '/admin/leave', icon: CalendarOff, label: 'Nghỉ phép' },
    { to: '/admin/settings', icon: SettingsIcon, label: 'Cấu hình' },
  ];

  return (
    <ToastProvider>
      <div className="flex h-screen bg-neutral-50 font-sans">
        {/* Sidebar */}
        <aside className="w-64 bg-neutral-900 text-white flex flex-col">
          <div className="h-16 flex items-center gap-3 px-4 border-b border-neutral-800">
            <img src={logo} alt="Acacy" className="h-10 w-auto rounded-md shrink-0" />
            <span className="text-[15px] font-semibold leading-snug text-neutral-100">Hệ thống chấm công</span>
          </div>
          <nav className="flex-1 py-4 flex flex-col gap-1 px-3">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                    isActive ? 'bg-primary-600 text-white' : 'text-neutral-400 hover:bg-neutral-800 hover:text-white'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="p-4 border-t border-neutral-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center font-bold text-sm">
                {user?.username?.charAt(0).toUpperCase()}
              </div>
              <span className="font-medium text-sm text-neutral-300">{user?.username}</span>
            </div>
            <button onClick={handleLogout} className="text-neutral-400 hover:text-white p-1 rounded-md hover:bg-neutral-800 transition-colors">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-16 bg-white border-b border-neutral-200 flex items-center px-6">
             {/* Title can be dynamic if we want, for now it's handled in pages */}
             <div className="flex-1"></div>
             <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-neutral-600">Trang quản trị</span>
             </div>
          </header>
          <main className="flex-1 p-6 overflow-y-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </ToastProvider>
  );
};

export default AdminLayout;
