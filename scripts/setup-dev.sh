#!/bin/bash
# Development environment setup
# Run this once after cloning: ./scripts/setup-dev.sh

set -e

echo "Setting up development environment..."

# Install package in development mode with test dependencies
echo "Installing package..."
pip install -e ".[dev]"

echo ""
echo "Setup complete!"
echo ""
echo "To run checks manually:"
echo "  python scripts/check_architecture.py"
echo "  behave --tags=@mvp-p0"
