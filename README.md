# 🧠 IKB Navigator - AI-Powered Knowledge Assistant

An intelligent knowledge base assistant that uses LangGraph agents, Google Drive integration, and advanced AI to help you search, analyze, and organize your documents.

## 🌟 Features

- **🤖 AI-Powered Search**: Intelligent document search using OpenAI embeddings
- **📁 Google Drive Integration**: Direct access to your Google Drive files
- **🧠 Smart Query Understanding**: Expands keywords and understands context
- **📊 Smart Document Grouping**: Automatically categorizes documents by type
- **🔗 Clickable Source Links**: Direct links to original documents
- **⚡ Real-time Processing**: Fast search and response times
- **🎯 Broad Subject Queries**: Handles both specific and general questions

## 🏗️ Architecture

```
Frontend (Next.js) ↔ API Gateway (FastAPI) ↔ Agent Pipeline (LangGraph) ↔ Data Layer (Supabase) ↔ External Services (Google Drive, OpenAI)
```

### Key Components:
- **Frontend**: Next.js React application with modern UI
- **Backend**: FastAPI with LangGraph agent pipeline
- **Database**: Supabase PostgreSQL with vector embeddings
- **AI Services**: OpenAI GPT-3.5-turbo and text-embedding-3-small
- **File Storage**: Google Drive API integration

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for FastAPI backend)
- **Node.js 18+** (for Next.js frontend)
- **Git** (for cloning)
- **PostgreSQL** (via Supabase)

### Required Accounts & API Keys

