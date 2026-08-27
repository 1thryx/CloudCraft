import subprocess
import time
import requests
import sys

def run_test():
    proc = subprocess.Popen(['python', 'app.py'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
    time.sleep(2)
    
    try:
        # Create an event
        r = requests.post('http://127.0.0.1:5001/api/events', 
                         json={'event_type': 'ticket.receipt.uploaded', 
                               'payload': {'ticket_id': 'test-123'}})
        print(f'Create event: {r.status_code} {r.json()}')
        assert r.status_code == 201, f'Expected 201, got {r.status_code}'
        
        # List events
        r = requests.get('http://127.0.0.1:5001/api/events')
        print(f'List events: {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        # List processed events
        r = requests.get('http://127.0.0.1:5001/api/events/processed')
        print(f'List processed: {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        # Process an event
        r = requests.post('http://127.0.0.1:5001/api/events/1/process')
        print(f'Process event: {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        print('\nAll Events service tests passed!')
    except AssertionError as e:
        print(f'Test failed: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_test()