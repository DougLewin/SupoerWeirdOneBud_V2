"""
Debug script to test S3 connection and data loading
"""
import boto3
import pandas as pd
import io

S3_BUCKET = "superweirdonebud"
S3_KEY = "Rotto_Tracker.csv"

print("=" * 60)
print("DEBUG: Testing S3 Connection and Data Loading")
print("=" * 60)

# Test 1: Initialize S3 client
print("\n1. Initializing S3 client...")

# Check if AWS environment variables are set
import os
env_vars_set = bool(os.environ.get('AWS_ACCESS_KEY_ID'))
print(f"   AWS environment variables set: {env_vars_set}")

try:
    # Try with environment variables first (this matches the app logic)
    s3 = boto3.client('s3', region_name='ap-southeast-2')
    print("   ✓ S3 client created (using environment variables)")
    print("   Testing with environment variables...")
    # Quick test to see if credentials work
    try:
        s3.list_buckets()
        print("   ✓ Environment variable credentials are VALID")
    except Exception as test_e:
        print(f"   ✗ Environment variable credentials are INVALID: {test_e}")
        raise Exception("Invalid environment credentials")
except Exception as e1:
    print(f"   ✗ Failed with environment variables: {e1}")
    try:
        # Fallback to local profile
        s3 = boto3.Session(profile_name='doug-personal').client('s3', region_name='ap-southeast-2')
        print("   ✓ S3 client created (using profile 'doug-personal')")
    except Exception as e2:
        print(f"   ✗ Failed with profile: {e2}")
        exit(1)

# Test 2: List bucket contents
print("\n2. Listing bucket contents...")
try:
    response = s3.list_objects_v2(Bucket=S3_BUCKET)
    if 'Contents' in response:
        print(f"   ✓ Found {len(response['Contents'])} objects in bucket:")
        for obj in response['Contents']:
            print(f"      - {obj['Key']} ({obj['Size']} bytes, modified: {obj['LastModified']})")
    else:
        print("   ⚠ Bucket is empty")
except Exception as e:
    print(f"   ✗ Failed to list bucket: {e}")

# Test 3: Download and read the CSV
print(f"\n3. Downloading '{S3_KEY}' from S3...")
try:
    obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    print(f"   ✓ File downloaded successfully")
    print(f"   - Content-Type: {obj['ContentType']}")
    print(f"   - Content-Length: {obj['ContentLength']} bytes")
    print(f"   - Last-Modified: {obj['LastModified']}")
except Exception as e:
    print(f"   ✗ Failed to download file: {e}")
    exit(1)

# Test 4: Parse CSV data
print("\n4. Parsing CSV data...")
try:
    df = pd.read_csv(obj['Body'])
    print(f"   ✓ CSV parsed successfully")
    print(f"   - Rows: {len(df)}")
    print(f"   - Columns: {len(df.columns)}")
    print(f"   - Column names: {list(df.columns)}")
except Exception as e:
    print(f"   ✗ Failed to parse CSV: {e}")
    exit(1)

# Test 5: Display data summary
print("\n5. Data Summary:")
print(f"   - Total records: {len(df)}")
if len(df) > 0:
    print(f"   - Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"   - Breaks: {df['Break'].unique().tolist()}")
    if 'Zone' in df.columns:
        print(f"   - Zones: {df['Zone'].unique().tolist()}")
    print(f"\n   First few rows:")
    print(df.head().to_string(index=False))
else:
    print("   ⚠ No records found in CSV")

print("\n" + "=" * 60)
print("DEBUG Complete")
print("=" * 60)
