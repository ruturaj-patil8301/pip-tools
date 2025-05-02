# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright 2019 VMware, Inc.  All rights reserved.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.guest.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.guest_client`` module provides classes for managing
guest customization specifications in the vCenter Server.

"""

__author__ = 'VMware, Inc.'
__docformat__ = 'restructuredtext en'

import sys

from vmware.vapi.bindings import type
from vmware.vapi.bindings.converter import TypeConverter
from vmware.vapi.bindings.enum import Enum
from vmware.vapi.bindings.error import VapiError
from vmware.vapi.bindings.struct import VapiStruct
from vmware.vapi.bindings.stub import (
    ApiInterfaceStub, StubFactoryBase, VapiInterface)
from vmware.vapi.bindings.common import raise_core_exception
from vmware.vapi.data.validator import (UnionValidator, HasFieldsOfValidator)
from vmware.vapi.exception import CoreException
from vmware.vapi.lib.constants import TaskType
from vmware.vapi.lib.rest import OperationRestMetadata


class CustomizationSpecs(VapiInterface):
    """
    The ``CustomizationSpecs`` class provides methods to manage guest
    customization specifications in the vCenter Server. This class was added in
    vSphere API 6.7.1.
    """
    RESOURCE_TYPE = "com.vmware.vcenter.guest.CustomizationSpec"
    """
    The resource type for a vCenter guest customization specification. This class
    attribute was added in vSphere API 6.7.1.

    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.guest.customization_specs'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _CustomizationSpecsStub)

    class OsType(Enum):
        """
        The ``CustomizationSpecs.OsType`` class defines the types of guest
        operating systems for which guest customization is supported. This
        enumeration was added in vSphere API 6.7.1.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        WINDOWS = None
        """
        A customization specification for a Windows guest operating system. This
        class attribute was added in vSphere API 6.7.1.

        """
        LINUX = None
        """
        A customization specification for a Linux guest operating system. This
        class attribute was added in vSphere API 6.7.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`OsType` instance.
            """
            Enum.__init__(string)

    OsType._set_values([
        OsType('WINDOWS'),
        OsType('LINUX'),
    ])
    OsType._set_binding_type(type.EnumType(
        'com.vmware.vcenter.guest.customization_specs.os_type',
        OsType))


    class FilterSpec(VapiStruct):
        """
        The ``CustomizationSpecs.FilterSpec`` class contains attributes used to
        filter the results when listing guest customization specifications (see
        :func:`CustomizationSpecs.list`). If multiple attributes are specified,
        only guest customization specifications matching all of the attributes
        match the filter. This class was added in vSphere API 6.7.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'OS_type': 'os_type',
                                }

        def __init__(self,
                     names=None,
                     os_type=None,
                    ):
            """
            :type  names: :class:`set` of :class:`str` or ``None``
            :param names: Names that guest customization specifications must have to match
                the filter (see :attr:`CustomizationSpecs.Summary.name`). This
                attribute was added in vSphere API 6.7.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.guest.CustomizationSpec``. When methods return
                a value of this class as a return value, the attribute will contain
                identifiers for the resource type:
                ``com.vmware.vcenter.guest.CustomizationSpec``.
                If None or empty, guest customization specifications with any name
                match the filter.
            :type  os_type: :class:`CustomizationSpecs.OsType` or ``None``
            :param os_type: Guest operating system type that guest customization specifications
                must have to match the filter (see
                :attr:`CustomizationSpecs.Summary.os_type`). This attribute was
                added in vSphere API 6.7.1.
                If None, guest customization specifications with any guest
                operating system type match the filter.
            """
            self.names = names
            self.os_type = os_type
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.guest.customization_specs.filter_spec', {
            'names': type.OptionalType(type.SetType(type.IdType())),
            'OS_type': type.OptionalType(type.ReferenceType(__name__, 'CustomizationSpecs.OsType')),
        },
        FilterSpec,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``CustomizationSpecs.Summary`` class contains commonly used information
        about a guest customization specification. This class was added in vSphere
        API 6.7.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'OS_type': 'os_type',
                                }

        def __init__(self,
                     name=None,
                     description=None,
                     os_type=None,
                     last_modified=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: Name of the guest customization specification. This attribute was
                added in vSphere API 6.7.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.guest.CustomizationSpec``. When methods return
                a value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.vcenter.guest.CustomizationSpec``.
            :type  description: :class:`str`
            :param description: Description of the guest customization specification. This
                attribute was added in vSphere API 6.7.1.
            :type  os_type: :class:`CustomizationSpecs.OsType`
            :param os_type: Guest operating system type for which that this guest customization
                specification applies. This attribute was added in vSphere API
                6.7.1.
            :type  last_modified: :class:`datetime.datetime`
            :param last_modified: Date and tme when this guest customization specification was last
                modified. This attribute was added in vSphere API 6.7.1.
            """
            self.name = name
            self.description = description
            self.os_type = os_type
            self.last_modified = last_modified
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.guest.customization_specs.summary', {
            'name': type.IdType(resource_types='com.vmware.vcenter.guest.CustomizationSpec'),
            'description': type.StringType(),
            'OS_type': type.ReferenceType(__name__, 'CustomizationSpecs.OsType'),
            'last_modified': type.DateTimeType(),
        },
        Summary,
        False,
        None))



    def list(self,
             filter=None,
             ):
        """
        Returns information about at most 1000 visible (subject to permission
        checks) guest customization specifications in vCenter matching the
        :class:`CustomizationSpecs.FilterSpec`. This method was added in
        vSphere API 6.7.1.

        :type  filter: :class:`CustomizationSpecs.FilterSpec` or ``None``
        :param filter: Specification of matching guest customization specifications for
            which information should be returned.
            If None, the behavior is equivalent to a
            :class:`CustomizationSpecs.FilterSpec` with all attributes None
            which means all guest customization specifications match the
            filter.
        :rtype: :class:`list` of :class:`CustomizationSpecs.Summary`
        :return: Commonly used information about the guest customization
            specifications matching the :class:`CustomizationSpecs.FilterSpec`.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the :attr:`CustomizationSpecs.FilterSpec.os_type` attribute
            contains a value that is not supported by the server.
        :raise: :class:`com.vmware.vapi.std.errors_client.UnableToAllocateResource` 
            if more than 1000 guest customization specifications match the
            :class:`CustomizationSpecs.FilterSpec`.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        """
        return self._invoke('list',
                            {
                            'filter': filter,
                            })
class _CustomizationSpecsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'filter': type.OptionalType(type.ReferenceType(__name__, 'CustomizationSpecs.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unable_to_allocate_resource':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnableToAllocateResource'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/guest/customization-specs',
            path_variables={
            },
            query_parameters={
            }
        )

        operations = {
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'CustomizationSpecs.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.guest.customization_specs',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'CustomizationSpecs': CustomizationSpecs,
    }

