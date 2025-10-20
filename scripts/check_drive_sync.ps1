# scripts\check_drive_sync.ps1
# Owlume — Google Drive Sync Verifier (ASCII-only, robust)

$local = "C:\Users\shenb\DesktopLocal\elx-repo"

function Find-DriveRepo {
    param([string]$folderName = "elx-repo")

    # Common locations to try (ASCII-only)
    $candidates = @(
        "G:\My Drive\$folderName",
        "C:\Users\shenb\Google Drive\$folderName",
        "C:\Users\shenb\My Drive\$folderName",
        "C:\Users\shenb\Drive\My Drive\$folderName"
    )

    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }

    # Not found
    return $null
}

# --- Resolve Drive path ---
$drive = "G:\My Drive\elx-repo"
if (-not $drive) {
    Write-Host ""
    Write-Host "Could not auto-detect your Google Drive path for elx-repo." -ForegroundColor Yellow
    Write-Host "Example paths (adjust if needed):"
    Write-Host "  G:\My Drive\elx-repo"
    Write-Host "  C:\Users\shenb\Google Drive\elx-repo"
    Write-Host ""
    $drive = Read-Host "Enter the full path to your elx-repo in Google Drive"
}

Write-Host ""
Write-Host "Checking Owlume repo sync status..."
Write-Host "Local:  $local"
Write-Host "Drive:  $drive"
Write-Host ""

# --- Validate paths ---
if (!(Test-Path $local)) {
    Write-Host "Local path not found: $local" -ForegroundColor Red
    exit 1
}
if (!(Test-Path $drive)) {
    Write-Host "Drive path not found: $drive" -ForegroundColor Red
    exit 1
}

# --- Gather files ---
$localFiles = Get-ChildItem -Path $local -Recurse | Where-Object { -not $_.PSIsContainer }
$driveFiles = Get-ChildItem -Path $drive -Recurse | Where-Object { -not $_.PSIsContainer }

# --- Compare ---
$report = foreach ($file in $localFiles) {
    $relPath = $file.FullName.Substring($local.Length)
    $driveMatch = $driveFiles | Where-Object { $_.FullName.Substring($drive.Length) -eq $relPath }

    if ($driveMatch) {
        [PSCustomObject]@{
            File      = $relPath
            LocalTime = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
            DriveTime = $driveMatch.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
            Status    = if ($file.LastWriteTime -gt $driveMatch.LastWriteTime) {
                "Local newer"
            }
            elseif ($file.LastWriteTime -lt $driveMatch.LastWriteTime) {
                "Drive newer"
            }
            else {
                "Synced"
            }
        }
    }
    else {
        [PSCustomObject]@{
            File      = $relPath
            LocalTime = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
            DriveTime = "-"
            Status    = "Missing on Drive"
        }
    }
}

# --- Output ---
$report | Sort-Object Status, File | Format-Table -AutoSize

Write-Host ""
Write-Host "Done. If most rows show 'Synced', your Owlume repo is safely mirrored."
