import json
import re
from typing import Dict, List, Optional, Union
import datetime
import uuid
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.models import SourceSnippet
from .SimulationEngine import utils
from google import genai
from google.genai import types
import sys
import os
from PyPDF2 import PdfReader


from APIs.ces_system_activation.SimulationEngine.custom_errors import (
    ActivationAttemptNotFoundError, 
    AppointmentNotFoundError, 
    InvalidServiceTypeError, 
    SlotNotFoundError, 
    TechnicianVisitNotFoundError,
    TemplateNotFoundError, 
    VisitNotFoundError,
    ValidationError,
    DuplicateAppointmentError,
    EnvironmentError
)

from .SimulationEngine import db


from .SimulationEngine.models import (
    # Output Models
    TechnicianVisitDetails,
    AppointmentAvailability,
    AvailableAppointmentSlot,
    FlaggedIssueConfirmation,
    ServiceActivationAttempt,
    NotificationResult,
    DataStoreQueryResult,
    EscalateOutput,
    FailOutput,
    CancelOutput,
    # Input Models
    GetActivationVisitDetailsInput,
    FindAvailableTechnicianAppointmentSlotsInput,
    RescheduleTechnicianVisitInput,
    ScheduleNewTechnicianVisitInput,
    FlagTechnicianVisitIssueInput,
    TriggerServiceActivationInput,
    GetServiceActivationStatusInput,
    SendCustomerNotificationInput,
    SearchOrderDetailsInput,
    SearchActivationGuidesInput,
    EscalateInput,
    FailInput,
    CancelInput,
)
from APIs.common_utils.tool_spec_decorator import tool_spec, ErrorObject

DB = db.DB

@tool_spec(
    input_model=GetActivationVisitDetailsInput,
    output_model=TechnicianVisitDetails,
    description='Retrieves all known details for a specific activation-related technician visit using its unique ID.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if visitId is not a non-empty string or doesn't match the expected pattern."]),
        ErrorObject(AppointmentNotFoundError, ["Raised if no appointment is found for visitId."])
    ],
    spec={
    'name': 'get_activation_visit_details',
    'description': 'Retrieves all known details for a specific activation-related technician\n\nvisit using its unique ID.\n\nWhen to Use:\n- When a user asks for the status or details of a known appointment (e.g.,\n"When is my technician coming?", "What are the details of my installation\nappointment?").\n- You must already have the \'visitId\' from a previous step or from the user.',
    'parameters': {
        'type': 'object',
        'properties': {
            'visitId': {
                'type': 'string',
                'description': 'The unique identifier of the technician visit to look up. Example:\n"VISIT-98765".'
            }
        },
        'required': [
            'visitId'
        ]
    },
    'response': {
        'description': "An object with the details of the technician visit.",
        'type': 'object',
        'properties': {
            'visitId': {
                'type': 'string',
                'description': 'The unique identifier of the technician visit.'
            },
            'accountId': {
                'type': 'string',
                'description': 'The customer\'s account ID.'
            },
            'orderId': {
                'type': 'string',
                'description': 'The service order ID associated with the visit.'
            },
            'status': {
                'type': 'string',
                'description': 'The current status of the visit (e.g., \'scheduled\', \'in_progress\', \'completed\').'
            },
            'scheduledStartTime': {
                'type': 'string',
                'description': 'The scheduled start time of the visit in ISO format.',
                'nullable': True
            },
            'scheduledEndTime': {
                'type': 'string',
                'description': 'The scheduled end time of the visit in ISO format.',
                'nullable': True
            },
            'technicianNotes': {
                'type': 'string',
                'description': 'Any notes from the technician about the visit.',
                'nullable': True
            },
            'issueDescription': {
                'type': 'string',
                'description': 'Description of the issue or service being performed.',
                'nullable': True
            }
        },
        'required': ['visitId', 'accountId', 'orderId', 'status']
    }
})
def get_activation_visit_details(
    visitId: str,
) -> Dict[str, Optional[str]]:
    """Retrieves all known details for a specific activation-related technician

    visit using its unique ID.

    When to Use:
    - When a user asks for the status or details of a known appointment (e.g.,
    "When is my technician coming?", "What are the details of my installation
    appointment?").
    - You must already have the 'visitId' from a previous step or from the user.

    Args:
      visitId(str): The unique identifier of the technician visit to look up. Example:
        "VISIT-98765".

    Raises:
      ValidationError: If visitId is not a non-empty string or doesn't match the expected pattern.
      AppointmentNotFoundError: If no appointment is found for visitId.
    
    Returns:
        Dict[str, Optional[str]]: An object with the details of the technician visit.
            - visitId (Optional[str]): The unique identifier of the technician visit.
            - accountId (Optional[str]): The customer's account ID.
            - orderId (Optional[str]): The service order ID associated with the visit.
            - status (Optional[str]): The current status of the visit (e.g., 'scheduled', 'in_progress', 'completed').
            - scheduledStartTime (Optional[str]): The scheduled start time of the visit in ISO format.
            - scheduledEndTime (Optional[str]): The scheduled end time of the visit in ISO format.
            - technicianNotes (Optional[str]): Any notes from the technician about the visit.
            - issueDescription (Optional[str]): Description of the issue or service being performed.
    """
    try:
        input_data = GetActivationVisitDetailsInput(visitId=visitId)
    except Exception as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for get_activation_visit_details: {finalMsg.strip()}')
    appointment_details = DB['appointmentDetails']
    appointment = next(
        (
            appointment
            for appointment in appointment_details
            if appointment['visitId'] == input_data.visitId
        ),
        None,
    )
    if appointment is None:
        raise AppointmentNotFoundError('No appointment found for visitId: %s' % input_data.visitId)
    return TechnicianVisitDetails(
        visitId=appointment['visitId'],
        accountId=appointment['accountId'],
        orderId=appointment['orderId'],
        status=appointment['status'],
        scheduledStartTime=appointment['scheduledStartTime'],
        scheduledEndTime=appointment['scheduledEndTime'],
        technicianNotes=appointment['technicianNotes'],
        issueDescription=appointment['issueDescription'],
    ).model_dump(exclude_none=False)


@tool_spec(
    input_model=FindAvailableTechnicianAppointmentSlotsInput,
    output_model=AppointmentAvailability,
    description='Checks for available time slots to schedule a new technician visit or reschedule an existing one.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if input parameters are invalid or don't match expected formats."])
    ],
    spec={
    'name': 'find_available_technician_appointment_slots',
    'description': 'Checks for available time slots to schedule a new technician visit or reschedule an existing one.\n\nWhen to Use:\n- When a user wants to schedule a new installation appointment.\n- When a user wants to reschedule an existing appointment and asks for\navailable times.',
    'parameters': {
        'type': 'object',
        'properties': {
            'startDate': {
                'type': 'string',
                'description': 'The desired starting date to search for availability, in\n\'YYYY-MM-DD\' format. Example: "2023-11-01".'
            },
            'postalCode': {
                'type': 'string',
                'description': 'Optional. The postal code for the service location, used to find local\ntechnicians. Example: "94105".',
                'nullable': True
            },
            'daysToSearch': {
                'type': 'integer',
                'description': 'Optional. The number of consecutive days to search for\navailability, starting from \'startDate\'. Defaults to 7 if not specified.\nExample: 14.',
                'nullable': True
            }
        },
        'required': [
            'startDate'
        ]
    },
    'response': {
        'description': "An object containing a list of available appointment slots.",
        'type': 'object',
        'properties': {
            'output': {
                'type': 'array',
                'description': 'A list of available appointment slots.',
                'items': {
                    'type': 'object',
                    'properties': {
                        'endTime': {
                            'type': 'string',
                            'description': 'The end time of the appointment slot in ISO format.',
                            'nullable': True
                        },
                        'slotId': {
                            'type': 'string',
                            'description': 'The unique identifier for the appointment slot.',
                            'nullable': True
                        },
                        'startTime': {
                            'type': 'string',
                            'description': 'The start time of the appointment slot in ISO format.',
                            'nullable': True
                        },
                        'technicianType': {
                            'type': 'string',
                            'description': 'The type of technician for this slot (e.g., \'ACTIVATION_INSTALL\').',
                            'nullable': True
                        }
                    },
                    'required': []
                },
                'nullable': True
            }
        },
        'required': []
    }
})
def find_available_technician_appointment_slots(
    startDate: str,
    postalCode: Optional[str] = None,
    daysToSearch: Optional[int] = None,
) -> Dict[str, Optional[List[Dict[str, Optional[str]]]]]:
    """Checks for available time slots to schedule a new technician visit or reschedule an existing one.

    When to Use:
    - When a user wants to schedule a new installation appointment.
    - When a user wants to reschedule an existing appointment and asks for
    available times.

    Args:
      startDate(str): The desired starting date to search for availability, in
        'YYYY-MM-DD' format. Example: "2023-11-01".
      postalCode(Optional[str]): The postal code for the service location, used to find local
        technicians. Example: "94105".
      daysToSearch(Optional[int]): Optional. The number of consecutive days to search for
        availability, starting from 'startDate'. Defaults to 7 if not specified.
        Example: 14.
      originalVisitId(Optional[str]): Optional. Include this only when rescheduling. It is the ID
        of the existing visit the user wants to change. This helps find compatible
        slots. Example: "VISIT-12345".

    Raises:
      ValidationError: If input parameters are invalid or don't match expected formats.
    
    Returns:
        Dict[str, Optional[List[Dict[str, Optional[str]]]]]: An object containing a list of available appointment slots.
            - output (Optional[List[Dict[str, Optional[str]]]]): A list of available appointment slots, where each slot contains:
                - endTime (Optional[str]): The end time of the appointment slot in ISO format.
                - slotId (Optional[str]): The unique identifier for the appointment slot.
                - startTime (Optional[str]): The start time of the appointment slot in ISO format.
                - technicianType (Optional[str]): The type of technician for this slot (e.g., 'ACTIVATION_INSTALL').
    """
    try:
        input_data = FindAvailableTechnicianAppointmentSlotsInput(
            startDate=startDate,
            postalCode=postalCode,
            daysToSearch=daysToSearch
        )
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for find_available_technician_appointment_slots: {finalMsg.strip()}')

    available_slots = DB['technicianSlots']
    if not isinstance(available_slots, list):
        raise ValueError('Error when processing slots. Invalid slots data.')
    try:
        start_date = datetime.date.fromisoformat(input_data.startDate)
    except ValueError:
        raise ValueError('Invalid start date format: %s' % input_data.startDate)
    if input_data.daysToSearch is not None:
        end_date = start_date + datetime.timedelta(days=input_data.daysToSearch)
    else:
        end_date = start_date + datetime.timedelta(days=7)
    available_slots = [
        slot
        for slot in available_slots
        if start_date
        <= datetime.date.fromisoformat(slot['startTime'][0:10])
        <= end_date
    ]

    if input_data.postalCode:
        available_slots = [
            slot for slot in available_slots if (
                len(slot['slotId'].split('-')) > 1 and
                slot['slotId'].split('-')[1] == input_data.postalCode
            )
        ]

    return AppointmentAvailability(
        output=[
            AvailableAppointmentSlot(
                endTime=slot['endTime'],
                slotId=slot['slotId'],
                startTime=slot['startTime'],
                technicianType=slot['technicianType'],
            )
            for slot in available_slots
        ]
    ).model_dump(exclude_none=False)


