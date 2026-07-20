@echo off
REM ──────────────────────────────────────────────────────────────────────────────
REM CareAnchor - Quick Deploy Script for Windows (Development)
REM This script builds the frontend and verifies the deployment is ready
REM ──────────────────────────────────────────────────────────────────────────────

echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║         CareAnchor - Windows Quick Deploy Helper                      ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.

cd ..

REM Step 1: Check .env file
echo ► Step 1: Checking environment...
if not exist .env (
    echo ✖ .env file not found!
    echo → Please create .env file with your configuration
    exit /b 1
)
echo ✓ Environment file found
echo.

REM Step 2: Install dependencies
echo ► Step 2: Installing dependencies...
if not exist node_modules (
    call npm install
)
echo ✓ Dependencies ready
echo.

REM Step 3: Build frontend
echo ► Step 3: Building frontend...
call npm run build
if not exist dist\index.html (
    echo ✖ Frontend build failed
    exit /b 1
)
echo ✓ Frontend built successfully
echo.

REM Step 4: Instructions for ECS deployment
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                    Frontend Build Complete! ✓                          ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
echo Next steps to deploy on Alibaba Cloud ECS:
echo.
echo   1. Upload code to ECS:
echo      scp -r . root@YOUR_ECS_IP:/root/Care-Anchor
echo.
echo   2. SSH into ECS:
echo      ssh root@YOUR_ECS_IP
echo.
echo   3. Run deployment:
echo      cd Care-Anchor
echo      ./deploy/quick-deploy.sh
echo.
echo For detailed instructions, see DEPLOYMENT_GUIDE.md
echo.
pause
