@echo off
cd /d "E:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI\backend"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
