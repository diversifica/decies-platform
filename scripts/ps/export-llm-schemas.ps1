$ErrorActionPreference = "Stop"

Write-Host "Exporting LLM schemas..."
python .\scripts\export-llm-schemas.py
Write-Host "OK"
