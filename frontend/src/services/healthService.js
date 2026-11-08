import apiClient from './api';

/**
 * Perform health check against the backend
 * @returns {Promise<{status: string, message: string}>}
 */
export const checkBackendHealth = async () => {
  const startTime = performance.now();
  const response = await apiClient.get('/health');
  const endTime = performance.now();
  
  return {
    data: response.data,
    status: response.status,
    latency: Math.round(endTime - startTime),
  };
};

