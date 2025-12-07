# Run Super Weird One Bud Locally
# This script runs the Streamlit app using the virtual environment

Write-Host "Starting Super Weird One Bud - Surf Tracker" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
$ProjectDir = "c:\Users\dougl\Desktop\Personal Projects\Code\SuperWeirdOneBud"
Set-Location $ProjectDir
Write-Host "Project directory: $ProjectDir" -ForegroundColor Green
Write-Host ""

# Define paths to virtual environment executables
$VenvPython = ".\superweirdonebud_venv\Scripts\python.exe"
$VenvStreamlit = ".\superweirdonebud_venv\Scripts\streamlit.exe"

# Check if virtual environment exists
if (-not (Test-Path $VenvPython)) {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Expected path: $VenvPython" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please create it with:" -ForegroundColor Yellow
    Write-Host "  python -m venv superweirdonebud_venv" -ForegroundColor Cyan
    Write-Host "  .\superweirdonebud_venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Cyan
    exit 1
}

# Display Python version from venv
Write-Host "Python version (from venv):" -ForegroundColor Yellow
& $VenvPython --version
Write-Host ""

# Check AWS credentials
Write-Host "Checking AWS configuration..." -ForegroundColor Yellow
if (Test-Path "$env:USERPROFILE\.aws\credentials") {
    Write-Host "AWS credentials found" -ForegroundColor Green
} else {
    Write-Host "AWS credentials not found - you may need to configure them" -ForegroundColor Red
}
Write-Host ""

# Check if streamlit is installed in venv
if (-not (Test-Path $VenvStreamlit)) {
    Write-Host "Streamlit not found in virtual environment" -ForegroundColor Yellow
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & $VenvPython -m pip install -r requirements.txt
    Write-Host ""
}

# Start Streamlit using the venv's streamlit
Write-Host "Starting Streamlit application..." -ForegroundColor Cyan
Write-Host "The app will open in your browser at http://localhost:8501" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

& $VenvStreamlit run superweirdonebud.py

