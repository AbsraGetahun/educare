@echo off
echo Setting up EDUCARE Backend Environment Configuration
echo.

REM Create .env file with proper configuration
(
echo # EDUCARE Backend Configuration
echo.
echo # Database
echo DB_HOST=localhost
echo DB_USER=root
echo DB_PASSWORD=absra123
echo DB_NAME=educare
echo.
echo # JWT
echo JWT_SECRET_KEY=educare-secret-key
echo.
echo # Email Configuration
echo EMAIL_MODE=console
echo.
echo # Console mode: Logs verification links to console
echo # SMTP mode: Uses Gmail SMTP
echo # SendGrid mode: Uses SendGrid API
echo.
echo # SMTP Settings (for EMAIL_MODE=smtp)
echo SMTP_HOST=smtp.gmail.com
echo SMTP_PORT=587
echo SMTP_USER=your-email@gmail.com
echo SMTP_PASSWORD=your-app-password
echo SMTP_FROM=noreply@educare.com
echo.
echo # SendGrid Settings (for EMAIL_MODE=sendgrid)
echo SENDGRID_API_KEY=your-sendgrid-api-key
echo.
echo # Verification Settings
echo VERIFICATION_TOKEN_EXPIRY_HOURS=24
echo.
echo # Frontend URL (for verification links)
echo BASE_URL=http://localhost:3000
) > .env

echo .env file created successfully!
echo.
echo Configuration:
echo - Database: MySQL on localhost
echo - Email Mode: console (verification links will be logged to console)
echo - Frontend URL: http://localhost:3000
echo.
echo You can now start the backend server.
pause
