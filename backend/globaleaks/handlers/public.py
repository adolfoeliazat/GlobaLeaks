# -*- coding: UTF-8
# public
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.
from storm.expr import In, Select

from globaleaks import models, LANGUAGES_SUPPORTED
from globaleaks.handlers.admin.files import db_get_file
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import l10n
from globaleaks.models.config import NodeFactory
from globaleaks.models.l10n import NodeL10NFactory
from globaleaks.orm import transact
from globaleaks.settings import GLSettings
from globaleaks.utils.sets import disjoint_union
from globaleaks.utils.structures import get_localized_values


def db_prepare_contexts_serialization(store, contexts):
    data = {'imgs': {}, 'receivers': {}}

    contexts_ids = []
    for c in contexts:
        data['imgs'][c.id] = None
        data['receivers'][c.id] = []
        contexts_ids.append(c.id)

    for o in store.find(models.ReceiverContext, In(models.ReceiverContext.context_id, contexts_ids)):
        data['receivers'][o.context_id].append(o.receiver_id)

    return data


def db_prepare_receivers_serialization(store, receivers):
    data = {'users': {}, 'imgs': {}, 'contexts': {}}

    receivers_ids = []
    for r in receivers:
        data['imgs'][r.id] = None
        data['contexts'][r.id] = []
        receivers_ids.append(r.id)

    for o in store.find(models.User, In(models.User.id, receivers_ids)):
        data['users'][o.id] = o

    for o in store.find(models.ReceiverContext, In(models.ReceiverContext.receiver_id, receivers_ids)):
        data['contexts'][o.receiver_id].append(o.context_id)

    return data


def db_prepare_fields_serialization(store, fields):
    ret = {
        'fields': {},
        'attrs': {},
        'options': {},
        'triggers': {}
    }

    fields_ids = [f.id for f in fields]
    for f in fields:
        if f.template_id is not None:
            fields_ids.append(f.template_id)

    for f in fields_ids:
         ret['fields'][f] = []
         ret['attrs'][f] = []
         ret['options'][f] = []
         ret['triggers'][f] = []

    while len(fields_ids):
        fs = store.find(models.Field, In(models.Field.fieldgroup_id, fields_ids))

        tmp = []
        for f in fs:
            ret['fields'][f.fieldgroup_id].append(f)
            tmp.append(f.id)
            if f.template_id is not None:
                fields_ids.append(f.template_id)
                tmp.append(f.template_id)

        del fields_ids[:]
        for f in tmp:
            ret['fields'][f] = []
            ret['attrs'][f] = []
            ret['options'][f] = []
            ret['triggers'][f] = []
            fields_ids.append(f)

    objs = store.find(models.FieldAttr, In(models.FieldAttr.field_id, ret['fields'].keys()))
    for obj in objs:
       ret['attrs'][obj.field_id].append(obj)

    objs = store.find(models.FieldOption, In(models.FieldOption.field_id, ret['fields'].keys()))
    for obj in objs:
       ret['options'][obj.field_id].append(obj)

    objs = store.find(models.FieldOption, In(models.FieldOption.trigger_field, ret['fields'].keys()))
    for obj in objs:
       ret['triggers'][obj.field_id].append(obj)

    return ret


def db_serialize_node(store, language):
    """
    Serialize node info.
    """
    # Contexts and Receivers relationship
    configured = store.find(models.ReceiverContext).count() > 0

    ro_node = NodeFactory(store).public_export()

    misc_dict = {
        'languages_enabled': l10n.EnabledLanguage.list(store),
        'languages_supported': LANGUAGES_SUPPORTED,
        'configured': configured,
        'accept_submissions': GLSettings.accept_submissions,
        'logo': db_get_file(store, u'logo'),
        'favicon': db_get_file(store, u'favicon'),
        'css': db_get_file(store, u'css'),
        'homepage': db_get_file(store, u'homepage'),
        'script': db_get_file(store, u'script')
    }

    l10n_dict = NodeL10NFactory(store).localized_dict(language)

    ret = disjoint_union(ro_node, l10n_dict, misc_dict)

    return ret


@transact
def serialize_node(store, language):
    return db_serialize_node(store, language)


def serialize_context(store, context, language, data=None):
    """
    Serialize context description

    @param context: a valid Storm object
    @return: a dict describing the contexts available for submission,
        (e.g. checks if almost one receiver is associated)
    """
    ret_dict = {
        'id': context.id,
        'presentation_order': context.presentation_order,
        'tip_timetolive': context.tip_timetolive,
        'select_all_receivers': context.select_all_receivers,
        'maximum_selectable_receivers': context.maximum_selectable_receivers,
        'show_context': context.show_context,
        'show_recipients_details': context.show_recipients_details,
        'allow_recipients_selection': context.allow_recipients_selection,
        'show_small_receiver_cards': context.show_small_receiver_cards,
        'enable_comments': context.enable_comments,
        'enable_messages': context.enable_messages,
        'enable_two_way_comments': context.enable_two_way_comments,
        'enable_two_way_messages': context.enable_two_way_messages,
        'enable_attachments': context.enable_attachments,
        'enable_rc_to_wb_files': context.enable_rc_to_wb_files,
        'show_receivers_in_alphabetical_order': context.show_receivers_in_alphabetical_order,
        'questionnaire_id': context.questionnaire_id,
        'receivers': data['receivers'][context.id],
        'picture': data['imgs'][context.id]
    }

    return get_localized_values(ret_dict, context, context.localized_keys, language)


