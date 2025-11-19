# CLAUDE.md - AI Assistant Guide for agt_suporte_gynprog

## Project Overview

**agt_suporte_gynprog** is an intelligent customer support automation system built on n8n that provides AI-powered WhatsApp support for Gynprog using Meta's WhatsApp Business API.

### Technology Stack
- **Automation Platform**: n8n (workflow automation)
- **Messaging**: Meta WhatsApp Business API (Graph API v20.0+)
- **AI/ML**: OpenAI (GPT-4o-mini, text-embedding-3-large)
- **Vector Database**: Pinecone (for semantic search)
- **Relational Database**: PostgreSQL (client memory & message history)
- **Language**: JavaScript (n8n Function nodes)

### Current Version
- **Latest**: v5.004 (security-hardened, production-ready)
- **Tagged**: `official`, `security-hardened`, `gynprog`, `memoria`

---

## Repository Structure

```
agt_suporte_gynprog/
├── agt_suporte_gynprog_v5.002.json  # Legacy (SQL injection vulnerabilities)
├── agt_suporte_gynprog_v5.003.json  # Security-hardened version
├── agt_suporte_gynprog_v5_004.json  # Latest production version
└── CLAUDE.md                         # This file
```

### Workflow Files
All workflow files are n8n JSON exports containing:
- **Nodes**: Individual processing units (webhooks, functions, API calls, database queries)
- **Connections**: Data flow between nodes
- **Credentials**: References to stored credentials (PostgreSQL, OpenAI, Pinecone, Meta)
- **Configuration**: Environment-based settings

---

## Architecture & Data Flow

### High-Level Architecture

```
┌─────────────────┐
│  WhatsApp User  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Meta WhatsApp Business API          │
│         (Webhook: /meta)                    │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│              n8n Workflow                   │
│  ┌─────────────────────────────────────┐   │
│  │ 1. Carregar Config Meta             │   │
│  │ 2. Webhook Verification (GET)       │   │
│  │ 3. Preparar Evento Meta (POST)      │   │
│  │ 4. Validar Assinatura (HMAC SHA256) │   │
│  │ 5. Roteamento Assinatura            │   │
│  └─────────────────────────────────────┘   │
│                    │                        │
│         ┌──────────┴──────────┐             │
│         ▼                     ▼             │
│  ┌──────────────┐      ┌──────────────┐    │
│  │   Messages   │      │   Statuses   │    │
│  └──────┬───────┘      └──────┬───────┘    │
│         │                     │             │
│         ▼                     │             │
│  ┌──────────────────────┐    │             │
│  │ Normalizar Mensagem  │    │             │
│  │ Rate Limit Check     │    │             │
│  └──────┬───────────────┘    │             │
│         │                     │             │
│         ▼                     │             │
│  ┌────────────────────────────────┐        │
│  │   Parallel Context Retrieval   │        │
│  │  • PostgreSQL: Buscar Memoria  │        │
│  │  • PostgreSQL: Mensagens Recent│        │
│  │  • OpenAI: Embedding           │        │
│  │    ├─ Pinecone: Historico      │        │
│  │    └─ Pinecone: Knowledge Base │        │
│  └────────┬───────────────────────┘        │
│           │                                 │
│           ▼                                 │
│  ┌──────────────────────┐                  │
│  │ GPT-4: Gerar Resposta│                  │
│  └──────┬───────────────┘                  │
│         │                                   │
│    ┌────┴────┐                              │
│    ▼         ▼                              │
│  ┌────┐  ┌──────────────────┐              │
│  │Mem │  │ Preparar Resposta│              │
│  │Upd │  │ Meta: Enviar Msg │              │
│  └────┘  └──────────────────┘              │
│                    │                        │
│         ┌──────────┴────────────┐           │
│         ▼                       ▼           │
│  ┌─────────────┐      ┌──────────────┐     │
│  │ Calc Latenc │      │ Registrar    │     │
│  │ Metricas    │      │ Metricas     │     │
│  └─────────────┘      └──────────────┘     │
│         │                       │           │
│         └──────────┬────────────┘           │
│                    ▼                        │
│         ┌──────────────────┐                │
│         │ Respond Webhook  │                │
│         └──────────────────┘                │
└─────────────────────────────────────────────┘
```

### Message Processing Flow