@tool_spec(
    input_model=RescheduleTechnicianVisitInput,
    output_model=TechnicianVisitDetails,
    description='Reschedules an existing activation technician visit to a new, available time slot.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if input parameters are invalid."]),
        ErrorObject(VisitNotFoundError, ["Raised if no appointment is found for originalVisitId."]),
        ErrorObject(SlotNotFoundError, ["Raised if the specified newSlotId is not available."]),
        ErrorObject(DuplicateAppointmentError, ["Raised if the new slot creates a scheduling conflict."])
    ],
    spec={
    'name': 'reschedule_technician_visit',
    'description': 'Reschedules an existing activation technician visit to a new, available time slot.\n\nWhen to Use:\n- After the user has selected a new time slot from the availability check and\nconfirmed they want to reschedule.\n- You must have the \'originalVisitId\' of the old appointment and the\n\'newSlotId\' of the desired new appointment.',
    'parameters': {
        'type': 'object',
        'properties': {
            'accountId': {
                'type': 'string',
                'description': 'The customer\'s account ID. Example: "ACC-102030".'
            },
            'newSlotId': {
                'type': 'string',
                'description': 'The ID of the newly chosen appointment slot, obtained from\n`find_available_technician_appointment_slots`. Example: "SLOT-XYZ-789".'
            },
            'orderId': {
                'type': 'string',
                'description': 'The service order ID associated with the visit. Example:\n"ORD-405060".'
            },
            'originalVisitId': {
                'type': 'string',
                'description': 'The ID of the existing activation appointment to be\nrescheduled. Example: "VISIT-12345".'
            },
            'reasonForChange': {
                'type': 'string',
                'description': 'Optional. A brief reason for the change, if provided by the\nuser. Example: "User has a conflicting meeting.".',
                'nullable': True
            }
        },
        'required': [
            'accountId',
            'newSlotId',
            'orderId',
            'originalVisitId'
        ]
    },
    'response': {
        'description': "An object with the details of the rescheduled technician visit.",
        'type': 'object',
        'properties': {
            'visitId': {
                'type': 'string',
                'description': 'The unique identifier of the rescheduled technician visit (prefixed with \'rescheduled_\').'
            },
            'accountId': {
                'type': 'string',
                'description': 'The customer\'s account ID.'
            },
            'orderId': {
                'type': 'string',
                'description': 'The service order ID associated with the visit.'
            },
            'status': {
                'type': 'string',
                'description': 'The current status of the visit (typically \'scheduled\').'
            },
            'scheduledStartTime': {
                'type': 'string',
                'description': 'The new scheduled start time of the visit in ISO format.',
                'nullable': True
            },
            'scheduledEndTime': {
                'type': 'string',
                'description': 'The new scheduled end time of the visit in ISO format.',
                'nullable': True
            },
            'technicianNotes': {
                'type': 'string',
                'description': 'Notes including the reason for the reschedule.',
                'nullable': True
            },
            'issueDescription': {
                'type': 'string',
                'description': 'Description of the service being performed.',
                'nullable': True
            }
        },
        'required': ['visitId', 'accountId', 'orderId', 'status']
    }
})
def reschedule_technician_visit(
    accountId: str,
    newSlotId: str,
    orderId: str,
    originalVisitId: str,
    reasonForChange: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Reschedules an existing activation technician visit to a new, available time slot.

    When to Use:
    - After the user has selected a new time slot from the availability check and
    confirmed they want to reschedule.
    - You must have the 'originalVisitId' of the old appointment and the
    'newSlotId' of the desired new appointment.

    Args:
      accountId(str): The customer's account ID. Example: "ACC-102030".
      newSlotId(str): The ID of the newly chosen appointment slot, obtained from
        `find_available_technician_appointment_slots`. Example: "SLOT-XYZ-789".
      orderId(str): The service order ID associated with the visit. Example:
        "ORD-405060".
      originalVisitId(str): The ID of the existing activation appointment to be
        rescheduled. Example: "VISIT-12345".
      reasonForChange(Optional[str]): Optional. A brief reason for the change, if provided by the
        user. Example: "User has a conflicting meeting.".

    Raises:
      ValidationError: If input parameters are invalid or don't match expected formats, if the appointment is completed, or if the appointment does not belong to the provided accountId (security validation).
      VisitNotFoundError: If no visit is found for the given visitId.
      SlotNotFoundError: If no slot is found for the given slotId.
    
    Returns:
        Dict[str, Optional[str]]: An object with the details of the rescheduled technician visit.
            - visitId (Optional[str]): The unique identifier of the rescheduled technician visit (prefixed with 'rescheduled_').
            - accountId (Optional[str]): The customer's account ID.
            - orderId (Optional[str]): The service order ID associated with the visit.
            - status (Optional[str]): The current status of the visit (typically 'scheduled').
            - scheduledStartTime (Optional[str]): The new scheduled start time of the visit in ISO format.
            - scheduledEndTime (Optional[str]): The new scheduled end time of the visit in ISO format.
            - technicianNotes (Optional[str]): Notes including the reason for the reschedule.
            - issueDescription (Optional[str]): Description of the service being performed.
    """
    try:
        reschedule_technician = RescheduleTechnicianVisitInput(
            accountId=accountId,
            newSlotId=newSlotId,
            orderId=orderId,
            originalVisitId=originalVisitId,
            reasonForChange=reasonForChange,
        )
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for reschedule_technician_visit: {finalMsg.strip()}')


    # check if the accountId exists in the system
    account_exists = next(
        (
            appointment
            for appointment in DB['appointmentDetails']
            if appointment['accountId'] == reschedule_technician.accountId
        ),
        None,
    )
    
    if account_exists is None:
        raise ValidationError(f'Account ID {reschedule_technician.accountId} does not exist in the system.')

    # check if the original appointment exists
    original_appointment = next(
        (
            appointment
            for appointment in DB['appointmentDetails']
            if appointment['visitId'] == reschedule_technician.originalVisitId
        ),
        None,
    )
    if original_appointment is None:
        raise VisitNotFoundError(f'No appointment found for visitId: {reschedule_technician.originalVisitId}')

    # SECURITY FIX: Validate that the original appointment belongs to the provided accountId
    if original_appointment['accountId'] != reschedule_technician.accountId:
        raise ValidationError(f'The appointment with visitId {reschedule_technician.originalVisitId} does not belong to account {reschedule_technician.accountId}.')

    if original_appointment['status'] == 'completed':
        raise ValidationError('Completed appointments cannot be rescheduled.')

    # check if the requested slot is available
    new_slot = next(
        (
            slot
            for slot in DB['technicianSlots']
            if slot['slotId'] == reschedule_technician.newSlotId
        ),
        None,
    )
    if new_slot is None:
        raise SlotNotFoundError(f'The slotId: {reschedule_technician.newSlotId} is not available.')

    technician_slots = DB['technicianSlots']
    
    # restore previous slot
    technician_slots.append({
        'slotId': original_appointment['slotId'],
        'startTime': original_appointment['scheduledStartTime'],
        'endTime': original_appointment['scheduledEndTime'],
        'technicianType': 'ACTIVATION_INSTALL',
    })

    # add new rescheduled appointment
    appointment_details = DB['appointmentDetails']
    appointment_details.append({
        'visitId': 'rescheduled_' + original_appointment['visitId'],
        'slotId': new_slot['slotId'],
        'accountId': reschedule_technician.accountId,
        'orderId': reschedule_technician.orderId,
        'status': 'scheduled',
        'scheduledStartTime': new_slot['startTime'],
        'scheduledEndTime': new_slot['endTime'],
        'technicianNotes': reschedule_technician.reasonForChange,
        'issueDescription': original_appointment['issueDescription'],
    })

    # remove old slot from list
    technician_slots = [
        slot for slot in technician_slots if slot['slotId'] != new_slot['slotId']
    ]
    appointment_details = [
        appointment
        for appointment in appointment_details
        if appointment['visitId'] != reschedule_technician.originalVisitId
    ]
    DB['technicianSlots'] = technician_slots
    DB['appointmentDetails'] = appointment_details

    return get_activation_visit_details(
        'rescheduled_' + original_appointment['visitId']
    )


@tool_spec(
    input_model=ScheduleNewTechnicianVisitInput,
    output_model=TechnicianVisitDetails,
    description='Schedules a new activation technician visit in a selected time slot.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if input parameters are invalid."]),
        ErrorObject(SlotNotFoundError, ["Raised if the specified slotId is not available."]),
        ErrorObject(DuplicateAppointmentError, ["Raised if a visit already exists for this order."])
    ],
    spec={
    'name': 'schedule_new_technician_visit',
    'description': 'Schedules a new activation technician visit in a selected time slot.\n\nWhen to Use:\n- After a user has selected a time slot for a new installation or service\nappointment and confirmed they want to schedule it.',
    'parameters': {
        'type': 'object',
        'properties': {
            'accountId': {
                'type': 'string',
                'description': 'The customer\'s account ID. Example: "ACC-102030".'
            },
            'orderId': {
                'type': 'string',
                'description': 'The service order ID that requires a technician visit. Example:\n"ORD-405060".'
            },
            'slotId': {
                'type': 'string',
                'description': 'The ID of the chosen appointment slot, obtained from\n`find_available_technician_appointment_slots`. Example: "SLOT-ABC-123". The slotId is a random string that does not represent a date'
            },
            'issueDescription': {
                'type': 'string',
                'description': 'Optional. A brief description of the issue or service being performed. Defaults to None. When None is provided or omitted, the implementation will use "New SunnyFiber Gigabit internet service installation and modem setup." as the default value.',
                'nullable': True
            }
        },
        'required': [
            'accountId',
            'orderId',
            'slotId'
        ]
    },
    'response': {
        'description': "An object with the details of the newly scheduled technician visit.",
        'type': 'object',
        'properties': {
            'visitId': {
                'type': 'string',
                'description': 'The unique identifier of the newly scheduled technician visit (format: \'VISIT-{uuid}\').'
            },
            'accountId': {
                'type': 'string',
                'description': 'The customer\'s account ID.'
            },
            'orderId': {
                'type': 'string',
                'description': 'The service order ID associated with the visit.'
            },
            'status': {
                'type': 'string',
                'description': 'The current status of the visit (typically \'scheduled\').'
            },
            'scheduledStartTime': {
                'type': 'string',
                'description': 'The scheduled start time of the visit in ISO format.',
                'nullable': True
            },
            'scheduledEndTime': {
                'type': 'string',
                'description': 'The scheduled end time of the visit in ISO format.',
                'nullable': True
            },
            'technicianNotes': {
                'type': 'string',
                'description': 'Any notes from the technician (initially None for new visits).',
                'nullable': True
            },
            'issueDescription': {
                'type': 'string',
                'description': 'Description of the service being performed.',
                'nullable': True
            }
        },
        'required': ['visitId', 'accountId', 'orderId', 'status']
    }
})
def schedule_new_technician_visit(
    accountId: str,
    orderId: str,
    slotId: str,
    issueDescription: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Schedules a new activation technician visit in a selected time slot.

    When to Use:
    - After a user has selected a time slot for a new installation or service
    appointment and confirmed they want to schedule it.

    Args:
      accountId(str): The customer's account ID. Example: "ACC-102030".
      orderId(str): The service order ID that requires a technician visit. Example:
        "ORD-405060".
      slotId(str): The ID of the chosen appointment slot, obtained from
        `find_available_technician_appointment_slots`. Example: "SLOT-ABC-123". The slotId is a random string that does not represent a date
      issueDescription(Optional[str]): Optional. A brief description of the issue or service being performed. Defaults to None. When None is provided or omitted, the implementation will use "New SunnyFiber Gigabit internet service installation and modem setup." as the default value.

    Raises:
      ValidationError: If input parameters are invalid or don't match expected formats, or if the accountId does not exist in the system, or if the orderId does not exist in the system, or if the orderId does not belong to the specified accountId.
      TechnicianVisitNotFoundError: If no technician visit is found for slotId.
      DuplicateAppointmentError: If an appointment for the given orderId already exists.
    
    Returns:
        Dict[str, Optional[str]]: An object with the details of the newly scheduled technician visit.
            - visitId (Optional[str]): The unique identifier of the newly scheduled technician visit (format: 'VISIT-{uuid}').
            - accountId (Optional[str]): The customer's account ID.
            - orderId (Optional[str]): The service order ID associated with the visit.
            - status (Optional[str]): The current status of the visit (typically 'scheduled').
            - scheduledStartTime (Optional[str]): The scheduled start time of the visit in ISO format.
            - scheduledEndTime (Optional[str]): The scheduled end time of the visit in ISO format.
            - technicianNotes (Optional[str]): Any notes from the technician (initially None for new visits).
            - issueDescription (Optional[str]): Description of the service being performed.
    """
    try:
        input_data = ScheduleNewTechnicianVisitInput(
            accountId=accountId,
            orderId=orderId,
            slotId=slotId,
            issueDescription=issueDescription,
        )
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for schedule_new_technician_visit: {finalMsg.strip()}')

    # Check if orderId exists and belongs to the specified accountId
    matching_order = None
    account_exists = False
    
    for order in DB['orderDetails'].values():
        if order.get('account_id') == input_data.accountId:
            account_exists = True
        if order.get('order_id') == input_data.orderId:
            matching_order = order
        if account_exists and matching_order:
            break
    
    if not account_exists:
        raise ValidationError(f'Account ID {input_data.accountId} does not exist in the system.')
    
    if matching_order is None:
        raise ValidationError(f'Order ID {input_data.orderId} does not exist in the system.')
    
    if matching_order.get('account_id') != input_data.accountId:
        raise ValidationError(f'Order ID {input_data.orderId} does not belong to Account ID {input_data.accountId}.')

    existing_appointment = next(
        (
            appointment
            for appointment in DB['appointmentDetails']
            if appointment['orderId'] == input_data.orderId and appointment['status'] not in ['completed', 'cancelled']
        ),
        None,
    )
    if existing_appointment:
        raise DuplicateAppointmentError(
            f'An appointment for orderId {input_data.orderId} already exists. '
            'Please use reschedule_technician_visit to make changes.'
        )
    visit_to_schedule = next(
        (slot for slot in DB['technicianSlots']
         if slot['slotId'] == input_data.slotId), None
    )
    if visit_to_schedule is None:
        raise TechnicianVisitNotFoundError('No technician visit found for slotId: %s' % input_data.slotId)
    appointment_details = DB['appointmentDetails']
    if not isinstance(appointment_details, list):
        raise ValueError('Error when processing appointments. Invalid appointments data.')
    new_visit_id = f'VISIT-{str(uuid.uuid4())}'
    description = issueDescription if issueDescription is not None else 'New SunnyFiber Gigabit internet service installation and modem setup.'
    appointment_details.append({
        'slotId': visit_to_schedule['slotId'],
        'visitId': new_visit_id,
        'accountId': input_data.accountId,
        'orderId': input_data.orderId,
        'status': 'scheduled',
        'scheduledStartTime': visit_to_schedule['startTime'],
        'scheduledEndTime': visit_to_schedule['endTime'],
        'technicianNotes': None,
        'issueDescription': description
    })

    DB['appointmentDetails'] = appointment_details
    technician_slots = DB['technicianSlots']
    if not isinstance(technician_slots, list):
        raise ValueError('Error when processing slots. Invalid slots data.')
    technician_slots = [
        slot for slot in technician_slots if slot['slotId'] != input_data.slotId
    ]
    DB['technicianSlots'] = technician_slots

    return get_activation_visit_details(new_visit_id)


@tool_spec(
    input_model=FlagTechnicianVisitIssueInput,
    output_model=FlaggedIssueConfirmation,
    description='Flags an issue with a completed or in-progress technician visit, requiring follow-up action.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if input parameters are invalid or text fields are empty."]),
        ErrorObject(VisitNotFoundError, ["Raised if no viable visits found for the specified identifiers."])
    ],
    spec={
    'name': 'flag_technician_visit_issue',
    'description': 'Flags an issue with a completed or in-progress technician visit, requiring follow-up action.\n\nWhen to Use:\n- A user reports that the technician came but the service is still not\nworking.\n- A user reports a problem that occurred during or after the technician\'s\nvisit (e.g., "the technician left but my internet is not on").',
    'parameters': {
        'type': 'object',
        'properties': {
            'accountId': {
                'type': 'string',
                'description': 'The customer\'s account ID. Example: "ACC-102030".'
            },
            'customerReportedFailure': {
                'type': 'boolean',
                'description': 'A boolean indicating if the customer is the one\nreporting the failure. Set to `True` in almost all cases for an agent.'
            },
            'issueSummary': {
                'type': 'string',
                'description': 'A concise summary of the problem reported by the user.\nExample: "Customer reports that the modem is not getting a signal after\nthe technician left.".'
            },
            'orderId': {
                'type': 'string',
                'description': 'The service order ID associated with the visit. Example:\n"ORD-405060".'
            },
            'requestedFollowUpAction': {
                'type': 'string',
                'description': 'The desired next step. Example: "Dispatch\ntechnician again", "Manager callback requested".'
            },
            'visitId': {
                'type': 'string',
                'description': 'The ID of the technician visit that has the issue. Example:\n"VISIT-12345".'
            }
        },
        'required': [
            'accountId',
            'customerReportedFailure',
            'issueSummary',
            'orderId',
            'requestedFollowUpAction',
            'visitId'
        ]
    },
    'response': {
        'description': "An object with the confirmation of the flagged issue.",
        'type': 'object',
        'properties': {
            'flagId': {
                'type': 'string',
                'description': 'The unique identifier for the flagged issue (e.g., \'FLAG-998877\').'
            },
            'message': {
                'type': 'string',
                'description': 'A confirmation message indicating the issue has been logged.'
            },
            'status': {
                'type': 'string',
                'description': 'The current status of the flagged issue (e.g., \'Logged for review\').'
            }
        },
        'required': ['flagId', 'message', 'status']
    }
})
def flag_technician_visit_issue(
    accountId: str,
    customerReportedFailure: bool,
    issueSummary: str,
    orderId: str,
    requestedFollowUpAction: str,
    visitId: str,
) -> Dict[str, str]:
    """Flags an issue with a completed or in-progress technician visit, requiring follow-up action.

    When to Use:
    - A user reports that the technician came but the service is still not
    working.
    - A user reports a problem that occurred during or after the technician's
    visit (e.g., "the technician left but my internet is not on").

    Args:
      accountId(str): The customer's account ID. Example: "ACC-102030".
      customerReportedFailure(bool): A boolean indicating if the customer is the one
        reporting the failure. Set to `True` in almost all cases for an agent.
      issueSummary(str): A concise summary of the problem reported by the user.
        Example: "Customer reports that the modem is not getting a signal after
          the technician left.".
      orderId(str): The service order ID associated with the visit. Example:
        "ORD-405060".
      requestedFollowUpAction(str): The desired next step. Example: "Dispatch
        technician again", "Manager callback requested".
      visitId(str): The ID of the technician visit that has the issue. Example:
        "VISIT-12345".

    Raises:
      ValidationError: If input parameters are invalid or don't match expected formats.
      VisitNotFoundError: if no viable visits are found for accountId, orderId, and visitId.
    
    Returns:
        Dict[str, str]: An object with the confirmation of the flagged issue.
            - flagId (str): The unique identifier for the flagged issue (e.g., 'FLAG-998877').
            - message (str): A confirmation message indicating the issue has been logged.
            - status (str): The current status of the flagged issue (e.g., 'Logged for review').
    """
    try:
        input_data = FlagTechnicianVisitIssueInput(
            accountId=accountId,
            customerReportedFailure=customerReportedFailure,
            issueSummary=issueSummary,
            orderId=orderId,
            requestedFollowUpAction=requestedFollowUpAction,
            visitId=visitId,
        )
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for flag_technician_visit_issue: {finalMsg.strip()}')

    visit_index = next(
        (
            index
            for index, appointment in enumerate(DB['appointmentDetails'])
            if appointment['accountId'] == input_data.accountId
            and appointment['visitId'] == input_data.visitId
            and appointment['orderId'] == input_data.orderId
        ),
        None,
    )
    if visit_index is None:
        raise VisitNotFoundError(
            f'No viable visits found for account: {input_data.accountId}, order: {input_data.orderId}, visit: {input_data.visitId}'
        )

    # Append to existing notes instead of overwriting to preserve historical context
    existing_notes = DB['appointmentDetails'][visit_index].get('technicianNotes', '')
    new_note = input_data.issueSummary + ' ' + input_data.requestedFollowUpAction
    
    if existing_notes:
        DB['appointmentDetails'][visit_index]['technicianNotes'] = existing_notes + ' | ' + new_note
    else:
        DB['appointmentDetails'][visit_index]['technicianNotes'] = new_note

    new_flag_issue_confirmation = FlaggedIssueConfirmation(
        flagId=f'FLAG-{str(uuid.uuid4())}',
        message=(
            'Thank you for flagging this. One of our technicians will review your'
            ' issue and get back to you.'
        ),
        status='Logged for review',
    ).model_dump(exclude_none=False)

    DB["flagTechnicianVisitIssues"].append(new_flag_issue_confirmation)

    return new_flag_issue_confirmation

