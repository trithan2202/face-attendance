import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-react';
import { cn } from '../../utils/cn';

const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, variant = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, variant }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => useContext(ToastContext);

const ToastItem = ({ toast, onClose }) => {
  const variants = {
    success: 'bg-success-50 text-success-700 border-success-500',
    error: 'bg-danger-50 text-danger-700 border-danger-500',
    warning: 'bg-warning-50 text-warning-700 border-warning-500',
    info: 'bg-primary-50 text-primary-700 border-primary-500',
  };

  const icons = {
    success: <CheckCircle className="w-5 h-5 text-success-500" />,
    error: <XCircle className="w-5 h-5 text-danger-500" />,
    warning: <AlertTriangle className="w-5 h-5 text-warning-500" />,
    info: <Info className="w-5 h-5 text-primary-500" />,
  };

  return (
    <div className={cn(
      "flex items-center justify-between w-80 p-4 rounded-md shadow-card border-l-4 transition-all transform ease-in-out duration-300",
      variants[toast.variant] || variants.info
    )}>
      <div className="flex items-center gap-3">
        {icons[toast.variant] || icons.info}
        <span className="text-sm font-medium">{toast.message}</span>
      </div>
      <button onClick={onClose} className="text-neutral-400 hover:text-neutral-600 focus:outline-none">
         <X className="w-4 h-4" />
      </button>
    </div>
  );
};
