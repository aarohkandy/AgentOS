#!/bin/bash
# Quick script to push ANOS to GitHub

echo "🚀 ANOS GitHub Setup"
echo "===================="
echo ""

# Check if remote exists
if git remote | grep -q origin; then
    echo "Remote 'origin' already exists:"
    git remote -v
    echo ""
    read -p "Push to existing remote? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push -u origin main
        exit 0
    fi
fi

echo "To push to GitHub:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   https://github.com/new"
echo "   Name: anos (or your choice)"
echo "   Don't initialize with README"
echo ""
echo "2. Run one of these commands:"
echo ""
echo "   For HTTPS (uses Personal Access Token):"
echo "   git remote add origin https://github.com/YOUR_USERNAME/anos.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "   For SSH (if you have SSH keys set up):"
echo "   git remote add origin git@github.com:YOUR_USERNAME/anos.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Replace YOUR_USERNAME with your GitHub username"
echo ""

