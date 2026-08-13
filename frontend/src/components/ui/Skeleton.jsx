import React from 'react';
import { cn } from '../../utils/cn';

const Skeleton = ({ className, ...props }) => {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-neutral-200", className)}
      {...props}
    />
  );
};

export default Skeleton;
