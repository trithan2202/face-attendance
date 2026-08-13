import React from 'react';
import { cn } from '../../utils/cn';

const Badge = ({ children, status, className }) => {
  const statusStyles = {
    'Active': 'bg-success-100 text-success-700',
    'Inactive': 'bg-neutral-200 text-neutral-700',
    'Pending enrollment': 'bg-warning-100 text-warning-700',
    'Present': 'bg-success-100 text-success-700',
    'Missing check-in': 'bg-danger-100 text-danger-700',
    'Check-in': 'bg-success-100 text-success-700',
    'Check-out': 'bg-primary-100 text-primary-700',
    'Late': 'bg-warning-100 text-warning-700',
    'Absent': 'bg-danger-100 text-danger-700',
    'Missing check-out': 'bg-danger-100 text-danger-700',
  };

  const defaultStyle = 'bg-neutral-100 text-neutral-700';

  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
      statusStyles[status] || defaultStyle,
      className
    )}>
      {children || status}
    </span>
  );
};

export default Badge;
