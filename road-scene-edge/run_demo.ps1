param(
    [string]$Video = "$PSScriptRoot/demo/source.mp4",
    [string]$Python = "python"
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& $Python roadscene.py demo --model models/roadscene_fp32.onnx --video $Video --output demo/latest.mp4 --seconds 20 --threads 2 --show
if ($LASTEXITCODE -ne 0) { throw 'The demo failed. See the error above.' }
