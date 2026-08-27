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
        # Create a ticket
        r = requests.post('http://127.0.0.1:5002/api/tickets', 
                         json={'user_id': 'testuser', 'title': 'Test Ticket', 'description': 'Test description'})
        print(f'Create ticket: {r.status_code} {r.json()}')
        assert r.status_code == 201, f'Expected 201, got {r.status_code}'
        ticket_id = r.json().get('id')
        assert ticket_id is not None
        
        # List tickets
        r = requests.get('http://127.0.0.1:5002/api/tickets')
        print(f'List tickets: {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        # Get ticket
        r = requests.get(f'http://127.0.0.1:5002/api/tickets/{ticket_id}')
        print(f'Get ticket: {r.status_code} {r.json()}')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        # Upload receipt - this should trigger the event flow
        r = requests.post(f'http://127.0.0.1:5002/api/tickets/{ticket_id}/receipt',
                         json={'receipt_key': 's3://tickets/receipts/test-123/receipt.pdf'})
        print(f'Upload receipt: {r.status_code} {r.json()}')
        # The receipt upload triggers the event flow which should contact notifications
        # We just verify the ticket status updated
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        
        print('\nAll Tickets service tests passed!')
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