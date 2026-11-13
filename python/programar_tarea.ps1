param([switch]$DryRun, [string]$Hora = '08:00')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
$taskScript = Join-Path $PSScriptRoot 'inferencia.py'
$taskName = 'TallerCodexUFA_Inferencia'
if (!(Test-Path -LiteralPath $taskPython)) { throw 'Falta el entorno .venv.' }
if (!(Test-Path -LiteralPath (Join-Path $taskRoot 'artifacts\modelo_fraude.joblib'))) { throw 'Ejecute primero el notebook 02.' }
$taskTime = [datetime]::ParseExact($Hora,'HH:mm',[cultureinfo]::InvariantCulture)
$taskArguments = '"' + $taskScript + '" --desde 2026-06-16'
if ($DryRun) {
    [pscustomobject]@{Tarea=$taskName; Ejecutable=$taskPython; Argumentos=$taskArguments; Directorio=$taskRoot; Hora=$Hora; Modo='Usuario con sesion iniciada'} | Format-List
    exit 0
}
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) { throw 'La tarea ya existe. Revise o elimine la anterior para evitar sobrescribirla.' }
$taskAction = New-ScheduledTaskAction -Execute $taskPython -Argument $taskArguments -WorkingDirectory $taskRoot
$taskTrigger = New-ScheduledTaskTrigger -Daily -At $taskTime
$taskUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskPrincipal = New-ScheduledTaskPrincipal -UserId $taskUser -LogonType Interactive -RunLevel Limited
$taskSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $taskTrigger -Principal $taskPrincipal -Settings $taskSettings -Description 'Inferencia didactica sobre datos sinteticos; archivo de entrada fijo.'
Write-Host 'Tarea creada. Hora local del equipo. Para eliminar: Unregister-ScheduledTask -TaskName TallerCodexUFA_Inferencia'
