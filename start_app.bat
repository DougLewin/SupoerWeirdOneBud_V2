@echo off
REM Windows deployment script for SuperWeirdOneBud

echo Starting SuperWeirdOneBud Streamlit App...

REM Activate virtual environment
call superweirdonebud_venv\Scripts\activate.bat

REM Set environment variables for AWS credentials (replace with your actual values)
set AWS_ACCESS_KEY_ID=your_access_key_here
set AWS_SECRET_ACCESS_KEY=your_secret_key_here
set AWS_DEFAULT_REGION=ap-southeast-2

REM Start Streamlit with production configuration
streamlit run superweirdonebud.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false