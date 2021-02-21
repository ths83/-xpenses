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
# TODO only current user
@app.route('/users/{user_id}', methods=['GET'], authorizer=authorizer)
def get_user_by_id(user_id):
    return users.get_user_by_name(user_id)


# Expenses
# TODO only if current user in activity users
@app.route('/expenses', methods=['POST'], authorizer=authorizer)
def create_expenses():
    return expenses.create(app.current_request.json_body)


# TODO only if current user in activity users
@app.route('/expenses/{expense_id}', methods=['GET'], authorizer=authorizer)
def get_expense_by_id(expense_id):
    return expenses.get_by_id(expense_id)


# TODO only expenses from given activity
@app.route('/expenses', methods=['GET'], authorizer=authorizer)
def get_expenses_by_activity():
    return expenses.get_expenses_by_activity(app.current_request.query_params)


# Activities
@app.route('/activities', methods=['POST'], authorizer=authorizer)
def create_activity():
    return activities.create(app.current_request.json_body)


# TODO only if current user in activity users
@app.route('/activities/{activity_id}', methods=['GET'], authorizer=authorizer)
def get_activity(activity_id):
    return activities.get_by_id(activity_id)


# TODO only current user
@app.route('/activities', methods=['GET'], authorizer=authorizer)
def get_activities_by_username():
    return activities.get_activities_by_username(app.current_request.query_params)


# TODO only if createdBy user == current user
@app.route('/activities/{activity_id}/expenses/{expense_id}', methods=['DELETE'], authorizer=authorizer)
def delete_expense_from_activity(activity_id, expense_id):
    return activities.remove_expense_to_activity(activity_id, expense_id)


# TODO only current user
@app.route('/activities/{activity_id}', methods=['PUT'], authorizer=authorizer)
def update_activity(activity_id):
    return activities.update(activity_id, app.current_request.json_body)


# TODO only current user
@app.route('/activities/{activity_id}', methods=['DELETE'], authorizer=authorizer)
def delete(activity_id):
    return activities.delete(activity_id)
