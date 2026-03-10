/**
 * Page wrapper for the form builder. Extracts formId from URL params.
 */
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FormBuilder } from '../components/FormBuilder/FormBuilder';

const FormBuilderPage: React.FC = () => {
  const { formId } = useParams<{ formId: string }>();
  const navigate = useNavigate();

  if (!formId) {
    navigate('/dashboard');
    return null;
  }

  return <FormBuilder formId={formId} />;
};

export default FormBuilderPage;
