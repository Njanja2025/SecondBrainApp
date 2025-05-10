#!/bin/bash

# AWS Deployment Script for SecondBrain

echo "Starting SecondBrain AWS Deployment..."

# Check for AWS CLI
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Installing..."
    pip install awscli
fi

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

# Validate required environment variables
required_vars=("AWS_REGION" "AWS_EC2_INSTANCE_ID" "AWS_ACCESS_KEY" "AWS_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set in .env file"
        exit 1
    fi
done

# Configure AWS CLI
aws configure set aws_access_key_id $AWS_ACCESS_KEY
aws configure set aws_secret_access_key $AWS_SECRET_KEY
aws configure set default.region $AWS_REGION

echo "Configuring EC2 instance..."

# Update system packages
ssh -i ~/.ssh/aws-key.pem ubuntu@$EC2_PUBLIC_IP "sudo apt-get update && sudo apt-get upgrade -y"

# Install required packages
ssh -i ~/.ssh/aws-key.pem ubuntu@$EC2_PUBLIC_IP "sudo apt-get install -y python3-pip nginx certbot python3-certbot-nginx"

# Copy application files
echo "Copying application files..."
scp -i ~/.ssh/aws-key.pem -r ./* ubuntu@$EC2_PUBLIC_IP:/home/ubuntu/secondbrain/

# Setup Python environment
ssh -i ~/.ssh/aws-key.pem ubuntu@$EC2_PUBLIC_IP << 'EOF'
cd /home/ubuntu/secondbrain
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup Nginx
sudo cp nginx/secondbrain.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/secondbrain.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# Setup SSL
sudo certbot --nginx -d samantha.njanja.net --non-interactive --agree-tos -m admin@njanja.net

# Setup systemd service
sudo cp systemd/secondbrain.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable secondbrain
sudo systemctl start secondbrain
EOF

echo "Deployment completed successfully!"
echo "Access the application at: https://samantha.njanja.net" 