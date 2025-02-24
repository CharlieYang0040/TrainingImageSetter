@echo off

chcp 65001
echo.

REM Python 설치 확인
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 Python을 설치해주세요.
    pause
    exit /b 1
)

set "VIRTUAL_ENV=%~dp0venv"

REM venv 폴더 존재 확인
if not exist "%VIRTUAL_ENV%" (
    echo 가상환경을 생성합니다...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo 가상환경 생성에 실패했습니다.
        pause
        exit /b 1
    )
    echo 가상환경이 생성되었습니다.
    echo.
)

set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
set "PYTHONPATH=%VIRTUAL_ENV%\Lib\site-packages;%PYTHONPATH%"

echo 가상환경 경로: %VIRTUAL_ENV%
echo Python 인터프리터: "%VIRTUAL_ENV%\Scripts\python.exe"
"%VIRTUAL_ENV%\Scripts\python.exe" -c "import sys; print('Python 버전:', sys.version)"
echo.

echo [필수 패키지 설치 확인]
"%VIRTUAL_ENV%\Scripts\python.exe" -m pip install --upgrade pip
"%VIRTUAL_ENV%\Scripts\python.exe" -m pip install -r "%~dp0AutoCrawler\requirements.txt"
echo.

echo [패키지 임포트 테스트]
"%VIRTUAL_ENV%\Scripts\python.exe" -c "from PIL import Image; import requests; from selenium import webdriver; print('필수 패키지 임포트 성공')"
echo.

echo 가상환경이 활성화되었습니다.
echo.

"%VIRTUAL_ENV%\Scripts\python.exe" "%~dp0gui_launcher.py"

pause 