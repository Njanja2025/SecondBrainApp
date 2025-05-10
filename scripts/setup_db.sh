#!/bin/bash

# Exit on error
set -e

# Configuration
VENV_DIR=".venv"
DB_DIR="data"
MIGRATIONS_DIR="migrations"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check virtual environment
check_venv() {
    log "Checking virtual environment..."
    if [ ! -d "$VENV_DIR" ]; then
        error "Virtual environment not found. Please run run_dev.sh first"
    fi
    
    source "$VENV_DIR/bin/activate"
}

# Create database directory
create_db_dir() {
    log "Creating database directory..."
    mkdir -p "$DB_DIR"
    chmod 755 "$DB_DIR"
}

# Initialize database
init_db() {
    log "Initializing database..."
    
    # Check if alembic is installed
    if ! pip show alembic &> /dev/null; then
        error "Alembic not found. Please install development requirements"
    fi
    
    # Initialize alembic if not already initialized
    if [ ! -d "$MIGRATIONS_DIR" ]; then
        log "Initializing Alembic..."
        alembic init "$MIGRATIONS_DIR"
        
        # Update alembic.ini with correct database URL
        sed -i '' "s|sqlalchemy.url = driver://user:pass@localhost/dbname|sqlalchemy.url = sqlite:///data/secondbrain.db|" alembic.ini
    fi
}

# Run migrations
run_migrations() {
    log "Running database migrations..."
    
    # Create initial migration if none exists
    if [ ! -d "$MIGRATIONS_DIR/versions" ]; then
        log "Creating initial migration..."
        alembic revision --autogenerate -m "Initial migration"
    fi
    
    # Run migrations
    alembic upgrade head
}

# Verify database
verify_db() {
    log "Verifying database..."
    
    # Check if database file exists
    if [ ! -f "$DB_DIR/secondbrain.db" ]; then
        error "Database file not found"
    fi
    
    # Check database connection
    python3 -c "
import sqlite3
conn = sqlite3.connect('data/secondbrain.db')
cursor = conn.cursor()
cursor.execute('SELECT 1')
conn.close()
"
    
    log "Database verification successful"
}

# Main execution
main() {
    log "Starting database setup..."
    
    # Run setup steps
    check_venv
    create_db_dir
    init_db
    run_migrations
    verify_db
    
    log "Database setup complete!"
}

# Run main function
main 