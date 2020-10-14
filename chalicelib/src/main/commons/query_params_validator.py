import logging

from chalice import BadRequestError


def validate(query_params, param):
    if query_params is None:
        error_message = "Missing query params"
        logging.error(error_message)
        raise BadRequestError(error_message)

    if query_params.get(param) is None or str(query_params.get(param)).isspace() or str(query_params.get(param)) == "":
        error_message = f'The following query param is missing : {param}'
        logging.error(error_message)
        raise BadRequestError(error_message)