def serialize_questionnaire(store, questionnaire, language):
    """
    Serialize the specified questionnaire

    :param store: the store on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary representing the serialization of the questionnaire.
    """
    ret_dict = {
        'id': questionnaire.id,
        'key': questionnaire.key,
        'editable': questionnaire.editable,
        'name': questionnaire.name,
        'show_steps_navigation_bar': questionnaire.show_steps_navigation_bar,
        'steps_navigation_requires_completion': questionnaire.steps_navigation_requires_completion,
        'steps': [serialize_step(store, s, language) for s in questionnaire.steps]
    }

    return get_localized_values(ret_dict, questionnaire, questionnaire.localized_keys, language)


def serialize_field_option(option, language):
    """
    Serialize a field option, localizing its content depending on the language.

    :param option: the field option object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    ret_dict = {
        'id': option.id,
        'presentation_order': option.presentation_order,
        'score_points': option.score_points,
        'trigger_field': option.trigger_field if option.trigger_field else '',
        'trigger_step': option.trigger_step if option.trigger_step else ''
    }

    return get_localized_values(ret_dict, option, option.localized_keys, language)


def serialize_field_attr(attr, language):
    """
    Serialize a field attribute, localizing its content depending on the language.

    :param option: the field attribute object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    ret_dict = {
        'id': attr.id,
        'name': attr.name,
        'type': attr.type,
        'value': attr.value
    }

    if attr.type == 'bool':
        ret_dict['value'] = True if ret_dict['value'] == 'True' else False
    elif attr.type == u'localized':
        get_localized_values(ret_dict, ret_dict, ['value'], language)

    return ret_dict


def serialize_field(store, field, language, data=None):
    """
    Serialize a field, localizing its content depending on the language.

    :param field: the field object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    if data is None:
        data = db_prepare_fields_serialization(store, [field])

    if field.template:
        f_to_serialize = field.template
    else:
        f_to_serialize = field

    attrs = {}
    for attr in store.find(models.FieldAttr, models.FieldAttr.field_id == f_to_serialize.id):
        attrs[attr.name] = serialize_field_attr(attr, language)

    triggered_by_options = [{
        'field': trigger.field_id,
        'option': trigger.id
    } for trigger in field.triggered_by_options]

    ret_dict = {
        'id': field.id,
        'key': f_to_serialize.key,
        'instance': field.instance,
        'editable': field.editable,
        'type': f_to_serialize.type,
        'template_id': field.template_id if field.template_id else '',
        'step_id': field.step_id if field.step_id else '',
        'fieldgroup_id': field.fieldgroup_id if field.fieldgroup_id else '',
        'multi_entry': field.multi_entry,
        'required': field.required,
        'preview': field.preview,
        'stats_enabled': field.stats_enabled,
        'attrs': attrs,
        'x': field.x,
        'y': field.y,
        'width': field.width,
        'triggered_by_score': field.triggered_by_score,
        'triggered_by_options': triggered_by_options,
        'options': [serialize_field_option(o, language) for o in f_to_serialize.options],
        'children': [serialize_field(store, f, language) for f in f_to_serialize.children]
    }

    return get_localized_values(ret_dict, f_to_serialize, field.localized_keys, language)


def serialize_step(store, step, language):
    """
    Serialize a step, localizing its content depending on the language.

    :param step: the step to be serialized.
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    triggered_by_options = [{
        'field': trigger.field_id,
        'option': trigger.id
    } for trigger in step.triggered_by_options]

    data = db_prepare_fields_serialization(store, step.children)

    ret_dict = {
        'id': step.id,
        'questionnaire_id': step.questionnaire_id,
        'presentation_order': step.presentation_order,
        'triggered_by_score': step.triggered_by_score,
        'triggered_by_options': triggered_by_options,
        'children': [serialize_field(store, f, language, data) for f in step.children]
    }

    return get_localized_values(ret_dict, step, step.localized_keys, language)


def serialize_receiver(store, receiver, language, data=None):
    """
    Serialize a receiver description

    :param receiver: the receiver to be serialized
    :param language: the language in which to localize data
    :return: a serializtion of the object
    """
    if data is None:
        data = db_prepare_receivers_serialization(store, [receiver])

    user = data['users'][receiver.id]

    ret_dict = {
        'id': receiver.id,
        'name': user.public_name,
        'username': receiver.user.username if GLSettings.memory_copy.simplified_login else '',
        'state': user.state,
        'configuration': receiver.configuration,
        'presentation_order': receiver.presentation_order,
        'contexts': data['contexts'][receiver.id],
        'picture': data['imgs'][receiver.id]
    }

    # description and eventually other localized strings should be taken from user model
    get_localized_values(ret_dict, receiver.user, ['description'], language)

    return get_localized_values(ret_dict, receiver, receiver.localized_keys, language)


def db_get_public_context_list(store, language):
    subselect = Select(models.ReceiverContext.context_id, distinct=True)

    contexts = store.find(models.Context, models.Context.id.is_in(subselect))

    data = db_prepare_contexts_serialization(store, contexts)

    return [serialize_context(store, context, language, data) for context in contexts]


def db_get_questionnaire_list(store, language):
    questionnaires = store.find(models.Questionnaire)

    return [serialize_questionnaire(store, questionnaire, language) for questionnaire in questionnaires]


def db_get_public_receiver_list(store, language):
    receivers = store.find(models.Receiver,
                           models.Receiver.id == models.User.id,
                           models.User.state != u'disabled')

    data = db_prepare_receivers_serialization(store, receivers)

    return [serialize_receiver(store, receiver, language, data) for receiver in receivers]


@transact
def get_public_resources(store, language):
    return {
        'node': db_serialize_node(store, language),
        'contexts': db_get_public_context_list(store, language),
        'questionnaires': db_get_questionnaire_list(store, language),
        'receivers': db_get_public_receiver_list(store, language),
    }


class PublicResource(BaseHandler):
    check_roles = '*'
    cache_resource = True

    def get(self):
        """
        Get all the public resources.
        """
        return get_public_resources(self.request.language)
