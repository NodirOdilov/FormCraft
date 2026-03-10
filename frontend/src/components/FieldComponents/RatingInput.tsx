import React, { useCallback, useState } from 'react';

interface RatingInputProps {
  value: string;
  onChange: (value: string) => void;
  maxRating?: number;
  primaryColor?: string;
}

export const RatingInput: React.FC<RatingInputProps> = ({
  value,
  onChange,
  maxRating = 5,
  primaryColor = '#4F46E5',
}) => {
  const currentRating = parseInt(value, 10) || 0;
  const [hoverRating, setHoverRating] = useState(0);

  const handleClick = useCallback(
    (rating: number) => {
      // Allow deselecting by clicking the same rating
      if (rating === currentRating) {
        onChange('');
      } else {
        onChange(String(rating));
      }
    },
    [currentRating, onChange],
  );

  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: maxRating }).map((_, i) => {
        const rating = i + 1;
        const isFilled = rating <= (hoverRating || currentRating);

        return (
          <button
            key={i}
            type="button"
            onClick={() => handleClick(rating)}
            onMouseEnter={() => setHoverRating(rating)}
            onMouseLeave={() => setHoverRating(0)}
            className="text-2xl transition-transform hover:scale-110 focus:outline-none"
            style={{ color: isFilled ? primaryColor : '#D1D5DB' }}
            aria-label={`Rate ${rating} out of ${maxRating}`}
          >
            {isFilled ? '\u2605' : '\u2606'}
          </button>
        );
      })}
      {currentRating > 0 && (
        <span className="ml-2 text-sm text-gray-500">
          {currentRating} / {maxRating}
        </span>
      )}
    </div>
  );
};

export default RatingInput;
