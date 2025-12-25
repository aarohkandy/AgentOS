#!/bin/bash
# Apply ANOS branding to system

# OS identification
if [ -f /root/os-release ]; then
    cp /root/os-release /etc/os-release
fi

if [ -f /root/issue ]; then
    cp /root/issue /etc/issue
    cp /root/issue /etc/issue.net
fi

# Set default hostname
echo "anos" > /etc/hostname
echo "127.0.0.1 localhost" > /etc/hosts
echo "127.0.1.1 anos.localdomain anos" >> /etc/hosts

# Create ANOS assets directory
mkdir -p /usr/share/anos
if [ -d /root/assets ]; then
    cp -r /root/assets/* /usr/share/anos/ 2>/dev/null || true
fi

echo "ANOS branding applied"




