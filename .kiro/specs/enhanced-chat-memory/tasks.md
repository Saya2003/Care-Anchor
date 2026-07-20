# Tasks: Enhanced Chat and Memory

## Phase 1: Database Schema and Core Infrastructure

### 1.1 Database Schema Migration
- [ ] 1.1.1 Create migration script for new tables (memory_summaries, message_metadata, conversation_threads, profile_versions, clinical_trends, memory_redactions)
- [ ] 1.1.2 Add new columns to existing tables (chat_logs, sessions)
- [ ] 1.1.3 Create database indexes for performance (session_id, message_id, thread_id, importance_score)
- [ ] 1.1.4 Test migration on development database
- [ ] 1.1.5 Create rollback script for schema changes

### 1.2 Memory Summarizer Service
- [ ] 1.2.1 Implement `MemorySummarizer` class with `should_summarize()` method
- [ ] 1.2.2 Implement `generate_summary()` method with LLM integration
- [ ] 1.2.3 Implement `archive_messages()` method to mark messages as archived
- [ ] 1.2.4 Create unit tests for summarization logic
- [ ] 1.2.5 Test token count reduction (verify >80% reduction)

### 1.3 Importance Scorer Service
- [ ] 1.3.1 Implement `ImportanceScorer` class with scoring rules
- [ ] 1.3.2 Implement `score_message()` method with safety event detection
- [ ] 1.3.3 Implement `score_clinical_entry()` method for vitals, medications, symptoms
- [ ] 1.3.4 Add score clamping validation (0.0-1.0 range)
- [ ] 1.3.5 Create unit tests for each severity level

## Phase 2: Memory Services

### 2.1 Semantic Embedder Service
- [ ] 2.1.1 Add `sentence-transformers` dependency to requirements.txt
- [ ] 2.1.2 Implement `SemanticEmbedder` class with model loading
- [ ] 2.1.3 Implement `embed_message()` method to generate 384-dim vectors
- [ ] 2.1.4 Implement `search_similar()` method with cosine similarity
- [ ] 2.1.5 Add `sqlite-vec` extension integration
- [ ] 2.1.6 Create async embedding generation queue
- [ ] 2.1.7 Test embedding generation performance (<2s per message)

### 2.2 Thread Manager Service
- [ ] 2.2.1 Implement `ThreadManager` class with thread assignment logic
- [ ] 2.2.2 Implement `assign_thread()` method with semantic similarity check
- [ ] 2.2.3 Implement `get_thread_label()` method for auto-labeling
- [ ] 2.2.4 Implement `merge_threads()` method for manual operations
- [ ] 2.2.5 Create unit tests for thread assignment scenarios
- [ ] 2.2.6 Test thread similarity threshold (0.75)

### 2.3 Trend Detector Service
- [ ] 2.3.1 Add `numpy` dependency to requirements.txt
- [ ] 2.3.2 Implement `TrendDetector` class with linear regression
- [ ] 2.3.3 Implement `calculate_trends()` method for vital signs
- [ ] 2.3.4 Implement `detect_anomalies()` method for pattern detection
- [ ] 2.3.5 Add minimum data point validation (3+ points)
- [ ] 2.3.6 Create unit tests for trend direction classification
- [ ] 2.3.7 Test insufficient data handling

### 2.4 Version Manager Service
- [ ] 2.4.1 Implement `VersionManager` class with snapshot creation
- [ ] 2.4.2 Implement `create_version()` method with diff generation
- [ ] 2.4.3 Implement `get_versions()` method with version history
- [ ] 2.4.4 Implement `restore_version()` method with rollback support
- [ ] 2.4.5 Add version retention logic (last 10 versions)
- [ ] 2.4.6 Create unit tests for version operations
- [ ] 2.4.7 Test rollback creates new version with metadata

