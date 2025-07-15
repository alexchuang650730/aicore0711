# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PowerAutomation Core v4.6.9 is an enterprise-grade automation platform focused on mobile/desktop-first development with deep Claude Code integration. The project features a multi-AI model routing system that prioritizes cost-efficient operation by routing Claude Code requests to Kimi K2 models while maintaining full compatibility with Claude Code's slash command system.

## Development Commands

### Starting the Claude Code Router MCP Service
```bash
# Activate virtual environment and start the router
source venv/bin/activate
python3 run_router.py

# Or start in background
nohup python3 run_router.py > router.log 2>&1 &

# Simple router server (for testing)
python3 simple_router_server.py
```

### Running PowerAutomation Main Service
```bash
# Start the main FastAPI service
python3 core/powerautomation_main.py

# Service will be available at http://localhost:8080
```

### Testing the Router Service
```bash
# Health check
curl -X GET http://localhost:8765/health

# List available models
curl -X GET http://localhost:8765/v1/models

# Get router statistics
curl -X GET http://localhost:8765/v1/stats

# Compare providers
curl -X GET http://localhost:8765/v1/providers/compare
```

### Testing Slash Commands
```bash
# Test slash command processing via Command MCP
python3 -c "
from core.components.command_mcp.command_manager import command_mcp
import asyncio

async def test_slash():
    await command_mcp.initialize()
    result = await command_mcp.handle_slash_command('/status')
    print(result)

asyncio.run(test_slash())
"
```

## High-Level Architecture

### Core Components Structure
- **Claude Code Router MCP**: Multi-AI model routing system that converts Claude Code requests to Kimi K2 for cost optimization (60% savings)
- **Command MCP**: Comprehensive slash command processor supporting all 18 Claude Code commands with Mirror Code fallback
- **MCP Component Manager**: Orchestrates multiple MCP components including test_mcp, stagewise_mcp, ag_ui_mcp, etc.
- **ClaudeEditor**: React-based cross-platform editor with Tauri desktop and React Native mobile implementations

### AI Model Routing Logic
The system implements intelligent model routing with the following priority:
1. **Primary**: Kimi K2 (Infini-AI) - 60% cost savings, 500 QPS
2. **Fallback**: Moonshot K2 Official - Higher stability, 60 QPS  
3. **Mirror Code Proxy**: When K2 models don't support specific Claude Code tools, requests are automatically routed through Mirror Code to Claude Code

### Slash Command Processing Flow
1. **Command Detection**: Identifies `/` prefixed commands in user input
2. **Local Processing**: Attempts to handle command with local Command MCP handlers
3. **Mirror Code Fallback**: If command unsupported, routes to Claude Code via Mirror Code integration
4. **Response Formatting**: Returns consistent response format regardless of processing path

### Configuration Management
- **Router Config**: Located at `~/.claude-code/config.json`, supports dynamic model switching
- **Environment Variables**: API keys and service endpoints configured via environment
- **Mirror Code Proxy**: Configurable fallback system for unsupported commands

## Key Development Patterns

### MCP Component Integration
All MCP components follow the pattern:
```python
class ComponentMCP:
    async def initialize(self):
        # Component initialization
    
    async def call_mcp(self, method, params):
        # Method dispatch
        
    def get_status(self):
        # Health status reporting
```

### Slash Command Handler Pattern
```python
async def _handle_command(self, args: List[str]) -> Dict[str, Any]:
    # Command processing logic
    return {
        "type": "command_type",
        "message": "Success message",
        "data": result_data
    }
```

### FastAPI Route Structure
All API routes follow OpenAI-compatible format under `/v1/` namespace with proper error handling and logging middleware.

## Important File Locations

### Core Service Files
- `core/powerautomation_main.py` - Main FastAPI service orchestrating all components
- `run_router.py` - Claude Code Router MCP startup script
- `core/components/claude_code_router_mcp/` - Complete router implementation

### Command Processing
- `core/components/command_mcp/command_manager.py` - Complete slash command processor
- `core/mirror_code/command_execution/claude_integration.py` - Mirror Code integration

### Frontend Components
- `claudeditor/src/components/SlashCommandPanel.jsx` - UI for slash command discovery
- `claudeditor/src/components/ProviderSelector.jsx` - AI model selection interface

## Environment Configuration

### Required Environment Variables
```bash
INFINI_AI_API_KEY=sk-kqbgz7fvqdutvns7  # Primary K2 provider
MOONSHOT_API_KEY=your-moonshot-api-key  # Fallback K2 provider
ANTHROPIC_API_KEY=your-anthropic-api-key  # Claude fallback
ROUTER_AUTH_TOKEN=your-router-auth-token  # Router authentication
```

### Service Dependencies
- Python 3.8+ with asyncio support
- FastAPI with uvicorn server
- httpx for HTTP client operations
- React 18+ for frontend components

## Testing Strategy

The project uses a comprehensive testing approach:
- **Unit Tests**: Component-level testing for MCP modules
- **Integration Tests**: End-to-end testing of router and command processing
- **Milestone Tests**: Validation of complete feature sets via `/test/milestone` endpoint
- **Manual Testing**: Slash command UI testing through ClaudeEditor interface

## Build and Deployment

### Development Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn httpx pydantic

# Start development servers
python3 core/powerautomation_main.py &  # Main service on :8080
python3 run_router.py &                 # Router service on :8765
```

### Production Deployment
The system is designed for enterprise deployment with Docker and Kubernetes support, featuring private AI model hosting and multi-platform client distribution through npm packages.