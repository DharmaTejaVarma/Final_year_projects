import apiClient from './api';

export const weatherService = {
  async getWeather({ latitude, longitude, startDate, endDate }) {
    const params = {
      latitude,
      longitude,
    };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    const response = await apiClient.get('/weather/forecast', { params });
    return response.data;
  },
};

export default weatherService;

