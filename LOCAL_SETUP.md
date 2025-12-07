# Local Setup Guide - Super Weird One Bud

## Quick Start (Windows PowerShell)

### 1. Activate Virtual Environment
```powershell
# Navigate to project directory
cd "c:\Users\dougl\Desktop\Personal Projects\Code\SuperWeirdOneBud"

# Activate the Windows virtual environment
.\superweirdonebud_venv\Scripts\Activate.ps1
```

**Note**: If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Verify Dependencies
```powershell
# Check installed packages
pip list

# Install/update requirements if needed
pip install -r requirements.txt
```

### 3. AWS Credentials Setup
The app requires AWS credentials to access the S3 bucket. You have two options:

**Option A: Use AWS Profile (Recommended for local dev)**
- The code tries to use profile `doug-personal`
- Ensure your `~/.aws/credentials` file has this profile configured

**Option B: Set Environment Variables**
```powershell
$env:AWS_ACCESS_KEY_ID = "your-access-key"
$env:AWS_SECRET_ACCESS_KEY = "your-secret-key"
$env:AWS_DEFAULT_REGION = "ap-southeast-2"
```

### 4. Run the Application
```powershell
streamlit run superweirdonebud.py
```

The app will open automatically in your browser at: `http://localhost:8501`

### 5. Deactivate When Done
```powershell
deactivate
```

---

## Project Structure

```
SuperWeirdOneBud/
├── superweirdonebud.py          # Main Streamlit application
├── requirements.txt              # Python dependencies
├── data/
│   └── Rotto_Tracker.csv        # Local CSV backup (S3 is primary)
├── superweirdonebud_venv/       # Windows Python 3.10 environment
└── superweirdonebud_linux.venv/ # Linux Python 3.12 environment (for EC2)
```

---

## Key Dependencies

- **streamlit** (1.50.0) - Web framework
- **pandas** (2.3.3) - Data manipulation
- **numpy** (2.2.6) - Numerical operations
- **boto3** (1.40.48) - AWS S3 integration

---

## AWS S3 Configuration

- **Bucket**: `superweirdonebud`
- **File**: `Rotto_Tracker.csv`
- **Region**: `ap-southeast-2` (Sydney)

---

## Application Features

### Main Views
1. **Summary List** - View all sessions with filtering and sorting
2. **Details View** - See full session details
3. **Create New** - Add new surf session
4. **Edit/Delete** - Password protected (password: "utfs")

### Data Tracked Per Session
- **Session Info**: Date, Time, Break, Zone
- **Swell**: Size (Surfline & Seabreeze), Period, Direction, Score
- **Wind**: Bearing, Speed, Score
- **Tide**: Reading, Direction, Score
- **Commentary**: Detailed notes for each condition

### Scoring System
- Each factor (Swell/Wind/Tide) scored 0-10
- Multiplied by suitability factor (Yes=1, Ok=0.5, No=0)
- Total Score = (Swell × Wind × Tide) / 3

---

## Troubleshooting

### AWS Connection Issues
If you see "Failed to connect to AWS S3":
1. Check AWS credentials are configured
2. Verify profile `doug-personal` exists in `~/.aws/credentials`
3. Or set environment variables as shown above

### Virtual Environment Issues
If activation fails:
```powershell
# Recreate venv if needed
python -m venv superweirdonebud_venv
.\superweirdonebud_venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Port Already in Use
If port 8501 is busy:
```powershell
streamlit run superweirdonebud.py --server.port 8502
```

---

## Development Workflow

### Current Branch Status
- **Active Branch**: `test-branch2`
- **Main Branch**: Production (auto-deploys to EC2)

### Making Changes
1. Work on feature branches
2. Test locally with instructions above
3. Merge to `main` to trigger EC2 deployment

### Testing Before Deployment
Always test locally before pushing to main:
```powershell
streamlit run superweirdonebud.py
```

---

## Next Steps / Where You Left Off

Based on the code review, it appears you were working on:
1. ✅ Responsive design improvements (mobile-friendly layout)
2. ✅ Zone-based filtering system
3. ✅ Enhanced sorting capabilities
4. ✅ Tide direction normalization (Dropping → Falling)
5. ✅ Wind bearing compass direction inputs
6. ✅ Validation for new entries

The application appears feature-complete and production-ready. The main deployment is configured for EC2 via GitHub Actions.

---

## Quick Command Reference

```powershell
# Activate environment
.\superweirdonebud_venv\Scripts\Activate.ps1

# Run app
streamlit run superweirdonebud.py

# Check dependencies
pip list

# Update dependencies
pip install -r requirements.txt --upgrade

# Deactivate
deactivate
```
