import logging
import os
import uuid
from datetime import datetime

import boto3
from chalice import Response, NotFoundError

from chalicelib.src.main.commons import request_body_validator, query_params_validator
from chalicelib.src.main.model.action import Action
from chalicelib.src.main.users import users

DYNAMODB = boto3.resource('dynamodb')

ACTIVITIES_TABLE = DYNAMODB.Table(os.environ.get("ACTIVITIES_TABLE"))


def create_activity(payload):
    request_body_validator.validate(payload, ('name', 'createdBy'))

    owner_username = payload.get("createdBy")
    activity_id = str(uuid.uuid4())

    request = {
        "id": activity_id,
        "name": payload.get("name"),
        "createdBy": owner_username,
        "expenses": [],
        "activityStatus": Action.IN_PROGRESS.value,
        "usersStatus": [f"{owner_username}/{Action.IN_PROGRESS.value}"],
        "date": datetime.now().isoformat()
    }

    ACTIVITIES_TABLE.put_item(
        Item=request
    )

    users.add_activity(owner_username, activity_id)

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


def get_activities_by_username(query_params):
    query_params_validator.validate(query_params, 'username')
    username = query_params['username']

    user = users.get_user_by_name(username)
    if len(user.get('activities')) == 0:
        not_found_message = f"No activities registered for user '{username}'"
        logging.warning(not_found_message)
        raise NotFoundError(not_found_message)

    response = DYNAMODB.meta.client.batch_get_item(
        RequestItems={
            ACTIVITIES_TABLE.name:
                {
                    'Keys': [
                        {
                            'id': str(activity_id)
                        }
                        for activity_id in user.get('activities')
                    ],
                },
        },
    )

    activities = response.get('Responses').get(ACTIVITIES_TABLE.name)

    logging.info(f"Successfully found {len(activities)} activities for user '{username}'")

    return activities


def add_expense_to_activity(activity_id, expense_id, user_id):
    response = ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression="SET expenses = list_append(expenses, :e)",
        ExpressionAttributeValues={
            ':e': [expense_id]
        },
        ReturnValues="ALL_NEW"
    )

    add_user_to_activity(activity_id, user_id)

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

    users.add_activity(user_id, activity_id)

    response = ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression="SET usersStatus = list_append(usersStatus, :u)",
        ExpressionAttributeValues={
            ':u': [f"{user_id}/{Action.IN_PROGRESS.value}"]
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

    request_body_validator.validate(payload, ('id', 'userId', 'userStatus'))

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

    updated_activity = ACTIVITIES_TABLE.update_item(
        Key={'id': payload.get('id')},
        UpdateExpression="SET usersStatus = list_append(usersStatus, :s)",
        ExpressionAttributeValues={
            ':s': [f"{payload.get('userId')}/{payload.get('userStatus')}"]
        },
        ReturnValues="ALL_NEW"
    )

    logging.info(f"Successfully updated user '{payload.get('userId')}' status from activity '{payload.get('id')}'")

    updated_activity = updated_activity.get("Attributes")

    closed_activity = close_activity(updated_activity)

    return updated_activity if closed_activity is None else closed_activity


def close_activity(activity):
    users_status = activity.get("usersStatus")
    for u in users_status:
        if str(u).endswith(Action.DONE.value):
            continue
        else:
            return None

    response = ACTIVITIES_TABLE.update_item(
        Key={'id': activity.get('id')},
        UpdateExpression="set activityStatus = :s",
        ExpressionAttributeValues={
            ':s': Action.DONE.value
        },
        ReturnValues="ALL_NEW"
    )
    logging.info(f"Successfully closed activity '{activity.get('id')}'")

    return response.get("Attributes")
