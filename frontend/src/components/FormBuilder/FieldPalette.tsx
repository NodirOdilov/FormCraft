/**
 * Sidebar palette showing all available field types grouped by category.
 * Fields can be clicked or dragged onto the canvas.
 */
import React from 'react';
import {
  ADVANCED_FIELDS,
  CHOICE_FIELDS,
  INPUT_FIELDS,
  LAYOUT_FIELDS,
  type FieldTypeMeta,
} from '../../utils/fieldTypes';

interface FieldPaletteProps {
  onAddField: (meta: FieldTypeMeta) => void;
}

interface FieldGroupProps {
  title: string;
  fields: FieldTypeMeta[];
  onAddField: (meta: FieldTypeMeta) => void;
}

const FieldGroup: React.FC<FieldGroupProps> = ({ title, fields, onAddField }) => (
  <div className="mb-6">
    <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
      {title}
    </h3>
    <div className="space-y-1">
      {fields.map((meta) => (
        <button
          key={meta.type}
          onClick={() => onAddField(meta)}
          draggable
          onDragStart={(e) => {
            e.dataTransfer.setData('application/formcraft-field', JSON.stringify(meta));
            e.dataTransfer.effectAllowed = 'copy';
          }}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-700 transition-colors cursor-grab active:cursor-grabbing"
        >
          <span className="w-5 h-5 flex items-center justify-center text-gray-400">
            {meta.icon.charAt(0)}
          </span>
          <span>{meta.label}</span>
        </button>
      ))}
    </div>
  </div>
);

export const FieldPalette: React.FC<FieldPaletteProps> = ({ onAddField }) => {
  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-900 mb-4">Add Fields</h2>
      <FieldGroup title="Input" fields={INPUT_FIELDS} onAddField={onAddField} />
      <FieldGroup title="Choice" fields={CHOICE_FIELDS} onAddField={onAddField} />
      <FieldGroup title="Advanced" fields={ADVANCED_FIELDS} onAddField={onAddField} />
      <FieldGroup title="Layout" fields={LAYOUT_FIELDS} onAddField={onAddField} />
    </div>
  );
};

export default FieldPalette;
