import React from 'react';
import { cn } from '../../utils/cn';
import EmptyState from './EmptyState';
import Skeleton from './Skeleton';

const Table = ({ columns, data, isLoading, emptyMessage = "Không có dữ liệu", className, dense = false }) => {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full" />)}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return <EmptyState message={emptyMessage} />;
  }

  return (
    <div className={cn("overflow-x-auto border border-neutral-200 rounded-lg bg-white shadow-card", className)}>
      <table className={cn("w-full text-left", dense ? "text-xs" : "text-sm")}>
        <thead className="text-xs text-neutral-500 bg-neutral-50 border-b border-neutral-200 uppercase">
          <tr>
            {columns.map((col, i) => (
              <th key={i} className={cn("font-medium", dense ? "px-3 py-2" : "px-6 py-3")}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} className="bg-white border-b border-neutral-100 hover:bg-neutral-50 transition-colors last:border-0">
              {columns.map((col, j) => (
                <td
                  key={j}
                  className={cn(
                    "whitespace-nowrap text-neutral-700",
                    dense ? "px-3 py-2" : "px-6 py-4"
                  )}
                >
                  {col.cell ? col.cell(row) : row[col.accessorKey]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Table;
