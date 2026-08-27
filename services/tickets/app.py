import os
import uuid
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from botocore.config import Config

app = Flask(__name__)
CORS(app)

# LocalStack configuration
LOCALSTACK_URL = os.getenv('LOCALSTACK_URL', 'http://localhost:4566')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', 'http://localhost:4566')
S3_BUCKET = os.getenv('S3_BUCKET', 'tickets')

# Create S3 client configured for LocalStack
s3 = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id='test',
    aws_secret_access_key='test',
    config=Config(signature_version='s3v4')
)

# Ensure bucket exists
try:
    s3.create_bucket(Bucket=S3_BUCKET)
except Exception:
    pass  # Bucket may already exist

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    description = data.get('description', '')

    if not user_id or not title:
        return jsonify({'error': 'user_id and title required'}), 400

    ticket_id = str(uuid.uuid4())
    ticket = {
        'id': ticket_id,
        'user_id': user_id,
        'title': title,
        'description': description,
        'status': 'pending',
        'receipt_url': None
    }

    # Store ticket metadata (in-memory)
    if not hasattr(app, 'tickets'):
        app.tickets = {}
    app.tickets[ticket_id] = ticket

    # Publish ticket created event to S3 event notification
    try:
        # Store event metadata in S3
        event_key = f"events/ticket.created/{ticket_id}.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=event_key,
            Body=json.dumps({
                'event_type': 'ticket.created',
                'ticket_id': ticket_id,
                'user_id': user_id,
                'title': title
            })
        )
    except Exception as e:
        print(f"Warning: Could not store event: {e}")

    return jsonify(ticket), 201

@app.route('/api/tickets/<ticket_id>/receipt', methods=['POST'])
def upload_receipt(ticket_id):
    ticket = None
    if hasattr(app, 'tickets') and ticket_id in app.tickets:
        ticket = app.tickets[ticket_id]

    if not ticket:
        return jsonify({'error': 'ticket not found'}), 404

    # Generate receipt key
    receipt_key = f"receipts/{ticket_id}/{uuid.uuid4().hex}.pdf"

    # Upload receipt to S3-compatible storage
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=receipt_key,
            Body=f"Receipt for ticket {ticket_id}"
        )
    except Exception as e:
        return jsonify({'error': f'Could not upload receipt: {str(e)}'}), 500

    # Update ticket status
    ticket['receipt_url'] = receipt_key
    ticket['status'] = 'completed'

    # Publish ticket.receipt.uploaded event
    try:
        event_key = f"events/ticket.receipt.uploaded/{ticket_id}.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=event_key,
            Body=json.dumps({
                'event_type': 'ticket.receipt.uploaded',
                'ticket_id': ticket_id,
                'receipt_key': receipt_key,
                'user_id': ticket['user_id']
            })
        )
    except Exception as e:
        print(f"Warning: Could not publish event: {e}")

    return jsonify({
        'message': 'Receipt uploaded successfully',
        'ticket': ticket
    }), 200

@app.route('/api/tickets', methods=['GET'])
def list_tickets():
    if hasattr(app, 'tickets'):
        return jsonify({'tickets': list(app.tickets.values())}), 200
    return jsonify({'tickets': []}), 200

@app.route('/api/tickets/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    if hasattr(app, 'tickets') and ticket_id in app.tickets:
        return jsonify(app.tickets[ticket_id]), 200
    return jsonify({'error': 'ticket not found'}), 404

if __name__ == '__main__':
    port = int(os.getenv('TICKETS_PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)