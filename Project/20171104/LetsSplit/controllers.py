from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug import secure_filename
from datetime import datetime
import os
from models import DB, users, friends, transactions, groups, group_transactions, friend_requests


app_blueprint = Blueprint('app_blueprint', __name__)

def search(username, request):
    #print("HAHA")
    search_user = request.args.get('search', None, str)
    user = friends.query.filter_by(username=username).first()
    print(user.friend)
    if search_user:
        if len(search_user) > 0:
            results = users.query.filter(users.username.startswith(search_user)).all()
            ans_list = {}
            user_friend_list = user.friend.split(',')

            if results is not None:
                for x in results:
                    if x.username in user_friend_list:
                        ans_list[x.username] = []
                        ans_list[x.username].append(x.name)
                        ans_list[x.username].append(x.profile_pic)
            return ans_list


def friend_request_search(username):
    friend_request_list = friend_requests.query.filter_by(to_user=username).all()
    return friend_request_list


def accept_friend_request(username, request):
    fr1 = friends.query.filter_by(username=username).first()  
    friend_status = {}  
    friend_request = friend_requests.query.filter_by(from_user=request.form['person']).filter_by(to_user=username).first()
    DB.session.delete(friend_request)
    fr2 = friends.query.filter_by(username=request.form['person']).first()
    a = fr2.friend
    z = fr1.friend
    fr1.friend = z + request.form['person'] + ','
    fr2.friend = a + username + ','
    friend_list = fr1.friend.split(',')
    #friend_list = friend_list + request.form['person'] + ','
    DB.session.commit()
    friend_requests_from_username = friend_requests.query.filter_by(from_user=username).all()
    friend_requests_to_username = friend_requests.query.filter_by(to_user=username).all()
    for x in friend_requests_from_username:
        friend_status[x.to_user] = "Friend Request sent by me"
    for x in friend_requests_to_username:
        friend_status[x.from_user] = "Friend Request sent to me"
    for x in friend_list:
        friend_status[x] = "Friend"
    return friend_status
        #print(friend_status)
        #print(friend_list)
        #print(friend_status)
        #return render_template('search_results.html', username=username, results=results, message=message, profile_pic_dict=url_dict, friend_status=friend_status, friend_requests_list=friend_request_search(username))


def delete_friend_request(username, request):
    friend_request = friend_requests.query.filter_by(from_user=request.form['person']).filter_by(to_user=username).first()
    DB.session.delete(friend_request)
    DB.session.commit()
    return


@app_blueprint.route('/<username>/search_people')
def searching(username):
    #print("HAHA")
    results = search(username, request)
    return jsonify(results)


@app_blueprint.route('/', methods = ['GET', 'POST'])
def sign_up(message=None):
    if request.method == 'POST':
        if 'SignUp' in request.form:
            if not request.form['email'] or not request.form['username'] or not request.form['password'] or not request.form['DOB'] or not request.form['passwordconfirm']:
                flash('Please enter all the fields', 'error')
            else:
                x = users.query.filter_by(username=request.form['username']).first()
                if request.form['password'] != request.form['passwordconfirm']:
                    message = 'Passwords Don\'t Match'
                if x is None:
                    img = request.files['profile_pic']
                    img.save(secure_filename(img.filename))
                    os.system("mv " + secure_filename(img.filename) + " ./static/")
                    user = users(email = request.form['email'], username = request.form['username'], password = request.form['password'], DOB = request.form['DOB'], profile_pic_url = secure_filename(img.filename), name = request.form['name'], bio = request.form['bio'])
                    user_friends = friends(username=request.form['username'])
                    DB.session.add(user)
                    DB.session.add(user_friends)
                    DB.session.commit()
                    return redirect(url_for('app_blueprint.profile_page', username=request.form['username']))
                else:
                    message = 'Username already taken'

        elif 'SignIn' in request.form:
            if request.form['username'] is '':
                message = "Please Enter Username"
            elif not request.form['password']:
                message = "Please Enter Password"
            else :
                x = users.query.filter_by(username=request.form['username']).first()
                if x is None:
                    message = "Incorrect Username"
                elif request.form['password'] is None:
                    message = 'Please Enter Password'
                elif x.check_password(str(request.form['password'])) == True and x is not None:
                    return redirect(url_for('app_blueprint.profile_page', username=request.form['username']))
                elif x.check_password(str(request.form['password'])) == False:
                    message = "Incorrect Password"

    return render_template('home.html', message=message)


