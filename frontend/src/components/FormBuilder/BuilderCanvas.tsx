/**
 * The central drag-and-drop canvas where form fields are rendered and reordered.
 * Supports drag handles, drop indicators, and field selection.
 */
import React, { useCallback, useRef, useState } from 'react';
import type { FormField } from '../../api/forms';
import { getFieldTypeMeta } from '../../utils/fieldTypes';

interface BuilderCanvasProps {
  fields: FormField[];
  selectedFieldId: string | null;
  onSelectField: (fieldId: string | null) => void;
  onMoveField: (fromIndex: number, toIndex: number) => void;
  onRemoveField: (fieldId: string) => void;
  formTitle: string;
  primaryColor: string;
}

export const BuilderCanvas: React.FC<BuilderCanvasProps> = ({
  fields,
  selectedFieldId,
  onSelectField,
  onMoveField,
  onRemoveField,
  formTitle,
  primaryColor,
}) => {
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const draggedIndex = useRef<number | null>(null);

  const handleDragStart = useCallback((index: number) => {
    draggedIndex.current = index;
  }, []);

  const handleDragOver = useCallback(
    (e: React.DragEvent, index: number) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      if (draggedIndex.current !== null && draggedIndex.current !== index) {
        setDragOverIndex(index);
      }
    },
    [],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent, dropIndex: number) => {
      e.preventDefault();
      setDragOverIndex(null);

      if (draggedIndex.current !== null && draggedIndex.current !== dropIndex) {
        onMoveField(draggedIndex.current, dropIndex);
      }
      draggedIndex.current = null;
    },
    [onMoveField],
  );

  const handleDragEnd = useCallback(() => {
    draggedIndex.current = null;
    setDragOverIndex(null);
  }, []);

  return (
    <div className="max-w-2xl mx-auto">
      {/* Form header preview */}
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-bold text-gray-900">{formTitle}</h2>
      </div>

      {/* Empty state */}
      {fields.length === 0 && (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <p className="text-gray-400 text-lg mb-2">No fields yet</p>
          <p className="text-gray-400 text-sm">
            Drag fields from the left panel or click to add
          </p>
        </div>
      )}

      {/* Field list */}
      <div className="space-y-3">
        {fields.map((field, index) => {
          const meta = getFieldTypeMeta(field.field_type);
          const isSelected = field.id === selectedFieldId;
          const isDragOver = dragOverIndex === index;

          return (
            <div
              key={field.id}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDrop={(e) => handleDrop(e, index)}
              onDragEnd={handleDragEnd}
              onClick={() => onSelectField(field.id)}
              className={`group relative bg-white border rounded-lg p-4 cursor-pointer transition-all ${
                isSelected
                  ? 'border-indigo-500 ring-2 ring-indigo-200'
                  : 'border-gray-200 hover:border-gray-300'
              } ${isDragOver ? 'border-t-4 border-t-indigo-400' : ''}`}
            >
              {/* Drag handle */}
              <div className="absolute left-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing text-gray-400 px-1">
                <span className="text-lg">&#x2630;</span>
              </div>

              {/* Field content */}
              <div className="pl-6 pr-8">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-gray-400 uppercase tracking-wider">
                    {meta?.label || field.field_type}
                  </span>
                  {field.required && (
                    <span className="text-red-500 text-xs font-bold">*</span>
                  )}
                </div>
                <p className="text-sm font-medium text-gray-800">
                  {field.label}
                </p>
                {field.description && (
                  <p className="text-xs text-gray-400 mt-1">
                    {field.description}
                  </p>
                )}

                {/* Preview of the field input */}
                <div className="mt-2">
                  <FieldPreview field={field} primaryColor={primaryColor} />
                </div>
              </div>

              {/* Delete button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemoveField(field.id);
                }}
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-red-500 p-1"
                title="Remove field"
              >
                &times;
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/**
 * Render a read-only preview of a field's input based on its type.
 */
const FieldPreview: React.FC<{
  field: FormField;
  primaryColor: string;
}> = ({ field, primaryColor }) => {
  const baseInputClasses =
    'w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-gray-400 bg-gray-50 pointer-events-none';

  switch (field.field_type) {
    case 'text':
    case 'email':
    case 'phone':
    case 'url':
    case 'number':
      return (
        <input
          type="text"
          placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}...`}
          className={baseInputClasses}
          readOnly
          tabIndex={-1}
        />
      );

    case 'textarea':
      return (
        <textarea
          placeholder={field.placeholder || 'Type your answer...'}
          rows={2}
          className={baseInputClasses}
          readOnly
          tabIndex={-1}
        />
      );

    case 'select':
      return (
        <select className={baseInputClasses} disabled>
          <option>{field.placeholder || 'Select an option...'}</option>
          {field.options?.map((opt) => (
            <option key={opt.id}>{opt.label}</option>
          ))}
        </select>
      );

    case 'radio':
      return (
        <div className="space-y-1">
          {(field.options?.length ? field.options : [{ id: '1', label: 'Option 1', value: '1', order: 0, is_default: false }]).map((opt) => (
            <label key={opt.id} className="flex items-center gap-2 text-sm text-gray-400">
              <input type="radio" disabled className="pointer-events-none" />
              {opt.label}
            </label>
          ))}
        </div>
      );

    case 'checkbox':
      return (
        <div className="space-y-1">
          {(field.options?.length ? field.options : [{ id: '1', label: 'Option 1', value: '1', order: 0, is_default: false }]).map((opt) => (
            <label key={opt.id} className="flex items-center gap-2 text-sm text-gray-400">
              <input type="checkbox" disabled className="pointer-events-none" />
              {opt.label}
            </label>
          ))}
        </div>
      );

    case 'rating': {
      const maxRating = (field.config as any)?.max_rating || 5;
      return (
        <div className="flex gap-1">
          {Array.from({ length: maxRating }).map((_, i) => (
            <span key={i} className="text-xl text-gray-300">
              &#9734;
            </span>
          ))}
        </div>
      );
    }

    case 'scale': {
      const min = (field.config as any)?.min || 1;
      const max = (field.config as any)?.max || 10;
      return (
        <div className="flex items-center gap-1">
          <span className="text-xs text-gray-400">{(field.config as any)?.min_label || min}</span>
          {Array.from({ length: max - min + 1 }).map((_, i) => (
            <button
              key={i}
              className="w-8 h-8 rounded border border-gray-300 text-xs text-gray-400 pointer-events-none"
            >
              {min + i}
            </button>
          ))}
          <span className="text-xs text-gray-400">{(field.config as any)?.max_label || max}</span>
        </div>
      );
    }

    case 'file_upload':
      return (
        <div className="border-2 border-dashed border-gray-300 rounded-md p-4 text-center text-sm text-gray-400">
          Click or drag to upload a file
        </div>
      );

    case 'date':
      return <input type="date" className={baseInputClasses} readOnly tabIndex={-1} />;

    case 'time':
      return <input type="time" className={baseInputClasses} readOnly tabIndex={-1} />;

    case 'heading':
      return <h3 className="text-lg font-semibold text-gray-600">{field.label}</h3>;

    case 'paragraph':
      return <p className="text-sm text-gray-500">{field.description || field.label}</p>;

    case 'divider':
      return <hr className="border-gray-300" />;

    case 'hidden':
      return (
        <span className="text-xs italic text-gray-400">
          Hidden field (value: {field.default_value || 'none'})
        </span>
      );

    default:
      return <input type="text" className={baseInputClasses} readOnly tabIndex={-1} />;
  }
};

export default BuilderCanvas;
