# custom_decorators.py

from functools import wraps
from flask import request, jsonify, redirect, url_for
from flask_login import current_user

def login_required_ajax(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response = jsonify({
                    'status': 'fail',
                    'message': 'Authentication required.'
                })
                return response, 401
            else:
                return redirect(url_for('auth.login'))  # or wherever your login route is named
        return f(*args, **kwargs)
    return decorated_function