@app_blueprint.route('/<username>', methods=['GET', 'POST'])
def profile_page(username, message=None):
    user = users.query.filter_by(username=username).first()
    friend_list = []
    #if request.method == 'GET':
    #    #print("HAHA")
    #    results = search(request)
    to_list = transactions.query.filter_by(from_user=username).all()
    from_list = transactions.query.filter_by(to_user=username).all()

    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'add_transaction' in request.form:
            if request.form['from_user'] == username:
                if request.form['to_user'] not in friend_list:
                    message = request.form['to_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            elif request.form['to_user'] == username:
                if request.form['from_user'] not in friend_list:
                    message = request.form['from_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            else:
                message = "You can only add your own transactions"
        if 'edit_transaction' in request.form:
            x = friends.query.filter_by(username=username).first()
            friend_list = x.friend.split(',')
            id = request.form['transaction_id']
            if request.form['from_user'] != username and request.form['to_user'] != username:
                message = "Please enter the correct usernames"
                return render_template('profile_page.html', username=username, user=user, message=message, to_list=to_list, from_list=from_list, friend_requests_list=friend_request_search(username))
            if request.form['from_user'] == username:
                if request.form['to_user'] not in friend_list:
                    message = "Please enter the correct usernames"
                    return render_template('profile_page.html', username=username, user=user, message=message, to_list=to_list, from_list=from_list, friend_requests_list=friend_request_search(username))
            if request.form['to_user'] == username:
                if request.form['from_user'] not in friend_list:
                    message = "Please enter the correct usernames"
                    return render_template('profile_page.html', username=username, user=user, message=message, to_list=to_list, from_list=from_list, friend_requests_list=friend_request_search(username))
            transaction = transactions.query.get(id)
            transaction.from_user = request.form['from_user']
            transaction.to_user = request.form['to_user']
            transaction.amount = request.form['amount_user']
            DB.session.commit()
        if 'delete' in request.form:
            id = request.form['del_id']
            transaction = transactions.query.get(id)
            DB.session.delete(transaction)
            DB.session.commit()
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'settle' in request.form:
            transaction = transactions.query.get(request.form['primary_id'])
            transaction.settled = "1"
            date_settled = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            transaction.date_settled = date_settled
            DB.session.commit()
        if 'comment_add' in request.form:
            x = transactions.query.get(request.form['transaction_id'])
            x.comments = x.comments + ',' + request.form['submitting_user'] + ' ' + request.form['comment']
            DB.session.commit()
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))
        if "friend_request_accept" in request.form:
            friend_status = accept_friend_request(username, request)
            to_list = transactions.query.filter_by(from_user=username).all()
            from_list = transactions.query.filter_by(to_user=username).all()
            return render_template('profile_page.html', username=username, user=user, message=message, to_list=to_list, from_list=from_list, friend_requests_list=friend_request_search(username))            
        if 'friend_request_delete' in request.form:
            delete_friend_request(username, request)

    to_list = transactions.query.filter_by(from_user=username).all()
    from_list = transactions.query.filter_by(to_user=username).all()

    return render_template('profile_page.html', username=username, user=user, message=message, to_list=to_list, from_list=from_list, friend_requests_list=friend_request_search(username))


@app_blueprint.route('/<username>/search/<query>', methods=['GET', 'POST'])
def search_results(username, query, message=None):
    url_dict = {}
    friend_list = []
    fr1 = friends.query.filter_by(username=username).first()
    friend_list = fr1.friend.split(',')
    results = users.query.filter(users.username.startswith(query)).all()
    for res in results:
        if res.username == username:
            results.remove(res)
            break
    for x in results:
        url_dict[x.username] = x.profile_pic
    if not results:
        message = "Oops... No results found"
    friend_requests_from_username = []
    friend_requests_to_username = []
    friend_status = {}
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'add_friend' in request.form:
            fr2 = friends.query.filter_by(username=request.form['friend_to_be_added']).first()
            # a = fr2.friend
            # z = fr1.friend
            # fr1.friend = z + request.form['friend_to_be_added'] + ','
            # fr2.friend = a + username + ','
            friend_list = fr1.friend.split(',')
            friend_request = friend_requests(from_user=username, to_user=request.form['friend_to_be_added'])
            DB.session.add(friend_request)
            DB.session.commit()
            friend_requests_from_username = friend_requests.query.filter_by(from_user=username).all()
            friend_requests_to_username = friend_requests.query.filter_by(to_user=username).all()
            for x in friend_requests_from_username:
                friend_status[x.to_user] = "Friend Request sent by me"
            for x in friend_requests_to_username:
                friend_status[x.from_user] = "Friend Request sent to me"
            for x in friend_list:
                friend_status[x] = "Friend"
        if "friend_request_accept" in request.form:
            friend_status = accept_friend_request(username, request)
            return render_template('search_results.html', username=username, results=results, message=message, profile_pic_dict=url_dict, friend_status=friend_status, friend_requests_list=friend_request_search(username))
        if 'friend_request_delete' in request.form:
            delete_friend_request(username, request)
        if 'add_transaction' in request.form:
            if request.form['from_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['from_user']).first()
                friend_list = x.friend.split(',')
                if request.form['to_user'] not in friend_list:
                    message = request.form['to_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled=False, date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            elif request.form['to_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['to_user']).first()
                friend_list = x.friend.split(',')
                if request.form['from_user'] not in friend_list:
                    message = request.form['from_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled=False, date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            else:
                message = "You can only add your own transactions"
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))
    friend_requests_from_username = friend_requests.query.filter_by(from_user=username).all()
    friend_requests_to_username = friend_requests.query.filter_by(to_user=username).all()
    for x in friend_requests_from_username:
        friend_status[x.to_user] = "Friend Request sent by me"
    for x in friend_requests_to_username:
        friend_status[x.from_user] = "Friend Request sent to me"
    for x in friend_list:
        friend_status[x] = "Friend"
    print(friend_status)
    return render_template('search_results.html', username=username, results=results, message=message, profile_pic_dict=url_dict, friend_status=friend_status, friend_requests_list=friend_request_search(username))


