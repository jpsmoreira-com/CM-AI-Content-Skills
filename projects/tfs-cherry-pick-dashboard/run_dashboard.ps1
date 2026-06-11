$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path $python) {
    & $python -m streamlit run app.py
} else {
    python -m streamlit run app.py
}
