#!/bin/bash

# Monitoring script for SecondBrain

echo "Running SecondBrain System Health Check..."

# Check service status
systemctl status secondbrain | grep "Active:"

# Check memory usage
echo -e "\nMemory Usage:"
free -h

# Check disk space
echo -e "\nDisk Usage:"
df -h /

# Check CPU load
echo -e "\nCPU Load:"
uptime

# Check Nginx status
echo -e "\nNginx Status:"
systemctl status nginx | grep "Active:"

# Check SSL certificate
echo -e "\nSSL Certificate Status:"
certbot certificates | grep "samantha.njanja.net"

# Check application logs
echo -e "\nRecent Application Logs:"
tail -n 10 /var/log/secondbrain/app.log

# Check backup status
echo -e "\nBackup Status:"
ls -lh /home/ubuntu/secondbrain/backups/

# Send status email
if [ -f /home/ubuntu/secondbrain/venv/bin/python ]; then
    /home/ubuntu/secondbrain/venv/bin/python << 'EOF'
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os

sender = "admin@njanja.net"
receiver = "lloydkavh77@gmail.com"
password = os.getenv("EMAIL_PASSWORD")

msg = MIMEText(f"System health check completed at {datetime.now()}")
msg['Subject'] = 'SecondBrain Health Check Report'
msg['From'] = sender
msg['To'] = receiver

with smtplib.SMTP_SSL('smtp.namecheap.com', 465) as server:
    server.login(sender, password)
    server.send_message(msg)
EOF
fi 