### 2.5 Deduplicator Service
- [ ] 2.5.1 Implement `Deduplicator` class with duplicate detection
- [ ] 2.5.2 Implement `check_duplicate()` method for medications and symptoms
- [ ] 2.5.3 Implement `merge_duplicates()` method with timestamp update
- [ ] 2.5.4 Add medication exact match logic (name + dosage)
- [ ] 2.5.5 Add symptom similarity logic (90% threshold within 24 hours)
- [ ] 2.5.6 Create unit tests for deduplication rules
- [ ] 2.5.7 Test vitals and safety events are never deduplicated

## Phase 3: Memory Store Integration

### 3.1 Extend Memory Store Class
- [ ] 3.1.1 Add `get_summaries()` method to retrieve summaries for session
- [ ] 3.1.2 Add `create_summary()` method to persist summary in database
- [ ] 3.1.3 Add `get_context_with_summaries()` method for response generation
- [ ] 3.1.4 Add `assign_importance_score()` method during append_chat
- [ ] 3.1.5 Add `get_prioritized_context()` method sorted by importance
- [ ] 3.1.6 Modify `append_chat()` to trigger background embedding generation
- [ ] 3.1.7 Create integration tests for memory store operations

### 3.2 Context Window Management
- [ ] 3.2.1 Implement token counting utility for context assembly
- [ ] 3.2.2 Implement prioritization logic (importance + recency + current thread)
- [ ] 3.2.3 Add 4000 token limit enforcement
- [ ] 3.2.4 Add summary inclusion logic for archived messages
- [ ] 3.2.5 Add safety events always-include logic
- [ ] 3.2.6 Create tests for token budget scenarios
- [ ] 3.2.7 Benchmark context assembly performance (<200ms)

## Phase 4: Agent Pipeline Integration

### 4.1 Agent Graph Modifications
- [ ] 4.1.1 Modify `run_agent()` to check message count before context assembly
- [ ] 4.1.2 Add summarization trigger when threshold (20 messages) exceeded
- [ ] 4.1.3 Integrate importance scorer in `apply_memory_update()` node
- [ ] 4.1.4 Integrate thread manager for message assignment
- [ ] 4.1.5 Add version creation on profile updates
- [ ] 4.1.6 Add deduplicator check before profile update
- [ ] 4.1.7 Test end-to-end agent flow with new services

### 4.2 Clinical Responder Updates
- [ ] 4.2.1 Modify context retrieval to use prioritized summaries
- [ ] 4.2.2 Add trend information to profile context
- [ ] 4.2.3 Add thread context to response generation
- [ ] 4.2.4 Test response quality with summarized context
- [ ] 4.2.5 Verify clinical facts preserved in responses

## Phase 5: REST API Endpoints

### 5.1 Memory Search API
- [ ] 5.1.1 Create `/api/memory/search` POST endpoint
- [ ] 5.1.2 Add request validation (query length, filters)
- [ ] 5.1.3 Integrate semantic embedder for query execution
- [ ] 5.1.4 Add pagination support with configurable page size
- [ ] 5.1.5 Add filters (date range, importance threshold, memory type)
- [ ] 5.1.6 Return results with message content, timestamp, clinical data
- [ ] 5.1.7 Test response time (<500ms for 20 results)
- [ ] 5.1.8 Add error handling for invalid queries (HTTP 400)

### 5.2 Conversation Export API
- [ ] 5.2.1 Create `/api/sessions/{session_id}/export` GET endpoint
- [ ] 5.2.2 Add format parameter (json, pdf, text)
- [ ] 5.2.3 Implement JSON export with full message history
- [ ] 5.2.4 Implement text export with formatted output
- [ ] 5.2.5 Implement PDF export using `reportlab` library
- [ ] 5.2.6 Add session metadata (timestamp, session_id) to exports
- [ ] 5.2.7 Add error handling for non-existent sessions (HTTP 404)
- [ ] 5.2.8 Test each export format

