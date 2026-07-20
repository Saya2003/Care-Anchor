# Requirements Document: Enhanced Chat and Memory

## Introduction

CareAnchor is a post-discharge clinical assistant that helps patients recover at home through conversational AI. The current system maintains clinical profiles (vitals, medications, symptoms) and chat history in a basic append-only format. As conversations grow, memory context becomes unwieldy, important information becomes buried, and there is no way to prioritize, search, or summarize clinical information over time.

This feature enhances the chat interface and clinical memory system by adding conversation summarization, memory importance scoring, semantic search capabilities, conversation threading, and memory versioning. These improvements will allow patients and caregivers to quickly access relevant clinical history, understand trends over time, and maintain context even across long conversations.

## Glossary

- **Memory_Store**: The persistence layer that stores clinical profiles, chat history, and safety events in SQLite
- **Clinical_Profile**: Structured clinical data including vitals, medications, symptoms, and care plans
- **Chat_History**: Chronological sequence of user and assistant messages within a session
- **Memory_Refiner**: Agent that extracts structured clinical data from natural language messages
- **Session**: A single conversation instance identified by a unique session_id
- **Memory_Segment**: A time-bounded or topic-bounded group of related messages and clinical observations
- **Importance_Score**: A numeric value (0.0 to 1.0) indicating the clinical relevance of a memory entry
- **Memory_Summary**: A condensed representation of multiple messages preserving key clinical information
- **Semantic_Index**: Vector embeddings of clinical memories enabling similarity-based retrieval
- **Memory_Version**: A snapshot of the Clinical_Profile at a specific point in time
- **Conversation_Thread**: A logically grouped sequence of messages related to a specific topic or concern
- **Safety_Event**: A clinical alert triggered when vital signs breach safety thresholds
- **Clinical_Trend**: Time-series analysis of repeated vital signs or symptom measurements

## Requirements

### Requirement 1: Memory Summarization

**User Story:** As a patient, I want the system to summarize long conversation history, so that context windows remain manageable and relevant information is preserved without overwhelming the AI.

#### Acceptance Criteria

1. WHEN Chat_History exceeds 20 messages, THE Memory_Store SHALL generate a Memory_Summary containing key clinical facts from the oldest 10 messages
2. THE Memory_Summary SHALL preserve all vitals, medications, symptoms, and safety events from the summarized messages
3. THE Memory_Summary SHALL exclude conversational pleasantries and non-clinical dialogue
4. WHEN a Memory_Summary is created, THE Memory_Store SHALL mark the original messages as archived
5. THE Memory_Store SHALL provide the Memory_Summary to the Clinical_Responder in place of archived messages
6. THE Memory_Summary SHALL include temporal context indicating the time range covered

### Requirement 2: Memory Importance Scoring

**User Story:** As a healthcare provider reviewing patient history, I want clinically significant information prioritized, so that I can quickly identify critical changes and trends.

#### Acceptance Criteria

1. WHEN the Memory_Refiner extracts clinical data, THE Memory_Store SHALL assign an Importance_Score to each memory entry
2. THE Importance_Score SHALL range from 0.0 (routine) to 1.0 (critical)
3. THE Memory_Store SHALL assign Importance_Score above 0.8 when vitals breach safety thresholds
4. THE Memory_Store SHALL assign Importance_Score above 0.6 when new medications are reported
5. THE Memory_Store SHALL assign Importance_Score above 0.7 when severe symptoms are reported
6. WHEN retrieving memory context, THE Memory_Store SHALL prioritize entries with higher Importance_Score
7. THE Clinical_Profile SHALL display memory entries sorted by Importance_Score in descending order

### Requirement 3: Semantic Memory Search

**User Story:** As a patient, I want to search my clinical history using natural language, so that I can quickly find when I last reported specific symptoms or vital readings.

#### Acceptance Criteria

1. THE Memory_Store SHALL generate Semantic_Index embeddings for all clinical memory entries
2. WHEN a user submits a search query, THE Memory_Store SHALL retrieve the top 5 most semantically similar memory entries
3. THE Memory_Store SHALL return search results with relevance scores above 0.7
4. THE search results SHALL include the original message text, timestamp, and extracted clinical data
5. WHEN no relevant memories are found, THE Memory_Store SHALL return an empty result set
6. THE Semantic_Index SHALL update within 2 seconds when new clinical data is extracted

### Requirement 4: Conversation Threading

**User Story:** As a patient managing multiple health concerns, I want conversations organized by topic, so that I can track specific issues independently without confusion.

#### Acceptance Criteria

1. THE Memory_Store SHALL group messages into Conversation_Threads based on topic similarity
2. WHEN a new message is received, THE Memory_Store SHALL assign it to an existing Conversation_Thread or create a new thread
3. THE Memory_Store SHALL assign a descriptive label to each Conversation_Thread based on the primary clinical topic
4. THE Chat_History SHALL display Conversation_Threads with visual separation in the user interface
5. THE Memory_Store SHALL allow users to manually merge or split Conversation_Threads
6. WHEN retrieving context for a response, THE Memory_Store SHALL prioritize messages from the current Conversation_Thread

### Requirement 5: Memory Versioning and Rollback

**User Story:** As a system administrator handling data correction requests, I want to view and restore previous versions of clinical profiles, so that incorrect extractions can be corrected without data loss.

#### Acceptance Criteria

1. WHEN the Clinical_Profile is updated, THE Memory_Store SHALL create a new Memory_Version with a timestamp
2. THE Memory_Store SHALL retain the previous 10 Memory_Versions for each Session
3. THE Memory_Store SHALL provide an API endpoint to retrieve all Memory_Versions for a Session
4. THE Memory_Store SHALL provide an API endpoint to restore a specific Memory_Version
5. WHEN a Memory_Version is restored, THE Memory_Store SHALL create a new Memory_Version marking it as a rollback operation
6. THE Memory_Version SHALL include metadata indicating which agent or user triggered the update