@tool_spec(
    input_model=TriggerServiceActivationInput,
    output_model=ServiceActivationAttempt,
    description='Initiates the activation process for a specific service on the network platform.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if input parameters are invalid or don't match expected formats."]),
        ErrorObject(InvalidServiceTypeError, ["Raised if serviceType is not one of MOBILE, INTERNET, IOT_DEVICE, or VOIP."])
    ],
    spec={
    'name': 'trigger_service_activation',
    'description': 'Initiates the activation process for a specific service on the network platform.\n\nWhen to Use:\n- When a user wants to activate a service that is ready for activation (e.g.,\n"I\'ve installed my modem, can you activate my internet?").\n- As part of an automated activation flow after a technician visit is\ncomplete.',
    'parameters': {
        'type': 'object',
        'properties': {
            'orderId': {
                'type': 'string',
                'description': 'The order ID associated with the service being activated. Example:\n"ORD-405060".'
            },
            'serviceIdentifier': {
                'type': 'string',
                'description': 'The unique identifier for the service. This could be a\nSIM card number (ICCID), modem MAC address, or phone number. Example:\n"8901123456789012345f" or "AA:BB:CC:11:22:33".'
            },
            'serviceType': {
                'type': 'string',
                'description': 'The category of service to be activated. Must be one of\n\'MOBILE\', \'INTERNET\', \'IOT_DEVICE\', \'VOIP\'.'
            },
            'accountId': {
                'type': 'string',
                'description': 'Optional. The customer\'s account ID, for logging and association.\nExample: "ACC-102030".',
                'nullable': True
            }
        },
        'required': [
            'orderId',
            'serviceIdentifier',
            'serviceType'
        ]
    },
    'response': {
        'description': "An object with the details of the service activation attempt.",
        'type': 'object',
        'properties': {
            'activationAttemptId': {
                'type': 'string',
                'description': 'The service identifier for the activation. Example: "8901123456789012345f" or "AA:BB:CC:11:22:33".'
            },
            'message': {
                'type': 'string',
                'description': 'A status message about the activation attempt.'
            },
            'status': {
                'type': 'string',
                'description': 'The current status of the activation (e.g., \'REQUEST_RECEIVED\', \'IN_PROGRESS\').'
            },
            'timestamp': {
                'type': 'string',
                'description': 'The timestamp when the activation was initiated in ISO format.'
            },
            'errorCode': {
                'type': 'string',
                'description': 'Any error code if the activation failed (optional).',
                'nullable': True
            }
        },
        'required': ['activationAttemptId', 'message', 'status', 'timestamp']
    }
})
def trigger_service_activation(
    orderId: str,
    serviceIdentifier: str,
    serviceType: str,
    accountId: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Initiates the activation process for a specific service on the network platform.

    When to Use:
    - When a user wants to activate a service that is ready for activation (e.g.,
    "I've installed my modem, can you activate my internet?").
    - As part of an automated activation flow after a technician visit is
    complete.

    Args:
      orderId(str): The order ID associated with the service being activated. Example:
        "ORD-405060".
      serviceIdentifier(str): The unique identifier for the service. This could be a
        SIM card number (ICCID), modem MAC address, or phone number. Example:
        "8901123456789012345f" or "AA:BB:CC:11:22:33".
      serviceType(str): The category of service to be activated. Must be one of
        'MOBILE', 'INTERNET', 'IOT_DEVICE', 'VOIP'.
      accountId(Optional[str]): Optional. The customer's account ID, for logging and association.
        Example: "ACC-102030".

    Raises:
      ValidationError: If input parameters are invalid or don't match expected formats.
      InvalidServiceTypeError: If serviceType is not one of MOBILE, INTERNET, IOT_DEVICE, or VOIP 
    
    Returns:
        Dict[str, Optional[str]]: An object with the details of the service activation attempt.
            - activationAttemptId (str): The service identifier for the activation. Example: "8901123456789012345f" or "AA:BB:CC:11:22:33".
            - message (str): A status message about the activation attempt.
            - status (str): The current status of the activation (e.g., 'REQUEST_RECEIVED', 'IN_PROGRESS').
            - timestamp (str): The timestamp when the activation was initiated in ISO format.
            - errorCode (Optional[str]): Any error code if the activation failed (optional).
    """
    try:
        input_data = TriggerServiceActivationInput(
            orderId=orderId,
            serviceIdentifier=serviceIdentifier,
            serviceType=serviceType,
            accountId=accountId,
        )
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for trigger_service_activation: {finalMsg.strip()}')
    
    order_details = DB['orderDetails']
    if not isinstance(order_details, dict):
        raise ValueError('Error when processing orders. Invalid orders data.')
    
    if input_data.serviceType not in DB['serviceTypes']:
        raise InvalidServiceTypeError(
            f'serviceType must be one of {json.dumps(DB["serviceTypes"])}. Got: {input_data.serviceType}'
        )

    # get order by orderId, serviceIdentifier, and serviceType
    target_order = None
    for order in order_details.values():
        # The key in the JSON is 'order_id', not 'orderId'
        if (order.get('order_id') == input_data.orderId and
            order.get('service_identifier_for_activation') == input_data.serviceIdentifier and
            order.get('service_type') == input_data.serviceType):
            target_order = order
            break

    if target_order is None:
        raise ValueError(
            f'No viable order found for order: {input_data.orderId}, serviceIdentifier: {input_data.serviceIdentifier},serviceType: {input_data.serviceType}'
        )
    
    if target_order.get('service_activation_status') != (
        'PENDING_SELF_ACTIVATION'
    ):
        raise ValueError(
            f'Order {input_data.orderId} is not in a pending self-activation state. Current status: {target_order.get("service_activation_status")}'
        )

    # update order service_activation_status to IN_PROGRESS
    target_order['service_activation_status'] = 'IN_PROGRESS'

    return ServiceActivationAttempt(
        activationAttemptId=target_order.get('service_identifier_for_activation'),
        message='Activation is in progress.',
        status=target_order.get('service_activation_status') ,
        timestamp=datetime.datetime.now(datetime.UTC).strftime(
            '%Y-%m-%dT%H:%M:%SZ'
        ),
    ).model_dump(exclude_none=False)


@tool_spec(
    input_model=GetServiceActivationStatusInput,
    output_model=ServiceActivationAttempt,
    description='Checks the current status of a pending or completed service activation attempt.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if activationAttemptIdOrServiceIdentifier is invalid."]),
        ErrorObject(ActivationAttemptNotFoundError, ["Raised if no activation attempt found for the identifier."])
    ],
    spec={
    'name': 'get_service_activation_status',
    'description': 'Checks the current status of a pending or completed service activation attempt.\n\nWhen to Use:\n- After using `trigger_service_activation` to check on the progress.\n- When a user asks for an update on their service activation.',
    'parameters': {
        'type': 'object',
        'properties': {
            'activationAttemptIdOrServiceIdentifier': {
                'type': 'string',
                'description': 'The identifier for the activation.\nThis can be the `activationAttemptId` returned by\n`trigger_service_activation` OR the `serviceIdentifier` (e.g., MAC\naddress) used to start the activation. Example: "ATTEMPT-afc3b1" or\n"AA:BB:CC:11:22:33".'
            }
        },
        'required': [
            'activationAttemptIdOrServiceIdentifier'
        ]
    },
    'response': {
        'description': "An object with the current status of the service activation attempt.",
        'type': 'object',
        'properties': {
            'activationAttemptId': {
                'type': 'string',
                'description': 'The identifier used for the activation (matches the serviceIdentifier).'
            },
            'message': {
                'type': 'string',
                'description': 'A status message describing the current state of the activation.'
            },
            'status': {
                'type': 'string',
                'description': 'The current status of the activation (e.g., \'PENDING_SELF_ACTIVATION\', \'IN_PROGRESS\', \'COMPLETED\').'
            },
            'timestamp': {
                'type': 'string',
                'description': 'The timestamp of the status check in ISO format.'
            },
            'errorCode': {
                'type': 'string',
                'description': 'Any error code if the activation failed (optional).',
                'nullable': True
            }
        },
        'required': ['activationAttemptId', 'message', 'status', 'timestamp']
    }
})
def get_service_activation_status(
    activationAttemptIdOrServiceIdentifier: str,
) -> Dict[str, Optional[str]]:
    """Checks the current status of a pending or completed service activation attempt.

    When to Use:
    - After using `trigger_service_activation` to check on the progress.
    - When a user asks for an update on their service activation.

    Args:
      activationAttemptIdOrServiceIdentifier(str): The identifier for the activation.
        This can be the `activationAttemptId` returned by
        `trigger_service_activation` OR the `serviceIdentifier` (e.g., MAC
        address) used to start the activation. Example: "ATTEMPT-afc3b1" or
        "AA:BB:CC:11:22:33".

    Raises:
      ValidationError: If activationAttemptIdOrServiceIdentifier is invalid.
      ActivationAttemptNotFoundError: If no activation attempt is found for the identifier.
    
    Returns:
        Dict[str, Optional[str]]: An object with the current status of the service activation attempt.
            - activationAttemptId (str): The identifier used for the activation (matches the serviceIdentifier).
            - message (str): A status message describing the current state of the activation.
            - status (str): The current status of the activation (e.g., 'PENDING_SELF_ACTIVATION', 'IN_PROGRESS', 'COMPLETED').
            - timestamp (str): The timestamp of the status check in ISO format.
            - errorCode (Optional[str]): Any error code if the activation failed (optional).
    """
    try:
        input_data = GetServiceActivationStatusInput(
            activationAttemptIdOrServiceIdentifier=activationAttemptIdOrServiceIdentifier
        )
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for get_service_activation_status: {finalMsg.strip()}')
    
    # get order by service_identifier_for_activation
    for order in DB['orderDetails'].values():
        if (
            order.get('service_identifier_for_activation')
            == input_data.activationAttemptIdOrServiceIdentifier
        ):
            return ServiceActivationAttempt(
                activationAttemptId=order['service_identifier_for_activation'],
                message=f'The current status is {order["service_activation_status"]}',
                status=order['service_activation_status'],
                timestamp=datetime.datetime.now(datetime.UTC).strftime(
                    '%Y-%m-%dT%H:%M:%SZ'
                ),
            ).model_dump(exclude_none=False)

    # raise error if no order is found
    raise ActivationAttemptNotFoundError(
        f'No activation attempt found for activationAttemptIdOrServiceIdentifier: {input_data.activationAttemptIdOrServiceIdentifier}' 
    )


@tool_spec(
    input_model=SendCustomerNotificationInput,
    output_model=NotificationResult,
    description='Sends a supplemental, non-standard notification to a customer.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if input parameters are invalid or don't match expected formats or either message or templateId is not provided."]),
        ErrorObject(TemplateNotFoundError, ["If template with ID {templateId} not found."])
    ],
    spec={
    'name': 'send_customer_notification',
    'description': 'Sends a supplemental, non-standard notification to a customer.\n\nIt is strongly preferred to use pre-defined templates for consistency and\ncompliance by providing a `templateId`. Free-form messages via the `message`\nparameter should be used sparingly.\n\nWhen to Use:\n- To send a confirmation after a complex action is completed (e.g., "Your\nappointment has been successfully rescheduled for...").\n- To provide a user with a reference number or other important information\nthey requested.\n- Do NOT use this for standard, automated notifications that the system\nalready sends (e.g., order confirmation).',
    'parameters': {
        'type': 'object',
        'properties': {
            'accountId': {
                'type': 'string',
                'description': 'The customer\'s account ID, used to retrieve contact preferences\nand for logging. Example: "ACC-102030".'
            },
            'message': {
                'type': 'string',
                'description': 'Optional. The raw message content. Use this only when a\npre-approved template is not available. This parameter is ignored if\n\'templateId\' is provided. Example: "As you requested, here is your service\norder number: ORD-405060.".',
                'nullable': True
            },
            'templateId': {
                'type': 'string',
                'description': 'Optional. The ID of a pre-approved notification template. This\nis the PREFERRED method. Example: "APPOINTMENT_CONFIRMATION_V2".',
                'nullable': True
            },
            'channel': {
                'type': 'string',
                'description': 'Optional. The preferred communication channel. If omitted, the\nsystem will use the customer\'s preferred channel or a system default.\nExample: "EMAIL".',
                'nullable': True
            },
            'orderId': {
                'type': 'string',
                'description': 'Optional. The relevant order ID to include in the notification\nlogs. Example: "ORD-405060".',
                'nullable': True
            },
            'recipient': {
                'type': 'string',
                'description': 'Optional. A specific recipient email address or phone number (in\nE.164 format). Use with caution, as it overrides the customer\'s preferred\ncontact details. Example: "+14155552671".',
                'nullable': True
            },
            'subject': {
                'type': 'string',
                'description': 'Optional. The subject line for the message, primarily for email\nnotifications. Example: "An Update on Your Recent Request".',
                'nullable': True
            },
            'urgency': {
                'type': 'string',
                'description': 'Optional. The urgency level of the notification. Defaults to\n\'NORMAL\'. Example: "HIGH".',
                'nullable': True
            }
        },
        'required': [
            'accountId'
        ]
    },
    'response': {
        'description': "An object with the result of the notification attempt.",
        'type': 'object',
        'properties': {
            'channelSent': {
                'type': 'string',
                'description': 'The communication channel used to send the notification (e.g., \'EMAIL\', \'SMS\').'
            },
            'message': {
                'type': 'string',
                'description': 'A confirmation message about the notification send status.'
            },
            'notificationId': {
                'type': 'string',
                'description': 'The unique identifier for the sent notification.'
            },
            'recipientUsed': {
                'type': 'string',
                'description': 'The recipient address or phone number used for the notification.',
                'nullable': True
            },
            'status': {
                'type': 'string',
                'description': 'The status of the notification (e.g., \'SENT\', \'FAILED\').'
            },
            'timestamp': {
                'type': 'string',
                'description': 'The timestamp when the notification was sent in ISO format.'
            },
            'accountId': {
                'type': 'string',
                'description': 'The customer\'s account ID, used to retrieve contact preferences\nand for logging. Example: "ACC-102030".',
                'nullable': True
            },
            'orderId': {
                'type': 'string',
                'description': 'The relevant order ID to include in the notification\nlogs. Example: "ORD-405060".',
                'nullable': True
            }
        },
        'required': ['channelSent', 'message', 'notificationId', 'status', 'timestamp']
    }
})
def send_customer_notification(
    accountId: str,
    channel: Optional[str] = 'EMAIL',
    message: Optional[str] = None,
    templateId: Optional[str] = None,
    orderId: Optional[str] = None,
    recipient: Optional[str] = None,
    subject: Optional[str] = None,
    urgency: Optional[str] = 'NORMAL', 
) -> Dict[str, Optional[str]]:
    """Sends a supplemental, non-standard notification to a customer.

    It is strongly preferred to use pre-defined templates for consistency and
    compliance by providing a `templateId`. Free-form messages via the `message`
    parameter should be used sparingly.

    When to Use:
    - To send a confirmation after a complex action is completed (e.g., "Your
    appointment has been successfully rescheduled for...").
    - To provide a user with a reference number or other important information
    they requested.
    - Do NOT use this for standard, automated notifications that the system
    already sends (e.g., order confirmation).

    Args:
      accountId(str): The customer's account ID, used to retrieve contact preferences
        and for logging. Example: "ACC-102030".
      message(Optional[str]): Optional. The raw message content. Use this only when a
        pre-approved template is not available. This parameter is ignored if
        'templateId' is provided. Example: "As you requested, here is your service
        order number: ORD-405060.".
      templateId(Optional[str]): Optional. The ID of a pre-approved notification template. This
        is the PREFERRED method. Example: "APPOINTMENT_CONFIRMATION_V2".
      channel(Optional[str]): Optional. The preferred communication channel. If omitted, the
        system will use the customer's preferred channel or a system default.
        Example: "EMAIL".
      orderId(Optional[str]): Optional. The relevant order ID to include in the notification
        logs. Example: "ORD-405060".
      recipient(Optional[str]): Optional. A specific recipient email address or phone number (in
        E.164 format). Use with caution, as it overrides the customer's preferred
        contact details. Example: "+14155552671".
      subject(Optional[str]): Optional. The subject line for the message, primarily for email
        notifications. Example: "An Update on Your Recent Request".
      urgency(Optional[str]): Optional. The urgency level of the notification. Defaults to
        'NORMAL'. Example: "HIGH".

    Raises:
      ValidationError: Raised if input parameters are invalid or don't match expected formats or either message or templateId is not provided.
      TemplateNotFoundError: If template with ID {templateId} not found
    
    Returns:
        Dict[str, Optional[str]]: An object with the result of the notification attempt.
            - channelSent (str): The communication channel used to send the notification (e.g., 'EMAIL', 'SMS').
            - message (str): A confirmation message about the notification send status.
            - notificationId (str): The unique identifier for the sent notification.
            - recipientUsed (Optional[str]): The recipient address or phone number used for the notification.
            - status (str): The status of the notification (e.g., 'SENT', 'FAILED').
            - timestamp (str): The timestamp when the notification was sent in ISO format.
    """
    try:
        input_data = SendCustomerNotificationInput(
            accountId=accountId,
            channel=channel,
            message=message,
            templateId=templateId,
            orderId=orderId,
            recipient=recipient,
            subject=subject,
            urgency=urgency,
        )
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for send_customer_notification: {finalMsg.strip()}')

    if not templateId and not message:
        raise ValidationError('Invalid input for send_customer_notification: Either message or templateId is required')

    if templateId:
        template = next((template for template in DB['templates'] if template['templateId'] == templateId), None)
        if template:
            message = template['message']
        else:
            raise TemplateNotFoundError(f'Template with ID {templateId} not found')

    notification_result = NotificationResult(
        channelSent=input_data.channel,
        message=message,
        notificationId=str(uuid.uuid4()),
        recipientUsed=input_data.recipient,
        status='SENT',
        timestamp=datetime.datetime.now(datetime.UTC).strftime(
            '%Y-%m-%dT%H:%M:%SZ'
        ),
        accountId=input_data.accountId,
        orderId=input_data.orderId,
    ).model_dump(exclude_none=False)

    DB['notifications'].append(notification_result)

    return notification_result


@tool_spec(
    input_model=SearchOrderDetailsInput,
    output_model=DataStoreQueryResult,
    description='Searches a structured database of customer order information.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if query is invalid or empty."]),
        ErrorObject(EnvironmentError, ["Raised when GOOGLE_API_KEY or GEMINI_API_KEY are not set."])
    ],
    spec={
    'name': 'search_order_details',
    'description': 'Searches a structured database of customer order information.\n\nWhen to Use:\n- Use this tool to find details about a customer\'s service orders, such as\nproducts ordered, order status, associated costs, and order dates.\n- This is the primary tool for answering questions like "What is the status of\nmy order?", "How much was my new internet plan?", or "When did I order my\nphone?".\n- ALWAYS use a customer\'s account ID or order ID as a filter in your query if\nyou have it.',
    'parameters': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'The natural language question to ask the order database. Be as\nspecific as possible. Good Example: "What is the current status of order\nORD-405060 for account ACC-102030?" Bad Example: "order status"'
            }
        },
        'required': [
            'query'
        ]
    },
    'response': {
        'description': "An object with the answer and snippets from the search.",
        'type': 'object',
        'properties': {
            'answer': {
                'type': 'string',
                'description': 'The answer to the query based on the order database search.'
            },
            'snippets': {
                'type': 'array',
                'description': 'A list of source snippets that support the answer.',
                'items': {
                    'type': 'object',
                    'properties': {
                        'text': {
                            'type': 'string',
                            'description': 'The relevant text content from the source.'
                        },
                        'title': {
                            'type': 'string',
                            'description': 'The title or heading of the source document.'
                        },
                        'uri': {
                            'type': 'string',
                            'description': 'The URI or identifier of the source document.'
                        }
                    },
                    'required': ['text', 'title', 'uri']
                }
            }
        },
        'required': ['answer', 'snippets']
    }
})
def search_order_details(
    query: str,
) -> Dict[str, Union[str, List[Dict]]]:
    """Searches a structured database of customer order information.

    When to Use:
    - Use this tool to find details about a customer's service orders, such as
    products ordered, order status, associated costs, and order dates.
    - This is the primary tool for answering questions like "What is the status of
    my order?", "How much was my new internet plan?", or "When did I order my
    phone?".
    - ALWAYS use a customer's account ID or order ID as a filter in your query if
    you have it.

    Args:
      query(str): The natural language question to ask the order database. Be as
        specific as possible. Good Example: "What is the current status of order
        ORD-405060 for account ACC-102030?" Bad Example: "order status"

    Raises:
      ValidationError: If query is invalid or empty.
      EnvironmentError: When GOOGLE_API_KEY or GEMINI_API_KEY are not set
    
    Returns:
        Dict[str, Union[str, List[Dict]]]: An object with the answer and snippets from the search.
            - answer (str): The answer to the query based on the order database search.
            - snippets (List[Dict]): A list of source snippets that support the answer, where each snippet contains:
                - text (str): The relevant text content from the source.
                - title (str): The title or heading of the source document.
                - uri (str): The URI or identifier of the source document.
    """
    try:
        input_data = SearchOrderDetailsInput(query=query)
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for search_order_details: {finalMsg.strip()}')
    
    if DB['use_real_datastore']:
        response = utils.query_order_details_infobot(input_data.query)
        return DataStoreQueryResult(
            answer=response.get('answer'),
            snippets=[
                SourceSnippet(
                    text=snippet.get('text'),
                    title=snippet.get('title'),
                    uri=snippet.get('uri'),
                )
                for snippet in response.get('snippets', [])
            ],
        ).model_dump(exclude_none=False)
    
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise EnvironmentError("Please set the GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")

    order_id = re.search(r'ORD-?\d+', input_data.query) 
    account_id = re.search(r'ACC-?\d+', input_data.query)

    if order_id:
        order_id = order_id.group().replace('-', '')
    if account_id:
        account_id = account_id.group().replace('-', '')

    if not order_id and not account_id and "pytest" not in sys.modules:
        
        client = genai.Client()

        response = client.models.generate_content(
            model="gemini-2.5-pro", contents="Based on the following query, return the order_id and account_id. If you are not sure about the order_id and account_id, return the same value for both. The order_id and account_id only contain numbers." + input_data.query,
            config=types.GenerateContentConfig(
                system_instruction="return as a json object to be parsed without markdown, this output will be parsed by json.loads function. The standard format is {order_id: 'ORD<ORDER_NUMBER>', account_id: 'ACC<ACCOUNT_NUMBER>'}",
                response_mime_type= "application/json",
            )
        )

        result = json.loads(response.text)
        if result.get('order_id'):
            order_id = result.get('order_id')
        if result.get('account_id'):
            account_id = result.get('account_id')

        if not order_id and not account_id:
            return DataStoreQueryResult(
                answer="I have no information about the order details.",
                snippets=[],
            ).model_dump(exclude_none=False)

    orders = utils.search_order_details_by_query(input_data.query, order_id, account_id)

    if orders:
        answer = []
        snippets = []

        for order in orders[:3]:
            order_info = f'{{"status": "{order["overall_order_status"]}", "customerName": "{order["customer_name"]}", "serviceType": "{order["service_type"]}", "accountId": "{order["account_id"]}", "serviceActivationStatus": "{order["service_activation_status"]}", "visitId": "{order["appointment_visit_id"]}"}}'
            answer.append(order_info)
            snippets.append(SourceSnippet(
                text=order['service_name'],
                title=f"{order['order_id']} {order['service_type']}",
                uri=order['equipment_tracking_url']
            ))
        answer = "Here are the available orders that match your query:\n" + "\n".join(answer)
    else:
        answer = "I have no information about the order details."
        snippets = []

    return DataStoreQueryResult(
        answer=answer,
        snippets=snippets,
    ).model_dump(exclude_none=False)

@tool_spec(
    input_model=SearchActivationGuidesInput,
    output_model=DataStoreQueryResult,
    description='Searches an unstructured knowledge base of activation guides, troubleshooting steps, and how-to articles.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if query is invalid or empty."])
    ],
    spec={
    'name': 'search_activation_guides',
    'description': 'Searches an unstructured knowledge base of activation guides, troubleshooting steps, and how-to articles.\n\nWhen to Use:\n- Use this tool to find procedural or explanatory information to help a\ncustomer with self-service activation or troubleshooting.\n- This is the primary tool for answering "how to" questions, like "How do I\nset up my new modem?", "What do the lights on my router mean?", or "My\ninternet is not working after setup, what should I do?".\n- Do NOT use this tool to look up specific customer order details. Use\n`search_order_details` for that.',
    'parameters': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'The natural language question to ask the knowledge base. Include the\ndevice model or service type for better results. Good Example:\n"Step-by-step instructions for installing the \'RouterModel X100\'" Bad\nExample: "help"'
            }
        },
        'required': [
            'query'
        ]
    },
    'response': {
        'description': "An object with the answer and snippets from the search.",
        'type': 'object',
        'properties': {
            'answer': {
                'type': 'string',
                'description': 'The answer to the query based on the activation guides knowledge base.'
            },
            'snippets': {
                'type': 'array',
                'description': 'A list of source snippets that support the answer.',
                'items': {
                    'type': 'object',
                    'properties': {
                        'text': {
                            'type': 'string',
                            'description': 'The relevant text content from the source.'
                        },
                        'title': {
                            'type': 'string',
                            'description': 'The title or heading of the source document.'
                        },
                        'uri': {
                            'type': 'string',
                            'description': 'The URI or identifier of the source document.'
                        }
                    },
                    'required': ['text', 'title', 'uri']
                }
            }
        },
        'required': ['answer', 'snippets']
    }
})
def search_activation_guides(
    query: str,
) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    """Searches an unstructured knowledge base of activation guides, troubleshooting steps, and how-to articles.

    When to Use:
    - Use this tool to find procedural or explanatory information to help a
    customer with self-service activation or troubleshooting.
    - This is the primary tool for answering "how to" questions, like "How do I
    set up my new modem?", "What do the lights on my router mean?", or "My
    internet is not working after setup, what should I do?".
    - Do NOT use this tool to look up specific customer order details. Use
    `search_order_details` for that.

    Args:
      query(str): The natural language question to ask the knowledge base. Include the
        device model or service type for better results. Good Example:
        "Step-by-step instructions for installing the 'RouterModel X100'" Bad
        Example: "help"

    Raises:
      ValidationError: If query is invalid or empty.
      EnvironmentError: When GOOGLE_API_KEY or GEMINI_API_KEY are not set
    
    Returns:
        Dict[str, Union[str, List[Dict[str, str]]]]: An object with the answer and snippets from the search.
            - answer (str): The answer to the query based on the activation guides knowledge base.
            - snippets (List[Dict]): A list of source snippets that support the answer, where each snippet contains:
                - text (str): The relevant text content from the source.
                - title (str): The title or heading of the source document.
                - uri (str): The URI or identifier of the source document.
    """
    try:
        input_data = SearchActivationGuidesInput(query=query)
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for search_activation_guides: {finalMsg.strip()}')
    
    

    if DB['use_real_datastore']:
        response = utils.query_activation_guides_infobot(input_data.query)
        return DataStoreQueryResult(
            answer=response.get('answer'),
            snippets=[
                SourceSnippet(
                    text=snippet.get('text'),
                    title=snippet.get('title'),
                    uri=snippet.get('uri'),
                )
                for snippet in response.get('snippets', [])
            ],
        ).model_dump(exclude_none=False)
    
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise EnvironmentError("Please set the GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")

    if "pytest" in sys.modules:
        answer = f"This is a mock answer for your query '{input_data.query}' based on the guide."
        snippets = []
    else:
        result = utils.search_activation_guides_by_llm(input_data.query)

        import json

        print(f"Result: {json.dumps(result, indent=4)}")

        if not result or result == {}:
            return DataStoreQueryResult(
                answer='I have no information about the activation guide.',
                snippets=[],
            ).model_dump(exclude_none=False)

        answer = result.get('answer', '')
        snippet = result.get('snippets', [])
        title = snippet.get('title', '')
        uri = snippet.get('uri', '')

        snippets = [
            SourceSnippet(
                text=snippet.get('introduction', ''),
                title=title,
                uri=uri
            )
        ]

    return DataStoreQueryResult(
        answer=answer,
        snippets=snippets,
    ).model_dump(exclude_none=False)

@tool_spec(spec={
    'name': 'add_activation_guide_from_pdf',
    'description': 'Parses a PDF file, extracts its text content, uses Gemini to categorize it, and adds it as a new entry to the activation guides knowledge base.',
    'parameters': {
        'type': 'object',
        'properties': {
            'pdf_file_path': {
                'type': 'string',
                'description': 'The absolute path to the PDF file to be added as an activation guide.'
            }
        },
        'required': ['pdf_file_path']
    },
    'response': {
        'description': "A confirmation message with the status and the key of the new guide.",
        'type': 'object',
        'properties': {
            'status': {
                'type': 'string',
                'description': 'Status of the operation (e.g., \'success\', \'failure\').'
            },
            'message': {
                'type': 'string',
                'description': 'Descriptive message about the operation result.'
            }
        },
        'required': ['status', 'message']
    }
})
def add_activation_guide_from_pdf(pdf_file_path: str) -> Dict[str, str]:
    """
    Parses a PDF file, extracts its text content, uses Gemini to categorize it, 
    and adds it as a new entry to the activationGuides in the CesSystemActivationDefaultDB.json file.

    Args:
        pdf_file_path (str): The absolute path to the PDF file.

    Returns:
        Dict[str, str]: A confirmation message with the status and the key of the new guide.
    """
    if not pdf_file_path or not isinstance(pdf_file_path, str):
        raise ValidationError("pdf_file_path must be a non-empty string.")

    if not os.path.exists(pdf_file_path):
        raise FileNotFoundError(f"The file {pdf_file_path} was not found.")

    if not pdf_file_path.lower().endswith('.pdf'):
        raise ValueError("The file must be a PDF.")

    try:
        reader = PdfReader(pdf_file_path)
        text = ""
        for page in reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
    except Exception as e:
        raise IOError(f"Error reading or parsing PDF file: {e}")

    if not text.strip():
        raise ValueError("Could not extract any text from the PDF.")

    guide_key = os.path.splitext(os.path.basename(pdf_file_path))[0]
    new_guide = {}

    if "pytest" not in sys.modules:
        # Use Gemini to categorize the text
        client = genai.Client()
        
        system_instruction = """
        You are an expert in categorizing technical documents. Based on the provided text from a PDF, you must create a JSON object that follows this exact structure:
        {
            "title": "A concise and descriptive title",
            "appliesTo": "The target audience (e.g., Home Internet Customers, eSIM-compatible devices)",
            "lastUpdated": "YYYY-MM-DD",
            "keywords": ["list", "of", "relevant", "keywords"],
            "introduction": "A brief introduction from the text.",
            "whatsInTheBox": ["A list of items, if mentioned"],
            "steps": [
                {
                    "step": 1,
                    "title": "Step 1 Title",
                    "description": "Description of step 1."
                }
            ],
            "troubleshooting": [
                {
                    "problem": "A potential problem",
                    "solution": "The corresponding solution."
                }
            ]
        }
        - The `lastUpdated` field should be today's date.
        - The `whatsInTheBox`, `steps`, and `troubleshooting` fields can be empty arrays if not applicable.
        - Return only the JSON object, without any markdown formatting.
        """
        
        prompt = f"Please categorize the following text into the specified JSON format:\n\n{text}"
        
        response = client.models.generate_content(
            model="gemini-2.5-pro", 
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            )
        )

        try:
            new_guide = json.loads(response.text)
        except json.JSONDecodeError:
            raise ValueError("Failed to parse the response from the language model as JSON.")
    else:
        # Provide mock data for testing environment
        new_guide = {
            "title": guide_key.replace("_", " ").title(),
            "appliesTo": "General Test",
            "keywords": ["test"],
            "introduction": "This is a test entry.",
            "whatsInTheBox": [],
            "steps": [],
            "troubleshooting": []
        }

    # Update lastUpdated to current date
    new_guide['lastUpdated'] = datetime.datetime.now().strftime("%Y-%m-%d")

    if "activationGuides" not in DB:
        DB["activationGuides"] = {}
    DB["activationGuides"][guide_key] = new_guide

    return {"status": "success", "message": f"Activation guide '{guide_key}' added successfully."}


@tool_spec(
    input_model=EscalateInput,
    output_model=EscalateOutput,
    description='Use this function to transfer the user to a human agent.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if reason is not a non-empty string or exceeds 1000 characters."])
    ],
    spec={
    'name': 'escalate',
    'description': 'Use this function to transfer the user to a human agent.\n\nThis is a terminal action and will end your conversation.\n\nWhen to Use:\n- The user explicitly asks to speak to a human, manager, or representative.\n- The user\'s request is outside of your capabilities (e.g., closing an\n  account,\n  handling sensitive personal information, or resolving a complex technical\n  issue you are not trained for).\n- The user is expressing extreme frustration or anger that you cannot resolve.',
    'parameters': {
        'type': 'object',
        'properties': {
            'reason': {
                'type': 'string',
                'description': 'A clear and concise explanation for the escalation. This reason will\nbe logged and shown to the human agent. Example: "The user filed a formal\ncomplaint about their billing, which requires a human representative."'
            }
        },
        'required': [
            'reason'
        ]
    },
    'response': {
        'description': "A dictionary with details about the escalation.",
        'type': 'object',
        'properties': {
            'action': {
                'type': 'string',
                'description': 'The action type, always \'escalate\'.'
            },
            'reason': {
                'type': 'string',
                'description': 'The reason for the escalation as provided.'
            },
            'status': {
                'type': 'string',
                'description': 'A message indicating the user will be connected to a human agent.'
            }
        },
        'required': ['action', 'reason', 'status']
    }
})
def escalate(reason: str) -> Dict[str, str]:
    """Use this function to transfer the user to a human agent.

    This is a terminal action and will end your conversation.

    When to Use:
    - The user explicitly asks to speak to a human, manager, or representative.
    - The user's request is outside of your capabilities (e.g., closing an
      account,
      handling sensitive personal information, or resolving a complex technical
      issue you are not trained for).
    - The user is expressing extreme frustration or anger that you cannot resolve.

    Args:
      reason(str): A clear and concise explanation for the escalation. This reason will
        be logged and shown to the human agent. Example: "The user filed a formal
        complaint about their billing, which requires a human representative."

    Raises:
      ValidationError: If the reason is empty or not a string.

    Returns:
        Dict[str, str]: A dictionary with details about the escalation.
            - action (str): The action type, always 'escalate'.
            - reason (str): The reason for the escalation as provided.
            - status (str): A message indicating the user will be connected to a human agent.
    """
    try:
        input_data = EscalateInput(reason=reason)
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for escalate: {finalMsg.strip()}')

    # update to reason why a call has been escalated
    DB['_end_of_conversation_status']['escalate'] = input_data.reason
    
    return {
        'action': 'escalate',
        'reason': input_data.reason,
        'status': 'You will be connected to a human agent shortly.',
    }

@tool_spec(
    input_model=FailInput,
    output_model=FailOutput,
    description='Use this function to gracefully end conversation if request cannot be fulfilled.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if reason is not a non-empty string or exceeds 1000 characters."])
    ],
    spec={
    'name': 'fail',
    'description': 'Use this function to gracefully end conversation if request can\'t be fulfilled.\n\nThis function should be used when you are unable to understand or fulfill the\nuser\'s request after multiple attempts. This is a terminal action.\n\nWhen to Use:\n- Only after you have tried to understand the user at least twice and are\n  still failing.\n- Use this if you are stuck in a loop of not understanding the user\'s intent.\n- Do NOT use this if the user is frustrated; use escalate() instead.',
    'parameters': {
        'type': 'object',
        'properties': {
            'reason': {
                'type': 'string',
                'description': 'A clear and concise internal-facing explanation for why the task\nfailed. This is used for logging and improving the agent. Example: "After three\nattempts, I could not understand the user\'s request. They said \'that thing on my\nbill\' but did not provide clarification when asked."'
            }
        },
        'required': [
            'reason'
        ]
    },
    'response': {
        'description': "A dictionary with details about the termination action.",
        'type': 'object',
        'properties': {
            'action': {
                'type': 'string',
                'description': 'The action type, always \'fail\'.'
            },
            'reason': {
                'type': 'string',
                'description': 'The reason for the failure as provided.'
            },
            'status': {
                'type': 'string',
                'description': 'A message apologizing for being unable to help.'
            }
        },
        'required': ['action', 'reason', 'status']
    }
})
def fail(reason: str) -> Dict[str, str]:
    """Use this function to gracefully end conversation if request can't be fulfilled.

    This function should be used when you are unable to understand or fulfill the
    user's request after multiple attempts. This is a terminal action.

    When to Use:
    - Only after you have tried to understand the user at least twice and are
      still failing.
    - Use this if you are stuck in a loop of not understanding the user's intent.
    - Do NOT use this if the user is frustrated; use escalate() instead.

    Args:
      reason(str): A clear and concise internal-facing explanation for why the task
        failed. This is used for logging and improving the agent. Example: "After three
        attempts, I could not understand the user's request. They said 'that thing on my
        bill' but did not provide clarification when asked."

    Raises:
      ValidationError: If the reason is empty or not a string.

    Returns:
        Dict[str, str]: A dictionary with details about the termination action.
            - action (str): The action type, always 'fail'.
            - reason (str): The reason for the failure as provided.
            - status (str): A message apologizing for being unable to help and suggesting to try again later.
    """
    try:
        input_data = FailInput(reason=reason)
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for fail: {finalMsg.strip()}')

    # update to reason why a call has been failed
    DB['_end_of_conversation_status']['fail'] = input_data.reason

    return {
        'action': 'fail',
        'reason': input_data.reason,
        'status': (
            "I'm sorry, I'm unable to help with that at the moment. Please try"
            ' again later.'
        ),
    }


@tool_spec(
    input_model=CancelInput,
    output_model=CancelOutput,
    description='Use this function to cancel task when user does not want to proceed.',
    error_model=[
        ErrorObject(ValidationError, ["Raised if reason is not a non-empty string or exceeds 1000 characters."])
    ],
    spec={
    'name': 'cancel',
    'description': 'Use this function to cancel task when user doesn\'t want to proceed.\n\nThis function should be used when the user explicitly states they do not want\nto proceed. This is a terminal action.\n\nWhen to Use:\n- The user says "never mind", "I don\'t want to do this anymore", "stop", or\n  "cancel".',
    'parameters': {
        'type': 'object',
        'properties': {
            'reason': {
                'type': 'string',
                'description': 'A clear and concise summary of why the task was canceled, based on\nthe user\'s request. Example: "The user did not have the account information\nready and asked to cancel."'
            }
        },
        'required': [
            'reason'
        ]
    },
    'response': {
        'description': "A dictionary with details about the cancel action.",
        'type': 'object',
        'properties': {
            'action': {
                'type': 'string',
                'description': 'The action type, always \'cancel\'.'
            },
            'reason': {
                'type': 'string',
                'description': 'The reason for the cancellation as provided.'
            },
            'status': {
                'type': 'string',
                'description': 'A message confirming that the request has been canceled.'
            }
        },
        'required': ['action', 'reason', 'status']
    }
})
def cancel(reason: str) -> Dict[str, str]:
    """Use this function to cancel task when user doesn't want to proceed.

    This function should be used when the user explicitly states they do not want
    to proceed. This is a terminal action.

    When to Use:
    - The user says "never mind", "I don't want to do this anymore", "stop", or
      "cancel". 

    Args:
      reason(str): A clear and concise summary of why the task was canceled, based on
        the user's request. Example: "The user did not have the account information
        ready and asked to cancel."

    Raises:
        ValidationError: If the reason is empty or not a string.

    Returns:
        Dict[str, str]: A dictionary with details about the cancel action.
            - action (str): The action type, always 'cancel'.
            - reason (str): The reason for the cancellation as provided.
            - status (str): A message confirming that the request has been canceled.
    """
    try:
        input_data = CancelInput(reason=reason)
    except PydanticValidationError as e:
        finalMsg = ''
        for error in e.errors():
            finalMsg += f'Param {"".join(map(str, error["loc"]))}: {error["msg"]}\n'
        raise ValidationError(f'Invalid input for cancel: {finalMsg.strip()}')

    # update to reason why a call has been canceled
    DB['_end_of_conversation_status']['cancel'] = input_data.reason

    return {
        'action': 'cancel',
        'reason': input_data.reason,
        'status': 'Okay, I have canceled this request.',
    }
