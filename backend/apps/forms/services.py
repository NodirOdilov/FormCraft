"""
Business logic services for the forms app.
"""
import copy
import logging
import uuid

from django.utils.crypto import get_random_string
from django.utils.text import slugify

from .models import ConditionalRule, FieldOption, Form, FormField, FormSettings

logger = logging.getLogger(__name__)


def duplicate_form(form: Form, user) -> Form:
    """
    Create a deep copy of a form including all fields, options,
    conditional rules, and settings.
    """
    original_fields = list(form.fields.all().prefetch_related("options", "conditional_rules"))
    original_settings = getattr(form, "settings", None)

    # Create new form
    new_form = Form.objects.create(
        workspace=form.workspace,
        created_by=user,
        title=f"{form.title} (Copy)",
        description=form.description,
        status=Form.Status.DRAFT,
        primary_color=form.primary_color,
        background_color=form.background_color,
        submit_button_text=form.submit_button_text,
        success_message=form.success_message,
        redirect_url=form.redirect_url,
        is_multi_page=form.is_multi_page,
        allow_multiple_submissions=form.allow_multiple_submissions,
        requires_login=form.requires_login,
    )

    # Map old field IDs to new field objects for conditional rules
    field_id_map = {}

    # Duplicate fields and options
    for field in original_fields:
        old_id = field.id
        new_field = FormField.objects.create(
            form=new_form,
            field_type=field.field_type,
            label=field.label,
            description=field.description,
            placeholder=field.placeholder,
            required=field.required,
            order=field.order,
            page=field.page,
            min_length=field.min_length,
            max_length=field.max_length,
            min_value=field.min_value,
            max_value=field.max_value,
            pattern=field.pattern,
            config=copy.deepcopy(field.config),
            default_value=field.default_value,
        )
        field_id_map[old_id] = new_field

        # Duplicate options
        for option in field.options.all():
            FieldOption.objects.create(
                field=new_field,
                label=option.label,
                value=option.value,
                order=option.order,
                is_default=option.is_default,
            )

    # Duplicate conditional rules with remapped field IDs
    for field in original_fields:
        for rule in field.conditional_rules.all():
            new_field = field_id_map.get(field.id)
            new_source = field_id_map.get(rule.source_field_id)
            new_target = field_id_map.get(rule.target_field_id) if rule.target_field_id else None

            if new_field and new_source:
                ConditionalRule.objects.create(
                    field=new_field,
                    action=rule.action,
                    source_field=new_source,
                    operator=rule.operator,
                    value=rule.value,
                    target_field=new_target,
                )

    # Duplicate settings
    if original_settings:
        FormSettings.objects.create(
            form=new_form,
            notification_emails=original_settings.notification_emails,
            send_confirmation_email=original_settings.send_confirmation_email,
            confirmation_email_subject=original_settings.confirmation_email_subject,
            confirmation_email_body=original_settings.confirmation_email_body,
            custom_css=original_settings.custom_css,
            meta_title=original_settings.meta_title,
            meta_description=original_settings.meta_description,
            embed_allowed_domains=original_settings.embed_allowed_domains,
        )
    else:
        FormSettings.objects.create(form=new_form)

    logger.info(f"Form duplicated: {form.id} -> {new_form.id} by user {user.email}")
    return new_form


def evaluate_condition(rule: ConditionalRule, answer_value: str) -> bool:
    """
    Evaluate a conditional rule against a submitted answer value.
    Returns True if the condition is met.
    """
    operator = rule.operator
    rule_value = rule.value

    if operator == ConditionalRule.Operator.EQUALS:
        return str(answer_value).lower() == str(rule_value).lower()
    elif operator == ConditionalRule.Operator.NOT_EQUALS:
        return str(answer_value).lower() != str(rule_value).lower()
    elif operator == ConditionalRule.Operator.CONTAINS:
        return str(rule_value).lower() in str(answer_value).lower()
    elif operator == ConditionalRule.Operator.NOT_CONTAINS:
        return str(rule_value).lower() not in str(answer_value).lower()
    elif operator == ConditionalRule.Operator.GREATER_THAN:
        try:
            return float(answer_value) > float(rule_value)
        except (ValueError, TypeError):
            return False
    elif operator == ConditionalRule.Operator.LESS_THAN:
        try:
            return float(answer_value) < float(rule_value)
        except (ValueError, TypeError):
            return False
    elif operator == ConditionalRule.Operator.IS_EMPTY:
        return not answer_value or str(answer_value).strip() == ""
    elif operator == ConditionalRule.Operator.IS_NOT_EMPTY:
        return bool(answer_value) and str(answer_value).strip() != ""
    return False
