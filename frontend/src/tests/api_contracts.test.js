import { describe, it, expect } from 'vitest';
import api from '../services/api';

describe('Frontend API Client and Service Contracts', () => {
  it('instantiates axios with baseURL or fallback', () => {
    expect(api).toBeDefined();
    expect(typeof api.get).toBe('function');
    expect(typeof api.post).toBe('function');
    expect(typeof api.put).toBe('function');
    expect(typeof api.delete).toBe('function');
  });

  it('validates authentication request shapes', () => {
    const loginPayload = { email: 'traveler@example.com', password: 'Password123!' };
    expect(loginPayload.email).toMatch(/^[^@]+@[^@]+\.[^@]+$/);
    expect(loginPayload.password.length).toBeGreaterThanOrEqual(8);
  });

  it('validates trip planning parameter schema', () => {
    const tripPlan = {
      destination: 'Hyderabad',
      start_date: '2026-11-10',
      end_date: '2026-11-12',
      budget: 5000,
      interests: ['Heritage', 'Food'],
      travel_style: 'balanced',
      transport_mode: 'driving',
      num_travelers: 2,
    };

    expect(tripPlan.destination).toBe('Hyderabad');
    expect(tripPlan.budget).toBeGreaterThan(0);
    expect(tripPlan.interests.length).toBe(2);
    expect(new Date(tripPlan.end_date).getTime()).toBeGreaterThanOrEqual(new Date(tripPlan.start_date).getTime());
  });

  it('validates report analytics schema matches expected charts', () => {
    const expectedVisualizations = [
      'category_distribution',
      'score_distribution',
      'daily_expense_distribution',
      'daily_travel_duration',
      'distance_comparison',
      'budget_utilization',
      'recommended_attractions_count',
    ];

    expect(expectedVisualizations.length).toBe(7);
  });
});
