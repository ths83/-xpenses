import logging
import os
import uuid
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from chalice import Response, NotFoundError

from chalicelib.src.main.activities import activities
from chalicelib.src.main.commons import request_body_validator, query_params_validator

DYNAMODB = boto3.resource('dynamodb')

EXPENSES_TABLE = DYNAMODB.Table(os.environ.get("EXPENSES_TABLE"))


def create_expense(payload):
    request_body_validator.validate(payload, ('currency', 'amount', 'userId', 'activityId'))
    payload['id'] = str(uuid.uuid4())
    payload['amount'] = Decimal(payload['amount'])

    EXPENSES_TABLE.put_item(
        Item=payload
    )

    activities.add_expense_to_activity(payload.get('activityId'), payload.get('id'))

    logging.info(f"Successfully created expense '{payload.get('id')}' to activity '{payload.get('activityId')}")
    return Response(body=payload, status_code=201)


def get_expense_by_id(expense_id):
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


def get_expenses_by_user_id(query_params):
    query_params_validator.validate(query_params, 'username')
    username = query_params['username']

    response = EXPENSES_TABLE.query(
        IndexName='userId-id-index',
        KeyConditionExpression=Key('userId').eq(username)
    )

    expenses = response.get('Items')
    if len(expenses) == 0:
        not_found_message = f"No expenses found for user '{username}'"
        logging.warning(not_found_message)
        raise NotFoundError(not_found_message)

    logging.info(f"Successfully found {len(expenses)} expenses for user '{username}'")

    return expenses


def update(expense_id, request):
    amount_property = 'amount'
    currency_property = 'currency'
    request_body_validator.validate(request, (amount_property, currency_property))

    response = EXPENSES_TABLE.update_item(
        Key={'id': expense_id},
        UpdateExpression="set amount=:a, currency=:c",
        ExpressionAttributeValues={
            ':a': Decimal(request[amount_property]),
            ':c': str(request[currency_property])
        },
        ReturnValues="ALL_NEW"
    )

    logging.info(f"Successfully updated expense '{expense_id}'")

    return response.get("Attributes")


def delete_currency(expense_id):
    EXPENSES_TABLE.delete_item(
        Key={'id': expense_id},
    )

    success_message = f"Successfully deleted expense '{expense_id}'"
    logging.info(success_message)

    return Response(success_message)
