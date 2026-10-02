$p = Join-Path $PSScriptRoot 'backend'
Set-Location -LiteralPath $p
& "$p\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
