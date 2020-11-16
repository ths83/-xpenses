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
        "status": "IN_PROGRESS",
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
        UpdateExpression="SET expenses = list_append(expenses, :expense)",
        ExpressionAttributeValues={
            ':expense': [expense_id]
        },
        ReturnValues="ALL_NEW"
    )

    logging.info(f"Successfully added expense '{expense_id}' to activity {activity_id}")

    return response.get("Attributes")


def remove_expense_to_activity(activity_id, expense_id):
    activity = get_activity_by_id(activity_id)
    expenses = activity.get("expenses")

    try:
        expense_id_index = expenses.index(expense_id)
    except ValueError:
        not_found_message = f"No expense '{expense_id}' found in activity {activity_id}"
        logging.warning(not_found_message)
        raise NotFoundError(not_found_message)

    ACTIVITIES_TABLE.update_item(
        Key={'id': activity_id},
        UpdateExpression=f"REMOVE expenses[{expense_id_index}]"
    )

    logging.info(f"Successfully deleted expense '{expense_id}' from activity {activity_id}")

    return Response(status_code=204, body='')
