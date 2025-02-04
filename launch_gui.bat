@echo off

chcp 65001
echo.

set "VIRTUAL_ENV=%~dp0venv"
set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
set "PYTHONPATH=%VIRTUAL_ENV%\Lib\site-packages;%PYTHONPATH%"

echo 가상환경 경로: %VIRTUAL_ENV%
echo Python 인터프리터: "%VIRTUAL_ENV%\Scripts\python.exe"
"%VIRTUAL_ENV%\Scripts\python.exe" -c "import sys; print('Python 버전:', sys.version)"
echo.

echo [Pillow 패키지 설치 확인]
"%VIRTUAL_ENV%\Scripts\python.exe" -m pip install --upgrade pip
"%VIRTUAL_ENV%\Scripts\python.exe" -m pip install --upgrade Pillow
echo.

echo [PIL 임포트 테스트]
"%VIRTUAL_ENV%\Scripts\python.exe" -c "from PIL import Image; print('PIL 임포트 성공')"
echo.

echo 가상환경이 활성화되었습니다.
echo.

"%VIRTUAL_ENV%\Scripts\python.exe" "%~dp0gui_launcher.py"

pause 