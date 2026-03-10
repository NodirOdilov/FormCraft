import React from 'react';

interface ScaleInputProps {
  value: string;
  onChange: (value: string) => void;
  min?: number;
  max?: number;
  minLabel?: string;
  maxLabel?: string;
  primaryColor?: string;
}

export const ScaleInput: React.FC<ScaleInputProps> = ({
  value,
  onChange,
  min = 1,
  max = 10,
  minLabel = '',
  maxLabel = '',
  primaryColor = '#4F46E5',
}) => {
  const selected = value ? parseInt(value, 10) : null;
  const points = Array.from({ length: max - min + 1 }, (_, i) => min + i);

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center gap-1 flex-wrap justify-center">
        {minLabel && (
          <span className="text-xs text-gray-500 mr-2">{minLabel}</span>
        )}
        {points.map((point) => {
          const isSelected = selected === point;
          return (
            <button
              key={point}
              type="button"
              onClick={() => onChange(String(point))}
              className={`w-9 h-9 rounded-full border-2 text-sm font-medium transition-all focus:outline-none ${
                isSelected
                  ? 'text-white scale-110'
                  : 'border-gray-300 text-gray-600 hover:border-gray-400'
              }`}
              style={
                isSelected
                  ? { backgroundColor: primaryColor, borderColor: primaryColor }
                  : {}
              }
              aria-label={`${point}`}
            >
              {point}
            </button>
          );
        })}
        {maxLabel && (
          <span className="text-xs text-gray-500 ml-2">{maxLabel}</span>
        )}
      </div>
    </div>
  );
};

export default ScaleInput;