- **OpenAI Account** - [Get API Key](https://platform.openai.com/api-keys)
- **Google Cloud Account** - [Enable Drive API](https://console.cloud.google.com)
- **Supabase Account** - [Create Project](https://supabase.com)

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/vishnu1136/finalagents.git
cd finalagents
```

### 2. Environment Setup

#### A. Create Environment File

```bash
# Copy the example environment file
cp apps/.env.example apps/.env
```

#### B. Configure Environment Variables

Edit `apps/.env` with your credentials:

```env
# OpenAI API Key (Required)
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=text-embedding-3-small

# Google Drive API (Required)
GDRIVE_API_KEY=your_google_drive_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_google_refresh_token
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id

# Supabase Database (Required)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# CORS Configuration
CORS_ORIGIN=http://localhost:3000

# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. Backend Setup (FastAPI)

#### A. Navigate to API Directory

```bash
cd apps/api
```

#### B. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### C. Install Dependencies

```bash
pip install -r requirements.txt
```

#### D. Start the Backend Server

```bash
python -m api.main
```

The backend will run on `http://localhost:8000`

### 4. Frontend Setup (Next.js)

#### A. Open New Terminal & Navigate to Web Directory

```bash
cd apps/web
```

#### B. Install Dependencies

```bash
npm install
# or
yarn install
```

#### C. Start the Frontend Server

```bash
npm run dev
# or
yarn dev
```

The frontend will run on `http://localhost:3000`

## 🗄️ Database Setup

### Supabase Configuration

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Get your project URL and API keys

2. **Run Database Migrations**:
   ```sql
   -- Execute the migration from supabase/migrations/0001_init.sql
   -- This creates the necessary tables:
   -- - sources (data source information)
   -- - documents (file metadata and URLs)
   -- - chunks (text chunks from processed files)
   -- - embeddings (vector embeddings for semantic search)
   ```

## 🌐 Google Drive Setup

### 1. Enable Google Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google Drive API
4. Create credentials (API Key + OAuth 2.0)

### 2. Configure OAuth

1. **Set up OAuth consent screen**:
   - Go to OAuth consent screen
   - Configure your application details
   - Add your domain

2. **Create OAuth 2.0 credentials**:
   - Go to Credentials
   - Create OAuth 2.0 Client ID
   - Download the credentials JSON

3. **Get Refresh Token**:
   - Use [OAuth 2.0 Playground](https://developers.google.com/oauthplayground)
   - Select Google Drive API v3
   - Authorize and get refresh token

### 3. Configure Drive Folder (Optional)

- Set `GOOGLE_DRIVE_FOLDER_ID` to limit search to specific folder
- Leave empty to search entire Google Drive

## ✅ Verification

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
```

### 2. Check Frontend

- Open http://localhost:3000
- You should see the IKB Navigator interface

### 3. Test Search

- Try searching for documents
- Check if Google Drive integration works
- Verify database connections

## 🔧 Configuration

### Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes | - |
| `EMBEDDING_MODEL` | OpenAI embedding model | No | text-embedding-3-small |
| `GDRIVE_API_KEY` | Google Drive API key | Yes | - |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Yes | - |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Yes | - |
| `GOOGLE_REFRESH_TOKEN` | Google OAuth refresh token | Yes | - |
| `GOOGLE_DRIVE_FOLDER_ID` | Specific Drive folder ID | No | - |
| `SUPABASE_URL` | Supabase project URL | Yes | - |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes | - |
| `SUPABASE_SERVICE_KEY` | Supabase service key | Yes | - |
| `CORS_ORIGIN` | Allowed CORS origins | No | http://localhost:3000 |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API URL | No | http://localhost:8000 |

## 🚨 Troubleshooting

### Common Issues

#### 1. Environment Variables Not Found
```bash
# Make sure .env file is in apps/ directory
# Check file permissions
# Verify variable names match exactly
```

#### 2. Database Connection Failed
```bash
# Verify Supabase credentials
# Check if database is accessible
# Run migrations again
# Check network connectivity
```

#### 3. Google Drive API Errors
```bash
# Verify API key is correct
# Check OAuth credentials
# Ensure Drive API is enabled
# Verify folder permissions
```

#### 4. Port Already in Use
```bash
# Backend: Change port in main.py
# Frontend: Change port in package.json
# Kill existing processes using the ports
```

#### 5. OpenAI API Errors
```bash
# Verify API key is valid
# Check API quota and billing
# Ensure model names are correct
```

### Debug Mode

Enable debug logging by setting:
```env
DEBUG=true
LOG_LEVEL=debug
```

## 📚 API Documentation

### Endpoints

- **POST /search** - Main search endpoint
- **GET /health** - Health check
- **POST /admin/ingest** - Document ingestion

### Search Request Format

```json
{
  "query": "your search query here"
}
```

### Search Response Format

```json
{
  "answer": "AI-generated response",
  "sources": [
    {
      "title": "Document Title",
      "url": "https://drive.google.com/file/...",
      "snippet": "Relevant content snippet..."
    }
  ],
  "grouped_sources": {
    "Implementation Guides": {
      "count": 5,
      "documents": [...]
    }
  }
}
```

## 🧪 Testing

### Run Tests

```bash
# Backend tests
cd apps/api
python -m pytest

# Frontend tests
cd apps/web
npm test
```

### Test Search Functionality

```bash
# Test with curl
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test search query"}'
```

## 🚀 Deployment

### Production Environment

1. **Set up production database** (Supabase)
2. **Configure production environment variables**
3. **Set up reverse proxy** (Nginx)
4. **Configure SSL certificates**
5. **Set up monitoring and logging**

### Docker Deployment (Optional)

```dockerfile
# Example Dockerfile for backend
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "api.main"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/vishnu1136/finalagents/issues)
- **Documentation**: [Wiki](https://github.com/vishnu1136/finalagents/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/vishnu1136/finalagents/discussions)

## 🙏 Acknowledgments

- **OpenAI** for AI capabilities
- **Google Drive API** for file integration
- **Supabase** for database services
- **LangGraph** for agent orchestration
- **Next.js** for frontend framework
- **FastAPI** for backend framework

---

**Made with ❤️ by the IKB Navigator Team**
