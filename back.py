from os import path
from flask import Blueprint, render_template, redirect, url_for, request, session, current_app
from werkzeug.security import check_password_hash, generate_password_hash

import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3

from sqlalchemy import or_
from db import db
from db.models import Users
from flask_login import login_required, login_user, current_user, logout_user

import json

back = Blueprint('back', __name__ ) 

PHOTO_CATALOG = 'static/ph'

# Фунция возвращает список обьектов Users и номера страниц вперед-назад
# params - словарь с параметрами поиска
def getUserList(params):
    # анализируем параметры запроса
    namelike = "%" + params['name'] + "%" if 'name' in params else '%'
    age = int(params['age']) if 'age' in params else 1
    age2 = int(params['age2']) if 'age2' in params else 100
    page = params['page'] if 'page' in params else 1
    
    # выбираем обьекты
    q = Users.query

    # в параметрах есть name и age, добавим их
    q = q.filter(Users.name.like(namelike)).filter(Users.age >= age).filter(Users.age <= age2)

    # если в параметрах есть gender и search, добавим их
    if 'gender' in params and 'search' in params:
        gender = params['gender']
        search = params['search']  
        q = q.filter(Users.gender == search).filter(Users.search == gender)
    
    # спрятать пользователей чьи анкеты hidden
    q = q.filter(or_(Users.hidden ==0, Users.hidden == None))

    # выполнием запрос
    users = q.order_by(Users.id).limit(4).offset( (page-1) * 3).all()

    # добавляем фотографии
    users = addPhotos(users)

    # превращаем список обьектов Users в список словарей
    users_list = [ {'name': user.name, 'age': user.age, 'aboutme': user.aboutme, 'photo': user.photo, 'login': user.login, 'id': user.id} for user in users ]

    back = page - 1
    forward = forward = page + 1 if len(users) > 3 else 0

    # возвращаем список обьектов Users и номера страниц вперед-назад, 0 - страница отсутствует
    return users_list[:3], back, forward

def profileUpdate(formvalues):
    attrs = ['name', 'age', 'gender', 'search', 'aboutme', 'hidden'] # только эти поля будут обновлены
    id = current_user.id
 
    # если есть id, то обновляем обьект с таким id
    if 'id' in formvalues:
        id = int(formvalues['id'])
        attrs.append('login')  # в список полей для обновления добавляем поле login

    # собираем словарь из значений полей, полученных из формы
    # значения полей могут отсутствовать, тогда игнорируем
    # также убираем пробелы в начале и конце
    user = {}
    for a in attrs:
        if a in formvalues:
            user[a] = formvalues[a].strip()

    # проверяем корректность полей
    errors = {}
    if user['name'] == '':
        errors['name'] = 'Вы забыли имя'
    if user['age'] == '':
        errors['age'] = 'не указан возраст'
    user['age'] = int(user['age'])
    if user['age'] < 18 or user['age'] > 70:
        errors['age'] = 'возраст должен быть в диапазоне от 18 до 70'
    # if user['aboutme'] == '':
    #     errors['aboutme'] = 'не указано о себе'

    # если нет ошибок, то обновляем данные
    if (not errors):
        Users.query.filter_by(id=id).update(user, synchronize_session='fetch')
        login_user(Users.query.get(id), remember=False)       
        db.session.commit()
    
    # возвращаем количество ошибок и список ошибок     
    return len(errors), errors  

def deleteUser(id):
    Users.query.filter_by(id=id).delete()
    db.session.commit()

def hideUser(id):
    Users.query.filter_by(id=id).update({'hidden': True}, synchronize_session='fetch')
    db.session.commit()



# получаем путь к фотографии
def pathPhotoToSave(user):
    dir_path = path.join(path.dirname(path.realpath(__file__)), PHOTO_CATALOG )
    full_path_photo = path.join(dir_path, user.login + '_1.jpeg')
    return full_path_photo

def savePhoto(isthisFile):
    isthisFile.save( pathPhotoToSave( current_user ) )

