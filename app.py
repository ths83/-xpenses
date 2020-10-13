import logging

from chalice import Chalice

from chalicelib.src.main.users import users

app = Chalice(app_name='xpenses')
app.debug = True
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@app.route('/users', methods=['POST'])
def create_users():
    return users.create_user(app.current_request.json_body)


@app.route('/users/{user_id}', methods=['GET'])
def get_user_by_id(user_id):
    return users.get_user_by_id(user_id)


# TODO
def add_expenses_to_activity(activity_id, user_id, expenses):
    pass


@app.route('/activities', methods=['POST'])
def create_activity():
    # TODO add status field when push to dynamoDB (WAITING FOR USERS, DONE, CANCELLED)
    # TODO set by default users (me, other one = 2 users)
    # TODO numbers of restant users
    pass


# @app.route('/activities/{activity_id}', methods=['GET'])
def get_activity(activity_id):
    # TODO
    pass


# @app.route('/activities', methods=['GET'])
def get_activities_by_user_id(user_id):
    # TODO use query param
    pass


# @app.route('/activities', methods=['PUT'])
def update_activity():
    # todo
    pass

# todo add dynamoDB lambda event endpoint when activity status == DONE