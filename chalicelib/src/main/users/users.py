import logging
import os
import uuid

import boto3
from chalice import Response

from chalicelib.src.main.commons import request_body_validator

DYNAMODB = boto3.resource('dynamodb')

USERS_TABLE = DYNAMODB.Table(os.environ.get("USERS_TABLE"))


def create_user(payload):
    request_body_validator.validate(payload, ['name'])
    payload['id'] = str(uuid.uuid4())
    USERS_TABLE.put_item(
        Item=payload
    )

    logging.info(f"Successfully created user '{payload.get('id')}'")
    return Response(body=payload, status_code=201)


def get_user_by_id(user_id):
    response = USERS_TABLE.get_item(
        Key={'id': user_id}
    )

    logging.info(f"Successfully found user '{user_id}'")
    return response['Item']
