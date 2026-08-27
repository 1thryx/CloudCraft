#!/usr/bin/env python3
"""Test script for Users service."""
import subprocess
import time
import requests
import signal
import os

def start_server():
    """Start the Flask server and wait for it to be ready."""
    proc = subprocess.Popen(
        ['python', 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    for _ in range(20):
        try:
            requests.get('http://127.0.0.1:5000/', timeout=1)
            return proc
        except requests.ConnectionError:
            time.sleep(0.5)
    
    raise RuntimeError("Server failed to start")

def stop_server(proc):
    """Stop the Flask server."""
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

def run_tests():
    """Run all Users service tests."""
    proc = start_server()
    
    try:
        # Test 1: User registration
        print('Test 1: User registration')
        r = requests.post('http://127.0.0.1:5000/api/users/register', 
                         json={'username': 'testuser', 'password': 'testpass', 'email': 'test@example.com'})
        print(f'  Register: {r.status_code} {r.json()}')
        assert r.status_code == 201, f'Expected 201, got {r.status_code}'
        
        # Test 2: User login
        print('Test 2: User login')
        r = requests.post('http://127.0.0.1:5000/api/users/login', 
                         json={'username': 'testuser', 'password': 'testpass'})
        print(f'  Login: {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        # Test 3: Get current user with token
        print('Test 3: Get current user with token')
        token = r.json().get('access_token')
        r = requests.get('http://127.0.0.1:5000/api/users/me', 
                        headers={'Authorization': f'Bearer {token}'})
        print(f'  Me: {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        assert r.json().get('username') == 'testuser'
        
        # Test 4: List users (requires auth)
        print('Test 4: List users (requires auth)')
        r = requests.get('http://127.0.0.1:5000/api/users', 
                        headers={'Authorization': f'Bearer {token}'})
        print(f'  List users: {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        # Test 5: Change password
        print('Test 5: Change password')
        r = requests.post('http://127.0.0.1:5000/api/users/change-password', 
                         json={'old_password': 'testpass', 'new_password': 'newpass123'},
                         headers={'Authorization': f'Bearer {token}'})
        print(f'  Change password: {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        # Test 6: Login with new password
        print('Test 6: Login with new password')
        r = requests.post('http://127.0.0.1:5000/api/users/login', 
                         json={'username': 'testuser', 'password': 'newpass123'})
        print(f'  Login (new pwd): {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        # Test 7: Me with new token
        print('Test 7: Me with new token')
        token = r.json().get('access_token')
        r = requests.get('http://127.0.0.1:5000/api/users/me', 
                        headers={'Authorization': f'Bearer {token}'})
        print(f'  Me (new): {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        print('\n=== All Users service tests passed! ===')
        
    except AssertionError as e:
        print(f'Test failed: {e}')
        raise
    except Exception as e:
        print(f'Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        raise
    finally:
        stop_server(proc)

if __name__ == '__main__':
    run_tests()