# Super Weird One Bud - Setup & Reference Guide

**Rottnest Island Surf Conditions Tracker**

---

## 🚀 Quick Start

### Run Locally (Windows)

```powershell
# Quick start
.\run_local.ps1

# Or manually
.\superweirdonebud_venv\Scripts\Activate.ps1
streamlit run superweirdonebud.py
```

The app will open at: http://localhost:8501

---

## 📋 Project Overview

A Streamlit web application for tracking surf conditions at Rottnest Island breaks:
- Record detailed session data (swell, wind, tide)
- Smart scoring system with weighted calculations
- Filter by zone and break
- Cloud storage with AWS S3

### Tech Stack
- **Frontend**: Streamlit 1.50.0
- **Data**: Pandas 2.3.3, NumPy 2.2.6
- **Cloud**: AWS S3 via Boto3 1.40.48
- **Hosting**: AWS EC2 (production)

---

## 🔧 Setup Instructions

### 1. Virtual Environment
The Windows venv is already configured:
```
superweirdonebud_venv/  # Python 3.10.4 (local development)
```

### 2. AWS Credentials

The app requires AWS S3 access. Configure your credentials:

#### Edit credentials file:
```powershell
code "$env:USERPROFILE\.aws\credentials"
```

#### Add your credentials:
```ini
[doug-personal]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
region = ap-southeast-2
```

#### Get AWS credentials:
1. Go to https://console.aws.amazon.com/
2. Navigate to: **IAM → Users → [Your User] → Security credentials**
3. Create access key (use case: "Application running outside AWS")
4. Copy both Access Key ID and Secret Access Key

#### Required S3 Permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
        "Resource": [
            "arn:aws:s3:::superweirdonebud",
            "arn:aws:s3:::superweirdonebud/*"
        ]
    }]
}
```

#### Test credentials:
```powershell
aws s3 ls s3://superweirdonebud/ --profile doug-personal
```

### 3. Dependencies

All dependencies are installed in the venv. To update:
```powershell
.\superweirdonebud_venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 📊 Application Features

### Data Structure
- **Session Info**: Date, Time, Break, Zone
- **Swell**: Size (Surfline & Seabreeze), Period, Direction, Score
- **Wind**: Bearing (compass), Speed, Score
- **Tide**: Reading, Direction, Score
- **Commentary**: Detailed notes per factor

### Scoring System
- Each factor (Swell/Wind/Tide) scored 0-10
- Multiplied by suitability (Yes=1, Ok=0.5, No=0, Too Big=0)
- **Total Score = (Swell × Wind × Tide) / 3**

### Workflows
1. **List View**: Filter by zone/break, sort, paginate
2. **Create**: Multi-page form with validation
3. **Edit**: Password-protected (password: "utfs")
4. **Delete**: Confirmation required

---

## 🌐 Deployment

### Production (EC2)
- **Branch**: `main` (auto-deploys via GitHub Actions)
- **Workflow**: `.github/workflows/deploy-to-ec2.yml`
- **Environment**: `superweirdonebud_linux.venv` (Python 3.12)

### Local Development
- **Branch**: `test-branch2` (current)
- **Environment**: `superweirdonebud_venv` (Python 3.10)

To deploy:
1. Test locally
2. Commit changes
3. Merge to `main` branch
4. GitHub Actions handles EC2 deployment

---

## 🗂️ Project Structure

```
SuperWeirdOneBud/
├── superweirdonebud.py           # Main application (700 lines)
├── requirements.txt               # Dependencies
├── run_local.ps1                  # Quick start script
├── SETUP.md                       # This file
├── data/
│   └── Rotto_Tracker.csv         # Local backup (S3 is primary)
├── superweirdonebud_venv/        # Windows venv
├── superweirdonebud_linux.venv/  # Linux venv (EC2)
└── .github/workflows/
    └── deploy-to-ec2.yml          # CI/CD
```

---

## 🐛 Troubleshooting

### AWS Connection Errors
- Check credentials: `aws s3 ls s3://superweirdonebud/ --profile doug-personal`
- Verify profile name is `doug-personal`
- Ensure no invalid environment variables: `$env:AWS_ACCESS_KEY_ID`

### Port Already in Use
```powershell
streamlit run superweirdonebud.py --server.port 8502
```

### Streamlit Won't Start
```powershell
# Check Python version
.\superweirdonebud_venv\Scripts\python.exe --version

# Reinstall dependencies
.\superweirdonebud_venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 🧪 Testing

### Syntax Check
```powershell
.\superweirdonebud_venv\Scripts\python.exe -m py_compile superweirdonebud.py
```

### Manual Testing Checklist
- [ ] App loads without errors
- [ ] Filter by zone
- [ ] Filter by break  
- [ ] Sort by different columns
- [ ] Create new record (all 4 pages)
- [ ] Edit existing record (password: "utfs")
- [ ] Delete record with confirmation
- [ ] Data persists in S3

---

## 📝 Data Storage

**Primary**: AWS S3 (`s3://superweirdonebud/Rotto_Tracker.csv`)
**Backup**: Local `data/Rotto_Tracker.csv` (manual, not auto-synced)

All create/edit/delete operations write directly to S3.

---

## 🔐 Security Notes

- Edit password: `utfs` (or `utsf`)
- Stored in code - consider environment variable for production
- AWS credentials never committed to repository
- S3 access limited to one bucket

---

## 📚 References

- **Streamlit Docs**: https://docs.streamlit.io/
- **Boto3 S3 Guide**: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3.html
- **AWS IAM Best Practices**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## 🎯 Quick Commands

```powershell
# Start app
.\run_local.ps1

# Check AWS credentials
aws s3 ls s3://superweirdonebud/ --profile doug-personal

# Update dependencies
.\superweirdonebud_venv\Scripts\Activate.ps1
pip install -r requirements.txt --upgrade

# Check Python version
.\superweirdonebud_venv\Scripts\python.exe --version

# Syntax check
.\superweirdonebud_venv\Scripts\python.exe -m py_compile superweirdonebud.py
```

---

**Happy Surfing! 🏄‍♂️🌊**

Last Updated: December 7, 2025
