import React from 'react';
import { PackageOpen } from 'lucide-react';
import Button from './Button';

const EmptyState = ({ icon: Icon = PackageOpen, message, action, actionLabel }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 bg-white rounded-lg border border-neutral-200 border-dashed">
      <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-neutral-400" />
      </div>
      <p className="text-neutral-500 font-medium mb-4">{message}</p>
      {action && actionLabel && (
        <Button variant="secondary" onClick={action}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};

export default EmptyState;
