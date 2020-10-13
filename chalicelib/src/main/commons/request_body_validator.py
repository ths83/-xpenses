import logging

from chalice import BadRequestError


def validate(payload, fields):
    missing_fields = []
    for field in fields:
        if payload.get(field) is None or str(payload.get(field)).isspace():
            missing_fields.append(field)

    if len(missing_fields) > 0:
        error_message = f'The following field(s) are missing in the request body : {missing_fields}'
        logging.error(error_message)
        raise BadRequestError(error_message)