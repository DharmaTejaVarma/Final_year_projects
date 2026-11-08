import apiClient from './api';

export const recommendationService = {
  async getRecommendations({
    destination,
    interests = ['Historical Places', 'Food', 'Photography'],
    budget = 5000,
    availableDurationDays = 2,
    transportation = 'driving-car',
    dailyTouringHours = 8.0,
    maxDistanceKm = 35.0,
    weights = null,
    limit = 12,
  }) {
    const payload = {
      destination,
      interests,
      budget: parseFloat(budget),
      available_duration_days: parseInt(availableDurationDays, 10),
      transportation,
      daily_touring_hours: parseFloat(dailyTouringHours),
      max_distance_km: parseFloat(maxDistanceKm),
      limit: parseInt(limit, 10),
    };

    if (weights) {
      payload.weights = weights;
    }

    const response = await apiClient.post('/recommendations/recommend', payload);
    return response.data;
  },
};

export default recommendationService;

