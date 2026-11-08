import apiClient from './api';

export const destinationService = {
  async searchDestinations(query) {
    if (!query || query.trim().length === 0) return [];
    const response = await apiClient.get('/destinations/search', {
      params: { query: query.trim() },
    });
    return response.data;
  },

  async searchPlaces({ latitude, longitude, category, radiusMeters = 10000, limit = 20 }) {
    const response = await apiClient.get('/places/search', {
      params: {
        latitude,
        longitude,
        category,
        radius_meters: radiusMeters,
        limit,
      },
    });
    return response.data;
  },

  async getPlaceDetails(placeId) {
    const response = await apiClient.get(`/places/${encodeURIComponent(placeId)}`);
    return response.data;
  },
};

export default destinationService;

