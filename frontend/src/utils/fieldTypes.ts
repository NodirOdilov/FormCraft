/**
 * Field type registry: metadata, icons, default configs, and validation.
 * Central source of truth for all supported form field types.
 */

export interface FieldTypeMeta {
  type: string;
  label: string;
  icon: string;
  category: 'input' | 'choice' | 'advanced' | 'layout';
  hasOptions: boolean;
  hasValidation: boolean;
  defaultConfig: Record<string, unknown>;
}

export const FIELD_TYPES: FieldTypeMeta[] = [
  // Input fields
  {
    type: 'text',
    label: 'Short Text',
    icon: 'Type',
    category: 'input',
    hasOptions: false,
    hasValidation: true,
    defaultConfig: {},
  },
  {
    type: 'textarea',
    label: 'Long Text',
    icon: 'AlignLeft',
    category: 'input',
    hasOptions: false,
    hasValidation: true,
    defaultConfig: { rows: 4 },
  },
  {
    type: 'email',
    label: 'Email',
    icon: 'Mail',
    category: 'input',
    hasOptions: false,
    hasValidation: true,
    defaultConfig: {},
  },
  {
    type: 'number',
    label: 'Number',
    icon: 'Hash',
    category: 'input',
    hasOptions: false,
    hasValidation: true,
    defaultConfig: { step: 1 },
  },
  {
    type: 'phone',
    label: 'Phone',
    icon: 'Phone',
    category: 'input',
    hasOptions: false,
    hasValidation: true,
    defaultConfig: {},
  },
  {
    type: 'url',
    label: 'URL',
    icon: 'Link',
    category: 'input',
    hasOptions: false,
    hasValidation: true,
    defaultConfig: {},
  },
  {
    type: 'date',
    label: 'Date',
    icon: 'Calendar',
    category: 'input',
    hasOptions: false,
    hasValidation: false,
    defaultConfig: {},
  },
  {
    type: 'time',
    label: 'Time',
    icon: 'Clock',
    category: 'input',
    hasOptions: false,
    hasValidation: false,
    defaultConfig: {},
  },

  // Choice fields
  {
    type: 'select',
    label: 'Dropdown',
    icon: 'ChevronDown',
    category: 'choice',
    hasOptions: true,
    hasValidation: false,
    defaultConfig: {},
  },
  {
    type: 'multi_select',
    label: 'Multi Select',
    icon: 'List',
    category: 'choice',
    hasOptions: true,
    hasValidation: false,
    defaultConfig: { max_selections: null },
  },
  {
    type: 'radio',
    label: 'Radio Buttons',
    icon: 'Circle',
    category: 'choice',
    hasOptions: true,
    hasValidation: false,
    defaultConfig: { layout: 'vertical' },
  },
  {
    type: 'checkbox',
    label: 'Checkboxes',
    icon: 'CheckSquare',
    category: 'choice',
    hasOptions: true,
    hasValidation: false,
    defaultConfig: { layout: 'vertical' },
  },

  // Advanced fields
  {
    type: 'file_upload',
    label: 'File Upload',
    icon: 'Upload',
    category: 'advanced',
    hasOptions: false,
    hasValidation: false,
    defaultConfig: { allowed_types: ['*'], max_size_mb: 10 },
  },
  {
    type: 'rating',
    label: 'Rating',
    icon: 'Star',
    category: 'advanced',
    hasOptions: false,
    hasValidation: false,
    defaultConfig: { max_rating: 5, icon: 'star' },
  },
  {
    type: 'scale',
    label: 'Linear Scale',
    icon: 'Sliders',
    category: 'advanced',
    hasOptions: false,
    hasValidation: false,
    defaultConfig: { min: 1, max: 10, min_label: '', max_label: '' },
  },
  {
    type: 'hidden',
    label: 'Hidden Field',
    icon: 'EyeOff',
    category: 'advanced',
    hasOptions: false,
    hasValidation: false,
    defaultConfig: {},
  },

  // Layout elements
  {
    type: 'heading',
    label: 'Section Heading',
    icon: 'Heading',
    category: 'layout',
    hasOptions: false,
    hasValidation: false,
    defaultConfig: { level: 2 },
  },
  {
    type: 'paragraph',
    label: 'Paragraph Text',
    icon: 'FileText',
    category: 'layout',
    hasOptions: false,
    hasValidation: false,
    defaultConfig: {},
  },
  {
    type: 'divider',
    label: 'Divider',
    icon: 'Minus',
    category: 'layout',
    hasOptions: false,
    hasValidation: false,
    defaultConfig: {},
  },
];

export function getFieldTypeMeta(type: string): FieldTypeMeta | undefined {
  return FIELD_TYPES.find((ft) => ft.type === type);
}

export function getFieldsByCategory(category: FieldTypeMeta['category']): FieldTypeMeta[] {
  return FIELD_TYPES.filter((ft) => ft.category === category);
}

export const INPUT_FIELDS = getFieldsByCategory('input');
export const CHOICE_FIELDS = getFieldsByCategory('choice');
export const ADVANCED_FIELDS = getFieldsByCategory('advanced');
export const LAYOUT_FIELDS = getFieldsByCategory('layout');
