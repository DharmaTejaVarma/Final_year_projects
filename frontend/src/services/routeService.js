import apiClient from './api';

export const routeService = {
  async calculateRoute({ coordinates, transportationMode = 'driving-car' }) {
    const response = await apiClient.post('/routes/calculate', {
      coordinates,
      transportation_mode: transportationMode,
    });
    return response.data;
  },

  async optimizeRoute({ stops, transportationMode = 'driving-car', iterations = 150 }) {
    const response = await apiClient.post('/routes/optimize', {
      stops,
      transportation_mode: transportationMode,
      max_iterations: iterations,
    });
    return response.data;
  },
};

export default routeService;

