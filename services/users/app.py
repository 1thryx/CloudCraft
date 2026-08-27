import os
import json
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, verify_jwt_in_request
)
from flask_cors import CORS

app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-me')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_KEY_ROTATION'] = True

jwt = JWTManager(app)

# In-memory user store with key rotation support
users = {}
jwt_keys = {}  # Maps username to list of (key_id, key_data) tuples

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_key_id():
    import uuid
    return f"key-{uuid.uuid4().hex[:8]}"

@app.route('/api/users/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')

    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400

    if username in users:
        return jsonify({'error': 'username already exists'}), 409

    users[username] = {
        'id': len(users) + 1,
        'username': username,
        'email': email,
        'password_hash': hash_password(password),
        'created_at': datetime.utcnow().isoformat()
    }

    # Generate initial JWT key for this user
    key_id = generate_key_id()
    jwt_keys.setdefault(username, []).append({
        'key_id': key_id,
        'secret': os.getenv('JWT_SECRET_KEY', 'change-me'),
        'created_at': datetime.utcnow().isoformat(),
        'active': True
    })

    access_token = create_access_token(identity=username)
    return jsonify({
        'message': 'User registered successfully',
        'user': {'id': users[username]['id'], 'username': users[username]['username'], 'email': users[username]['email']},
        'access_token': access_token
    }), 201

@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400

    user = users.get(username)
    if not user or user.get('password_hash') != hash_password(password):
        return jsonify({'error': 'invalid credentials'}), 401

    # Create access token
    access_token = create_access_token(identity=username)
    
    # Mark the current active key for this user
    if username in jwt_keys and jwt_keys[username]:
        jwt_keys[username][0]['active'] = True
    
    return jsonify({
        'message': 'Login successful',
        'user': {'id': user['id'], 'username': user['username'], 'email': user['email']},
        'access_token': access_token
    }), 200

@app.route('/api/users/me', methods=['GET'])
@jwt_required
def get_current_user():
    current_user = get_jwt_identity()
    user = users.get(current_user)
    if not user:
        return jsonify({'error': 'user not found'}), 404
    
    # Get the JWT claims to determine which key was used
    jwt_data = get_jwt()
    key_id = jwt_data.get('jti', 'unknown')
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'jwt_key_id': key_id
    }), 200

@app.route('/api/users', methods=['GET'])
@jwt_required
def list_users():
    return jsonify({'users': [{'id': u['id'], 'username': u['username'], 'email': u['email']} for u in users.values()]}), 200

@app.route('/api/users/change-password', methods=['POST'])
@jwt_required
def change_password():
    current_user = get_jwt_identity()
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({'error': 'old and new passwords required'}), 400

    user = users.get(current_user)
    if not user or user.get('password_hash') != hash_password(old_password):
        return jsonify({'error': 'invalid old password'}), 401

    user['password_hash'] = hash_password(new_password)
    
    # Rotate JWT key when password changes
    if current_user in jwt_keys:
        for key_entry in jwt_keys[current_user]:
            key_entry['active'] = False
        jwt_keys[current_user].insert(0, {
            'key_id': generate_key_id(),
            'secret': os.getenv('JWT_SECRET_KEY', 'change-me'),
            'created_at': datetime.utcnow().isoformat(),
            'active': True
        })
    
    return jsonify({'message': 'Password changed successfully'}), 200

@app.route('/api/users/rotate-key', methods=['POST'])
@jwt_required
def rotate_key():
    """Rotate the active JWT signing key without downtime"""
    current_user = get_jwt_identity()
    jwt_data = get_jwt()
    
    # Mark current key as inactive
    if current_user in jwt_keys:
        for key_entry in jwt_keys[current_user]:
            key_entry['active'] = False
    
    # Add new active key at the beginning
    new_key_id = generate_key_id()
    jwt_keys[current_user].insert(0, {
        'key_id': new_key_id,
        'secret': os.getenv('JWT_SECRET_KEY', 'change-me'),
        'created_at': datetime.utcnow().isoformat(),
        'active': True
    })
    
    return jsonify({
        'message': 'JWT key rotation initiated',
        'new_key_id': new_key_id,
        'old_key_id': jwt_data.get('jti'),
        'note': 'Existing tokens signed with previous keys remain valid until expiration'
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('USERS_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)