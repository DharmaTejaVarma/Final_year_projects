import { describe, it, expect, beforeEach, vi } from 'vitest';
import imageService from '../services/imageService';
import apiClient from '../services/api';

describe('Attraction Image Client Service', () => {
  beforeEach(() => {
    imageService.cache.clear();
    imageService.inFlightRequests.clear();
    vi.restoreAllMocks();
  });

  it('normalizes lookup keys consistently', () => {
    const key1 = imageService.normalizeKey('Charminar', 'Hyderabad');
    const key2 = imageService.normalizeKey('charminar ', 'hyderabad');
    const key3 = imageService.normalizeKey('Charminar - Monument!', 'Hyderabad');

    expect(key1).toBe('charminar::hyderabad');
    expect(key2).toBe('charminar::hyderabad');
    expect(key3).toBe('charminar::hyderabad');
  });

  it('pre-seeds client cache from recommendation payload', () => {
    const mockImage = {
      image_url: 'https://upload.wikimedia.org/wikipedia/commons/charminar.jpg',
      image_attribution: 'Wikimedia Commons / Bernard Gagnon',
      image_verified: true,
      is_placeholder: false,
    };

    imageService.seedCache('Charminar', 'Hyderabad', mockImage);

    const cached = imageService.cache.get('charminar::hyderabad');
    expect(cached).toBeDefined();
    expect(cached.image_url).toBe(mockImage.image_url);
    expect(cached.image_verified).toBe(true);
  });

  it('reuses cached record without making repeated API calls', async () => {
    const mockData = {
      attraction_name: 'Golconda Fort',
      city: 'Hyderabad',
      image_url: 'https://upload.wikimedia.org/wikipedia/commons/golconda.jpg',
      image_source: 'wikimedia',
      image_attribution: 'Wikimedia Commons / Ramnath Bhat',
      image_verified: true,
      is_placeholder: false,
    };

    // Pre-populate cache
    imageService.seedCache('Golconda Fort', 'Hyderabad', mockData);

    const getSpy = vi.spyOn(apiClient, 'get');

    const result = await imageService.fetchAttractionImage('Golconda Fort', 'Hyderabad');

    expect(result.image_url).toBe(mockData.image_url);
    expect(getSpy).not.toHaveBeenCalled();
  });

  it('calls backend API when image is not in cache and caches result', async () => {
    const mockResponse = {
      data: {
        attraction_name: 'Taj Mahal',
        city: 'Agra',
        image_url: 'https://upload.wikimedia.org/wikipedia/commons/taj.jpg',
        image_source: 'wikimedia',
        image_attribution: 'Wikimedia Commons / Yann Forget',
        image_verified: true,
        is_placeholder: false,
      },
    };

    vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockResponse);

    const result = await imageService.fetchAttractionImage('Taj Mahal', 'Agra');

    expect(result.image_url).toBe('https://upload.wikimedia.org/wikipedia/commons/taj.jpg');
    expect(imageService.cache.has('taj mahal::agra')).toBe(true);
  });

  it('handles API errors gracefully by returning a clean placeholder record', async () => {
    vi.spyOn(apiClient, 'get').mockRejectedValueOnce(new Error('Network unreachable'));

    const result = await imageService.fetchAttractionImage('Unknown Hidden Cave', 'Mars');

    expect(result.is_placeholder).toBe(true);
    expect(result.image_url).toBeNull();
    expect(result.attraction_name).toBe('Unknown Hidden Cave');
  });
});
