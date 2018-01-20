from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from oauth import AuthClient, AuthException

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'github': {
        'key': 'ed3d864fa006f2ab5071',
        'secret': '14890487d51df43013cb5b559a243fd496742c72'
    },
    'facebook': {
        'key': '1182730845163848',
        'secret': '3a7ac784a303a2a3234c7d3bc491a757'
    },
    #'twitter': {
    #    'key': '3RzWQclolxWZIMq5LJqzRZPTl',
    #    'secret': 'm9TEd58DSEtRrZHpz2EjrV9AhsBRxKMo8m3kuIZj3zLwzwIimt'
    #}
}

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    email = db.Column(db.String(64), nullable=False)


@app.route('/oauth/<provider>/redirect')
def oauth_authorize(provider):
    oauth = AuthClient.get_provider(provider)
    if oauth is None:
        return jsonify({'error': 'Provider {} does not exists'.format(provider)})

    return oauth.authorization_url()


# TODO: move to frontend
@app.route('/oauth/<provider>/callback')
def oauth_callback(provider):
    return 'OK'

@app.route('/oauth/<provider>/token')
def oauth_token(provider):
    oauth = AuthClient.get_provider(provider)
    if oauth is None:
        return jsonify({'error': 'Provider {} does not exists'.format(provider)})

    try:
        social_id, email = oauth.fetch(request.args)
    except AuthException as e:
        # TODO: make_error
        return jsonify({'error': str(e)})

    if social_id is None:
        # TODO: make_error
        return jsonify({'error': 'Not autorized'})
    if email is None:
        # TODO: make_error
        return jsonify({'error': 'Email not provided'})

    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, email=email)
        db.session.add(user)
        db.session.commit()

    return jsonify(dict(email=email, social_id=social_id)) # TODO: token
    

if __name__ == '__main__':
    db.create_all()
    app.run(host='dbadmins.ru', debug=True)