### Requirement 6: Clinical Trend Detection

**User Story:** As a patient monitoring my recovery, I want to see trends in my vital signs over time, so that I can understand whether my condition is improving or worsening.

#### Acceptance Criteria

1. WHEN the Clinical_Profile contains 3 or more measurements of the same vital sign, THE Memory_Store SHALL calculate a Clinical_Trend
2. THE Clinical_Trend SHALL indicate whether the vital sign is improving, stable, or worsening
3. THE Clinical_Trend SHALL include the rate of change per day for each vital sign
4. THE Memory_Store SHALL flag Clinical_Trends showing worsening conditions with Importance_Score above 0.75
5. THE Clinical_Profile SHALL display Clinical_Trends visually using trend indicators (up arrow, down arrow, flat line)
6. WHEN a Clinical_Trend shows significant worsening, THE Memory_Store SHALL notify the Clinical_Responder to acknowledge it in the response

### Requirement 7: Memory Context Window Management

**User Story:** As the AI responder, I want relevant memory context within token budget, so that I can generate accurate responses without exceeding model limits.

#### Acceptance Criteria

1. THE Memory_Store SHALL retrieve memory context not exceeding 4000 tokens for each response generation
2. WHEN memory context exceeds 4000 tokens, THE Memory_Store SHALL prioritize entries by Importance_Score and recency
3. THE Memory_Store SHALL include the current Conversation_Thread messages with highest priority
4. THE Memory_Store SHALL include Memory_Summaries for archived conversations
5. THE Memory_Store SHALL include recent Safety_Events regardless of token count
6. WHEN token budget is constrained, THE Memory_Store SHALL truncate lower-priority routine messages

### Requirement 8: Memory Search API

**User Story:** As a frontend developer, I want a search API for clinical memories, so that users can query their history through the user interface.

#### Acceptance Criteria

1. THE Memory_Store SHALL expose a REST API endpoint accepting natural language search queries
2. THE API endpoint SHALL return search results in JSON format with message content, timestamp, and clinical data
3. THE API endpoint SHALL support pagination with configurable page size
4. THE API endpoint SHALL accept filters for date range, importance threshold, and memory type
5. WHEN an invalid search query is received, THE API endpoint SHALL return an HTTP 400 error with a descriptive message
6. THE API endpoint SHALL respond within 500 milliseconds for queries returning up to 20 results

### Requirement 9: Conversation Export

**User Story:** As a patient preparing for a doctor's appointment, I want to export my conversation history, so that I can share my recovery progress with my healthcare provider.

#### Acceptance Criteria

1. THE Memory_Store SHALL provide an API endpoint to export complete conversation history for a Session
2. THE export SHALL include all messages, clinical data extractions, and Safety_Events in chronological order
3. THE Memory_Store SHALL support export formats including JSON, PDF, and plain text
4. THE PDF export SHALL format clinical data in a table structure for readability
5. THE export SHALL include a timestamp and Session identifier
6. WHEN export is requested for a non-existent Session, THE Memory_Store SHALL return an HTTP 404 error

### Requirement 10: Memory Deduplication

**User Story:** As a patient who sometimes repeats information, I want the system to detect and merge duplicate clinical data, so that my profile remains accurate without redundant entries.

#### Acceptance Criteria

1. WHEN the Memory_Refiner extracts clinical data, THE Memory_Store SHALL check for duplicate entries in the Clinical_Profile
2. THE Memory_Store SHALL consider medications with identical names and dosages as duplicates
3. THE Memory_Store SHALL consider symptoms with identical descriptions reported within 24 hours as duplicates
4. WHEN a duplicate is detected, THE Memory_Store SHALL update the timestamp of the existing entry instead of creating a new entry
5. THE Memory_Store SHALL log all deduplication actions for audit purposes
6. THE Memory_Store SHALL preserve all duplicate vitals measurements as these represent time-series data

### Requirement 11: Memory Privacy and Redaction

**User Story:** As a patient concerned about privacy, I want to redact sensitive personal information from memory, so that I can share clinical data without exposing private details.

#### Acceptance Criteria

1. THE Memory_Store SHALL provide an API endpoint to mark specific messages or memory entries as redacted
2. WHEN a memory entry is redacted, THE Memory_Store SHALL replace the content with placeholder text "[REDACTED]"
3. THE redacted memory entry SHALL remain in the database for audit purposes but SHALL NOT be included in exported conversations
4. THE Memory_Store SHALL allow users to undo redaction within 30 days
5. THE Memory_Store SHALL log all redaction and un-redaction operations with timestamps and user identifiers
6. WHEN a message is redacted, THE Memory_Store SHALL preserve the associated clinical data extractions unless explicitly deleted

### Requirement 12: Memory Retention Policy

**User Story:** As a system administrator managing storage costs, I want configurable retention policies for old conversations, so that the database does not grow indefinitely while preserving clinically relevant data.

#### Acceptance Criteria

1. THE Memory_Store SHALL support configurable retention periods for Chat_History, Memory_Versions, and Safety_Events
2. THE default retention period SHALL be 90 days for archived Chat_History and 30 days for Memory_Versions
3. WHEN retention period expires, THE Memory_Store SHALL archive the data to cold storage before deletion
4. THE Memory_Store SHALL never delete Clinical_Profile data or Safety_Events marked as critical
5. THE Memory_Store SHALL provide an API endpoint to extend retention period for specific Sessions
6. WHEN data is archived, THE Memory_Store SHALL create a Memory_Summary preserving key clinical facts

