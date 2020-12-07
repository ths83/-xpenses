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

# @app.route('/users', methods=['POST'], authorizer=authorizer)
@app.route('/users', methods=['POST'], cors=True)
def create_users():
    return users.create_user(app.current_request.json_body)


# @app.route('/users/{user_id}', methods=['GET'], authorizer=authorizer)
@app.route('/users/{user_id}', methods=['GET'], cors=True)
def get_user_by_id(user_id):
    return users.get_user_by_name(user_id)


# Expenses

# @app.route('/expenses', methods=['POST'], authorizer=authorizer)
@app.route('/expenses', methods=['POST'], cors=True)
def create_expenses():
    return expenses.create_expenses(app.current_request.json_body)


# @app.route('/expenses/{expense_id}', methods=['GET'], authorizer=authorizer)
@app.route('/expenses/{expense_id}', methods=['GET'], cors=True)
def get_expense_by_id(expense_id):
    return expenses.get_expense_by_id(expense_id)


# @app.route('/expenses', methods=['GET'], authorizer=authorizer)
@app.route('/expenses', methods=['GET'], cors=True)
def get_expense_by_user_id():
    return expenses.get_expenses_by_user_id(app.current_request.query_params)


# @app.route('/expenses/{expense_id}', methods=['PATCH'], authorizer=authorizer)
@app.route('/expenses/{expense_id}', methods=['PATCH'], cors=True)
def update_expense(expense_id):
    return expenses.update(expense_id, app.current_request.json_body)


# @app.route('/expenses/{expense_id}', methods=['DELETE'], authorizer=authorizer)
@app.route('/expenses/{expense_id}', methods=['DELETE'], cors=True)
def delete_expense(expense_id):
    return expenses.delete_currency(expense_id)


# Activities

# @app.route('/activities', methods=['POST'], authorizer=authorizer)
@app.route('/activities', methods=['POST'], cors=True)
def create_activity():
    return activities.create_activities(app.current_request.json_body)


# @app.route('/activities/{activity_id}', methods=['GET'], authorizer=authorizer)
@app.route('/activities/{activity_id}', methods=['GET'], cors=True)
def get_activity(activity_id):
    return activities.get_activity_by_id(activity_id)


# @app.route('/activities', methods=['GET'], authorizer=authorizer)
@app.route('/activities', methods=['GET'], cors=True)
def get_activity_by_username():
    return activities.get_activities_by_username(app.current_request.query_params)


# @app.route('/activities/{activity_id}/expenses/{expense_id}', methods=['PUT'], authorizer=authorizer)
@app.route('/activities/{activity_id}/expenses/{expense_id}', methods=['PUT'], cors=True)
def add_expense_to_activity(activity_id, expense_id):
    return activities.add_expense_to_activity(activity_id, expense_id)


# @app.route('/activities/{activity_id}/expenses/{expense_id}', methods=['DELETE'], authorizer=authorizer)
@app.route('/activities/{activity_id}/expenses/{expense_id}', methods=['DELETE'], cors=True)
def delete_expense_from_activity(activity_id, expense_id):
    return activities.remove_expense_to_activity(activity_id, expense_id)


# @app.route('/activities/{activity_id}/users/{user_id}', methods=['PUT'], authorizer=authorizer)
@app.route('/activities/{activity_id}/users/{user_id}', methods=['PUT'], cors=True)
def add_user_to_activity(activity_id, user_id):
    return activities.add_user_to_activity(activity_id, user_id)


# @app.route('/activities/{activity_id}/users/{user_id}', methods=['DELETE'], authorizer=authorizer)
@app.route('/activities/{activity_id}/users/{user_id}', methods=['DELETE'], cors=True)
def delete_user_from_activity(activity_id, user_id):
    return activities.remove_user_from_activity(activity_id, user_id)


# @app.route('/activities', methods=['PUT'], authorizer=authorizer)
@app.route('/activities', methods=['PUT'], cors=True)
def update_activity():
    return activities.update_user_status(app.current_request.json_body)
