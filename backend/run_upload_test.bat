@echo off
setlocal enabledelayedexpansion
cd /d "D:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI\backend"
echo === STEP 1 : Create PNG ===
python -c "import base64;open('test_image.png','wb').write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='))" && echo PNG_OK || echo PNG_FAIL
echo === STEP 2 : Login ===
curl -s -X POST http://127.0.0.1:8000/auth/login -F "username=etudiant.test@dexter.dev" -F "password=Etudiant2026!" -o token.json
set "TOK="
for /f "tokens=2 delims=:" %%a in ('findstr "access_token" token.json') do (
  set "TOK=%%a"
  set "TOK=!TOK: =!"
  set "TOK=!TOK:\"=!"
  set "TOK=!TOK:,,=!"
)
echo TOKEN_RECOVERED: !TOK:~0,10!...
if "!TOK!"=="" (echo AUTH_FAILED && exit /b 1)
echo === STEP 3 : Upload image to conversation 1 ===
curl -s -o upload_resp.txt -w "HTTP_%{http_code}" -X POST http://127.0.0.1:8000/conversations/1/documents -F "file=@test_image.png" -H "Authorization: Bearer !TOK!"
echo.
echo === STEP 4 : Upload response body ===
more upload_resp.txt
echo === STEP 5 : Check document in conversation ===
curl -s http://127.0.0.1:8000/conversations/1/documents -H "Authorization: Bearer !TOK!" -o docs_list.txt
more docs_list.txt
endlocal