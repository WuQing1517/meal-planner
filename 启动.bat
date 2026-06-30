@echo off
chcp 65001
echo ========================================
echo         备餐系统启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] 正在安装依赖包...
pip install -r requirements.txt -q

echo [2/2] 正在启动服务...
echo.
echo 启动成功后，请访问: http://localhost:5000
echo 按 Ctrl+C 可停止服务
echo.
python app.py

pause
