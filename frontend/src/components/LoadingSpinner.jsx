import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ label = 'Loading...', size = 'md', className = '' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-7 h-7',
    lg: 'w-10 h-10',
    xl: 'w-14 h-14',
  };

  return (
    <div className={`flex flex-col items-center justify-center p-6 text-[#52636A] ${className}`}>
      <Loader2 className={`${sizeClasses[size] || sizeClasses.md} animate-spin text-[#18B8A6] mb-3`} />
      {label && <p className="text-xs font-semibold text-[#163B46] animate-pulse">{label}</p>}
    </div>
  );
}
