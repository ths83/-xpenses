import logging
import os
import uuid

import boto3
from boto3.dynamodb.conditions import Key
from chalice import Response, NotFoundError

from chalicelib.src.main.commons import request_body_validator, query_params_validator

DYNAMODB = boto3.resource('dynamodb')

ACTIVITIES_TABLE = DYNAMODB.Table(os.environ.get("ACTIVITIES_TABLE"))


def create_activities(payload):
    request_body_validator.validate(payload, ('name', 'createdBy'))

    request = {
        "id": str(uuid.uuid4()),
        "name": payload.get("name"),
        "createdBy": payload.get("createdBy"),
        "expenses": [],
        "activityStatus": "IN_PROGRESS",
        "usersStatus": []
    }

    ACTIVITIES_TABLE.put_item(
        Item=request
    )

    logging.info(f"Successfully created activity '{request['id']}'")
    return Response(body=request, status_code=201)


def get_activity_by_id(activity_id):
    response = ACTIVITIES_TABLE.get_item(
        Key={'id': activity_id}
    )

    response = response.get('Item')
    if response is None:
        not_found_message = f"No activity '{activity_id}' found"
        logging.warning(not_found_message)
        raise NotFoundError(not_found_message)

    logging.info(f"Successfully found activity '{activity_id}'")
    return response


def get_activities_by_creator_id(query_params):
    query_params_validator.validate(query_params, 'createdBy')
    user_id = query_params['createdBy']

    response = ACTIVITIES_TABLE.query(
        IndexName='createdBy-index',
        KeyConditionExpression=Key('createdBy').eq(user_id)
    )

    activities = response.get('Items')
    if len(activities) == 0:
        not_found_message = f"No activities created by user '{user_id}' found"
        logging.warning(not_found_message)
        raise NotFoundError(not_found_message)

    logging.info(f"Successfully found {len(activities)} activities created by user '{user_id}'")

    return activities


def add_expense_to_activity(activity_id, expense_id):
    response = ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression="SET expenses = list_append(expenses, :e)",
        ExpressionAttributeValues={
            ':e': [expense_id]
        },
        ReturnValues="ALL_NEW"
    )

    logging.info(f"Successfully added expense '{expense_id}' to activity '{activity_id}'")

    return response.get("Attributes")


def remove_expense_to_activity(activity_id, expense_id):
    activity = get_activity_by_id(activity_id)
    expenses = activity.get("expenses")

    try:
        expense_id_index = expenses.index(expense_id)
    except ValueError:
        not_found_message = f"No expense '{expense_id}' found in activity '{activity_id}'"
        logging.warning(not_found_message)
        raise NotFoundError(not_found_message)

    ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression=f"REMOVE expenses[{expense_id_index}]"
    )

    logging.info(f"Successfully deleted expense '{expense_id}' from activity '{activity_id}'")

    return Response(status_code=204, body='')


def add_user_to_activity(activity_id, user_id):
    activity = get_activity_by_id(activity_id)
    users_status = activity.get("usersStatus")

    for u in users_status:
        if str(u).startswith(user_id):
            already_exist_message = f"The user '{user_id}' is already in activity '{activity_id}'"
            logging.warning(already_exist_message)
            return already_exist_message

    response = ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression="SET usersStatus = :s",
        ExpressionAttributeValues={
            ':s': [f"{user_id}/IN_PROGRESS"]
        },
        ReturnValues="ALL_NEW"
    )

    logging.info(f"Successfully added user '{user_id}' to activity '{activity_id}'")

    return response.get("Attributes")


def remove_user_from_activity(activity_id, user_id):
    activity = get_activity_by_id(activity_id)
    users_status = activity.get("usersStatus")

    for u in users_status:
        if str(u).startswith(user_id):
            user_id_index = users_status.index(u)
            break
    else:
        not_found_message = f"No user '{user_id}' found in activity '{activity_id}'"
        logging.warning(not_found_message)
        raise NotFoundError(not_found_message)

    ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression=f"REMOVE usersStatus[{user_id_index}]"
    )

    logging.info(f"Successfully deleted user '{user_id}' from activity '{activity_id}'")

    return Response(status_code=204, body='')


def update_user_status(payload):
    global user_id_index, updated_status

    request_body_validator.validate(payload, ('id', 'userId', 'userStatus', 'activityStatus'))

    activity = get_activity_by_id(payload.get('id'))
    users_status = activity.get("usersStatus")

    for u in users_status:
        if str(u).startswith(payload.get('userId')):
            user_id_index = users_status.index(u)
            str(u).split("/")[-1] = payload.get('userId')
            updated_status = u
            break

    if user_id_index is None:
        not_found_message = f"No user '{payload.get('userId')}' found in activity '{payload.get('id')}'"
        logging.warning(not_found_message)
        raise NotFoundError(not_found_message)

    ACTIVITIES_TABLE.update_item(
        Key={'id': payload.get('id')},
        UpdateExpression=f"REMOVE usersStatus[{user_id_index}]"
    )

    response = ACTIVITIES_TABLE.update_item(
        Key={'id': payload.get('id')},
        UpdateExpression="SET usersStatus = list_append(usersStatus, :s)",
        ExpressionAttributeValues={
            ':s': [f"{payload.get('userId')}/{payload.get('status')}"]
        },
        ReturnValues="ALL_NEW"
    )

    logging.info(f"Successfully updated user '{payload.get('userId')}' status from activity '{payload.get('id')}'")

    response = update_activity_status(payload, response)

    return response.get("Attributes")


def update_activity_status(payload, response):
    activity_status = str(payload.get('activityStatus'))
    if not activity_status.isspace():
        response = ACTIVITIES_TABLE.update_item(
            Key={'id': payload.get('id')},
            UpdateExpression="set activityStatus = :s",
            ExpressionAttributeValues={
                ':s': activity_status
            },
            ReturnValues="ALL_NEW"
        )
        logging.info(f"Successfully updated activity status '{payload.get('id')}'")

    return response