### 5.3 Memory Management API
- [ ] 5.3.1 Create `/api/memory/redact` POST endpoint for redaction
- [ ] 5.3.2 Create `/api/memory/undo-redact` POST endpoint for undo
- [ ] 5.3.3 Create `/api/memory/versions/{session_id}` GET endpoint
- [ ] 5.3.4 Create `/api/memory/restore` POST endpoint for rollback
- [ ] 5.3.5 Create `/api/memory/extend-retention` POST endpoint
- [ ] 5.3.6 Add audit logging for all memory operations
- [ ] 5.3.7 Test redaction replaces content with "[REDACTED]"
- [ ] 5.3.8 Test undo redaction within 30-day window

### 5.4 Thread Management API
- [ ] 5.4.1 Create `/api/threads/{session_id}` GET endpoint
- [ ] 5.4.2 Create `/api/threads/merge` POST endpoint
- [ ] 5.4.3 Create `/api/threads/split` POST endpoint
- [ ] 5.4.4 Create `/api/threads/{thread_id}/rename` PUT endpoint
- [ ] 5.4.5 Test thread operations maintain message integrity

### 5.5 Trends API
- [ ] 5.5.1 Create `/api/trends/{session_id}` GET endpoint
- [ ] 5.5.2 Add vital_type filter parameter
- [ ] 5.5.3 Return trend direction, rate of change, data points
- [ ] 5.5.4 Test insufficient data response
- [ ] 5.5.5 Test trend caching (1 hour TTL)

## Phase 6: Frontend Components

### 6.1 Enhanced Chat History Sidebar
- [ ] 6.1.1 Add search input field at top of sidebar
- [ ] 6.1.2 Add importance indicator (colored dots) to sessions
- [ ] 6.1.3 Add thread badges to conversation entries
- [ ] 6.1.4 Add export button on session hover
- [ ] 6.1.5 Integrate with search API on query submission
- [ ] 6.1.6 Display search results with relevance scores
- [ ] 6.1.7 Test search UX with 50+ messages

### 6.2 Memory Search UI Component
- [ ] 6.2.1 Create `MemorySearchPanel` component
- [ ] 6.2.2 Add search input with filters (date range, importance)
- [ ] 6.2.3 Display search results with message preview
- [ ] 6.2.4 Add click-to-navigate to original message in chat
- [ ] 6.2.5 Add loading and empty states
- [ ] 6.2.6 Test search interaction flow

### 6.3 Clinical Profile Viewer Enhancements
- [ ] 6.3.1 Add trend indicators (arrows) to vital signs display
- [ ] 6.3.2 Add trend chart visualization using charting library
- [ ] 6.3.3 Add version history dropdown
- [ ] 6.3.4 Add rollback confirmation dialog
- [ ] 6.3.5 Display importance scores on memory entries
- [ ] 6.3.6 Test trend visualization with multiple data points

### 6.4 Export Dialog Component
- [ ] 6.4.1 Create `ExportDialog` component with format selection
- [ ] 6.4.2 Add download button triggering export API
- [ ] 6.4.3 Show export progress indicator
- [ ] 6.4.4 Handle export errors gracefully
- [ ] 6.4.5 Test PDF download in browser

### 6.5 Thread Management UI
- [ ] 6.5.1 Add thread labels to messages in chat interface
- [ ] 6.5.2 Add thread filter dropdown in sidebar
- [ ] 6.5.3 Add manual thread assignment UI (right-click menu)
- [ ] 6.5.4 Add thread merge confirmation dialog
- [ ] 6.5.5 Test thread visual separation

## Phase 7: Background Jobs and Retention

### 7.1 Embedding Generation Job
- [ ] 7.1.1 Create background worker for async embedding generation
- [ ] 7.1.2 Add queue management (pending embeddings queue)
- [ ] 7.1.3 Add retry logic for failed embeddings
- [ ] 7.1.4 Monitor queue length and processing rate
- [ ] 7.1.5 Test backfill of existing messages

### 7.2 Summarization Job
- [ ] 7.2.1 Create background job triggered at message threshold
- [ ] 7.2.2 Add summarization queue for concurrent sessions
- [ ] 7.2.3 Add retry with exponential backoff
- [ ] 7.2.4 Add fallback to keep original messages after 3 failures
- [ ] 7.2.5 Monitor summarization success rate

