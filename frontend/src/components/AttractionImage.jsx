import React, { useState, useEffect } from 'react';
import { MapPin, ImageOff, ShieldCheck, Info } from 'lucide-react';
import imageService from '../services/imageService';

/**
 * AttractionImage Component
 *
 * Renders location-specific, verified photographs for any landmark or attraction.
 * Features:
 * - Lazy loading (`loading="lazy"`)
 * - Pre-seeded or dynamic fetching via backend image service
 * - Shimmer skeleton loader
 * - Complete broken-image prevention (`onError` fails over to branded placeholder)
 * - Clean SVG/CSS fallback containing landmark name (never another attraction's photo)
 * - Subtle hover zoom (`group-hover:scale-105`)
 * - Verified source attribution badge
 */
export default function AttractionImage({
  name,
  city = '',
  attractionId = null,
  initialUrl = null,
  initialAttribution = null,
  className = 'w-full h-full object-cover',
  aspectRatio = 'h-48',
  showAttribution = true,
  alt = '',
}) {
  const [imageUrl, setImageUrl] = useState(initialUrl);
  const [attribution, setAttribution] = useState(initialAttribution);
  const [isPlaceholder, setIsPlaceholder] = useState(false);
  const [loading, setLoading] = useState(!initialUrl);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let isMounted = true;

    // If initialUrl is provided and valid, use it immediately
    if (initialUrl) {
      setImageUrl(initialUrl);
      setAttribution(initialAttribution);
      setIsPlaceholder(false);
      setLoading(false);
      setHasError(false);
      return;
    }

    // Otherwise, fetch via image service
    if (name) {
      setLoading(true);
      imageService
        .fetchAttractionImage(name, city, attractionId)
        .then((data) => {
          if (!isMounted) return;
          if (data && data.image_url) {
            setImageUrl(data.image_url);
            setAttribution(data.image_attribution);
            setIsPlaceholder(data.is_placeholder || false);
          } else {
            setIsPlaceholder(true);
          }
          setLoading(false);
        })
        .catch(() => {
          if (!isMounted) return;
          setIsPlaceholder(true);
          setLoading(false);
        });
    }

    return () => {
      isMounted = false;
    };
  }, [name, city, attractionId, initialUrl, initialAttribution]);

  const handleImageError = () => {
    // If image fails to load (404, CORS, broken link), gracefully switch to branded placeholder
    setHasError(true);
    setIsPlaceholder(true);
  };

  // 1. Shimmer Skeleton Loader
  if (loading) {
    return (
      <div className={`relative ${aspectRatio} w-full overflow-hidden bg-[#EEF3F1] animate-pulse flex items-center justify-center`}>
        <div className="flex flex-col items-center space-y-2 text-[#829196]/60">
          <MapPin className="w-6 h-6 animate-bounce" />
          <span className="text-[11px] font-medium tracking-wide">Loading photograph...</span>
        </div>
      </div>
    );
  }

  // 2. Clean Branded Placeholder (When no verified photo is available or link is broken)
  if (hasError || isPlaceholder || !imageUrl) {
    return (
      <div
        className={`relative ${aspectRatio} w-full overflow-hidden bg-gradient-to-br from-[#163B46] to-[#244F59] p-4 flex flex-col justify-between text-white select-none`}
      >
        <div className="flex items-center justify-between">
          <span className="px-2 py-0.5 rounded-full bg-white/10 backdrop-blur-md text-[10px] font-semibold text-[#18B8A6] border border-[#18B8A6]/30 uppercase tracking-wider">
            {city || 'Destination'}
          </span>
          <div className="flex items-center space-x-1 text-[10px] text-white/70">
            <ShieldCheck className="w-3.5 h-3.5 text-[#18B8A6]" />
            <span>Verified POI</span>
          </div>
        </div>

        <div className="text-center my-auto py-2">
          <div className="w-10 h-10 mx-auto rounded-full bg-[#18B8A6]/20 border border-[#18B8A6]/40 flex items-center justify-center mb-2">
            <MapPin className="w-5 h-5 text-[#18B8A6]" />
          </div>
          <h4 className="text-sm font-bold text-white line-clamp-2 px-2 leading-snug">
            {name || 'Tourist Attraction'}
          </h4>
        </div>

        <div className="text-[9px] text-center text-white/40 tracking-wider">
          TravelSenseAI Location Record
        </div>
      </div>
    );
  }

  // 3. Real Verified Attraction Photograph
  return (
    <div className={`relative ${aspectRatio} w-full overflow-hidden bg-[#EEF3F1] group`}>
      <img
        src={imageUrl}
        alt={alt || name || 'Tourist Attraction'}
        loading="lazy"
        onError={handleImageError}
        className={`${className} transition-transform duration-500 group-hover:scale-105`}
      />

      {/* Subtle Bottom Gradient for visual depth */}
      <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-black/40 to-transparent pointer-events-none" />

      {/* Optional Attribution Badge (Shows on hover or subtle pill) */}
      {showAttribution && attribution && (
        <div
          title={attribution}
          className="absolute bottom-2 right-2 max-w-[85%] px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-sm text-[9px] text-white/80 truncate opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none flex items-center space-x-1"
        >
          <Info className="w-2.5 h-2.5 text-[#18B8A6] shrink-0" />
          <span className="truncate">{attribution}</span>
        </div>
      )}
    </div>
  );
}

