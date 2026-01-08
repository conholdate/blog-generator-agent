#!/bin/bash

# Content Gap Analyzer - Easy Run Script
# This script simplifies running the analyzer with various options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
OUTPUT_DIR="./output"
CACHE_DIR="./repo_cache"

# Function to print colored messages
print_error() {
    echo -e "${RED}Error: $1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_info() {
    echo -e "$1"
}

# Function to check if API key is set
check_api_key() {
    if [ -z "$PROFESSIONALIZE_API_KEY" ]; then
        print_error "PROFESSIONALIZE_API_KEY environment variable is not set"
        echo ""
        echo "Please set your OpenAI API key:"
        echo "  export PROFESSIONALIZE_API_KEY='your-api-key-here'"
        echo ""
        echo "Or create a .env file with:"
        echo "  PROFESSIONALIZE_API_KEY=your-api-key-here"
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    if ! python3 -c "import openai, git, yaml" 2>/dev/null; then
        print_warning "Some dependencies are missing"
        echo ""
        read -p "Install dependencies now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pip install -r requirements.txt
            print_success "Dependencies installed"
        else
            print_error "Please install dependencies: pip install -r requirements.txt"
            exit 1
        fi
    fi
}

# Function to display help
show_help() {
    cat << EOF
Content Gap Analyzer - Run Script

Usage: ./scripts/run_analyzer.sh [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -t, --test              Run setup verification tests only
    -o, --output DIR        Set output directory (default: ./output)
    -c, --cache DIR         Set cache directory (default: ./repo_cache)
    -f, --force             Force fresh clone (clear cache)
    -v, --verbose           Verbose output

EXAMPLES:
    ./scripts/run_analyzer.sh                    # Run with defaults
    ./scripts/run_analyzer.sh --test             # Test setup
    ./scripts/run_analyzer.sh -o ./reports       # Custom output directory
    ./scripts/run_analyzer.sh --force            # Clear cache and run fresh

ENVIRONMENT:
    PROFESSIONALIZE_API_KEY         OpenAI API key (required)

EOF
}

# Parse command line arguments
FORCE_FRESH=false
RUN_TEST=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--test)
            RUN_TEST=true
            shift
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -c|--cache)
            CACHE_DIR="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_FRESH=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Load .env file if it exists
if [ -f .env ]; then
    print_info "Loading environment from .env file"
    export $(grep -v '^#' .env | xargs)
fi

# Run tests if requested
if [ "$RUN_TEST" = true ]; then
    print_info "Running setup verification tests..."
    python3 -m pytest tests/test_setup.py -v
    exit $?
fi

# Check API key and dependencies
check_api_key
check_dependencies

# Clear cache if force fresh
if [ "$FORCE_FRESH" = true ]; then
    print_info "Clearing repository cache..."
    rm -rf "$CACHE_DIR"
    print_success "Cache cleared"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Print run information
echo ""
echo "=========================================="
echo "Content Gap Analyzer"
echo "=========================================="
echo "Output directory: $OUTPUT_DIR"
echo "Cache directory:  $CACHE_DIR"
echo "API Key:          ${PROFESSIONALIZE_API_KEY:0:7}..."
echo "=========================================="
echo ""

# Run the analyzer
print_info "Starting analysis..."
echo ""

if [ "$VERBOSE" = true ]; then
    python3 -m content_gap_agent \
        --output-dir "$OUTPUT_DIR" \
        --cache-dir "$CACHE_DIR"
else
    python3 -m content_gap_agent \
        --output-dir "$OUTPUT_DIR" \
        --cache-dir "$CACHE_DIR" 2>&1 | grep -v "^  "
fi

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    print_success "Analysis completed successfully!"
    echo ""
    print_info "Reports saved to: $OUTPUT_DIR"
    echo ""
    echo "View reports:"
    echo "  ls -lh $OUTPUT_DIR"
    echo ""
    echo "Latest report:"
    LATEST_MD=$(ls -t "$OUTPUT_DIR"/*.md 2>/dev/null | head -1)
    if [ -n "$LATEST_MD" ]; then
        echo "  cat '$LATEST_MD'"
    fi
else
    print_error "Analysis failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi
