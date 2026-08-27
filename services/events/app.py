import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
app.config['ENV'] = os.getenv('ENV', 'development')

# In-memory event store
events = []

@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.get_json()
    event_type = data.get('event_type')
    payload = data.get('payload', {})
    
    if not event_type:
        return jsonify({'error': 'event_type required'}), 400
    
    event = {
        'id': len(events) + 1,
        'event_type': event_type,
        'payload': payload,
        'processed': False
    }
    events.append(event)
    return jsonify(event), 201

@app.route('/api/events', methods=['GET'])
def list_events():
    return jsonify({'events': events}), 200

@app.route('/api/events/processed', methods=['GET'])
def list_processed_events():
    processed = [e for e in events if e.get('processed')]
    return jsonify({'events': processed}), 200

@app.route('/api/events/<int:event_id>/process', methods=['POST'])
def process_event(event_id):
    event = next((e for e in events if e['id'] == event_id), None)
    if not event:
        return jsonify({'error': 'event not found'}), 404
    
    event['processed'] = True
    return jsonify({'message': 'event processed', 'event': event}), 200

if __name__ == '__main__':
    port = int(os.getenv('EVENTS_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)