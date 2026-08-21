import React from 'react';
import { cn } from '../../utils/cn';

const Select = React.forwardRef(({ className, label, error, options = [], ...props }, ref) => {
  return (
    <div className="flex flex-col gap-1 w-full">
      {label && <label className="text-sm font-medium text-neutral-700">{label}</label>}
      <select
        ref={ref}
        className={cn(
          "flex w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
          error && "border-danger-500 focus:ring-danger-500",
          className
        )}
        {...props}
      >
        <option value="" disabled>Chọn một tùy chọn</option>
        {options.map((opt, i) => (
          <option key={i} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {error && <span className="text-xs text-danger-500">{error}</span>}
    </div>
  );
});

Select.displayName = 'Select';
export default Select;
