# 🚨 Troubleshooting Guide - IKB Navigator

This guide helps you resolve common issues when setting up and running IKB Navigator.

## 🔍 Quick Diagnostics

### Check System Status
```bash
# Check if services are running
curl http://localhost:8000/health  # Backend health
curl http://localhost:3000         # Frontend health

# Check logs
tail -f apps/api/logs/app.log      # Backend logs
tail -f apps/web/logs/app.log      # Frontend logs
```

## 🐛 Common Issues & Solutions

### 1. Environment Variables Issues

#### Problem: "Environment variable not found"
```
Error: OPENAI_API_KEY not found
```

**Solutions:**
- ✅ Check if `.env` file exists in `apps/` directory
- ✅ Verify variable names match exactly (case-sensitive)
- ✅ Ensure no extra spaces or quotes around values
- ✅ Restart the application after changing `.env`

```bash
# Verify .env file
cat apps/.env

# Check if variables are loaded
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

#### Problem: "Invalid API key"
```
Error: Invalid API key provided
```

**Solutions:**
- ✅ Verify API key is correct and active
- ✅ Check if API key has proper permissions
- ✅ Ensure no extra characters or spaces
- ✅ Test API key independently

```bash
# Test OpenAI API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

### 2. Database Connection Issues

#### Problem: "Database connection failed"
```
Error: Failed to connect to Supabase
```

**Solutions:**
- ✅ Verify Supabase URL and keys are correct
- ✅ Check if Supabase project is active
- ✅ Ensure database is accessible from your IP
- ✅ Run database migrations

```bash
# Test Supabase connection
curl -H "apikey: $SUPABASE_ANON_KEY" \
     "$SUPABASE_URL/rest/v1/"
```

#### Problem: "Table does not exist"
```
Error: relation "documents" does not exist
```

**Solutions:**
- ✅ Run database migrations
- ✅ Check if migrations were applied correctly
- ✅ Verify table names in migration file

```sql
-- Check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
```

### 3. Google Drive API Issues

#### Problem: "Google Drive API error"
```
Error: 403 Forbidden - Google Drive API
```

**Solutions:**
- ✅ Verify Google Drive API is enabled
- ✅ Check API key permissions
- ✅ Ensure OAuth credentials are correct
- ✅ Verify folder permissions

```bash
# Test Google Drive API
curl "https://www.googleapis.com/drive/v3/files?key=$GDRIVE_API_KEY"
```

#### Problem: "Refresh token expired"
```
Error: Invalid refresh token
```

**Solutions:**
- ✅ Generate new refresh token
- ✅ Check OAuth consent screen configuration
- ✅ Verify client ID and secret

### 4. Port Issues

#### Problem: "Port already in use"
```
Error: Address already in use: 8000
```

**Solutions:**
- ✅ Kill existing processes using the port
- ✅ Change port in configuration
- ✅ Use different ports for different services

```bash
# Find process using port
netstat -ano | findstr :8000
lsof -i :8000

# Kill process (Windows)
taskkill /PID <PID> /F

# Kill process (Unix/macOS)
kill -9 <PID>
```

### 5. Python/Node.js Issues

#### Problem: "Python module not found"
```
Error: No module named 'fastapi'
```

**Solutions:**
- ✅ Activate virtual environment
- ✅ Install dependencies
- ✅ Check Python path

```bash
# Activate virtual environment
source apps/api/venv/bin/activate  # Unix/macOS
apps\api\venv\Scripts\activate     # Windows

# Install dependencies
pip install -r apps/api/requirements.txt
```

#### Problem: "Node modules not found"
```
Error: Cannot find module 'next'
```

**Solutions:**
- ✅ Install Node.js dependencies
- ✅ Check Node.js version
- ✅ Clear npm cache

```bash
# Install dependencies
cd apps/web
npm install

# Clear cache
npm cache clean --force
```

### 6. CORS Issues

