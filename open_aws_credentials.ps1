# Quick script to open AWS credentials file for editing

$CredentialsFile = "$env:USERPROFILE\.aws\credentials"

Write-Host "Opening AWS credentials file..." -ForegroundColor Cyan
Write-Host "File location: $CredentialsFile" -ForegroundColor Yellow
Write-Host ""

if (Test-Path $CredentialsFile) {
    Write-Host "File exists. Opening in VS Code..." -ForegroundColor Green
    code $CredentialsFile
    Write-Host ""
    Write-Host "Instructions:" -ForegroundColor Cyan
    Write-Host "1. Find or add the [doug-personal] section" -ForegroundColor White
    Write-Host "2. Update these values:" -ForegroundColor White
    Write-Host "   aws_access_key_id = YOUR_ACCESS_KEY_HERE" -ForegroundColor Yellow
    Write-Host "   aws_secret_access_key = YOUR_SECRET_KEY_HERE" -ForegroundColor Yellow
    Write-Host "   region = ap-southeast-2" -ForegroundColor Yellow
    Write-Host "3. Save the file" -ForegroundColor White
    Write-Host "4. Run: aws s3 ls s3://superweirdonebud/ --profile doug-personal" -ForegroundColor Green
} else {
    Write-Host "Credentials file doesn't exist. Creating directory..." -ForegroundColor Yellow
    $AwsDir = "$env:USERPROFILE\.aws"
    if (-not (Test-Path $AwsDir)) {
        New-Item -ItemType Directory -Path $AwsDir | Out-Null
    }
    
    Write-Host "Creating credentials file template..." -ForegroundColor Yellow
    $Template = @"
[doug-personal]
aws_access_key_id = YOUR_ACCESS_KEY_ID_HERE
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY_HERE
region = ap-southeast-2
"@
    
    $Template | Out-File -FilePath $CredentialsFile -Encoding UTF8
    Write-Host "Created: $CredentialsFile" -ForegroundColor Green
    code $CredentialsFile
    Write-Host ""
    Write-Host "Please update the placeholder values with your actual AWS credentials!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To get AWS credentials:" -ForegroundColor Cyan
Write-Host "1. Go to: https://console.aws.amazon.com/" -ForegroundColor White
Write-Host "2. Navigate to: IAM > Users > [Your User] > Security credentials" -ForegroundColor White
Write-Host "3. Create a new access key or use an existing one" -ForegroundColor White
