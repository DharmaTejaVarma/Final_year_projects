import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorMessage({ message = 'An error occurred while communicating with the server.', onRetry, title = 'Request Failed' }) {
  return (
    <div className="rounded-2xl bg-red-50 border border-red-200 p-4 sm:p-5 text-[#26383D] shadow-soft">
      <div className="flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-[#DC5555] flex-shrink-0 mt-0.5" />
        <div className="flex-1 space-y-1">
          <h4 className="text-sm font-bold text-[#DC5555]">{title}</h4>
          <p className="text-xs text-[#52636A] leading-relaxed">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-red-100/60 text-[#DC5555] text-xs font-semibold border border-red-200 transition-colors shadow-soft"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Request</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
