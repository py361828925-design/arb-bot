$response = Invoke-WebRequest -Uri 'http://127.0.0.1:8003/config/current'
Write-Host "Status: $($response.StatusCode)"
Write-Host "Access-Control-Allow-Origin: $($response.Headers['Access-Control-Allow-Origin'])"
