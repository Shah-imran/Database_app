from flask import render_template, redirect, request, url_for, flash, current_app, jsonify
from . import main
from .. import config, db
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime


@main.route('/')
@main.route('/index')
def index():
    return redirect(url_for('section_1.edit'))


# @main.route('/section_1')
# def section_1():
#     return render_template('section_1.html')

@main.route('/section_2')
def section_2():
    return render_template('section_2.html')

@main.route('/section_3')
def section_3():
    return render_template('section_3.html')

# @main.route('/pending_request', methods=['GET'], defaults={"page": 1})
# @main.route('/pending_request/<int:page>', methods=['GET'])
# @login_required
# def pending_request(page):
#     per_page = current_app.config["PER_PAGE_PAGINATION"]
#     # subscribers = Subscriber.query.filter_by(
#     #     active=False).paginate(page,per_page,error_out=False)
#     subscribers = Subscriber.query.paginate(page,per_page,error_out=False)
#     return render_template('pending_request.html', subscribers=subscribers, page=page)


# @main.route('/active_user', methods=['GET'], defaults={"page": 1})
# @main.route('/active_user/<int:page>', methods=['GET'])
# @login_required
# def active_user(page):
#     per_page = current_app.config["PER_PAGE_PAGINATION"]
#     subscribers = Subscriber.query.filter_by(
#         active=True).paginate(page,per_page,error_out=False)
#     return render_template('active_user.html', subscribers=subscribers, page=page)

# @main.route('/activate_user/<string:end_date>/<int:id>', methods=['POST'])
# @login_required
# def activate_user(end_date, id):
#     sub = Subscriber.query.get(id)
#     if not sub:
#         return jsonify({'message': 'User not found!'}), 401
#     sub.end_date = datetime.strptime(end_date, '%Y-%m-%d')
#     sub.active = True
#     print(sub.end_date)
#     db.session.add(sub)
#     db.session.commit()
#     return jsonify({"message": "User Activated!"}), 200

# @main.route('/change_subscription/<string:end_date>/<int:id>', methods=['POST'])
# @login_required
# def change_subscription(end_date, id):
#     sub = Subscriber.query.get(id)
#     if not sub:
#         return jsonify({'message': 'User not found!'}), 401
#     sub.end_date = datetime.strptime(end_date, '%Y-%m-%d')
#     # print(sub.end_date)
#     db.session.add(sub)
#     db.session.commit()
#     return jsonify({"message": "Date Changed!"}), 200

# @main.route('/delete_user/<int:id>', methods=['DELETE'])
# @login_required
# def delete_user(id):
#     sub = Subscriber.query.get(id)
#     if not sub:
#         return jsonify({'message': 'User not found!'}), 401
#     db.session.delete(sub)
#     db.session.commit()
#     return jsonify({"message": "User Deleted!"}), 200

# @main.route('/deactivate_user/<int:id>', methods=['POST'])
# @login_required
# def deactivate_user(id):
#     sub = Subscriber.query.get(id)
#     if not sub:
#         return jsonify({'message': 'User not found!'}), 401
#     sub.active = False
#     db.session.add(sub)
#     db.session.commit()
#     return jsonify({"message": "User deactivated!"}), 200
