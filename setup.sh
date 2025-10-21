#!/bin/bash

# ===========================================
# IKB Navigator - Automated Setup Script
# ===========================================
# This script automates the setup process for IKB Navigator

set -e  # Exit on any error

echo "🧠 IKB Navigator - Automated Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+ and try again."
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ and try again."
        exit 1
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install Git and try again."
        exit 1
    fi
    
    print_success "All prerequisites are installed!"
}

# Setup backend
setup_backend() {
    print_status "Setting up backend (FastAPI)..."
    
    cd apps/api
    
    # Create virtual environment
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Backend setup complete!"
    cd ../..
}

# Setup frontend
setup_frontend() {
    print_status "Setting up frontend (Next.js)..."
    
    cd apps/web
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    print_success "Frontend setup complete!"
    cd ../..
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f "apps/.env" ]; then
        if [ -f "apps/.env.example" ]; then
            cp apps/.env.example apps/.env
            print_success "Created .env file from example"
            print_warning "Please edit apps/.env with your actual API keys and credentials"
        else
            print_error ".env.example file not found. Please create apps/.env manually"
        fi
    else
        print_warning ".env file already exists. Skipping creation."
    fi
}

# Main setup function
main() {
    echo ""
    print_status "Starting IKB Navigator setup..."
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Setup backend
    setup_backend
    
    # Setup frontend
    setup_frontend
    
    # Setup environment
    setup_environment
    
    echo ""
    print_success "🎉 Setup complete!"
    echo ""
    print_status "Next steps:"
    echo "1. Edit apps/.env with your API keys and credentials"
    echo "2. Set up your Supabase database (run migrations)"
    echo "3. Configure Google Drive API access"
    echo "4. Start the backend: cd apps/api && source venv/bin/activate && python -m api.main"
    echo "5. Start the frontend: cd apps/web && npm run dev"
    echo ""
    print_status "For detailed instructions, see README.md"
    echo ""
}

# Run main function
main "$@"
