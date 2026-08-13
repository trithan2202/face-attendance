import React from 'react';
import { Outlet } from 'react-router-dom';
import { ToastProvider } from '../components/ui/Toast';

const KioskLayout = () => {
  return (
    <ToastProvider>
      <div className="min-h-screen bg-neutral-900 text-white font-sans overflow-hidden">
        <Outlet />
      </div>
    </ToastProvider>
  );
};

export default KioskLayout;