# проверяем существует ли фотография пользователя
def checkUserPhoto(user):
    photo = user.login + '_1.jpeg'
    if path.isfile( pathPhotoToSave(user) ):
        return photo
    else:
        return {0: 'default-m.jpeg', 1: 'default-f.jpeg'  }[user.gender]

# добавляем фотографии в список пользователей
def addPhotos(users):
    for user in users:
        user.photo = checkUserPhoto(user)
    return users

# получаем название пола по его числовому значению
def getGenderName(gender):
    return {0: 'Парень', 1: 'Девушка'}[gender]

def getGenderSearchName(gender):
    return {0: 'Парней', 1: 'Девушек'}[gender]

################### Routes ##################3

@back.route('/') 
def index(): 
    return render_template('index.html') 

@back.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/search')
    
    if request.method == 'GET':
        return render_template('login.html')
    
    login = request.form.get('login')
    password = request.form.get('password')

    user = Users.query.filter_by(login=login).first()
    if user:
        if user.check_password(password):
            login_user(user, remember=False)

            if user.isFillProfile():
                return redirect('/search')
            else:
                return redirect('/profile')
        
    return render_template('login.html', error = 'Извините, но ваш логин и/или пароль неверны.')

@back.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')

@back.route("/reg", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return redirect('/login')
    
    login = request.form.get('login')
    password = request.form.get('password')

    login_exists = Users.query.filter_by(login=login).first()
    if login_exists:
        return render_template('register.html', error_reg = 'Такой пользователь уже существует!')
    if login == '':
        return render_template('register.html', error_reg = 'Имя пользователя не должно быть пустым')
    if password == '':
        return render_template('register.html', error_reg = 'Пароль не должен быть пустым')

    user = Users(login=login, password=password)   
    db.session.add(user)    
    db.session.commit()
    login_user(user, remember=False)

    return redirect('/profile')

@back.route("/delete", methods=['GET'])
@login_required
def delete():
    deleteUser(current_user.id)
    logout_user()
    return redirect('/login')
  

@back.route("/profile", methods = ['GET'])
@login_required
def profile():
    user = Users.query.get(current_user.id)
    user.photo = checkUserPhoto(user)
    return render_template('profile.html', user=user)

@back.route('/photo', methods=['POST'])
@login_required
def uploadPhoto():
    #data=json.loads(request.form.get('data'))
    isthisFile = request.files.get('file')
    if not isthisFile:
        return {
            'jsonrpc': '2.0', 
            'error': {
                'code': 10122,
                'message': 'No file in upload request'
            },
          #  'id': request.json['id']
        }
    savePhoto(isthisFile)
    return {
        'jsonrpc': '2.0', 
        'result': True,
    }



@back.route('/search', methods=['GET'])
@login_required
def search_view():
    return render_template('search.html', user = current_user,
                getGenderName=getGenderName,
                getGenderSearchName=getGenderSearchName)

@back.route('/api/', methods=['POST'])
def api():
    data = request.json
    id = data['id']
    
    if not current_user.is_authenticated:
        return {
            'jsonrpc': '2.0', 
            'error': {
                'code': 1,
                'message': 'Unauthorized'
            },
            'id': id
        }
    
    if data['method'] == 'list':
        users, back, forward = getUserList( data['params'] )
        return {
            'jsonrpc': '2.0', 
            'result': users,
            'back': back,
            'forward': forward,
            'id': id
        }

    if data['method'] == 'profile_update':
        result, errors = profileUpdate( data['params'] )
        #print(result, errors)
        return {
            'jsonrpc': '2.0', 
            'result': result,
            'errors': errors,
            'id': id
        }


    return {
        'jsonrpc': '2.0', 
        'error': {
            'code': -32601,
            'message': 'Method not found'
        },
        'id': id
    }


@back.route('/1', methods=['GET'])
def test1():
    return render_template('1.html')

@back.route('/admin') 
@login_required
def admin(): 
    return render_template('admin.html') 

@back.route("/admin/<int:id>", methods = ['GET'])
@login_required
def admin_profile(id):
    user = Users.query.get(id)
    user.photo = checkUserPhoto(user)
    return render_template('profile.html', user=user, admin = True)