import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory notification store
notifications = []

@app.route('/api/notifications', methods=['POST'])
def create_notification():
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    message = data.get('message')
    channel = data.get('channel', 'email')
    
    if not ticket_id or not user_id or not message:
        return jsonify({'error': 'ticket_id, user_id, and message required'}), 400
    
    notification = {
        'id': len(notifications) + 1,
        'ticket_id': ticket_id,
        'user_id': user_id,
        'message': message,
        'channel': channel,
        'status': 'sent'
    }
    notifications.append(notification)
    return jsonify(notification), 201

@app.route('/api/notifications/ticket-receipt', methods=['POST'])
def ticket_receipt_notification():
    """Special endpoint for ticket receipt-triggered notifications"""
    data = request.get_json()
    ticket_id = data.get('payload', {}).get('ticket_id')
    user_id = data.get('payload', {}).get('user_id')
    
    if not ticket_id or not user_id:
        return jsonify({'error': 'ticket_id and user_id required'}), 400
    
    message = f"Your ticket {ticket_id} receipt has been processed and is ready."
    
    notification = {
        'id': len(notifications) + 1,
        'ticket_id': ticket_id,
        'user_id': user_id,
        'message': message,
        'channel': 'email',
        'status': 'sent'
    }
    notifications.append(notification)
    return jsonify(notification), 201

@app.route('/api/notifications', methods=['GET'])
def list_notifications():
    return jsonify({'notifications': notifications}), 200

if __name__ == '__main__':
    port = int(os.getenv('NOTIFICATIONS_PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=False)