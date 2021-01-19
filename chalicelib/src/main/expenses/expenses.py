import logging
import os
import uuid
from datetime import datetime
from decimal import Decimal

import boto3
from chalice import Response, NotFoundError

from chalicelib.src.main.activities import activities
from chalicelib.src.main.commons import request_body_validator

DYNAMODB = boto3.resource('dynamodb')

EXPENSES_TABLE = DYNAMODB.Table(os.environ.get("EXPENSES_TABLE"))


def create(payload):
    currency_field = 'currency'
    amount_field = 'amount'
    user_field = 'user'
    name_field = 'name'
    activity_id = 'activityId'

    request_body_validator.validate(payload, (currency_field, amount_field, user_field, activity_id, name_field))

    expense_id = str(uuid.uuid4())
    EXPENSES_TABLE.put_item(
        Item={
            "id": expense_id,
            "name": payload[name_field],
            "amount": Decimal(payload[amount_field]),
            "currency": payload[currency_field],
            "user": payload[user_field],
            "date": datetime.now().isoformat()
        }
    )

    activities.add_expense(payload.get(activity_id), expense_id, payload.get(user_field))

    logging.info(f"Successfully created expense '{payload.get('id')}'")
    return Response(body=payload, status_code=201)


def get_by_id(expense_id):
    response = EXPENSES_TABLE.get_item(
        Key={'id': expense_id}
    )

    response = response.get('Item')
    if response is None:
        not_found_message = f"No expense '{expense_id}' found"
        logging.warning(not_found_message)
        raise NotFoundError(not_found_message)

    logging.info(f"Successfully found expense '{expense_id}'")
    return response


# def get_expenses_by_username(query_params):
#     query_params_validator.validate(query_params, 'username')
#     username = query_params['username']
#
#     response = EXPENSES_TABLE.query(
#         IndexName='user-id-index',
#         KeyConditionExpression=Key('user').eq(username)
#     )
#
#     expenses = response.get('Items')
#     if len(expenses) == 0:
#         not_found_message = f"No expenses found for user '{username}'"
#         logging.warning(not_found_message)
#         raise NotFoundError(not_found_message)
#
#     logging.info(f"Successfully found {len(expenses)} expenses for user '{username}'")
#
#     return expenses


def update(expense_id, request):
    name_field = 'name'
    amount_field = 'amount'
    currency_field = 'currency'
    request_body_validator.validate(request, (name_field, amount_field, currency_field))

    get_by_id(expense_id)

    EXPENSES_TABLE.update_item(
        Key={'id': expense_id},
        UpdateExpression="set name=:n, amount=:a, currency=:c",
        ExpressionAttributeValues={
            ':n': str(request[name_field]),
            ':a': Decimal(request[amount_field]),
            ':c': str(request[currency_field])
        },
    )

    logging.info(f"Successfully updated expense '{expense_id}'")

    return Response(status_code=204, body='')


def delete(expense_id):
    EXPENSES_TABLE.delete_item(
        Key={'id': expense_id},
    )

    success_message = f"Successfully deleted expense '{expense_id}'"
    logging.info(success_message)

    return Response(status_code=204, body='')
