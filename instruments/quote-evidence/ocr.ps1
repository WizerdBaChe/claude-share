# Local OCR with the Windows built-in engine. Instrument only: writes <OutDir>/<stem>.txt per PNG in
# <InDir>; prints line counts, never the text. Called by qe.py ocr (which upscales first).
param([Parameter(Mandatory)][string]$InDir, [Parameter(Mandatory)][string]$OutDir, [string]$Lang = 'zh-Hant-TW')
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
# without this load, New-Object Windows.Globalization.Language fails with "type not found"
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) {
    $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(); $task.Result
}
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language $Lang))
if ($null -eq $engine) { Write-Error "OCR engine for $Lang unavailable (install the language's OCR capability)"; exit 2 }
New-Item -ItemType Directory -Force $OutDir | Out-Null
Get-ChildItem $InDir -Filter *.png | ForEach-Object {
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($_.FullName)) ([Windows.Storage.StorageFile])
    $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
    $lines = @($result.Lines | ForEach-Object { $_.Text })
    [System.IO.File]::WriteAllLines((Join-Path $OutDir ($_.BaseName + '.txt')), [string[]]$lines, (New-Object System.Text.UTF8Encoding $false))
    "{0}: {1} lines" -f $_.Name, $lines.Count
}
