/**
 * Attraction-Specific Image Service for TravelSenseAI Frontend.
 *
 * Provides intelligent client-side caching and API orchestration for verified,
 * location-specific photographs for attractions, landmarks, and destinations.
 */

import apiClient from './api';

class AttractionImageClientService {
  constructor() {
    // Client-side cache: normalizedKey -> { image_url, image_source, image_attribution, image_verified, is_placeholder }
    this.cache = new Map();
    this.inFlightRequests = new Map();
  }

  normalizeKey(name, city) {
    const cleanName = (name || '')
      .toLowerCase()
      .replace(/\b(the|monument|attraction|poi|parking|ticket counter|gate|entry)\b/g, '')
      .replace(/[^\w\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    const cleanCity = (city || '')
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    return cleanCity ? `${cleanName}::${cleanCity}` : cleanName;
  }

  /**
   * Pre-seed client cache with backend-provided image metadata (e.g. from recommendations)
   */
  seedCache(name, city, data) {
    if (!name || !data?.image_url) return;
    const key = this.normalizeKey(name, city);
    this.cache.set(key, data);
  }

  /**
   * Fetch image metadata for a single attraction
   */
  async fetchAttractionImage(name, city = null, attractionId = null) {
    if (!name) return null;

    const key = this.normalizeKey(name, city);
    if (this.cache.has(key)) {
      return this.cache.get(key);
    }

    // Deduplicate in-flight requests for the exact same attraction
    if (this.inFlightRequests.has(key)) {
      return this.inFlightRequests.get(key);
    }

    const promise = (async () => {
      try {
        const response = await apiClient.get('/places/image', {
          params: {
            name: name.trim(),
            city: city ? city.trim() : undefined,
            attraction_id: attractionId || undefined,
          },
        });
        const data = response.data;
        this.cache.set(key, data);
        return data;
      } catch (err) {
        console.warn(`[ImageService] Failed to fetch image for "${name}":`, err.message);
        // Fallback placeholder object
        const fallback = {
          attraction_name: name,
          city: city,
          image_url: null,
          image_source: 'client_fallback',
          image_attribution: `TravelSenseAI Destination Graphic • ${name}`,
          image_verified: false,
          is_placeholder: true,
        };
        this.cache.set(key, fallback);
        return fallback;
      } finally {
        this.inFlightRequests.delete(key);
      }
    })();

    this.inFlightRequests.set(key, promise);
    return promise;
  }

  /**
   * Batch-fetch image metadata for multiple attractions
   */
  async batchFetchImages(places = []) {
    if (!places || places.length === 0) return [];

    const uncached = [];
    const results = new Map();

    for (const p of places) {
      const key = this.normalizeKey(p.name, p.city);
      if (this.cache.has(key)) {
        results.set(key, this.cache.get(key));
      } else {
        uncached.push(p);
      }
    }

    if (uncached.length > 0) {
      try {
        const response = await apiClient.post('/places/images/batch', {
          places: uncached.map((p) => ({
            name: p.name,
            city: p.city || undefined,
            attraction_id: p.id || p.place_id || undefined,
          })),
        });

        const list = response.data?.images || [];
        for (const item of list) {
          const key = this.normalizeKey(item.attraction_name, item.city);
          this.cache.set(key, item);
          results.set(key, item);
        }
      } catch (err) {
        console.warn('[ImageService] Batch fetch failed:', err.message);
      }
    }

    return places.map((p) => results.get(this.normalizeKey(p.name, p.city)) || null);
  }
}

export const imageService = new AttractionImageClientService();
export default imageService;
