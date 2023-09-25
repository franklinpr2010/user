from flask import Blueprint, jsonify, request, make_response
from models import db, User
from flask_login import login_user, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import logging

user_blueprint = Blueprint('user_api_routes', __name__,
                           url_prefix='/api/user')

API_CEP = "https://viacep.com.br/ws/";



@user_blueprint.route('/all', methods=['GET'])
def get_all_users():
    all_user = User.query.all()
    result = [user.serialize() for user in all_user]
    response = {
        'message': 'Retornando todos os usuários',
        'result': result
    }
    return jsonify(response)


def get_cep(cep):
    url = API_CEP + cep + '/json/'
    response = requests.get(url)
    print('cep')
    resp = response.json()
    
    if('logradouro' in resp.keys()):
        return response.json()
     
    if ('erro' in resp.keys()): 
      return None
    


@user_blueprint.route('/create', methods=['POST'])
def create_user():
    try:
        user = User()
        user.username = request.form["username"]
        user.password = generate_password_hash(request.form['password'],
                                               method='sha256')
        logging.info('generate_password_hash')
        logging.debug(user.password)
        user.cep = request.form["cep"]
        print(user.cep)
        cep = user.cep.replace("-", "").replace(".", "").replace(" ", "")
        logging.info('cep')
        logging.debug(cep)
        if len(cep) == 8:
            endereco = get_cep(cep);
            if(endereco == None):
                return jsonify({'message': "cep inválido", "status": '400'})
            user.endereco = endereco['logradouro'];
            print(user.endereco)
        else:
            return jsonify({'message': "cep inválido", "status": '400'})
        user.is_admin = False
        db.session.add(user)
        db.session.commit()
        response = {'message': 'Usuário Criado', 'result': user.serialize(), "status": '200'}
        logging.info('usuario criado')
    except Exception as e:
        print(str(e))
        response = { "status": '400', 'message': 'Erro ao criar o usuário!!'}
    return jsonify(response)


@user_blueprint.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if not user:
        response = {'message': 'Usuário não existe!'}
        return make_response(jsonify(response), 401)
    if check_password_hash(user.password, password):
        print('entrou')
        user.update_api_key()
        db.session.commit()
        print('entrou 2')
        login_user(user)
        response = {'message': 'logged in ', 'api_key': user.api_key}
        return make_response(jsonify(response), 200)
    response = {'message': 'Acesso não permitido'}
    return make_response(jsonify(response), 401)


@user_blueprint.route('/logout', methods=['POST'])
def logout():
    if current_user.is_authenticated:
        logout_user()
        return jsonify({'message': 'Logged out'})
    return jsonify({'message': 'Nenhum usuário logado!!'}), 401


@user_blueprint.route('/<username>/exists', methods=['GET'])
def user_exists(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"result": True}), 200
    return jsonify({"result": False}), 404


@user_blueprint.route('/', methods=['GET'])
def get_current_user():
    print(current_user.is_authenticated)
    print(current_user.serialize())
    if current_user.is_authenticated:
        return jsonify({'result': current_user.serialize(), 'status': '200'})
    else:
        return jsonify({'message': "Usuário não logado", 'status': '401'})