1. **Webhook Reception** (`Meta: Webhook`)
   - GET requests → Webhook verification (challenge-response)
   - POST requests → Message/Status processing

2. **Configuration Loading** (`Carregar Config Meta`)
   - Loads environment variables (tokens, IDs, secrets)
   - Sets up Meta API configuration

3. **Security Validation** (`Validar Assinatura`)
   - HMAC SHA256 signature verification
   - Prevents spoofing/unauthorized requests
   - Uses timing-safe comparison

4. **Event Routing** (`Roteamento Evento`)
   - **Messages** → Support conversation flow
   - **Statuses** → Delivery receipts
   - **Unknown** → Ignored with logging

5. **Message Normalization** (`Normalizar Mensagem`)
   - Sanitizes input (prevents injection)
   - Extracts text from various message types
   - Creates normalized data structure

6. **Rate Limiting** (`Rate Limit Check`)
   - Basic in-memory implementation (v5.003+)
   - TODO: Redis integration for production

7. **Context Retrieval** (Parallel)
   - **PostgreSQL: Buscar Memoria** → Client conversation summary
   - **PostgreSQL: Mensagens Recentes** → Last 10 messages
   - **OpenAI: Embedding** → Vector representation
     - **Pinecone: Historico** → Similar past conversations (top 3)
     - **Pinecone: Knowledge Base** → Relevant KB articles (top 5)

8. **Response Generation** (`GPT-4: Gerar Resposta`)
   - Combines all context sources
   - Generates empathetic, professional PT-BR response
   - Model: gpt-4o-mini

9. **Memory Update** (`GPT-4: Atualizar Memoria`)
   - Consolidates conversation summary
   - Tracks resolved/pending issues
   - Identifies key topics and sentiment

10. **Response Delivery** (`Meta: Enviar Mensagem`)
    - Sends text or template message
    - Implements retry logic (up to 4 retries)
    - Exponential backoff with jitter

11. **Metrics & Logging**
    - Calculates latency
    - Logs execution details
    - Returns webhook response

---

## Database Schema

### PostgreSQL Tables

#### `gynprog_support.client_memory`
Stores consolidated client conversation history and context.

```sql
CREATE TABLE gynprog_support.client_memory (
    client_id VARCHAR(50) PRIMARY KEY,
    conversation_summary TEXT,
    resolved_issues TEXT[],
    pending_issues TEXT[],
    key_topics TEXT[],
    sentiment VARCHAR(20),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_client_memory_client_id
ON gynprog_support.client_memory(client_id);
```

#### `gynprog_support.messages`
Stores individual messages for short-term recall.

```sql
CREATE TABLE gynprog_support.messages (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    content TEXT,
    timestamp TIMESTAMP NOT NULL,
    direction VARCHAR(10), -- 'inbound' or 'outbound'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_messages_client_timestamp
ON gynprog_support.messages(client_id, timestamp DESC);

CREATE INDEX idx_messages_timestamp
ON gynprog_support.messages(timestamp DESC);
```

#### `gynprog_support.metrics` (Optional)
For detailed execution metrics.

```sql
CREATE TABLE gynprog_support.metrics (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100),
    client_id VARCHAR(50),
    latency_ms INTEGER,
    status VARCHAR(20),
    route VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_metrics_created_at
ON gynprog_support.metrics(created_at DESC);
```

---

## Environment Variables

### Required Configuration

#### Meta WhatsApp Business API
```bash
META_ENV=production                    # Environment: sandbox|production
META_GRAPH_VERSION=v20.0               # Graph API version
META_PHONE_NUMBER_ID=123456789012345   # WhatsApp phone number ID
META_WABA_TOKEN=EAAB...                # WhatsApp Business Account token
META_VERIFY_TOKEN=your_verify_token    # Webhook verification token
META_APP_SECRET=your_app_secret        # For HMAC signature validation
META_TEMPLATE_LANGUAGE=pt_BR           # Template message language
```

#### OpenAI
```bash
OPENAI_API_KEY=sk-...                  # OpenAI API key
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_CHAT_MODEL=gpt-4o-mini
```

#### Pinecone
```bash
PINECONE_API_KEY=...                   # Pinecone API key
PINECONE_HOST=gynprog-xjegwcj.svc.aped-4627-b74a.pinecone.io
PINECONE_NAMESPACE_HISTORY=client_history
PINECONE_NAMESPACE_KB=gynprog_knowledge
PINECONE_TOP_K_HISTORY=3               # Number of similar conversations
PINECONE_TOP_K_KB=5                    # Number of KB articles
```