@app_blueprint.route('/<username>/history', methods=['GET', 'POST'])
def log(username, message=None):
    user = users.query.filter_by(username=username).first()
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'add_transaction' in request.form:
            if request.form['from_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['from_user']).first()
                friend_list = x.friend.split(',')
                if request.form['to_user'] not in friend_list:
                    message = request.form['to_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            elif request.form['to_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['to_user']).first()
                friend_list = x.friend.split(',')
                if request.form['from_user'] not in friend_list:
                    message = request.form['from_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            else:
                message = "You can only add your own transactions"
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'comment_add' in request.form:
            x = transactions.query.get(request.form['transaction_id'])
            x.comments = x.comments + ',' + request.form['submitting_user'] + ' ' + request.form['comment']
            DB.session.commit()
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))
        if "friend_request_accept" in request.form:
            friend_status = accept_friend_request(username, request)
            to_list = transactions.query.filter_by(from_user=username).all()
            from_list = transactions.query.filter_by(to_user=username).all()
            return render_template('log.html', username=username, user=user, to_list=to_list, from_list=from_list, message=message, friend_requests_list=friend_request_search(username))
        if 'friend_request_delete' in request.form:
            delete_friend_request(username, request)

    to_list = transactions.query.filter_by(from_user=username).all()
    from_list = transactions.query.filter_by(to_user=username).all()

    return render_template('log.html', username=username, user=user, to_list=to_list, from_list=from_list, message=message, friend_requests_list=friend_request_search(username))


