import { useState, useEffect, useCallback } from 'react';
import { checkBackendHealth } from '../services/healthService';

export const useHealthCheck = (autoCheck = true) => {
  const [status, setStatus] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'
  const [data, setData] = useState(null);
  const [latency, setLatency] = useState(null);
  const [error, setError] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  const performCheck = useCallback(async () => {
    setStatus('loading');
    setError(null);
    try {
      const result = await checkBackendHealth();
      setData(result.data);
      setLatency(result.latency);
      setStatus('success');
      setLastChecked(new Date());
    } catch (err) {
      setError(err.message || 'Failed to connect to backend server');
      setStatus('error');
      setData(null);
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    if (autoCheck) {
      performCheck();
    }
  }, [autoCheck, performCheck]);

  return {
    status,
    data,
    latency,
    error,
    lastChecked,
    refetch: performCheck,
    isLoading: status === 'loading',
    isSuccess: status === 'success',
    isError: status === 'error',
  };
};

