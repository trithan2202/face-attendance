import React from 'react';
import { cn } from '../../utils/cn';

const Input = React.forwardRef(({ className, label, error, icon: Icon, ...props }, ref) => {
  return (
    <div className="flex flex-col gap-1 w-full">
      {label && <label className="text-sm font-medium text-neutral-700">{label}</label>}
      <div className="relative">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Icon className="h-5 w-5 text-neutral-400" />
          </div>
        )}
        <input
          ref={ref}
          className={cn(
            "flex w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
            Icon && "pl-10",
            error && "border-danger-500 focus:ring-danger-500",
            className
          )}
          {...props}
        />
      </div>
      {error && <span className="text-xs text-danger-500">{error}</span>}
    </div>
  );
});

Input.displayName = 'Input';
export default Input;