@app_blueprint.route('/<username>/search/<query>/profile', methods = ['GET', 'POST'])
def open_else_profile(username, query, message=None):
    query_user = users.query.filter_by(username=query).first()
    to_list = transactions.query.filter_by(from_user=query).all()
    from_list = transactions.query.filter_by(to_user=query).all()
    total_amount = 0
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'settle' in request.form:
            transaction = transactions.query.get(request.form['primary_id'])
            transaction.settled = "1"
            date_settled = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            transaction.date_settled = date_settled
            DB.session.commit()
        if 'comment_add' in request.form:
            x = transactions.query.get(request.form['transaction_id'])
            x.comments = x.comments + ',' + request.form['submitting_user'] + ' ' + request.form['comment']
            DB.session.commit()
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))
        if 'edit_transaction' in request.form:
            id = request.form['transaction_id']
            transaction = transactions.query.filter_by(id=id).first()
            if request.form['from_user'] == username:
                if request.form['to_user'] == query:
                    transaction.from_user = request.form['from_user']
                    transaction.to_user = request.form['to_user']
                    transaction.amount = request.form['amount_user']
                    DB.session.commit()
            elif request.form['to_user'] == username:
                if request.form['from_user'] == query:
                    transaction.from_user = request.form['from_user']
                    transaction.to_user = request.form['to_user']
                    transaction.amount = request.form['amount_user']
                    DB.session.commit()
            else:
                message = "Please enter the correct usernames"
                return render_template('else_profile.html', username=username, query=query, query_user=query_user, from_list=from_list, to_list=to_list, message=message, total_amount=total_amount, friend_requests_list=friend_request_search(username))
        if 'delete' in request.form:
            id = request.form['del_id']
            transaction = transactions.query.get(id)
            DB.session.delete(transaction)
            DB.session.commit()
        if "friend_request_accept" in request.form:
            friend_status = accept_friend_request(username, request)
            to_list = transactions.query.filter_by(from_user=query).all()
            from_list = transactions.query.filter_by(to_user=query).all()
            total_amount = 0
            for x in to_list:
                if x.to_user == username and x.settled=="0":
                    total_amount += int(x.amount)
            for x in from_list:
                if x.from_user == username and x.settled=="0":
                    total_amount -= int(x.amount)
            return render_template('else_profile.html', username=username, query=query, query_user=query_user, from_list=from_list, to_list=to_list, message=message, total_amount=total_amount, friend_requests_list=friend_request_search(username))
        if 'friend_request_delete' in request.form:
            delete_friend_request(username, request)
        if 'settle_all' in request.form:
            all_trans = transactions.query.filter_by(from_user=username).filter_by(to_user=query).all()
            date_settled = datetime.now().strftime('%Y-%m-%d %H:%M:%S')            
            for trans in all_trans:
                trans.settled = "1"
                trans.date_settled = date_settled
            all_trans = transactions.query.filter_by(from_user=query).filter_by(to_user=username).all()
            for trans in all_trans:
                trans.settled = "1"
                trans.date_settled = date_settled
            DB.session.commit()

    to_list = transactions.query.filter_by(from_user=query).all()
    from_list = transactions.query.filter_by(to_user=query).all()
    total_amount = 0
    for x in to_list:
        if x.to_user == username and x.settled=="0":
            total_amount += int(x.amount)
    for x in from_list:
        if x.from_user == username and x.settled=="0":
            total_amount -= int(x.amount)
    return render_template('else_profile.html', username=username, query=query, query_user=query_user, from_list=from_list, to_list=to_list, message=message, total_amount=total_amount, friend_requests_list=friend_request_search(username))


@app_blueprint.route('/<username>/friends', methods = ['GET', 'POST'])
def friends_display(username, message=None):
    user = users.query.filter_by(username=username).first()
    x = []
    friend_list = []
    url_list = []
    x = friends.query.filter_by(username=username).first()
    friend_list = x.friend.split(',')
    for y in friend_list:
        if y != '':
            z = users.query.filter_by(username=y).first()
            url_list.append(z)
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'add_transaction' in request.form:
            if request.form['from_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['from_user']).first()
                friend_list = x.friend.split(',')
                if request.form['to_user'] not in friend_list:
                    message = request.form['to_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            elif request.form['to_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['to_user']).first()
                friend_list = x.friend.split(',')
                if request.form['from_user'] not in friend_list:
                    message = request.form['from_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            else:
                message = "You can only add your own transactions"
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))
        if 'group_submission' in request.form:
            group_name = request.form['group_name']
            group_members = request.form['people_in_group']
            group = groups(name=group_name, group_members=group_members)
            DB.session.add(group)
            DB.session.commit()
            return redirect(url_for('app_blueprint.group_page', username=username, group_name=group_name))
        if "friend_request_accept" in request.form:
            friend_status = accept_friend_request(username, request)
            return render_template('friends.html', username=username, user=user, friend_list=url_list, message=message, friend_requests_list=friend_request_search(username))            
        if 'friend_request_delete' in request.form:
            delete_friend_request(username, request)

    return render_template('friends.html', username=username, user=user, friend_list=url_list, message=message, friend_requests_list=friend_request_search(username))


@app_blueprint.route('/<username>/groups', methods = ['GET', 'POST'])
def groups_display(username):
    user = users.query.filter_by(username=username).first()
    group_list = []
    groups_all = groups.query.all()
    for group in groups_all:
        if username in group.group_members.split(','):
            group_list.append(group)
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))
        if "friend_request_accept" in request.form:
            friend_status = accept_friend_request(username, request)
            return render_template('all_groups.html', username=username, user=user, group_list=group_list, friend_requests_list=friend_request_search(username))                        
        if 'friend_request_delete' in request.form:
            delete_friend_request(username, request)


    return render_template('all_groups.html', username=username, user=user, group_list=group_list, friend_requests_list=friend_request_search(username))