#### PostgreSQL
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=gynprog
POSTGRES_USER=...
POSTGRES_PASSWORD=...
```

#### Application
```bash
RATE_LIMIT_PER_MINUTE=10               # Rate limit threshold
POSTGRES_MAX_MESSAGES=10                # Messages to retrieve
```

---

## Security Considerations

### Critical Security Patterns (v5.003+)

#### 1. SQL Injection Prevention
**ALWAYS use prepared statements with parameterized queries.**

❌ **NEVER do this** (v5.002 pattern):
```javascript
query: `SELECT * FROM table WHERE client_id = '${$json.client_id}'`
```

✅ **ALWAYS do this** (v5.003+ pattern):
```javascript
query: "SELECT * FROM table WHERE client_id = $1",
options: {
  queryParameters: "={{ [($json.client_id || null)] }}"
}
```

#### 2. Input Sanitization
All user inputs are sanitized in the `Normalizar Mensagem` node:

```javascript
function sanitizeString(str, maxLength = 500) {
  if (typeof str !== 'string') return '';
  return str.trim().slice(0, maxLength);
}

function sanitizePhoneNumber(phone) {
  if (!phone) return '';
  const cleaned = String(phone).replace(/[^0-9]/g, '');
  return cleaned.slice(0, 20);
}
```

#### 3. HMAC Signature Validation
Meta webhook payloads are validated using timing-safe comparison:

```javascript
const hmac = crypto.createHmac('sha256', config.app_secret);
hmac.update(rawBody, 'utf8');
const expectedSignature = 'sha256=' + hmac.digest('hex');

const valid = crypto.timingSafeEqual(
  Buffer.from(headerSignature),
  Buffer.from(expectedSignature)
);
```

#### 4. Rate Limiting
Basic implementation in v5.003+ (needs Redis for production scale).

### Security Checklist for AI Assistants

When modifying workflows:

- [ ] Use prepared statements for ALL database queries
- [ ] Sanitize ALL user inputs before processing
- [ ] Validate webhook signatures before processing events
- [ ] Never log sensitive data (tokens, secrets, PII)
- [ ] Implement proper error handling (don't expose internals)
- [ ] Use environment variables for credentials
- [ ] Validate data types and bounds
- [ ] Implement rate limiting for user-facing endpoints

---

## Development Workflow

### Version Control Strategy

1. **Workflow Naming Convention**
   - `agt_suporte_gynprog_v{MAJOR}.{MINOR}.json`
   - Example: `agt_suporte_gynprog_v5.003.json`

2. **Tagging Strategy**
   - `v{N}`: Version number (e.g., `v3`, `v4`)
   - `official`: Production-approved version
   - `security-hardened`: Security review completed
   - `gynprog`: Project identifier
   - `memoria`: Feature flag (memory-enabled)

3. **Version History**
   - **v5.002**: Initial version with security vulnerabilities
   - **v5.003**: Security hardening (prepared statements, validation, error handling, rate limiting)
   - **v5.004**: Latest production version with refinements

### Making Changes

#### Step 1: Read Current Workflow
```bash
# Identify the latest version
ls -lt agt_suporte_gynprog_v*.json | head -1

# Read and understand the workflow
cat agt_suporte_gynprog_v5_004.json
```

#### Step 2: Modify in n8n
1. Import JSON into n8n
2. Make necessary changes
3. Test thoroughly (use sandbox environment)
4. Export updated workflow

#### Step 3: Version Bump
- **Patch changes** (bug fixes): Increment minor (e.g., v5.004 → v5.005)
- **Feature additions**: Increment minor (e.g., v5.004 → v5.010)
- **Breaking changes**: Increment major (e.g., v5.004 → v6.001)

#### Step 4: Document Changes
Add notes to node descriptions:
```
"notesInFlow": "FIXED v5.005: Description of the fix"
"notesInFlow": "ADDED v5.010: New feature description"
"notesInFlow": "BREAKING v6.001: Breaking change description"
```

#### Step 5: Git Workflow
```bash
# Current branch
git checkout claude/claude-md-mi281496vls544en-016BrqEyVKt5t5KtRN9kPRKC

# Add changes
git add agt_suporte_gynprog_v5.005.json CLAUDE.md

