import logging
import os
import uuid
from datetime import datetime
from operator import itemgetter

import boto3
from chalice import Response, NotFoundError

from chalicelib.src.main.commons import request_body_validator, query_params_validator
from chalicelib.src.main.expenses import expenses
from chalicelib.src.main.model.action import Action
from chalicelib.src.main.users import users

DYNAMODB = boto3.resource('dynamodb')

ACTIVITIES_TABLE = DYNAMODB.Table(os.environ.get("ACTIVITIES_TABLE"))


def create(payload):
    request_body_validator.validate(payload, ('activityName', 'createdBy'))

    owner_username = payload.get("createdBy")
    activity_id = str(uuid.uuid4())

    request = {
        "id": activity_id,
        "activityName": payload.get("activityName"),
        "createdBy": owner_username,
        "expenses": [],
        "users": [os.environ.get("USER_1"), os.environ.get("USER_2")],
        "startDate": datetime.now().isoformat(),
        "activityStatus": Action.IN_PROGRESS.value
    }

    ACTIVITIES_TABLE.put_item(
        Item=request
    )

    users.add_activity(os.environ.get("USER_1"), activity_id)
    users.add_activity(os.environ.get("USER_2"), activity_id)

    logging.info(f"Successfully created activity '{request['id']}'")
    return Response(body=request, status_code=201)


def get_by_id(activity_id):
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
        return []

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

    activities = sorted(response.get('Responses').get(ACTIVITIES_TABLE.name), key=itemgetter('startDate'), reverse=True)

    logging.info(f"Successfully found {len(activities)} activities for user '{username}'")

    return activities


def add_expense(activity_id, expense_id, user_id):
    ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression="SET expenses = list_append(expenses, :e)",
        ExpressionAttributeValues={
            ':e': [expense_id]
        },
    )

    add_user(activity_id, user_id)

    logging.info(f"Successfully added expense '{expense_id}' to activity '{activity_id}'")

    return Response(status_code=204, body="")


def remove_expense_to_activity(activity_id, expense_id):
    activity = get_by_id(activity_id)
    act_expenses = activity.get("expenses")

    try:
        expense_id_index = act_expenses.index(expense_id)
    except ValueError:
        not_found_message = f"No expense '{expense_id}' found in activity '{activity_id}'"
        logging.warning(not_found_message)
        raise NotFoundError(not_found_message)

    expenses.delete(expense_id)

    ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression=f"REMOVE expenses[{expense_id_index}]"
    )

    logging.info(f"Successfully deleted expense '{expense_id}' from activity '{activity_id}'")

    return Response(status_code=204, body="")


def add_user(activity_id, user_id):
    activity = get_by_id(activity_id)
    activity_users = activity.get("users")

    for u in activity_users:
        if str(u) == user_id:
            already_exist_message = f"The user '{user_id}' is already in activity '{activity_id}'"
            logging.warning(already_exist_message)
            return already_exist_message

    users.add_activity(user_id, activity_id)

    ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression="SET users = list_append(users, :u)",
        ExpressionAttributeValues={
            ':u': [f"{user_id}"]
        },
    )

    logging.info(f"Successfully added user '{user_id}' to activity '{activity_id}'")

    return Response(status_code=204, body="")


def update(activity_id, payload):
    get_by_id(activity_id)
    request_body_validator.validate(payload, ['activityName', 'date'])

    activity_name = str(payload.get('activityName'))
    start_date = str(payload.get('date'))

    ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression=f"SET activityName = :name, startDate = :date",
        ExpressionAttributeValues={
            ':name': f"{activity_name}",
            ':date': f"{start_date}"
        },
    ),

    logging.info(f"Successfully updated activity name for activity '{activity_id}'")

    return Response(status_code=204, body="")


def delete(activity_id):
    activity = get_by_id(activity_id)

    users.delete_activity_from_all_users(activity_id)

    [expenses.delete(expense_id) for expense_id in activity.get('expenses')]

    ACTIVITIES_TABLE.delete_item(
        Key={'id': activity_id},
    )

    logging.info(f"Successfully deleted activity '{activity_id}'")

    return Response(status_code=204, body="")


def close(activity_id):
    get_by_id(activity_id)

    ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression=f"SET activityStatus = :status",
        ExpressionAttributeValues={
            ':status': Action.DONE.value,
        },
    ),

    logging.info(f"Successfully closed activity '{activity_id}'")

    return Response(status_code=204, body="")
