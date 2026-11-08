import apiClient from './api';

export const itineraryService = {
  async generateItinerary({
    destination,
    startDate,
    endDate,
    travelersCount = 1,
    budget = 5000,
    dailyAvailableHours = 8.0,
    transportation = 'driving-car',
    pace = 'moderate',
    selectedAttractions = null,
  }) {
    const payload = {
      destination,
      start_date: startDate,
      end_date: endDate,
      travelers_count: parseInt(travelersCount, 10),
      budget: parseFloat(budget),
      daily_available_hours: parseFloat(dailyAvailableHours),
      transportation,
      pace,
    };

    if (selectedAttractions && selectedAttractions.length > 0) {
      payload.selected_attractions = selectedAttractions.map((attr) => ({
        id: attr.place_id || attr.id,
        name: attr.name,
        latitude: attr.latitude,
        longitude: attr.longitude,
        category: attr.category || 'attraction',
        address: attr.address || '',
        visit_duration_mins: attr.estimated_duration_mins || attr.visit_duration_mins || 90,
        opening_hours: attr.opening_hours || null,
        is_opening_hours_verified: !!attr.is_opening_hours_verified,
        entrance_fee: attr.entrance_fee !== undefined ? attr.entrance_fee : null,
        is_fee_verified: !!attr.is_fee_verified,
        recommendation_score: attr.final_score || attr.recommendation_score || null,
        is_outdoor: attr.is_outdoor !== undefined ? attr.is_outdoor : null,
      }));
    }

    const response = await apiClient.post('/itinerary/generate', payload);
    return response.data;
  },

  async getItineraryById(itineraryId) {
    const response = await apiClient.get(`/itinerary/${encodeURIComponent(itineraryId)}`);
    return response.data;
  },

  async validateItinerary(itineraryData) {
    const response = await apiClient.post('/itinerary/validate', itineraryData);
    return response.data;
  },
};

export default itineraryService;