# Commit with descriptive message
git commit -m "feat: Add retry logic to Pinecone queries (v5.005)"

# Push to remote
git push -u origin claude/claude-md-mi281496vls544en-016BrqEyVKt5t5KtRN9kPRKC
```

---

## Key Conventions

### JavaScript Function Nodes

#### Error Handling Pattern
```javascript
const results = [];
const errors = [];

for (let i = 0; i < items.length; i++) {
  try {
    // Processing logic
    results.push({ json: processedData });
  } catch (error) {
    errors.push({
      stage: 'processing',
      item_index: i,
      error: error.message
    });
    console.error('Error processing item:', error);
  }
}

if (errors.length > 0) {
  console.error('Total errors:', errors.length, errors);
}

if (results.length === 0) {
  throw new Error('No valid items processed');
}

return results;
```

#### Retry Logic with Exponential Backoff
```javascript
const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
const maxRetries = 4;

let retries = 0;
let success = false;

while (true) {
  try {
    // Attempt operation
    const response = await this.helpers.httpRequest({...});
    success = true;
  } catch (error) {
    shouldRetry = retries < maxRetries && isRetryable(error);
  }

  if (success || !shouldRetry) break;

  retries += 1;
  const backoffMs = Math.min(12000, Math.pow(2, retries) * 1000 + Math.random() * 250);
  await wait(backoffMs);
}
```

#### Metadata Pattern
All nodes maintain consistent metadata structure:

```javascript
const meta = {
  start_at: Date.now(),              // Request start time
  provider: 'meta',                  // Service provider
  channel: 'whatsapp',               // Communication channel
  environment: 'production',         // Environment
  route: 'meta_inbound',             // Processing route
  http_status: 200,                  // HTTP response status
  success: true,                     // Success flag
  latency_ms: 150,                   // Processing latency
  client_mask: '1234',               // Last 4 digits of client ID
  response: { status: 'ok' }         // Response data
};
```

### Naming Conventions

#### Nodes
- **Portuguese names**: Use PT-BR for node names (workflow language)
- **Descriptive**: Clearly indicate purpose
- **Prefixed by service**: `PostgreSQL:`, `OpenAI:`, `GPT-4:`, `Meta:`
- Examples:
  - `PostgreSQL: Buscar Memoria`
  - `GPT-4: Gerar Resposta`
  - `Meta: Enviar Mensagem`

#### Variables
- **camelCase**: JavaScript variables
- **snake_case**: Database fields, JSON keys
- **SCREAMING_SNAKE_CASE**: Environment variables

---

## Common Tasks

### Task 1: Update AI Prompt
Location: `GPT-4: Gerar Resposta` or `GPT-4: Atualizar Memoria` nodes

1. Locate the node in the workflow JSON
2. Find the `notesInFlow` field (documents current prompt)
3. Modify the prompt in the node parameters
4. Update `notesInFlow` with version and change description
5. Test with sample messages
6. Version bump and commit

### Task 2: Add New Context Source
1. Add new node after `Normalizar Mensagem`
2. Connect to parallel context retrieval
3. Merge results before `GPT-4: Gerar Resposta`
4. Update prompt to use new context
5. Test and version bump

### Task 3: Modify Database Queries
⚠️ **CRITICAL**: Always use prepared statements

1. Locate PostgreSQL node
2. Update `query` field with parameterized query
3. Update `options.queryParameters` with parameter array
4. Add/update `notesInFlow` with security note
5. Test for SQL injection vulnerabilities
6. Version bump

### Task 4: Adjust Rate Limiting
Location: `Rate Limit Check` node

Current implementation is basic (in-memory). For production:

1. Implement Redis-backed rate limiting
2. Configure threshold via environment variable
3. Add proper error responses for exceeded limits
4. Update node documentation

### Task 5: Add Error Handling
The workflow includes an `Error Handler v5.003` node:

1. Ensure errors are caught and logged
2. Return user-friendly error messages
3. Log execution details for debugging
4. Monitor error rates

---

## Debugging & Monitoring

### Metrics Logging
All executions log metrics in this format:

```json
{
  "timestamp": "2025-11-16T21:30:00.000Z",
  "route": "meta_inbound",
  "environment": "production",
  "provider": "meta",
  "status": 200,
  "success": true,
  "latency_ms": 1250,
  "client_mask": "5678",
  "message_id": "wamid.ABC123..."
}
```

Search logs with:
```bash
grep '[meta-metrics]' /path/to/n8n/logs
```

### Common Issues

#### Issue 1: Missing Credentials
**Symptom**: `missing_meta_credentials` error

**Solution**: Check environment variables are set
```javascript
// Node: Carregar Config Meta
config.access_token !== ''
config.phone_number_id !== ''
```

#### Issue 2: Invalid Signature
**Symptom**: 401 responses, `invalid_signature` in logs

**Solution**: Verify `META_APP_SECRET` matches Meta app configuration

#### Issue 3: Rate Limiting
**Symptom**: 429 responses from OpenAI/Meta

**Solution**:
- Implement proper rate limiting
- Use Redis for distributed rate limiting
- Add exponential backoff (already implemented in v5.003+)

#### Issue 4: Slow Responses
**Symptom**: High latency_ms in metrics

**Solution**:
- Check Pinecone query performance
- Optimize PostgreSQL queries (add indexes)
- Consider caching embeddings for frequent messages
- Review GPT-4 response time

---

## Best Practices for AI Assistants

### When Analyzing This Codebase

1. **Always identify the latest version** before making changes
   - Check file modification dates
   - Review version tags in JSON
   - Prefer `security-hardened` + `official` tagged versions

2. **Understand the full workflow** before modifying
   - Trace data flow from webhook to response
   - Identify all dependencies
   - Check for parallel execution paths

3. **Maintain security standards**
   - Never introduce SQL injection vulnerabilities
   - Always sanitize user inputs
   - Preserve HMAC signature validation
   - Don't expose credentials or secrets

4. **Document all changes**
   - Update node `notesInFlow` fields
   - Include version number in notes
   - Update CLAUDE.md if architecture changes
   - Commit messages should be descriptive

5. **Test thoroughly**
   - Use sandbox environment first
   - Test error cases
   - Verify security measures
   - Check performance impact

### When Creating New Features

1. **Follow existing patterns**
   - Use the metadata structure
   - Implement error handling
   - Add retry logic for external APIs
   - Include metrics logging

2. **Consider scalability**
   - Will this work with high message volume?
   - Does it need Redis/caching?
   - Are database queries optimized?

3. **Maintain language consistency**
   - Node names in Portuguese (PT-BR)
   - Comments in English (for international devs)
   - User-facing messages in Portuguese
   - System messages follow template

### When Reviewing Code

Look for:
- [ ] SQL injection vulnerabilities (string concatenation in queries)
- [ ] Missing input validation
- [ ] Hardcoded credentials
- [ ] Missing error handling
- [ ] Unvalidated webhook payloads
- [ ] Missing rate limiting
- [ ] Sensitive data in logs
- [ ] Missing retry logic for external APIs

---

## Troubleshooting Guide

### Workflow Won't Activate
1. Check all credentials are configured in n8n
2. Verify webhook path is correct: `/webhook/meta`
3. Ensure environment variables are loaded
4. Check n8n logs for startup errors

### Messages Not Processing
1. Verify webhook is reachable from Meta servers
2. Check signature validation (may be rejecting valid requests)
3. Review `Roteamento Evento` logic
4. Check for errors in `Normalizar Mensagem`

### Database Errors
1. Verify PostgreSQL connection
2. Check schema exists: `gynprog_support`
3. Ensure tables are created
4. Review prepared statement parameters
5. Check for NULL values in required fields

### AI Response Issues
1. Verify OpenAI API key is valid
2. Check prompt format in `GPT-4: Gerar Resposta`
3. Review context retrieval (memory, messages, Pinecone)
4. Check for rate limits (OpenAI)
5. Review temperature and max_tokens settings

### Pinecone Errors
1. Verify API key and host configuration
2. Check namespace exists
3. Review embedding dimensions match
4. Ensure vectors are indexed
5. Check for timeout issues (add retry logic)

---

## Future Improvements

### Suggested Enhancements

1. **Redis Integration**
   - Distributed rate limiting
   - Session management
   - Caching frequent queries

2. **Monitoring & Alerting**
   - Integrate with monitoring service (DataDog, Prometheus)
   - Set up alerts for high error rates
   - Track SLA metrics (response time, success rate)

3. **Enhanced Security**
   - Add request size limits
   - Implement IP whitelisting
   - Add anomaly detection
   - Encrypt sensitive data at rest

4. **Performance Optimization**
   - Cache embeddings for common queries
   - Batch PostgreSQL operations
   - Optimize Pinecone queries
   - Add CDN for static assets

5. **Feature Additions**
   - Multi-language support
   - Sentiment analysis
   - Escalation to human agents
   - Proactive messaging based on triggers

6. **Testing**
   - Unit tests for function nodes
   - Integration tests for workflows
   - Load testing for scalability
   - Security testing (penetration tests)

---

## Quick Reference

### Important Files
- **Latest Workflow**: `agt_suporte_gynprog_v5_004.json`
- **Documentation**: `CLAUDE.md` (this file)

### Key Nodes
- **Entry Point**: `Meta: Webhook`
- **Security**: `Validar Assinatura`
- **Core Logic**: `GPT-4: Gerar Resposta`
- **Memory**: `GPT-4: Atualizar Memoria`, `PostgreSQL: Salvar Memoria`
- **Error Handler**: `Error Handler v5.003`

### Critical Security Nodes
- `Validar Assinatura` (HMAC validation)
- `Normalizar Mensagem` (input sanitization)
- All PostgreSQL nodes (prepared statements)

### External Services
- **Meta**: WhatsApp webhook + Graph API
- **OpenAI**: Embeddings + GPT-4 chat completions
- **Pinecone**: Vector similarity search
- **PostgreSQL**: Structured data storage

---

## Contact & Support

### For Questions About:
- **n8n Workflows**: Review n8n documentation
- **Meta WhatsApp API**: https://developers.facebook.com/docs/whatsapp
- **OpenAI API**: https://platform.openai.com/docs
- **Pinecone**: https://docs.pinecone.io
- **Security Issues**: Tag with `security-hardened` and review carefully

### Version Information
- **Document Version**: 1.0
- **Last Updated**: 2025-11-16
- **Workflow Version**: v5.004
- **n8n Version**: Compatible with n8n v1.0+

---

## Appendix: Node Reference

### Complete Node List (v5.004)

| Node Name | Type | Purpose |
|-----------|------|---------|
| Meta: Webhook | Webhook | Receives WhatsApp events from Meta |
| Carregar Config Meta | Set | Loads environment configuration |
| If | If | Routes GET vs POST requests |
| Code in JavaScript | Code | Validates webhook verification token |
| Respond to Webhook1 | RespondToWebhook | Returns challenge for verification |
| Preparar Evento Meta | Function | Parses webhook payload |
| Validar Assinatura | Function | HMAC SHA256 signature validation |
| Roteamento Assinatura | Switch | Routes valid vs invalid signatures |
| Assinatura Invalida | Function | Handles invalid signatures |
| Roteamento Evento | Switch | Routes messages/statuses/unknown |
| Normalizar Mensagem | Function | Sanitizes and normalizes input |
| Rate Limit Check | Function | Basic rate limiting (needs Redis) |
| PostgreSQL: Buscar Memoria | Postgres | Retrieves client memory |
| PostgreSQL: Mensagens Recentes | Postgres | Gets last 10 messages |
| OpenAI: Embedding | OpenAI | Generates text embeddings |
| Pinecone: Historico (HTTP) | HTTP Request | Queries client history vectors |
| Pinecone: Knowledge Base (HTTP) | HTTP Request | Queries knowledge base vectors |
| GPT-4: Gerar Resposta | OpenAI | Generates support response |
| GPT-4: Atualizar Memoria | OpenAI | Updates client memory |
| PostgreSQL: Salvar Memoria | Postgres | Persists updated memory |
| Empacotar Resposta GPT | Function | Wraps GPT response |
| Merge GPT + Contexto | Merge | Combines response with context |
| Preparar Resposta | Function | Formats outbound message |
| Meta: Enviar Mensagem | Function | Sends message via Meta API |
| Processar Status | Function | Handles delivery statuses |
| Evento Desconhecido | Function | Handles unknown event types |
| Calcular Latencia | Function | Calculates execution time |
| Registrar Metricas | Function | Logs metrics to console |
| Respond to Webhook | RespondToWebhook | Final webhook response |
| Error Handler v5.003 | ErrorTrigger | Catches workflow errors |
| Log Error | Function | Logs error details |
| Error Response | RespondToWebhook | Returns error response |

---

**End of CLAUDE.md**
