import { describe, it, expect } from 'vitest';
import {
  formatLatency,
  formatTimestamp,
  formatCurrency,
  formatDurationMins,
  formatDistanceKm,
  formatDateDisplay,
  getCategoryBadgeColor,
} from '../utils/formatters';

describe('Frontend Formatter Utilities', () => {
  it('formats latency correctly', () => {
    expect(formatLatency(120)).toBe('120 ms');
    expect(formatLatency(null)).toBe('N/A');
    expect(formatLatency(undefined)).toBe('N/A');
  });

  it('formats Indian rupee currency correctly', () => {
    expect(formatCurrency(5000)).toMatch(/₹5,?000/);
    expect(formatCurrency(0)).toBe('₹0');
    expect(formatCurrency(null)).toBe('₹0');
    expect(formatCurrency(undefined)).toBe('₹0');
    expect(formatCurrency(NaN)).toBe('₹0');
  });

  it('formats duration in minutes and hours properly', () => {
    expect(formatDurationMins(45)).toBe('45m');
    expect(formatDurationMins(60)).toBe('1h');
    expect(formatDurationMins(150)).toBe('2h 30m');
    expect(formatDurationMins(0)).toBe('0 min');
    expect(formatDurationMins(-10)).toBe('0 min');
  });

  it('formats distance in kilometers with one decimal place', () => {
    expect(formatDistanceKm(12.345)).toBe('12.3 km');
    expect(formatDistanceKm(0)).toBe('0.0 km');
    expect(formatDistanceKm(null)).toBe('0 km');
  });

  it('formats date strings reliably', () => {
    const formatted = formatDateDisplay('2026-11-15');
    expect(formatted).toContain('Nov');
    expect(formatted).toContain('15');
    expect(formatted).toContain('2026');
    expect(formatDateDisplay('')).toBe('');
  });

  it('assigns appropriate Tailwind color classes by category', () => {
    expect(getCategoryBadgeColor('Heritage Monument')).toContain('amber');
    expect(getCategoryBadgeColor('Hyderabadi Cuisine')).toContain('emerald');
    expect(getCategoryBadgeColor('Art Museum')).toContain('indigo');
    expect(getCategoryBadgeColor('Public Park & Lake')).toContain('teal');
    expect(getCategoryBadgeColor('Night Bazaar')).toContain('purple');
    expect(getCategoryBadgeColor('Unknown Genre')).toContain('sky');
  });
});

