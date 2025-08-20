---
description: 'Comprehensive development guidelines for Archon multi-agent knowledge management system'
applyTo: '**/*'
---

# Archon Multi-Agent Development Instructions

## Project Overview

Archon V2 Alpha is a microservices-based knowledge management system with MCP (Model Context Protocol) integration designed for local-only deployment. Each user runs their own instance focusing on rapid iteration and feature development.

### Core Architecture

- **Frontend (port 3737)**: React + TypeScript + Vite + TailwindCSS
- **Main Server (port 8181)**: FastAPI + Socket.IO for real-time updates  
- **MCP Server (port 8051)**: Lightweight HTTP-based MCP protocol server
- **Agents Service (port 8052)**: PydanticAI agents for AI/ML operations
- **Database**: Supabase (PostgreSQL + pgvector for embeddings)

## Alpha Development Philosophy

### Core Principles

- **No backwards compatibility** - remove deprecated code immediately
- **Detailed errors over graceful failures** - identify and fix issues fast
- **Break things to improve them** - alpha is for rapid iteration
- **Local-only deployment** - each user runs their own instance

### Error Handling Strategy

**Critical Decision Framework**: Intelligently decide when to fail fast vs. complete with detailed logging.

#### Fail Fast and Loud (Let it Crash!)

Stop execution immediately for:
- Service startup failures (credentials, database, services can't initialize)
- Missing configuration (environment variables, invalid settings)
- Database connection failures
- Authentication/authorization failures
- Data corruption or validation errors
- Critical dependencies unavailable
- Invalid data that would corrupt state

#### Complete but Log Detailed Errors

Continue processing but track failures for:
- Batch processing (crawling, document processing)
- Background tasks (embedding generation, async jobs)
- WebSocket events
- Optional features (when projects/tasks disabled)
- External API calls (with exponential backoff)

**Never Accept Corrupted Data**: Skip failed items entirely rather than storing corrupted data.

```python
# ✅ CORRECT - Skip Failed Items
try:
    embedding = create_embedding(text)
    store_document(doc, embedding)  # Only store on success
except Exception as e:
    failed_items.append({'doc': doc, 'error': str(e)})
    logger.error(f"Skipping document {doc.id}: {e}")
    # Continue with next document, don't store anything

# ❌ WRONG - Silent Corruption
try:
    embedding = create_embedding(text)
except Exception as e:
    embedding = [0.0] * 1536  # NEVER DO THIS
    store_document(doc, embedding)
```

## Python Development Standards

### Code Quality Requirements

- **Python 3.12** with 120 character line length
- **Ruff** for linting and formatting
- **Mypy** for type checking
- **uv** for dependency management

### FastAPI Patterns

```python
# Route handler structure
@router.post("/api/endpoint")
async def endpoint_handler(
    request: RequestModel,
    db: AsyncSession = Depends(get_db)
) -> ResponseModel:
    """
    Clear docstring describing the endpoint purpose.
    
    Args:
        request: Description of request model
        db: Database session dependency
        
    Returns:
        ResponseModel: Description of response
        
    Raises:
        HTTPException: When validation fails
    """
    try:
        result = await service_function(request.data, db)
        return ResponseModel(data=result)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Service Layer Patterns

```python
# Service function structure
async def service_function(
    data: InputType,
    db: AsyncSession,
    user_context: Optional[UserContext] = None
) -> OutputType:
    """
    Business logic with clear separation of concerns.
    
    Args:
        data: Input data with proper typing
        db: Database session for operations
        user_context: Optional user context for auth
        
    Returns:
        OutputType: Processed result
        
    Raises:
        ServiceError: When business logic fails
        ValidationError: When data validation fails
    """
    # Validate inputs
    if not data.is_valid():
        raise ValidationError("Invalid input data")
    
    # Business logic
    result = await process_data(data, db)
    
    # Return typed result
    return OutputType(result=result)
```

### Database Patterns

```python
# Use async/await for all database operations
async def get_documents_by_source(
    source_id: int,
    db: AsyncSession,
    limit: int = 10,
    offset: int = 0
) -> list[Document]:
    """Get documents by source with pagination."""
    query = select(Document).where(Document.source_id == source_id)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()

# Use proper error handling
async def create_document(
    document_data: DocumentCreate,
    db: AsyncSession
) -> Document:
    """Create new document with error handling."""
    try:
        document = Document(**document_data.model_dump())
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document
    except IntegrityError as e:
        await db.rollback()
        raise ServiceError(f"Document creation failed: {e}")
```

### Testing Patterns

```python
# Use pytest with async support
@pytest.mark.asyncio
async def test_service_function():
    """Test service function with proper mocking."""
    # Arrange
    mock_data = create_test_data()
    mock_db = AsyncMock()
    
    # Act
    result = await service_function(mock_data, mock_db)
    
    # Assert
    assert result.is_valid()
    assert result.data == expected_data
    mock_db.execute.assert_called_once()
```

## TypeScript/React Development Standards

### Component Structure

```typescript
// Use functional components with proper typing
interface ComponentProps {
  data: DataType;
  onAction: (id: string) => void;
  className?: string;
}

export const Component: React.FC<ComponentProps> = ({ 
  data, 
  onAction, 
  className = "" 
}) => {
  // Use custom hooks for state management
  const { state, actions } = useComponentState(data);
  
  // Handle events with proper typing
  const handleClick = useCallback((id: string) => {
    onAction(id);
    actions.updateState(id);
  }, [onAction, actions]);
  
  return (
    <div className={`component-base ${className}`}>
      {/* Component JSX */}
    </div>
  );
};
```

### Service Layer (Frontend)

```typescript
// API service with proper error handling
class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    try {
      const response = await fetch(`/api${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });
      
      if (!response.ok) {
        throw new ApiError(`API request failed: ${response.statusText}`);
      }
      
      return response.json();
    } catch (error) {
      logger.error(`API request failed: ${error}`);
      throw error;
    }
  }
  
  async getData(id: string): Promise<DataType> {
    return this.request<DataType>(`/data/${id}`);
  }
}
```

### Custom Hooks

```typescript
// Custom hook with proper state management
export const useDataFetching = (id: string) => {
  const [data, setData] = useState<DataType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiService.getData(id);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [id]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  return { data, loading, error, refetch: fetchData };
};
```

## MCP (Model Context Protocol) Development

### MCP Tool Implementation

```python
# MCP tool with proper structure
@mcp_server.tool("archon:perform_rag_query")
async def perform_rag_query(
    query: str,
    limit: int = 5,
    source_filter: Optional[str] = None
) -> MCPResult:
    """
    Perform RAG query against knowledge base.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        source_filter: Optional source ID filter
        
    Returns:
        MCPResult: Formatted search results
    """
    try:
        # Validate inputs
        if not query.strip():
            raise ValueError("Query cannot be empty")
            
        # Perform search
        results = await search_service.semantic_search(
            query=query,
            limit=limit,
            source_filter=source_filter
        )
        
        # Format results for MCP
        return MCPResult(
            success=True,
            data=results,
            message=f"Found {len(results)} results"
        )
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        return MCPResult(
            success=False,
            error=str(e),
            message="RAG query failed"
        )
```

## Socket.IO Real-time Updates

### Backend WebSocket Patterns

```python
# Socket.IO event handling
@sio.event
async def connect(sid: str, environ: dict):
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")
    await sio.emit('connection_status', {'status': 'connected'}, room=sid)

@sio.event
async def disconnect(sid: str):
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {sid}")

# Emit progress updates
async def emit_progress(
    event_type: str,
    progress: dict,
    room: Optional[str] = None
):
    """Emit progress updates to clients."""
    await sio.emit(event_type, {
        'timestamp': datetime.utcnow().isoformat(),
        'progress': progress
    }, room=room)
```

### Frontend WebSocket Integration

```typescript
// Socket.IO client with proper typing
interface SocketEvents {
  crawl_progress: (data: CrawlProgress) => void;
  project_creation_progress: (data: ProjectProgress) => void;
  task_update: (data: TaskUpdate) => void;
}

export const useSocketIO = () => {
  const [socket, setSocket] = useState<Socket | null>(null);
  
  useEffect(() => {
    const newSocket = io('http://localhost:8181');
    
    newSocket.on('connect', () => {
      console.log('Connected to server');
    });
    
    setSocket(newSocket);
    
    return () => {
      newSocket.close();
    };
  }, []);
  
  const emitEvent = useCallback((event: string, data: any) => {
    socket?.emit(event, data);
  }, [socket]);
  
  return { socket, emitEvent };
};
```

## Testing Strategies

### Backend Testing

```python
# API endpoint testing
@pytest.mark.asyncio
async def test_api_endpoint(client: TestClient, mock_db: AsyncSession):
    """Test API endpoint with proper setup."""
    # Arrange
    test_data = {"key": "value"}
    expected_response = {"result": "success"}
    
    # Act
    response = await client.post("/api/endpoint", json=test_data)
    
    # Assert
    assert response.status_code == 200
    assert response.json() == expected_response

# Service testing with mocks
@pytest.mark.asyncio
async def test_service_function(mock_db: AsyncSession):
    """Test service function with database mocking."""
    # Mock database responses
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        mock_document()
    ]
    
    # Test service function
    result = await service_function(test_input, mock_db)
    
    assert result is not None
    assert len(result) == 1
```

### Frontend Testing

```typescript
// Component testing with React Testing Library
describe('Component', () => {
  it('renders correctly with data', () => {
    const mockData = { id: '1', title: 'Test' };
    const mockOnAction = jest.fn();
    
    render(
      <Component data={mockData} onAction={mockOnAction} />
    );
    
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
  
  it('handles user interactions', async () => {
    const mockOnAction = jest.fn();
    
    render(
      <Component data={mockData} onAction={mockOnAction} />
    );
    
    await user.click(screen.getByRole('button'));
    
    expect(mockOnAction).toHaveBeenCalledWith('1');
  });
});
```

## File Organization Patterns

### Backend Structure

```
python/src/
├── server/
│   ├── main.py              # FastAPI app entry point
│   ├── api_routes/          # Route handlers
│   │   ├── knowledge_api.py
│   │   ├── projects_api.py
│   │   └── tasks_api.py
│   ├── services/            # Business logic
│   │   ├── knowledge/
│   │   ├── projects/
│   │   └── tasks/
│   ├── models/              # Database models
│   └── dependencies/        # FastAPI dependencies
├── mcp/                     # MCP server implementation
├── agents/                  # PydanticAI agents
└── tests/                   # Test files
```

### Frontend Structure

```
archon-ui-main/src/
├── components/              # Reusable UI components
│   ├── ui/                 # Base UI components
│   ├── knowledge/          # Knowledge-specific components
│   └── projects/           # Project-specific components
├── pages/                   # Main application pages
├── services/                # API communication
├── hooks/                   # Custom React hooks
├── contexts/                # React context providers
└── types/                   # TypeScript type definitions
```

## Development Workflow

### Adding New Features

1. **API Development**:
   - Create route handler in `python/src/server/api_routes/`
   - Add service logic in `python/src/server/services/`
   - Include router in `python/src/server/main.py`
   - Write tests in `python/tests/`

2. **Frontend Development**:
   - Create component in `archon-ui-main/src/components/`
   - Add to page in `archon-ui-main/src/pages/`
   - Update service in `archon-ui-main/src/services/`
   - Add tests in `archon-ui-main/test/`

3. **MCP Integration**:
   - Implement tool in `python/src/mcp/`
   - Add to tool registry
   - Test via UI MCP page

### Code Quality Checks

```bash
# Backend checks
cd python/
uv run ruff check          # Linting
uv run ruff format         # Formatting
uv run mypy src/           # Type checking
uv run pytest             # Testing

# Frontend checks
cd archon-ui-main/
npm run lint               # ESLint
npm run test               # Vitest tests
npm run test:coverage      # Coverage report
```

## Common Patterns and Best Practices

### Database Operations

- Always use async/await for database operations
- Use proper transaction handling with rollback on errors
- Implement pagination for large datasets
- Use typed models with Pydantic for validation

### API Design

- Follow RESTful conventions
- Use proper HTTP status codes
- Include detailed error messages
- Implement rate limiting for public endpoints
- Use dependency injection for database sessions

### Real-time Features

- Use Socket.IO for real-time updates
- Emit progress events for long-running operations
- Handle connection failures gracefully
- Implement room-based messaging for user isolation

### Security Considerations

- Validate all input data
- Use parameterized queries to prevent SQL injection
- Implement proper authentication for sensitive operations
- Log security-related events

### Performance Optimization

- Use connection pooling for database access
- Implement caching for frequently accessed data
- Use lazy loading for large datasets
- Optimize embeddings and vector searches
- Monitor performance with detailed logging

Remember: This is alpha software focused on rapid iteration and user experience. Prioritize functionality and clear error messages over production-ready patterns.