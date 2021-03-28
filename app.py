import logging
import os

from chalice import Chalice, CognitoUserPoolAuthorizer

from chalicelib.src.main.activities import activities
from chalicelib.src.main.expenses import expenses
from chalicelib.src.main.users import users

app = Chalice(app_name='xpenses')
app.debug = True
logger = logging.getLogger()
logger.setLevel(logging.INFO)

authorizer = CognitoUserPoolAuthorizer('xpensesPool', provider_arns=[os.environ.get("COGNITO_USER_POOL_ARN")])


# Users
@app.route('/users/{username}', methods=['GET'], authorizer=authorizer)
def get_user_by_id(username):
    return users.get_user_by_name(username)


# Expenses
@app.route('/expenses', methods=['POST'], authorizer=authorizer)
def create_expenses():
    return expenses.create(app.current_request.json_body)


@app.route('/expenses/{expense_id}', methods=['GET'], authorizer=authorizer)
def get_expense_by_id(expense_id):
    return expenses.get_by_id(expense_id)


@app.route('/expenses', methods=['GET'], authorizer=authorizer)
def get_expenses_by_activity():
    return expenses.get_expenses_by_activity(app.current_request.query_params)


@app.route('/expenses/{expense_id}', methods=['PUT'], authorizer=authorizer)
def update(expense_id):
    return expenses.update(expense_id, app.current_request.json_body)


# Activities
@app.route('/activities', methods=['POST'], authorizer=authorizer)
def create_activity():
    return activities.create(app.current_request.json_body)


@app.route('/activities/{activity_id}', methods=['GET'], authorizer=authorizer)
def get_activity(activity_id):
    return activities.get_by_id(activity_id)


@app.route('/activities', methods=['GET'], authorizer=authorizer)
def get_activities_by_username():
    return activities.get_activities_by_username(app.current_request.query_params)


@app.route('/activities/{activity_id}/expenses/{expense_id}', methods=['DELETE'], authorizer=authorizer)
def delete_expense_from_activity(activity_id, expense_id):
    return activities.remove_expense_to_activity(activity_id, expense_id)


@app.route('/activities/{activity_id}', methods=['PUT'], authorizer=authorizer)
def update_activity(activity_id):
    return activities.update(activity_id, app.current_request.json_body)


@app.route('/activities/{activity_id}', methods=['DELETE'], authorizer=authorizer)
def delete(activity_id):
    return activities.delete(activity_id)


@app.route('/activities/{activity_id}', methods=['PATCH'], authorizer=authorizer)
def close(activity_id):
    return activities.close(activity_id)
