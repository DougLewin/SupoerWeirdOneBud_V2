# EC2 Deployment Guide for SuperWeirdOneBud

## Prerequisites
- EC2 instance running (Ubuntu/Amazon Linux recommended)
- Security Group allowing inbound traffic on port 8501
- Your AWS Access Key ID and Secret Access Key

## Step 1: Connect to Your EC2 Instance
```bash
ssh -i "your-key.pem" ec2-user@your-ec2-public-ip
```

## Step 2: Install Required System Packages
```bash
# Update system
sudo yum update -y  # For Amazon Linux
# OR
sudo apt update && sudo apt upgrade -y  # For Ubuntu

# Install Python and Git
sudo yum install python3 python3-pip git -y  # Amazon Linux
# OR
sudo apt install python3 python3-pip python3-venv git -y  # Ubuntu
```

## Step 3: Upload Your Project Files
Choose one of these methods:

### Option A: Using Git (Recommended)
```bash
git clone https://github.com/DougLewin/SuperWeirdOneBud.git
cd SuperWeirdOneBud
```

### Option B: Using SCP
```bash
# From your local machine
scp -i "your-key.pem" -r "C:\Users\dougl\Desktop\Personal Projects\Code\SuperWeirdOneBud" ec2-user@your-ec2-public-ip:~/
```

## Step 4: Set Up Python Environment
```bash
cd SuperWeirdOneBud
python3 -m venv superweirdonebud_venv
source superweirdonebud_venv/bin/activate
pip install -r requirements.txt
```

## Step 5: Configure AWS Credentials
Choose one of these methods:

### Option A: Environment Variables (in start_app.sh)
Edit the start_app.sh file:
```bash
nano start_app.sh
```
Replace the placeholder values with your actual AWS credentials.

### Option B: IAM Role (Recommended for production)
1. Create an IAM role with S3 access permissions
2. Attach the role to your EC2 instance
3. No need to modify credentials in the script

## Step 6: Make Script Executable and Run
```bash
chmod +x start_app.sh
./start_app.sh
```

## Step 7: Access Your App
Open your browser and go to:
```
http://your-ec2-public-ip:8501
```

## Optional: Run as Background Service
To keep the app running after you disconnect:

### Using nohup:
```bash
nohup ./start_app.sh > app.log 2>&1 &
```

### Using systemd service:
1. Create service file:
```bash
sudo nano /etc/systemd/system/superweirdonebud.service
```

2. Add this content:
```ini
[Unit]
Description=SuperWeirdOneBud Streamlit App
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/SuperWeirdOneBud
ExecStart=/home/ec2-user/SuperWeirdOneBud/start_app.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable superweirdonebud
sudo systemctl start superweirdonebud
```

## Security Group Configuration
Make sure your EC2 Security Group allows:
- **Inbound**: Port 8501 from 0.0.0.0/0 (or your specific IP range)
- **Outbound**: All traffic (for S3 access)

## Troubleshooting
- Check logs: `tail -f app.log` (if using nohup)
- Check service status: `sudo systemctl status superweirdonebud`
- Test S3 connection: Run the S3 Test.py script first
- Verify port is open: `netstat -tlnp | grep 8501`

## Files Created for Deployment
- `requirements.txt` - Python dependencies
- `start_app.sh` - Linux startup script
- `start_app.bat` - Windows startup script
- `.streamlit/config.toml` - Streamlit production configuration
- `EC2_DEPLOYMENT.md` - This deployment guide