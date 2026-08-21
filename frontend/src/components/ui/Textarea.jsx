import React from 'react';
import { cn } from '../../utils/cn';

const Textarea = React.forwardRef(({ className, label, error, required, rows = 3, ...props }, ref) => {
  return (
    <div className="flex flex-col gap-1 w-full">
      {label && (
        <label className="text-sm font-medium text-neutral-700">
          {label}{required && <span className="text-danger-500"> *</span>}
        </label>
      )}
      <textarea
        ref={ref}
        rows={rows}
        className={cn(
          "w-full rounded-md border bg-white px-3 py-2 text-sm placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
          error ? "border-danger-500 focus:ring-danger-500" : "border-neutral-300",
          className
        )}
        {...props}
      />
      {error && <span className="text-xs text-danger-500">{error}</span>}
    </div>
  );
});

Textarea.displayName = 'Textarea';
export default Textarea;
