import logging
import os

import boto3
from chalice import Response, NotFoundError

from chalicelib.src.main.commons import request_body_validator
from chalicelib.src.main.expenses import expenses

DYNAMODB = boto3.resource('dynamodb')

USERS_TABLE = DYNAMODB.Table(os.environ.get("USERS_TABLE"))


def create(payload):
    request_body_validator.validate(payload, ['name'])
    payload['activities'] = []
    USERS_TABLE.put_item(
        Item=payload
    )

    logging.info(f"Successfully created user '{payload.get('name')}'")
    return Response(status_code=201, body=payload)


def get_user_by_name(username):
    response = USERS_TABLE.get_item(
        Key={'username': username}
    )

    user = response.get('Item')

    if user is None:
        not_found_message = f"The user '{username}' does not exist"
        logging.error(not_found_message)
        raise NotFoundError(not_found_message)

    logging.info(f"Successfully found user '{username}'")

    return user


def add_activity(username, activity_id):
    user = get_user_by_name(username)

    for activity in user.get('activities'):
        if str(activity) is activity_id:
            already_exist_message = f"The user '{user.get('username')}' is already registered to activity '{activity_id}'"
            logging.warning(already_exist_message)
            return already_exist_message

    USERS_TABLE.update_item(
        Key={'username': username},
        UpdateExpression="SET activities = list_append(activities, :act)",
        ExpressionAttributeValues={
            ':act': [f"{activity_id}"]
        },
    )

    logging.info(f"Successfully added activity '{activity_id}' to user '{username}'")

    return Response(status_code=204, body='')


# TODO test
def delete_activity(username, activity_id):
    user = get_user_by_name(username)

    exp = expenses.get_expenses_by_activity({"activityId": activity_id})
    [expenses.delete(i) for i in exp]

    index = user.get('activities').index(activity_id)

    USERS_TABLE.update_item(
        Key={'username': username},
        UpdateExpression=f"REMOVE activities[{index}]"
    )

    logging.info(f"Successfully deleted activity '{activity_id}' to user '{username}'")

    return Response(status_code=204, body='')
