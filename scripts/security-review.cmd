@echo off
rem L2/L3 LLM 安全审查入口
python "%~dp0security-review.py" %*
exit /b %ERRORLEVEL%
