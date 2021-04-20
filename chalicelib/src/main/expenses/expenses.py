import logging
import os
import uuid
from decimal import Decimal
from operator import itemgetter

import boto3
from chalice import Response, NotFoundError

from chalicelib.src.main.activities import activities
from chalicelib.src.main.commons import request_body_validator, query_params_validator

DYNAMODB = boto3.resource('dynamodb')

EXPENSES_TABLE = DYNAMODB.Table(os.environ.get("EXPENSES_TABLE"))


def create(payload):
    currency_field = 'currency'
    amount_field = 'amount'
    user_field = 'user'
    name_field = 'expenseName'
    activity_id = 'activityId'
    date = "date"
    category_field = "category"

    request_body_validator.validate(payload, (
        currency_field, amount_field, user_field, activity_id, name_field, date, category_field))

    expense_id = str(uuid.uuid4())
    EXPENSES_TABLE.put_item(
        Item={
            "id": expense_id,
            name_field: payload[name_field],
            amount_field: Decimal(payload[amount_field]),
            currency_field: payload[currency_field],
            user_field: payload[user_field],
            "startDate": payload[date],
            category_field: payload[category_field]
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


def get_expenses_by_activity(query_params):
    query_params_validator.validate(query_params, 'activityId')
    activity_id = query_params['activityId']

    activity = activities.get_by_id(activity_id)

    if len(activity.get('expenses')) == 0:
        not_found_message = f"No expenses found for activity '{activity_id}'"
        logging.warning(not_found_message)
        return []

    response = DYNAMODB.meta.client.batch_get_item(
        RequestItems={
            EXPENSES_TABLE.name:
                {
                    'Keys': [
                        {
                            'id': str(expense_id)
                        }
                        for expense_id in activity.get('expenses')
                    ],
                },
        },
    )

    expenses = sorted(response.get('Responses').get(EXPENSES_TABLE.name), key=itemgetter('startDate'), reverse=True)

    logging.info(f"Successfully found {len(expenses)} expenses for activity '{activity_id}'")

    return expenses


def update(expense_id, request):
    name_field = 'expenseName'
    amount_field = 'amount'
    currency_field = 'currency'
    date_field = 'startDate'
    category_field = 'category'
    request_body_validator.validate(request, (name_field, amount_field, currency_field, date_field, category_field))

    get_by_id(expense_id)

    EXPENSES_TABLE.update_item(
        Key={'id': expense_id},
        UpdateExpression="set expenseName=:n, amount=:a, currency=:c, startDate=:d, category=:cat",
        ExpressionAttributeValues={
            ':n': str(request[name_field]),
            ':a': Decimal(request[amount_field]),
            ':c': str(request[currency_field]),
            ':d': str(request[date_field]),
            ':cat': str(request[category_field]),
        },
    )

    logging.info(f"Successfully updated expense '{expense_id}'")

    return Response(status_code=204, body="")


def delete(expense_id):
    EXPENSES_TABLE.delete_item(
        Key={'id': expense_id},
    )

    logging.info(f"Successfully deleted expense '{expense_id}'")

    return Response(status_code=204, body="")
