#!/bin/bash

# Function to log messages with timestamps
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Kill any process running on port 10000
kill_existing_process() {
    log_message "Checking for processes on port 10000..."
    if lsof -i :10000 > /dev/null; then
        log_message "Found process on port 10000. Stopping it..."
        lsof -i :10000 | grep LISTEN | awk '{print $2}' | xargs kill -9
        sleep 1  # Give the process time to fully stop
    else
        log_message "No process found on port 10000"
    fi
}

# Change to the correct directory
change_directory() {
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"
    log_message "Changed to directory: $(pwd)"
}

# Start the application based on environment
start_application() {
    local env=${1:-development}
    
    if [ "$env" = "production" ]; then
        log_message "Starting application in production mode..."
        FLASK_ENV=production gunicorn --bind 0.0.0.0:10000 app:app --workers=4
    else
        log_message "Starting application in development mode..."
        # Use SSL in development mode with adhoc certificates
        FLASK_ENV=development flask run --port=10000 --cert=adhoc
    fi
}

# Main execution
main() {
    local env=${1:-development}
    
    log_message "Starting application management script..."
    kill_existing_process
    change_directory
    start_application "$env"
}

# Execute main function with environment argument
main "$1" 