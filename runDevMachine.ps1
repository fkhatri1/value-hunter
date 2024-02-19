# Get source and target paths from environment variables
$sourcePath = $env:SOURCE_PATH
$targetPath = $env:TARGET_PATH

# Check if environment variables are set
if (-not $sourcePath -or -not $targetPath) {
    Write-Host "Error: SOURCE_PATH or TARGET_PATH environment variables are not set."
    exit 1
}


# Start the Docker container in detached mode
Start-Process -NoNewWindow -FilePath "docker" -ArgumentList "run", "--name", "python_dev", "--mount", "type=bind,source=$sourcePath,target=$targetPath", "-p", "52022:22", "-p", "8888:8888", "fkhatri/devmachine:1"

# Exit PowerShell
exit