#### Problem: "CORS error"
```
Error: Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solutions:**
- ✅ Check CORS_ORIGIN configuration
- ✅ Verify frontend and backend URLs
- ✅ Update CORS settings

```bash
# Check CORS configuration
grep CORS_ORIGIN apps/.env
```

### 7. Search Issues

#### Problem: "No results found"
```
Response: "I couldn't find any relevant documents"
```

**Solutions:**
- ✅ Check if documents exist in database
- ✅ Verify Google Drive integration
- ✅ Check search query format
- ✅ Ensure embeddings are generated

```bash
# Check database content
curl -H "apikey: $SUPABASE_ANON_KEY" \
     "$SUPABASE_URL/rest/v1/documents?select=*"
```

#### Problem: "Search is slow"
```
Response takes more than 10 seconds
```

**Solutions:**
- ✅ Check database performance
- ✅ Optimize search queries
- ✅ Reduce search result limit
- ✅ Check network connectivity

### 8. AI Response Issues

#### Problem: "AI response is empty"
```
Response: ""
```

**Solutions:**
- ✅ Check OpenAI API key
- ✅ Verify API quota and billing
- ✅ Check model availability
- ✅ Review error logs

```bash
# Test OpenAI API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}]}' \
     https://api.openai.com/v1/chat/completions
```

## 🔧 Debug Mode

### Enable Debug Logging

Add to your `.env` file:
```env
DEBUG=true
LOG_LEVEL=debug
```

### Check Logs

```bash
# Backend logs
tail -f apps/api/logs/app.log

# Frontend logs
tail -f apps/web/logs/app.log

# System logs
journalctl -u your-service-name
```

### Verbose Output

```bash
# Run with verbose output
python -m api.main --verbose
npm run dev -- --verbose
```

## 🧪 Testing Components

### Test Database Connection
```python
# test_db.py
import os
from api.services.db import get_supabase_client

client = get_supabase_client()
result = client.table('sources').select('*').execute()
print(f"Database connection: {len(result.data)} sources found")
```

### Test Google Drive API
```python
# test_gdrive.py
import os
from api.integrations.mcp_client import GDriveMCPClient

client = GDriveMCPClient()
files = await client.list_files()
print(f"Google Drive: {len(files)} files found")
```

### Test OpenAI API
```python
# test_openai.py
import os
import openai

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello"}]
)
print(f"OpenAI: {response.choices[0].message.content}")
```

## 📊 Performance Issues

### Slow Search Performance

**Symptoms:**
- Search takes more than 5 seconds
- High CPU usage
- Memory issues

**Solutions:**
- ✅ Optimize database queries
- ✅ Add database indexes
- ✅ Reduce search result limit
- ✅ Implement caching
- ✅ Use connection pooling

### High Memory Usage

**Symptoms:**
- Application crashes
- Slow response times
- System becomes unresponsive

**Solutions:**
- ✅ Monitor memory usage
- ✅ Optimize data processing
- ✅ Implement pagination
- ✅ Use streaming responses
- ✅ Add memory limits

## 🆘 Getting Help

### Before Asking for Help

1. ✅ Check this troubleshooting guide
2. ✅ Enable debug logging
3. ✅ Check error logs
4. ✅ Verify configuration
5. ✅ Test individual components

### When Reporting Issues

Include the following information:
- **Error message** (exact text)
- **Steps to reproduce**
- **Environment details** (OS, Python version, Node.js version)
- **Configuration** (sanitized .env file)
- **Logs** (relevant error logs)
- **Screenshots** (if applicable)

### Support Channels

- **GitHub Issues**: [Create an issue](https://github.com/vishnu1136/finalagents/issues)
- **GitHub Discussions**: [Ask a question](https://github.com/vishnu1136/finalagents/discussions)
- **Documentation**: [Read the docs](https://github.com/vishnu1136/finalagents/wiki)

## 🔄 Reset and Reinstall

### Complete Reset

```bash
# Stop all services
pkill -f "python -m api.main"
pkill -f "npm run dev"

# Remove virtual environment
rm -rf apps/api/venv

# Remove node modules
rm -rf apps/web/node_modules

# Remove database data (if using local database)
rm -rf data/

# Reinstall everything
./setup.sh
```

### Partial Reset

```bash
# Reset backend only
cd apps/api
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Reset frontend only
cd apps/web
rm -rf node_modules
npm install
```

---

**Still having issues?** Check the [GitHub Issues](https://github.com/vishnu1136/finalagents/issues) or create a new one with detailed information about your problem.
