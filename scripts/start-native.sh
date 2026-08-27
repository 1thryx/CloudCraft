#!/bin/bash
# Local development startup script for CloudCrafter
# Starts all four microservices natively (no Docker required)

set -e

echo "Starting CloudCrafter services natively..."

# Start Users service
echo "Starting Users service on port 5000..."
cd services/users
python app.py &
USERS_PID=$!

# Start Events service
echo "Starting Events service on port 5001..."
cd ../events
python app.py &
EVENTS_PID=$!

# Start Tickets service
echo "Starting Tickets service on port 5002..."
cd ../tickets
python app.py &
TICKETS_PID=$!

# Start Notifications service
echo "Starting Notifications service on port 5003..."
cd ../notifications
python app.py &
NOTIFICATIONS_PID=$!

echo ""
echo "All services started:"
echo "  Users:      http://localhost:5000"
echo "  Events:     http://localhost:5001"
echo "  Tickets:    http://localhost:5002"
echo "  Notifications: http://localhost:5003"
echo ""
echo "PIDs - Users: $USERS_PID, Events: $EVENTS_PID, Tickets: $TICKETS_PID, Notifications: $NOTIFICATIONS_PID"
echo ""

# Wait for interrupt
trap "echo 'Stopping services...'; kill $USERS_PID $EVENTS_PID $TICKETS_PID $NOTIFICATIONS_PID 2>/dev/null; exit 0" INT TERM

wait