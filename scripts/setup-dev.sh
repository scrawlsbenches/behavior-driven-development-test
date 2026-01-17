#!/bin/bash
# Development environment setup
# Run this once after cloning: ./scripts/setup-dev.sh

set -e

echo "Setting up development environment..."

# Configure git to use repo hooks
echo "Configuring git hooks..."
git config core.hooksPath scripts/hooks

# Install package in development mode with test dependencies
echo "Installing package..."
pip install -e ".[dev]"

echo ""
echo "Setup complete!"
echo ""
echo "Git hooks are now active. The following checks run on commit:"
echo "  - Architecture enforcement (scripts/check_architecture.py)"
echo ""
echo "To run checks manually:"
echo "  python scripts/check_architecture.py"
echo "  behave --tags=@mvp-p0"
