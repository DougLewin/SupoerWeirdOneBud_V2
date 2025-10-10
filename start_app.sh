#!/bin/bash
# EC2 Deployment Script for SuperWeirdOneBud

echo "Starting SuperWeirdOneBud Streamlit App..."

# Activate virtual environment
source superweirdonebud_venv/bin/activate

# Set environment variables for AWS credentials (replace with your actual values)
export AWS_ACCESS_KEY_ID="your_access_key_here"
export AWS_SECRET_ACCESS_KEY="your_secret_key_here"
export AWS_DEFAULT_REGION="ap-southeast-2"

# Start Streamlit with production configuration
streamlit run superweirdonebud.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false