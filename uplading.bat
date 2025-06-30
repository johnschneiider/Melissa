@echo off
cd /d %~dp0

:: Pide el mensaje del commit
set /p commitMsg=Escribe el mensaje del commit: 

:: Agrega todos los cambios
git add .

:: Hace el commit con el mensaje ingresado
git commit -m "%commitMsg%"

:: Sube los cambios a la rama principal (main)
git push origin main

echo.
echo ✅ Cambios subidos exitosamente sin perder versiones anteriores.
pause
