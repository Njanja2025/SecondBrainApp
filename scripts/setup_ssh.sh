#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SSH_KEY_PATH="$HOME/.ssh/baddyagent_rsa"
REMOTE_HOST="baddyagent.example.com"
REMOTE_USER="baddyagent"

echo -e "${YELLOW}Setting up SSH access for BaddyAgent...${NC}"

# Check if SSH key already exists
if [ -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}SSH key already exists at $SSH_KEY_PATH${NC}"
    read -p "Do you want to generate a new key? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm "$SSH_KEY_PATH"
    else
        echo -e "${GREEN}Using existing SSH key${NC}"
    fi
fi

# Generate new SSH key if needed
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}Generating new SSH key...${NC}"
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "baddyagent@$(hostname)"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}SSH key generated successfully${NC}"
    else
        echo -e "${RED}Failed to generate SSH key${NC}"
        exit 1
    fi
fi

# Ensure correct permissions
chmod 600 "$SSH_KEY_PATH"
chmod 644 "$SSH_KEY_PATH.pub"

# Copy public key to remote server
echo -e "${YELLOW}Copying public key to remote server...${NC}"
echo -e "${YELLOW}Please enter the password for $REMOTE_USER@$REMOTE_HOST when prompted${NC}"
ssh-copy-id -i "$SSH_KEY_PATH.pub" "$REMOTE_USER@$REMOTE_HOST"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Public key copied successfully${NC}"
else
    echo -e "${RED}Failed to copy public key${NC}"
    exit 1
fi

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
ssh -i "$SSH_KEY_PATH" -o BatchMode=yes -o ConnectTimeout=5 "$REMOTE_USER@$REMOTE_HOST" echo "SSH connection successful"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}SSH connection test successful${NC}"
else
    echo -e "${RED}SSH connection test failed${NC}"
    exit 1
fi

# Create necessary directories on remote server
echo -e "${YELLOW}Creating necessary directories on remote server...${NC}"
ssh -i "$SSH_KEY_PATH" "$REMOTE_USER@$REMOTE_HOST" "mkdir -p /opt/baddyagent/brain /var/backups/baddyagent /var/log/baddyagent"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Remote directories created successfully${NC}"
else
    echo -e "${RED}Failed to create remote directories${NC}"
    exit 1
fi

echo -e "${GREEN}SSH setup completed successfully${NC}"
echo -e "${YELLOW}Please update the hostname in the configuration files if needed:${NC}"
echo "- scripts/automation_config.json"
echo "- scripts/monitor_config.json" 