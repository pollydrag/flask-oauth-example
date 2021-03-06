import json

from authlib.client import OAuthClient
from authlib.client.errors import OAuthException
from flask import current_app, url_for, jsonify


class AuthException(Exception):
    pass


class AuthClient(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.client_key = credentials['key']
        self.client_secret = credentials['secret']

    def authorization_url(self):
        pass

    def fetch(self, args):
        pass

    def _callback_url(self):
        # TODO:
        return url_for(
            'oauth_callback', 
            provider=self.provider_name,
            _external=True
        )

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers.get(provider_name)


class GitHub(AuthClient):
    def __init__(self):
        super(GitHub, self).__init__('github')
        self.client = OAuthClient(
            client_key=self.client_key,
            client_secret=self.client_secret,
            api_base_url='https://api.github.com',
            access_token_url='https://github.com/login/oauth/access_token',
            authorize_url='https://github.com/login/oauth/authorize',
            client_kwargs={'scope': 'user:email'},
        )

    def authorization_url(self):
        url, state = self.client.generate_authorize_redirect(
            callback_uri=self._callback_url()
        )
        return jsonify({'url': url})
        
    def fetch(self, args):
        if 'code' not in args:
            return None, None

        self.client.fetch_access_token(code=args['code'])

        user = self.client.get('user').json()
        return 'github${}'.format(user['id']), user.get('email')
        

class Facebook(AuthClient):
    def __init__(self):
        super(Facebook, self).__init__('facebook')
        self.client = OAuthClient(
            client_key=self.client_key,
            client_secret=self.client_secret,
            api_base_url='https://graph.facebook.com/v2.11',
            access_token_url='https://graph.facebook.com/v2.11/oauth/access_token',
            access_token_params={'method': 'GET'},
            authorize_url='https://www.facebook.com/v2.11/dialog/oauth',
            client_kwargs={'scope': 'email'},
        )

    def authorization_url(self):
        url, state = self.client.generate_authorize_redirect(
            callback_uri=self._callback_url()
        )
        return jsonify({'url': url})
        
    def fetch(self, args):
        if 'code' not in args:
            return None, None

        try:
            self.client.fetch_access_token(
                code=args['code'],
                callback_uri=self._callback_url()
            )

            user = self.client.get('me?fields=id,email').json()
        except OAuthException as e:
            raise AuthException(e.message.get('message'))

        return 'facbook${}'.format(user['id']), user.get('email')


#class TwitterSignIn(OAuthSignIn):
#    def __init__(self):
#        super(TwitterSignIn, self).__init__('twitter')
#        self.service = OAuth1Service(
#            name='twitter',
#            consumer_key=self.consumer_id,
#            consumer_secret=self.consumer_secret,
#            request_token_url='https://api.twitter.com/oauth/request_token',
#            authorize_url='https://api.twitter.com/oauth/authorize',
#            access_token_url='https://api.twitter.com/oauth/access_token',
#            base_url='https://api.twitter.com/1.1/'
#        )
#
#    def authorize(self):
#        request_token = self.service.get_request_token(
#            params={'oauth_callback': self.get_callback_url()}
#        )
#        session['request_token'] = request_token
#        return redirect(self.service.get_authorize_url(request_token[0]))
#
#    def callback(self):
#        request_token = session.pop('request_token')
#        if 'oauth_verifier' not in request.args:
#            return None, None, None
#        oauth_session = self.service.get_auth_session(
#            request_token[0],
#            request_token[1],
#            data={'oauth_verifier': request.args['oauth_verifier']}
#        )
#        me = oauth_session.get('account/verify_credentials.json').json()
#        social_id = 'twitter$' + str(me.get('id'))
#        username = me.get('screen_name')
#        return social_id, username, None   # Twitter does not provide email