@app_blueprint.route('/<username>/groups/<group_name>', methods = ['GET', 'POST'])
def group_page(username, group_name):
    group = groups.query.filter_by(group_name=group_name).first()
    members_list = []
    url_list = []
    transaction_list = group_transactions.query.filter_by(group_name=group_name).all()
    members_list = group.group_members.split(',')
    for m in members_list:
        if m != '':
            z = users.query.filter_by(username=m).first()
            url_list.append(z)
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))
        if 'add_transaction' in request.form:
            date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if request.form['from_member'] not in members_list or request.form['to_member'] not in members_list:
                message = "Not a group member"
                return render_template('group_page.html', username=username, group_name=group_name, group_members=group.group_members, members_list=url_list, transaction_list=transaction_list, message=message, friend_requests_list=friend_request_search(username))
            transaction = group_transactions(group_name=group_name, from_member=request.form['from_member'], to_member=request.form['to_member'], amount=request.form['amount'], settled="0", date_created=date_created)
            DB.session.add(transaction)
            DB.session.commit()
        if 'add_equal_transaction' in request.form:
            members_receiving = []
            members_paying = []
            total_people = int(request.form['num_members_total'])
            total_amount = int(request.form['total_amount'])
            members_receiving = request.form['members_receiving'].split(',')
            members_paying = request.form['members_paying'].split(',')
            members_receiving[0] = members_receiving[0].strip()
            members_paying[0] = members_paying[0].strip()
            num_receiving = len(members_receiving) - 1
            num_paying = len(members_paying) - 1
            each_recieves = (total_amount/num_receiving) - (total_amount/total_people)
            each_pays = each_recieves/num_paying
            date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for receiver in members_receiving:
                for payee in members_paying:
                    if receiver != '' and payee != '':
                        transaction = group_transactions(group_name=group_name, from_member=payee, to_member=receiver, amount=each_pays, settled="0", date_created=date_created)
                        DB.session.add(transaction)
                        DB.session.commit()
        if 'comment_add' in request.form:
            x = group_transactions.query.get(request.form['transaction_id'])
            x.comments = x.comments + ',' + request.form['submitting_user'] + ' ' + request.form['comment']
            DB.session.commit()
        if 'settle' in request.form:
            transaction = group_transactions.query.get(request.form['primary_id'])
            transaction.settled = "1"
            date_settled = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            transaction.date_settled = date_settled
            DB.session.commit()
        if 'person_to_be_added' in request.form:
            x =  friends.query.filter_by(username=username).first()
            if request.form['person_to_be_added'] not in x.friend.split(','):
                return render_template('group_page.html', username=username, group_name=group_name, group_members=group.group_members, members_list=url_list, transaction_list=transaction_list, message="Not Your Friend", friend_requests_list=friend_request_search(username))
            else:
                z = groups.query.filter_by(group_name=group_name).first()
                z.group_members = z.group_members + request.form['person_to_be_added'] + ','
                DB.session.commit()
                group = groups.query.filter_by(group_name=group_name).first()
                members_list = []
                url_list = []
                transaction_list = group_transactions.query.filter_by(group_name=group_name).all()
                members_list = group.group_members.split(',')
                for m in members_list:
                    if m != '':
                        z = users.query.filter_by(username=m).first()
                        url_list.append(z)
                return render_template('group_page.html', username=username, group_name=group_name, group_members=group.group_members, members_list=url_list, transaction_list=transaction_list, message=None, friend_requests_list=friend_request_search(username))
        if 'edit_transaction' in request.form:
            print (request.form)
            id = request.form['transaction_id']
            if request.form['from_user'] not in members_list or request.form['to_user'] not in members_list:
                message = "Please Enter Correct Usernames"
                return render_template('group_page.html', username=username, group_name=group_name, group_members=group.group_members, members_list=url_list, transaction_list=transaction_list, message=message, friend_requests_list=friend_request_search(username))
            transaction = group_transactions.query.filter_by(id=id).first()
            transaction.from_member = request.form['from_user']
            transaction.to_member = request.form['to_user']
            transaction.amount = request.form['amount_user']
            DB.session.commit()
        if 'delete' in request.form:
            id = request.form['del_id']
            transaction = group_transactions.query.get(id)
            DB.session.delete(transaction)
            DB.session.commit()
        if "friend_request_accept" in request.form:
            friend_status = accept_friend_request(username, request)
            transaction_list = group_transactions.query.filter_by(group_name=group_name).all()
            group = groups.query.filter_by(group_name=group_name).first()
            return render_template('group_page.html', username=username, group_name=group_name, group_members=group.group_members, members_list=url_list, transaction_list=transaction_list, message=None, friend_requests_list=friend_request_search(username))
        if 'friend_request_delete' in request.form:
            delete_friend_request(username, request)


    transaction_list = group_transactions.query.filter_by(group_name=group_name).all()
    group = groups.query.filter_by(group_name=group_name).first()

    return render_template('group_page.html', username=username, group_name=group_name, group_members=group.group_members, members_list=url_list, transaction_list=transaction_list, message=None, friend_requests_list=friend_request_search(username))
