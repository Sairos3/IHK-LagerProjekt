$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "backups\$timestamp"

New-Item -ItemType Directory -Path $backupPath -Force

Copy-Item "db.sqlite3" "$backupPath\db.sqlite3" -Force

if (Test-Path "media") {
    Copy-Item "media" "$backupPath\media" -Recurse -Force
}

Write-Host "Backup created at $backupPath"