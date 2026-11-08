import React from 'react';
import { Activity, CheckCircle2, XCircle, RefreshCw, Server, Globe, Clock, ShieldCheck } from 'lucide-react';
import { API_BASE_URL } from '../services/api';

export default function BackendStatusCard({ healthState }) {
  const { status, data, latency, error, lastChecked, refetch, isLoading } = healthState;

  return (
    <div id="health-status" className="w-full max-w-4xl mx-auto rounded-2xl bg-white border border-[#DCE6E3] shadow-soft-lg p-6 sm:p-8 relative overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#DCE6E3]">
        <div>
          <div className="flex items-center space-x-2 text-[#18B8A6] text-xs font-bold tracking-wide uppercase">
            <Activity className="w-4 h-4" />
            <span>Phase 1 Verification</span>
          </div>
          <h2 className="text-2xl font-bold text-[#163B46] mt-1">Backend Connection Status</h2>
          <p className="text-xs sm:text-sm text-[#52636A] mt-0.5">
            Real-time health check communication between React (Vite) and FastAPI
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={refetch}
          disabled={isLoading}
          className="inline-flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] disabled:opacity-60 text-white font-semibold text-xs sm:text-sm transition-all shadow-soft active:scale-95 flex-shrink-0"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>{isLoading ? 'Checking...' : 'Retest Health API'}</span>
        </button>
      </div>

      {/* Main Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-6">
        {/* Connection State */}
        <div className="p-4 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3]">
          <span className="text-[11px] text-[#829196] uppercase tracking-wider font-semibold">Status</span>
          <div className="mt-2 flex items-center space-x-2">
            {status === 'loading' && (
              <>
                <RefreshCw className="w-5 h-5 text-[#E6A23C] animate-spin" />
                <span className="text-base font-bold text-[#E6A23C]">Connecting...</span>
              </>
            )}
            {status === 'success' && (
              <>
                <CheckCircle2 className="w-5 h-5 text-[#16A36A]" />
                <span className="text-base font-bold text-[#16A36A]">Healthy & Connected</span>
              </>
            )}
            {status === 'error' && (
              <>
                <XCircle className="w-5 h-5 text-[#DC5555]" />
                <span className="text-base font-bold text-[#DC5555]">Connection Failed</span>
              </>
            )}
          </div>
        </div>

        {/* Latency */}
        <div className="p-4 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3]">
          <span className="text-[11px] text-[#829196] uppercase tracking-wider font-semibold">Round-Trip Latency</span>
          <div className="mt-2 flex items-center space-x-2">
            <Clock className="w-5 h-5 text-[#18B8A6]" />
            <span className="text-base font-bold text-[#163B46]">
              {latency ? `${latency} ms` : '—'}
            </span>
            {latency && (
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                latency < 100 ? 'bg-emerald-50 text-[#16A36A] border border-emerald-200' : 'bg-amber-50 text-[#E6A23C] border border-amber-200'
              }`}>
                {latency < 100 ? 'Optimal' : 'Acceptable'}
              </span>
            )}
          </div>
        </div>

        {/* API Endpoint */}
        <div className="p-4 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3]">
          <span className="text-[11px] text-[#829196] uppercase tracking-wider font-semibold">Target Server</span>
          <div className="mt-2 flex items-center space-x-2">
            <Globe className="w-5 h-5 text-[#163B46]" />
            <span className="text-xs font-mono font-medium text-[#26383D] truncate" title={API_BASE_URL}>
              {API_BASE_URL}
            </span>
          </div>
        </div>
      </div>

      {/* Details Box */}
      {status === 'success' && data && (
        <div className="mt-4 p-4 rounded-xl bg-[#EEF3F1] border border-[#DCE6E3] space-y-2">
          <div className="flex items-center justify-between text-xs text-[#52636A]">
            <span className="flex items-center space-x-1 font-medium">
              <Server className="w-3.5 h-3.5 text-[#18B8A6]" />
              <span>Server Payload:</span>
            </span>
            <span className="text-[#829196]">
              Last checked: {lastChecked ? lastChecked.toLocaleTimeString() : 'Just now'}
            </span>
          </div>
          <pre className="p-3 rounded-lg bg-white border border-[#DCE6E3] text-[11px] font-mono text-[#26383D] overflow-x-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}

      {status === 'error' && (
        <div className="mt-4 p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-[#DC5555] space-y-1">
          <p className="font-semibold">Unable to establish connection to the FastAPI backend service.</p>
          <p className="text-[#52636A]">
            Ensure the FastAPI server is running on <code className="font-mono bg-white px-1.5 py-0.5 rounded border border-red-200">{API_BASE_URL}</code> and CORS settings permit localhost requests.
          </p>
          {error && <p className="font-mono text-[11px] text-red-600 mt-2">{error}</p>}
        </div>
      )}
    </div>
  );
}