### 7.3 Retention Policy Job
- [ ] 7.3.1 Create scheduled job for retention enforcement (daily)
- [ ] 7.3.2 Implement archive-to-cold-storage for expired data
- [ ] 7.3.3 Add preservation logic for critical safety events
- [ ] 7.3.4 Add extension check for retention_extended_until
- [ ] 7.3.5 Log all retention actions
- [ ] 7.3.6 Test retention periods (90 days chat, 30 days versions)

### 7.4 Trend Calculation Job
- [ ] 7.4.1 Create scheduled job for trend updates (hourly)
- [ ] 7.4.2 Calculate trends for all sessions with 3+ data points
- [ ] 7.4.3 Cache trend results with 1-hour TTL
- [ ] 7.4.4 Invalidate cache on new vital entry
- [ ] 7.4.5 Monitor calculation performance

## Phase 8: Testing and Quality Assurance

### 8.1 Unit Tests
- [ ] 8.1.1 Complete unit test coverage for all service classes
- [ ] 8.1.2 Test edge cases (empty inputs, boundary values)
- [ ] 8.1.3 Test error handling paths
- [ ] 8.1.4 Achieve >80% code coverage
- [ ] 8.1.5 Run tests in CI pipeline

### 8.2 Integration Tests
- [ ] 8.2.1 Test end-to-end summarization flow
- [ ] 8.2.2 Test search with embedding generation
- [ ] 8.2.3 Test version management operations
- [ ] 8.2.4 Test API endpoints with real database
- [ ] 8.2.5 Test agent pipeline with all services integrated

### 8.3 Performance Tests
- [ ] 8.3.1 Benchmark context assembly with 100-message sessions
- [ ] 8.3.2 Benchmark search queries with 1000+ messages
- [ ] 8.3.3 Benchmark embedding generation rate
- [ ] 8.3.4 Benchmark trend calculation with 50+ measurements
- [ ] 8.3.5 Verify all operations meet performance targets

### 8.4 Manual Testing
- [ ] 8.4.1 Test long conversation flow (25+ messages)
- [ ] 8.4.2 Test trend detection with real vital data
- [ ] 8.4.3 Test search and export workflows
- [ ] 8.4.4 Test redaction and rollback operations
- [ ] 8.4.5 Test UI components in browser

## Phase 9: Documentation and Deployment

### 9.1 Documentation
- [ ] 9.1.1 Document new API endpoints (OpenAPI spec)
- [ ] 9.1.2 Update user guide with search and export features
- [ ] 9.1.3 Create admin guide for retention policy management
- [ ] 9.1.4 Document configuration options
- [ ] 9.1.5 Create migration guide for existing deployments

### 9.2 Configuration
- [ ] 9.2.1 Add configuration file for summarization settings
- [ ] 9.2.2 Add configuration file for search settings
- [ ] 9.2.3 Add configuration file for retention settings
- [ ] 9.2.4 Add environment variable overrides
- [ ] 9.2.5 Document all configuration options

### 9.3 Deployment
- [ ] 9.3.1 Run schema migration on production database (with backup)
- [ ] 9.3.2 Deploy backend services with new dependencies
- [ ] 9.3.3 Deploy frontend components
- [ ] 9.3.4 Start background jobs (embedding, retention)
- [ ] 9.3.5 Monitor system after deployment
- [ ] 9.3.6 Backfill embeddings for existing messages
- [ ] 9.3.7 Verify backward compatibility with existing sessions

### 9.4 Monitoring
- [ ] 9.4.1 Add metrics for summarization trigger rate
- [ ] 9.4.2 Add metrics for search query latency
- [ ] 9.4.3 Add metrics for embedding queue length
- [ ] 9.4.4 Add alerts for performance degradation
- [ ] 9.4.5 Add dashboard for storage usage tracking
