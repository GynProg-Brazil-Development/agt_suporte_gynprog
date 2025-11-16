# Análise Minuciosa: agt_suporte_gynprog_v5_004.json

## Metadata do Workflow

```json
{
  "name": "agt_suporte_gynprog_v5.004",
  "id": "7xDMU5LbMXw1hAWd",
  "versionId": "d7c9a27b-9c7b-426b-8ca0-9641a931721f",
  "active": false,
  "settings": {
    "executionOrder": "v1"
  }
}
```

### Tags Aplicadas
- `v4` (⚠️ Inconsistência: workflow é v5.004 mas tag é v4)
- `memoria` - Feature flag indicando suporte a memória
- `gynprog` - Identificador do projeto
- `official` - Aprovado para produção
- `security-hardened` - Passou por hardening de segurança

---

## Análise Node por Node (33 nodes total)

### 1️⃣ Meta: Webhook (ID: 746e1ff7)

**Tipo**: `n8n-nodes-base.webhook`
**Posição**: [-624, 1184] (Entry point)
**Linha JSON**: 436-451

```json
{
  "parameters": {
    "multipleMethods": true,
    "path": "meta",
    "responseMode": "responseNode",
    "options": {}
  },
  "webhookId": "6c01cb74-bb50-4e48-8e13-aae11077cc9d"
}
```

#### Análise Técnica

**Configuração**:
- ✅ `multipleMethods: true` - Aceita GET (verification) e POST (events)
- ✅ `path: "meta"` - URL: `https://seu-n8n.com/webhook/meta`
- ✅ `responseMode: "responseNode"` - Resposta controlada por nodes downstream
- ✅ `webhookId` fixo - Garante consistência de URL entre deployments

**Segurança**:
- ✅ **Sem autenticação HTTP básica** - Correto, pois Meta usa HMAC signature
- ⚠️ **Sem rate limiting no webhook** - Vulnerável a abuse
- ⚠️ **Sem validação de headers** - Aceita qualquer request

**Edge Cases**:
1. ❌ **Body muito grande** - Sem limite de tamanho
   - Potencial DoS se enviar payload gigante
   - **Recomendação**: Adicionar `options.bodySize: 1048576` (1MB)

2. ❌ **Headers maliciosos** - Sem sanitização
   - Pode causar issues downstream
   - **Recomendação**: Validar headers esperados

3. ⚠️ **Timeout** - Sem configuração explícita
   - Default n8n timeout pode ser inadequado
   - **Recomendação**: Definir timeout apropriado

**Conexões**:
- Output 1 (main) → `Carregar Config Meta`
- Output 2 (vazio) → Sem uso

**Código de Melhoria Sugerido**:
```json
{
  "parameters": {
    "multipleMethods": true,
    "path": "meta",
    "responseMode": "responseNode",
    "options": {
      "rawBody": true,
      "bodySize": 1048576,
      "timeout": 30000
    }
  }
}
```

---

### 2️⃣ Carregar Config Meta (ID: b64a28a2)

**Tipo**: `n8n-nodes-base.set`
**Posição**: [-400, 1184]
**Linha JSON**: 250-302

```json
{
  "parameters": {
    "values": {
      "string": [
        { "name": "config.meta_env", "value": "={{ $env.META_ENV ? $env.META_ENV.toLowerCase() : 'sandbox' }}" },
        { "name": "config.graph_version", "value": "={{ $env.META_GRAPH_VERSION || 'v20.0' }}" },
        { "name": "config.phone_number_id", "value": "={{ $env.META_PHONE_NUMBER_ID || '' }}" },
        { "name": "config.access_token", "value": "={{ $env.META_WABA_TOKEN || '' }}" },
        { "name": "config.verify_token", "value": "={{ $env.META_VERIFY_TOKEN || '' }}" },
        { "name": "config.app_secret", "value": "={{ $env.META_APP_SECRET || '' }}" },
        { "name": "config.base_url", "value": "={{ 'https://graph.facebook.com/' + ($env.META_GRAPH_VERSION || 'v20.0') }}" },
        { "name": "config.template_language", "value": "={{ $env.META_TEMPLATE_LANGUAGE || 'pt_BR' }}" },
        { "name": "meta.environment", "value": "={{ $env.META_ENV ? $env.META_ENV.toLowerCase() : 'sandbox' }}" }
      ]
    }
  }
}
```

#### Análise Técnica

**Variáveis de Ambiente Carregadas**:
1. `META_ENV` → `config.meta_env` + `meta.environment`
2. `META_GRAPH_VERSION` → `config.graph_version` + usado em `base_url`
3. `META_PHONE_NUMBER_ID` → `config.phone_number_id`
4. `META_WABA_TOKEN` → `config.access_token`
5. `META_VERIFY_TOKEN` → `config.verify_token`
6. `META_APP_SECRET` → `config.app_secret`
7. `META_TEMPLATE_LANGUAGE` → `config.template_language`

**Segurança**:
- ✅ **Defaults seguros**: `sandbox`, `v20.0`, `pt_BR`
- ⚠️ **Credenciais vazias aceitas**: `|| ''` permite valores vazios
  - Falha só acontece downstream (na validação de assinatura)
  - **Recomendação**: Validar credenciais obrigatórias aqui

**Edge Cases**:
1. ⚠️ **META_ENV com espaços**: `" production "` → `" production "` (toLowerCase mantém espaços)
   ```javascript
   // Melhor:
   value: "={{ ($env.META_ENV || 'sandbox').toLowerCase().trim() }}"
   ```

2. ⚠️ **META_GRAPH_VERSION inválida**: `"v999.0"` aceito sem validação
   ```javascript
   // Melhor validar:
   value: "={{ /^v\d+\.\d+$/.test($env.META_GRAPH_VERSION) ? $env.META_GRAPH_VERSION : 'v20.0' }}"
   ```

3. ❌ **Duplicação de lógica**: `meta.environment` duplica `config.meta_env`
   - Pode causar inconsistência se lógica mudar
   - **Recomendação**: Referenciar `config.meta_env` em vez de recalcular

4. ⚠️ **URL construída manualmente**: Potencial para injeção
   ```javascript
   // Atual (seguro por acaso):
   'https://graph.facebook.com/' + ($env.META_GRAPH_VERSION || 'v20.0')

   // Se META_GRAPH_VERSION = "v20.0/../malicious"
   // URL = "https://graph.facebook.com/v20.0/../malicious"

   // Melhor com validação:
   const version = ($env.META_GRAPH_VERSION || 'v20.0');
   const validVersion = /^v\d+\.\d+$/.test(version) ? version : 'v20.0';
   `https://graph.facebook.com/${validVersion}`
   ```

**Problemas de Ambiente**:
- ❌ **Sem validação se variáveis estão definidas**
- ❌ **Sem logging de valores carregados** (para debug)
- ❌ **Sem fallback notification** se usar defaults

**Código de Melhoria**:
```javascript
// Adicionar Function Node "Validar Config" após este node
const config = $json.config || {};
const meta = $json.meta || {};

const required = {
  'META_PHONE_NUMBER_ID': config.phone_number_id,
  'META_WABA_TOKEN': config.access_token,
  'META_VERIFY_TOKEN': config.verify_token,
  'META_APP_SECRET': config.app_secret
};

const missing = Object.entries(required)
  .filter(([key, value]) => !value || value === '')
  .map(([key]) => key);

if (missing.length > 0) {
  console.error('Missing required environment variables:', missing);
  throw new Error(`Missing env vars: ${missing.join(', ')}`);
}

// Validar formato
if (!/^v\d+\.\d+$/.test(config.graph_version)) {
  console.warn(`Invalid META_GRAPH_VERSION: ${config.graph_version}, using v20.0`);
  config.graph_version = 'v20.0';
}

// Sanitizar environment
config.meta_env = (config.meta_env || 'sandbox').toLowerCase().trim();
meta.environment = config.meta_env;

// Log config (sem secrets)
console.log('Config loaded:', {
  environment: config.meta_env,
  graph_version: config.graph_version,
  phone_number_id: config.phone_number_id,
  has_token: !!config.access_token,
  has_secret: !!config.app_secret
});

return [{ json: { config, meta, ...($json || {}) } }];
```

---

### 3️⃣ If (ID: 90eccfcd)

**Tipo**: `n8n-nodes-base.if`
**Posição**: [-176, 1184]
**Linha JSON**: 452-485

```json
{
  "parameters": {
    "conditions": {
      "options": {
        "caseSensitive": true,
        "leftValue": "",
        "typeValidation": "strict",
        "version": 2
      },
      "conditions": [
        {
          "id": "method-check",
          "leftValue": "={{ ($json.method || $json.req?.method || 'POST').toUpperCase() }}",
          "rightValue": "GET",
          "operator": {
            "type": "string",
            "operation": "equals"
          }
        }
      ],
      "combinator": "and"
    }
  }
}
```

#### Análise Técnica

**Lógica**:
- Rota GET requests (webhook verification) vs POST requests (events)
- Default: `POST` se método não encontrado

**Segurança**:
- ✅ `caseSensitive: true` - Correto
- ✅ `typeValidation: "strict"` - Boa prática
- ✅ `toUpperCase()` - Normaliza antes de comparar

**Edge Cases**:
1. ⚠️ **Métodos não-standard**: PUT, PATCH, DELETE não tratados
   - Atualmente seriam tratados como POST (default)
   - **Comportamento**: Tentariam processar como event, falhariam na validação
   - **Recomendação**: Rejeitar explicitamente métodos não-suportados

2. ⚠️ **method undefined**: `($json.method || $json.req?.method || 'POST')`
   - Se webhook node não passar `method`, assume POST
   - **Risco**: Se n8n mudar comportamento, pode quebrar
   - **Recomendação**: Logar warning se method não encontrado

3. ✅ **Optional chaining**: `$json.req?.method` - Seguro contra null/undefined

**Estrutura de Dados Esperada**:
```javascript
// GET request (verification)
{
  "method": "GET",
  "query": {
    "hub.mode": "subscribe",
    "hub.verify_token": "...",
    "hub.challenge": "..."
  }
}

// POST request (event)
{
  "method": "POST",
  "headers": {
    "x-hub-signature-256": "sha256=..."
  },
  "body": { /* Meta event payload */ }
}
```

**Fluxo**:
- TRUE (GET) → `Code in JavaScript` (verification)
- FALSE (POST) → `Preparar Evento Meta` (event processing)

**Melhorias**:
```json
{
  "conditions": {
    "conditions": [
      {
        "id": "method-check",
        "leftValue": "={{ ($json.method || $json.req?.method || 'POST').toUpperCase() }}",
        "rightValue": "GET",
        "operator": { "type": "string", "operation": "equals" }
      },
      {
        "id": "valid-methods",
        "leftValue": "={{ ['GET', 'POST'].includes(($json.method || 'POST').toUpperCase()) }}",
        "rightValue": true,
        "operator": { "type": "boolean", "operation": "equals" }
      }
    ],
    "combinator": "and"
  }
}
```

---

### 4️⃣ Code in JavaScript (ID: 316cc07f)

**Tipo**: `n8n-nodes-base.code`
**Posição**: [48, 1088]
**Linha JSON**: 511-523

```javascript
const verifyToken = $input.item.json.query['hub.verify_token'];
const challenge = $input.item.json.query['hub.challenge'];
const expectedToken = $input.item.json.config?.verify_token || $env.META_VERIFY_TOKEN || '';

if (verifyToken && expectedToken && verifyToken === expectedToken) {
  return [{ json: { challenge } }];
}

throw new Error('Token de verificação inválido');
```

#### Análise Técnica - Webhook Verification

**Protocolo Meta**:
Quando você configura um webhook no Meta, ele faz um GET request:
```
GET /webhook/meta?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=RANDOM_STRING
```

Você deve retornar o `challenge` se o token está correto.

**Análise do Código**:

**✅ Pontos Fortes**:
1. Validação simples e direta
2. Fallback para `$env.META_VERIFY_TOKEN`
3. Throw error se inválido (causa 500 response, Meta rejeita)

**🔴 Vulnerabilidades Críticas**:

1. **❌ Timing Attack**
   ```javascript
   // ATUAL (vulnerável):
   verifyToken === expectedToken

   // Permite timing attack para descobrir o token
   // Atacante pode tentar tokens e medir tempo de resposta

   // SEGURO:
   const crypto = require('crypto');

   const verifyTokenBuf = Buffer.from(verifyToken || '', 'utf8');
   const expectedTokenBuf = Buffer.from(expectedToken || '', 'utf8');

   // Garante buffers de mesmo tamanho (previne timing leak)
   if (verifyTokenBuf.length !== expectedTokenBuf.length) {
     throw new Error('Token de verificação inválido');
   }

   const valid = crypto.timingSafeEqual(verifyTokenBuf, expectedTokenBuf);
   ```

2. **⚠️ Validação Fraca**
   ```javascript
   // ATUAL:
   if (verifyToken && expectedToken && verifyToken === expectedToken)

   // Problemas:
   // - Aceita empty string se ambos forem ''
   // - Não valida formato do challenge
   // - Não valida hub.mode

   // MELHOR:
   const mode = $input.item.json.query['hub.mode'];
   const verifyToken = $input.item.json.query['hub.verify_token'];
   const challenge = $input.item.json.query['hub.challenge'];
   const expectedToken = $input.item.json.config?.verify_token || $env.META_VERIFY_TOKEN || '';

   // Validações
   if (!expectedToken || expectedToken.length < 10) {
     throw new Error('META_VERIFY_TOKEN not configured or too short');
   }

   if (mode !== 'subscribe') {
     throw new Error('Invalid hub.mode');
   }

   if (!challenge || challenge.length === 0) {
     throw new Error('Missing hub.challenge');
   }

   if (!verifyToken || verifyToken.length === 0) {
     throw new Error('Missing hub.verify_token');
   }

   // Timing-safe comparison
   const crypto = require('crypto');
   const verifyTokenBuf = Buffer.from(verifyToken, 'utf8');
   const expectedTokenBuf = Buffer.from(expectedToken, 'utf8');

   if (verifyTokenBuf.length !== expectedTokenBuf.length) {
     throw new Error('Token de verificação inválido');
   }

   const valid = crypto.timingSafeEqual(verifyTokenBuf, expectedTokenBuf);

   if (!valid) {
     throw new Error('Token de verificação inválido');
   }

   // Retorna challenge
   return [{ json: { challenge } }];
   ```

3. **⚠️ Sem Logging**
   - Falhas de verificação não são logadas
   - Dificulta troubleshooting
   ```javascript
   // Adicionar:
   console.log('Webhook verification:', {
     mode,
     has_verify_token: !!verifyToken,
     has_expected_token: !!expectedToken,
     challenge_length: challenge?.length || 0,
     timestamp: new Date().toISOString()
   });
   ```

4. **⚠️ Sem Rate Limiting**
   - Atacante pode tentar múltiplos tokens
   - **Recomendação**: Adicionar rate limit por IP

**Edge Cases**:

1. **query não existe**:
   ```javascript
   $input.item.json.query['hub.verify_token']
   // Se query é undefined → TypeError

   // Seguro:
   const query = $input.item.json.query || {};
   const verifyToken = query['hub.verify_token'];
   ```

2. **Valores não-string**:
   ```javascript
   // Se hub.verify_token é number: 12345
   verifyToken === expectedToken // false (12345 !== "12345")

   // Seguro:
   const verifyToken = String(query['hub.verify_token'] || '');
   ```

3. **Challenge muito grande**:
   ```javascript
   // Challenge pode ser usado em ataque de memória
   if (challenge && challenge.length > 1000) {
     throw new Error('Challenge too large');
   }
   ```

**Código Completo Recomendado**:
```javascript
// Webhook Verification - Security Hardened
const crypto = require('crypto');

try {
  const query = $input.item.json.query || {};
  const config = $input.item.json.config || {};

  const mode = String(query['hub.mode'] || '');
  const verifyToken = String(query['hub.verify_token'] || '');
  const challenge = String(query['hub.challenge'] || '');
  const expectedToken = config.verify_token || $env.META_VERIFY_TOKEN || '';

  // Logging (sem expor tokens)
  console.log('Webhook verification attempt:', {
    mode,
    has_verify_token: verifyToken.length > 0,
    verify_token_length: verifyToken.length,
    has_expected_token: expectedToken.length > 0,
    challenge_length: challenge.length,
    timestamp: new Date().toISOString()
  });

  // Validações de input
  if (!expectedToken || expectedToken.length < 10) {
    console.error('META_VERIFY_TOKEN not configured or too short');
    throw new Error('Server configuration error');
  }

  if (mode !== 'subscribe') {
    console.warn('Invalid hub.mode:', mode);
    throw new Error('Invalid verification mode');
  }

  if (!challenge || challenge.length === 0) {
    throw new Error('Missing challenge');
  }

  if (challenge.length > 1000) {
    console.warn('Challenge too large:', challenge.length);
    throw new Error('Challenge too large');
  }

  if (!verifyToken || verifyToken.length === 0) {
    throw new Error('Missing verify_token');
  }

  // Timing-safe token comparison
  const verifyTokenBuf = Buffer.from(verifyToken, 'utf8');
  const expectedTokenBuf = Buffer.from(expectedToken, 'utf8');

  if (verifyTokenBuf.length !== expectedTokenBuf.length) {
    console.warn('Token length mismatch');
    throw new Error('Token de verificação inválido');
  }

  const valid = crypto.timingSafeEqual(verifyTokenBuf, expectedTokenBuf);

  if (!valid) {
    console.warn('Token verification failed');
    throw new Error('Token de verificação inválido');
  }

  // Success
  console.log('Webhook verification successful');
  return [{ json: { challenge } }];

} catch (error) {
  console.error('Webhook verification error:', error.message);
  throw error;
}
```

---

### 5️⃣ Respond to Webhook1 (ID: cd37ef24)

**Tipo**: `n8n-nodes-base.respondToWebhook`
**Posição**: [272, 1088]
**Linha JSON**: 486-510

```json
{
  "parameters": {
    "respondWith": "text",
    "responseBody": "={{$json.challenge}}",
    "options": {
      "responseCode": 200,
      "responseHeaders": {
        "entries": [
          {
            "name": "Content-Type",
            "value": "text/plain"
          }
        ]
      }
    }
  }
}
```

#### Análise Técnica

**Comportamento**:
- Retorna o `challenge` recebido como texto plano
- HTTP 200 com Content-Type: text/plain

**✅ Pontos Fortes**:
1. Content-Type correto (`text/plain`)
2. Status 200 adequado
3. Resposta simples conforme spec Meta

**⚠️ Edge Cases**:

1. **Challenge undefined**:
   ```javascript
   // Se $json.challenge é undefined
   responseBody: "={{$json.challenge}}" // Retorna "undefined" (string)

   // Meta espera challenge exato, não "undefined"
   // Causa: Falha na verificação

   // Melhor:
   responseBody: "={{$json.challenge || ''}}"

   // Ou validar antes:
   if (!$json.challenge) {
     throw new Error('Challenge not provided');
   }
   ```

2. **Challenge com caracteres especiais**:
   ```javascript
   // Challenge pode conter qualquer caractere
   // Content-Type: text/plain é correto (não precisa encoding)
   // ✅ OK
   ```

3. **Challenge muito grande**:
   ```javascript
   // Se challenge tem 10MB, resposta será 10MB
   // Pode causar timeout
   // Validação deve ser feita no node anterior
   ```

**Melhorias**:
```json
{
  "parameters": {
    "respondWith": "text",
    "responseBody": "={{$json.challenge || ''}}",
    "options": {
      "responseCode": 200,
      "responseHeaders": {
        "entries": [
          {
            "name": "Content-Type",
            "value": "text/plain; charset=utf-8"
          },
          {
            "name": "Cache-Control",
            "value": "no-store, no-cache, must-revalidate"
          }
        ]
      }
    }
  }
}
```

---

### 6️⃣ Preparar Evento Meta (ID: 1398b687)

**Tipo**: `n8n-nodes-base.function`
**Posição**: [48, 1280]
**Linha JSON**: 237-249

```javascript
const results = [];

for (const item of items) {
  const binary = item.binary?.rawBody?.data;
  let rawBody = '';

  if (binary) {
    rawBody = Buffer.from(binary, 'base64').toString('utf8');
  } else if (typeof item.json.body === 'string') {
    rawBody = item.json.body;
  } else if (item.json.body !== undefined) {
    try {
      rawBody = JSON.stringify(item.json.body);
    } catch (error) {
      rawBody = '';
    }
  }

  let parsedBody = null;
  if (rawBody) {
    try {
      parsedBody = JSON.parse(rawBody);
    } catch (error) {
      parsedBody = null;
    }
  } else if (item.json.body && typeof item.json.body === 'object') {
    parsedBody = item.json.body;
  }

  const entry = parsedBody?.entry?.[0] || {};
  const change = entry.changes?.[0] || {};
  const value = change.value || null;

  const meta = {
    start_at: Date.now(),
    provider: 'meta',
    channel: 'whatsapp',
    environment: item.json.meta?.environment || null,
    phone_number_id: value?.metadata?.phone_number_id || null,
    display_phone_number: value?.metadata?.display_phone_number || null,
  };

  results.push({
    json: {
      meta,
      headers: item.json.headers || {},
      query: item.json.query || {},
      raw_body: rawBody,
      entry,
      event: value,
      method: item.json.method || 'POST',
      config: item.json.config || {},
    },
  });
}

return results;
```

#### Análise Técnica Profunda

**Propósito**: Extrair e normalizar o evento Meta do webhook payload

**Fluxo de Parsing**:
```
1. Tentar extrair raw body de binary.rawBody.data (base64)
2. Senão, usar item.json.body (se string)
3. Senão, JSON.stringify(item.json.body) (se objeto)
4. Parse JSON do raw body
5. Extrair estrutura Meta: entry[0].changes[0].value
```

**✅ Pontos Fortes**:
1. Múltiplos fallbacks para obter body
2. Try-catch em JSON operations
3. Optional chaining seguro
4. Preserva `raw_body` para validação HMAC

**🔴 Problemas e Edge Cases**:

1. **❌ Perda de Erro Silenciosa**:
   ```javascript
   } catch (error) {
     rawBody = '';
   }
   // Erro é silenciado, continua processamento
   // Pode resultar em evento inválido processado

   // MELHOR:
   } catch (error) {
     console.error('JSON stringify error:', error, item.json.body);
     rawBody = '';
   }
   ```

2. **❌ JSON.parse Silencioso**:
   ```javascript
   try {
     parsedBody = JSON.parse(rawBody);
   } catch (error) {
     parsedBody = null;
   }
   // Se rawBody é inválido, parsedBody = null
   // entry, change, value todos = {}
   // Evento vazio é processado normalmente

   // MELHOR:
   } catch (error) {
     console.error('JSON parse error:', {
       error: error.message,
       rawBody: rawBody.substring(0, 200), // Primeiros 200 chars
       itemIndex: results.length
     });
     parsedBody = null;
   }
   ```

3. **⚠️ Múltiplos Entries Ignorados**:
   ```javascript
   const entry = parsedBody?.entry?.[0] || {};
   // Meta pode enviar múltiplos entries em um webhook
   // Apenas o primeiro é processado, resto é descartado

   // Estrutura real do Meta:
   {
     "object": "whatsapp_business_account",
     "entry": [
       {
         "id": "...",
         "changes": [
           { "value": {...}, "field": "messages" },
           { "value": {...}, "field": "messages" }
         ]
       },
       {
         "id": "...",
         "changes": [...]
       }
     ]
   }

   // MELHOR - Processar todos entries:
   const results = [];

   for (const item of items) {
     // ... parsing do rawBody ...

     const entries = parsedBody?.entry || [];

     if (entries.length === 0) {
       console.warn('No entries in webhook payload');
       // Ainda assim criar um item vazio para logging
       results.push({
         json: {
           meta: { ...meta, route: 'empty_payload' },
           headers: item.json.headers || {},
           raw_body: rawBody,
           entry: {},
           event: null,
           config: item.json.config || {}
         }
       });
       continue;
     }

     // Processar cada entry
     for (const entry of entries) {
       const changes = entry.changes || [];

       for (const change of changes) {
         const value = change.value || null;

         results.push({
           json: {
             meta: {
               start_at: Date.now(),
               provider: 'meta',
               channel: 'whatsapp',
               environment: item.json.meta?.environment || null,
               phone_number_id: value?.metadata?.phone_number_id || null,
               display_phone_number: value?.metadata?.display_phone_number || null,
               entry_id: entry.id || null,
               field: change.field || null
             },
             headers: item.json.headers || {},
             query: item.json.query || {},
             raw_body: rawBody,
             entry,
             change,
             event: value,
             method: item.json.method || 'POST',
             config: item.json.config || {},
           }
         });
       }
     }
   }

   return results;
   ```

4. **⚠️ Buffer Encoding Assumption**:
   ```javascript
   Buffer.from(binary, 'base64').toString('utf8');
   // Assume UTF-8, mas Meta pode enviar outros encodings
   // Verificar Content-Type header

   // MELHOR:
   const contentType = (item.json.headers['content-type'] || '').toLowerCase();
   const charset = contentType.includes('charset=')
     ? contentType.split('charset=')[1].split(';')[0].trim()
     : 'utf8';

   rawBody = Buffer.from(binary, 'base64').toString(charset);
   ```

5. **❌ Sem Validação de Tamanho**:
   ```javascript
   // rawBody pode ser gigante (DoS)
   if (rawBody.length > 1048576) { // 1MB
     console.error('Payload too large:', rawBody.length);
     throw new Error('Payload exceeds maximum size');
   }
   ```

6. **⚠️ Metadata Pode Estar Ausente**:
   ```javascript
   phone_number_id: value?.metadata?.phone_number_id || null,
   // Se value é null, metadata não existe
   // Mas entrada "changes" pode ter outros tipos que não têm metadata
   // Exemplo: status updates podem não ter metadata
   // ✅ Tratamento correto com optional chaining
   ```

7. **⚠️ Perda de Headers Importantes**:
   ```javascript
   headers: item.json.headers || {},
   // Preserva todos headers (bom)
   // Mas não valida headers obrigatórios

   // Adicionar validação:
   const requiredHeaders = ['x-hub-signature-256'];
   const missingHeaders = requiredHeaders.filter(h => !item.json.headers[h]);

   if (missingHeaders.length > 0) {
     console.error('Missing required headers:', missingHeaders);
   }
   ```

**Código Melhorado Completo**:
```javascript
const results = [];
const errors = [];

for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
  try {
    const item = items[itemIndex];

    // 1. Extrair raw body
    const binary = item.binary?.rawBody?.data;
    let rawBody = '';

    if (binary) {
      // Detectar charset do Content-Type
      const contentType = (item.json.headers?.['content-type'] || '').toLowerCase();
      const charset = contentType.includes('charset=')
        ? contentType.split('charset=')[1].split(';')[0].trim()
        : 'utf8';

      try {
        rawBody = Buffer.from(binary, 'base64').toString(charset);
      } catch (error) {
        console.error('Buffer decode error:', error);
        throw new Error('Failed to decode payload');
      }
    } else if (typeof item.json.body === 'string') {
      rawBody = item.json.body;
    } else if (item.json.body !== undefined) {
      try {
        rawBody = JSON.stringify(item.json.body);
      } catch (error) {
        console.error('JSON stringify error:', error);
        throw new Error('Failed to stringify body');
      }
    }

    // Validar tamanho
    if (rawBody.length > 1048576) { // 1MB
      console.error('Payload too large:', rawBody.length);
      throw new Error('Payload exceeds maximum size (1MB)');
    }

    // 2. Parse JSON
    let parsedBody = null;
    if (rawBody) {
      try {
        parsedBody = JSON.parse(rawBody);
      } catch (error) {
        console.error('JSON parse error:', {
          error: error.message,
          rawBodyPreview: rawBody.substring(0, 200)
        });
        throw new Error('Invalid JSON payload');
      }
    } else if (item.json.body && typeof item.json.body === 'object') {
      parsedBody = item.json.body;
    }

    // Validar estrutura básica
    if (!parsedBody || typeof parsedBody !== 'object') {
      console.error('Invalid parsed body type:', typeof parsedBody);
      throw new Error('Parsed body is not an object');
    }

    // Validar headers obrigatórios
    const requiredHeaders = ['x-hub-signature-256'];
    const missingHeaders = requiredHeaders.filter(h => !item.json.headers?.[h]);

    if (missingHeaders.length > 0) {
      console.error('Missing required headers:', missingHeaders);
      // Não throw - validação HMAC vai pegar depois
    }

    // 3. Processar entries
    const entries = parsedBody.entry || [];

    if (entries.length === 0) {
      console.warn('Webhook payload has no entries');
      // Criar item vazio para tracking
      results.push({
        json: {
          meta: {
            start_at: Date.now(),
            provider: 'meta',
            channel: 'whatsapp',
            environment: item.json.meta?.environment || null,
            route: 'empty_payload',
            warning: 'no_entries'
          },
          headers: item.json.headers || {},
          query: item.json.query || {},
          raw_body: rawBody,
          entry: {},
          event: null,
          method: item.json.method || 'POST',
          config: item.json.config || {}
        }
      });
      continue;
    }

    // Processar cada entry e change
    for (const entry of entries) {
      const changes = entry.changes || [];

      if (changes.length === 0) {
        console.warn('Entry has no changes:', entry.id);
        continue;
      }

      for (const change of changes) {
        const value = change.value || null;

        const meta = {
          start_at: Date.now(),
          provider: 'meta',
          channel: 'whatsapp',
          environment: item.json.meta?.environment || null,
          phone_number_id: value?.metadata?.phone_number_id || null,
          display_phone_number: value?.metadata?.display_phone_number || null,
          entry_id: entry.id || null,
          field: change.field || null
        };

        results.push({
          json: {
            meta,
            headers: item.json.headers || {},
            query: item.json.query || {},
            raw_body: rawBody,
            entry,
            change,
            event: value,
            method: item.json.method || 'POST',
            config: item.json.config || {}
          }
        });
      }
    }
  } catch (error) {
    errors.push({
      item_index: itemIndex,
      error: error.message,
      timestamp: new Date().toISOString()
    });
    console.error(`Error processing item ${itemIndex}:`, error);
  }
}

// Log de erros
if (errors.length > 0) {
  console.error('Processing errors:', errors);
}

// Se nenhum resultado válido, falhar
if (results.length === 0) {
  throw new Error('No valid webhook events could be processed');
}

return results;
```

---

### 7️⃣ Validar Assinatura (ID: 09291872) - 🔒 CRÍTICO DE SEGURANÇA

**Tipo**: `n8n-nodes-base.function`
**Posição**: [272, 1280]
**Linha JSON**: 303-315

```javascript
// ✅ VALIDAÇÃO HMAC SHA256 - Meta WhatsApp
// crypto já está disponível globalmente no n8n - NÃO importar!

const items = $input.all();

return items.map(item => {
  const config = item.json.config;
  const rawBody = item.json.raw_body;
  const headerSignature = item.json.headers['x-hub-signature-256'];

  // Validações básicas
  if (!config?.app_secret) {
    return {
      json: {
        ...item.json,
        signature: {
          valid: false,
          reason: 'META_APP_SECRET não configurado',
          header: headerSignature || 'missing',
          expected: null
        }
      }
    };
  }

  if (!rawBody) {
    return {
      json: {
        ...item.json,
        signature: {
          valid: false,
          reason: 'raw_body ausente',
          header: headerSignature || 'missing',
          expected: null
        }
      }
    };
  }

  if (!headerSignature) {
    return {
      json: {
        ...item.json,
        signature: {
          valid: false,
          reason: 'Header X-Hub-Signature-256 ausente',
          header: 'missing',
          expected: null
        }
      }
    };
  }

  // Calcular HMAC SHA256
  const hmac = crypto.createHmac('sha256', config.app_secret);
  hmac.update(rawBody, 'utf8');
  const expectedSignature = 'sha256=' + hmac.digest('hex');

  // Comparação segura (timing-safe)
  const valid = crypto.timingSafeEqual(
    Buffer.from(headerSignature),
    Buffer.from(expectedSignature)
  );

  return {
    json: {
      ...item.json,
      signature: {
        valid: valid,
        reason: valid ? 'Assinatura válida' : 'Assinatura inválida - possível tentativa de spoofing',
        header: headerSignature,
        expected: expectedSignature
      }
    }
  };
});
```

#### Análise de Segurança - HMAC Validation

**Propósito**: Validar que o webhook realmente veio do Meta (não de atacante)

**Protocolo HMAC SHA256**:
1. Meta assina o payload com secret compartilhado
2. Signature enviada no header `X-Hub-Signature-256`
3. Servidor recalcula signature com mesmo secret
4. Se signatures match → autêntico

**✅ EXCELENTE Implementação de Segurança**:

1. **Timing-Safe Comparison**
   ```javascript
   crypto.timingSafeEqual(Buffer.from(headerSignature), Buffer.from(expectedSignature))
   ```
   - ✅ **Previne timing attacks**
   - Comparação leva tempo constante independente de onde strings diferem
   - Atacante não pode descobrir signature byte-a-byte medindo tempo

2. **Validações Granulares**
   ```javascript
   if (!config?.app_secret) { return { valid: false, reason: '...' } }
   if (!rawBody) { return { valid: false, reason: '...' } }
   if (!headerSignature) { return { valid: false, reason: '...' } }
   ```
   - ✅ Fail early com motivos específicos
   - ✅ Facilita debugging

3. **Preserva Expected Signature**
   ```javascript
   expected: expectedSignature
   ```
   - ✅ Útil para debugging (mas cuidado em logs)

**🔴 VULNERABILIDADES E MELHORIAS**:

1. **❌ Buffer Length Mismatch Não Tratado**
   ```javascript
   // ATUAL:
   const valid = crypto.timingSafeEqual(
     Buffer.from(headerSignature),
     Buffer.from(expectedSignature)
   );

   // PROBLEMA: Se headerSignature e expectedSignature têm tamanhos diferentes,
   // timingSafeEqual lança erro: "Input buffers must have the same length"
   // Erro é pego downstream, mas não é ideal

   // MELHOR:
   let valid = false;
   try {
     const headerBuf = Buffer.from(headerSignature);
     const expectedBuf = Buffer.from(expectedSignature);

     if (headerBuf.length !== expectedBuf.length) {
       console.warn('Signature length mismatch:', {
         header_length: headerBuf.length,
         expected_length: expectedBuf.length
       });
       valid = false;
     } else {
       valid = crypto.timingSafeEqual(headerBuf, expectedBuf);
     }
   } catch (error) {
     console.error('Signature comparison error:', error);
     valid = false;
   }
   ```

2. **⚠️ Exposição de Expected Signature**
   ```javascript
   expected: expectedSignature // Expõe o secret hash
   ```
   - Em logs, isso pode vazar informação sobre o secret
   - Atacante poderia tentar reverse engineering
   - **Recomendação**: Só incluir em modo debug

   ```javascript
   signature: {
     valid,
     reason: valid ? 'Assinatura válida' : 'Assinatura inválida',
     header: headerSignature,
     expected: process.env.DEBUG ? expectedSignature : undefined // Só em debug
   }
   ```

3. **⚠️ Header Case Sensitivity**
   ```javascript
   item.json.headers['x-hub-signature-256']
   ```
   - HTTP headers são case-insensitive
   - Meta pode enviar `X-Hub-Signature-256` ou `x-hub-signature-256`
   - n8n geralmente normaliza para lowercase, mas não é garantido

   ```javascript
   // Mais seguro:
   const headers = item.json.headers || {};
   const headerSignature = headers['x-hub-signature-256']
     || headers['X-Hub-Signature-256']
     || Object.keys(headers).find(k => k.toLowerCase() === 'x-hub-signature-256')
       && headers[Object.keys(headers).find(k => k.toLowerCase() === 'x-hub-signature-256')];
   ```

4. **❌ Sem Logging de Tentativas Inválidas**
   ```javascript
   // Se signature é inválida, é ataque?
   // Deve ser logado para security monitoring

   if (!valid) {
     console.warn('SECURITY: Invalid webhook signature detected', {
       timestamp: new Date().toISOString(),
       source_ip: item.json.headers['x-forwarded-for'] || 'unknown',
       header_signature_prefix: headerSignature?.substring(0, 15),
       expected_signature_prefix: expectedSignature?.substring(0, 15),
       body_size: rawBody.length
     });
   }
   ```

5. **⚠️ rawBody Encoding**
   ```javascript
   hmac.update(rawBody, 'utf8');
   ```
   - Assume rawBody é string UTF-8
   - Meta sempre envia UTF-8? Provável, mas não validado
   - Se rawBody vier como Buffer, pode dar erro

   ```javascript
   // Mais robusto:
   const bodyBuffer = Buffer.isBuffer(rawBody)
     ? rawBody
     : Buffer.from(rawBody, 'utf8');

   const hmac = crypto.createHmac('sha256', config.app_secret);
   hmac.update(bodyBuffer);
   ```

6. **⚠️ app_secret Whitespace**
   ```javascript
   config.app_secret
   ```
   - Se secret tiver espaços no início/fim (erro de config)
   - HMAC vai falhar sempre
   - Deve trimmar?

   ```javascript
   const appSecret = (config.app_secret || '').trim();

   if (!appSecret) {
     return { valid: false, reason: 'META_APP_SECRET não configurado' };
   }

   const hmac = crypto.createHmac('sha256', appSecret);
   ```

**Edge Cases**:

1. **Signature com formato inválido**:
   ```javascript
   // Meta envia: "sha256=abc123..."
   // Se vem só "abc123" ou "sha512=abc123"

   if (headerSignature && !headerSignature.startsWith('sha256=')) {
     console.warn('Invalid signature format:', headerSignature.substring(0, 20));
     return {
       json: {
         ...item.json,
         signature: {
           valid: false,
           reason: 'Invalid signature format (must start with sha256=)',
           header: headerSignature
         }
       }
     };
   }
   ```

2. **rawBody vazio**:
   ```javascript
   if (!rawBody) { /* ... */ }
   ```
   - ✅ Tratado corretamente
   - Mas `rawBody === ''` (empty string) passa no check
   - Meta nunca envia body vazio? Provável

3. **Multiple signature headers**:
   ```javascript
   // Se headers['x-hub-signature-256'] é array (múltiplos headers)
   // Improvável com Meta, mas possível em HTTP

   if (Array.isArray(headerSignature)) {
     headerSignature = headerSignature[0]; // Pegar primeiro
   }
   ```

**Código Completo Hardened**:

```javascript
// HMAC Signature Validation - Security Hardened v2
const items = $input.all();

return items.map((item, index) => {
  const config = item.json.config || {};
  const rawBody = item.json.raw_body;
  const headers = item.json.headers || {};

  // 1. Extrair signature (case-insensitive)
  let headerSignature = headers['x-hub-signature-256'];
  if (!headerSignature) {
    // Fallback para case-insensitive
    const signatureKey = Object.keys(headers).find(
      k => k.toLowerCase() === 'x-hub-signature-256'
    );
    headerSignature = signatureKey ? headers[signatureKey] : null;
  }

  // Se múltiplos headers (improvável), pegar primeiro
  if (Array.isArray(headerSignature)) {
    headerSignature = headerSignature[0];
  }

  // 2. Validar app_secret
  const appSecret = (config.app_secret || '').trim();
  if (!appSecret) {
    console.error('META_APP_SECRET not configured');
    return {
      json: {
        ...item.json,
        signature: {
          valid: false,
          reason: 'META_APP_SECRET não configurado',
          header: headerSignature || 'missing'
        }
      }
    };
  }

  // 3. Validar rawBody
  if (rawBody === undefined || rawBody === null) {
    console.error('raw_body is missing');
    return {
      json: {
        ...item.json,
        signature: {
          valid: false,
          reason: 'raw_body ausente',
          header: headerSignature || 'missing'
        }
      }
    };
  }

  // 4. Validar headerSignature
  if (!headerSignature) {
    console.warn('Missing X-Hub-Signature-256 header');
    return {
      json: {
        ...item.json,
        signature: {
          valid: false,
          reason: 'Header X-Hub-Signature-256 ausente',
          header: 'missing'
        }
      }
    };
  }

  // Validar formato da signature
  if (!headerSignature.startsWith('sha256=')) {
    console.warn('Invalid signature format:', headerSignature.substring(0, 20));
    return {
      json: {
        ...item.json,
        signature: {
          valid: false,
          reason: 'Formato de assinatura inválido (deve começar com sha256=)',
          header: headerSignature
        }
      }
    };
  }

  // 5. Calcular HMAC
  const bodyBuffer = Buffer.isBuffer(rawBody)
    ? rawBody
    : Buffer.from(String(rawBody), 'utf8');

  const hmac = crypto.createHmac('sha256', appSecret);
  hmac.update(bodyBuffer);
  const expectedSignature = 'sha256=' + hmac.digest('hex');

  // 6. Timing-safe comparison
  let valid = false;
  try {
    const headerBuf = Buffer.from(headerSignature);
    const expectedBuf = Buffer.from(expectedSignature);

    if (headerBuf.length !== expectedBuf.length) {
      console.warn('Signature length mismatch:', {
        header_length: headerBuf.length,
        expected_length: expectedBuf.length
      });
      valid = false;
    } else {
      valid = crypto.timingSafeEqual(headerBuf, expectedBuf);
    }
  } catch (error) {
    console.error('Signature comparison error:', error);
    valid = false;
  }

  // 7. Log security events
  if (!valid) {
    console.warn('SECURITY: Invalid webhook signature detected', {
      timestamp: new Date().toISOString(),
      item_index: index,
      source_ip: headers['x-forwarded-for'] || headers['x-real-ip'] || 'unknown',
      body_size: bodyBuffer.length,
      signature_format_valid: headerSignature.startsWith('sha256=')
    });
  } else {
    console.log('Valid webhook signature verified');
  }

  // 8. Retornar resultado
  return {
    json: {
      ...item.json,
      signature: {
        valid,
        reason: valid
          ? 'Assinatura válida'
          : 'Assinatura inválida - possível tentativa de spoofing',
        header: headerSignature,
        // Só incluir expected em modo debug (segurança)
        ...(process.env.DEBUG === 'true' && { expected: expectedSignature })
      }
    }
  };
});
```

**Security Score**: 9/10 → 9.5/10 (com melhorias)

---

### 8️⃣ Normalizar Mensagem (ID: a12eacab) - 🔒 INPUT SANITIZATION

**Tipo**: `n8n-nodes-base.function`
**Posição**: [-624, 192]
**Linha JSON**: 223-236
**Tamanho do Código**: ~350 linhas

```javascript
// =================================================================
// FUNÇÃO REFATORADA v5.003 - Normalização de Mensagens Meta
// Correções: validação de entrada, funções auxiliares, comentários
// =================================================================
```

Este é o node **MAIS COMPLEXO** do workflow (350 linhas). Vou analisar cada função:

#### Funções Auxiliares

**1. sanitizeString()**
```javascript
function sanitizeString(str, maxLength = 500) {
  if (typeof str !== 'string') return '';
  return str.trim().slice(0, maxLength);
}
```

**Análise**:
- ✅ Type check antes de processar
- ✅ trim() remove whitespace
- ✅ Limite de tamanho (DoS protection)
- ⚠️ **Não remove caracteres especiais** (apenas trunca)

**Edge Cases**:
1. `str = null` → `typeof null = 'object'` → return `''` ✅
2. `str = undefined` → `typeof undefined = 'undefined'` → return `''` ✅
3. `str = 123` → `typeof 123 = 'number'` → return `''` ✅
4. `str = '   '` → trim → `''` ✅
5. `str = 'a'.repeat(1000)` → slice(0, 500) → 500 chars ✅

**Potenciais Problemas**:
```javascript
// String com caracteres Unicode multi-byte
const str = '🔥'.repeat(300); // 300 emojis
sanitizeString(str, 500); // Slice pode cortar no meio de char

// MELHOR:
function sanitizeString(str, maxLength = 500) {
  if (typeof str !== 'string') return '';
  str = str.trim();

  // Usar Array.from para contar caracteres Unicode corretamente
  if (Array.from(str).length > maxLength) {
    return Array.from(str).slice(0, maxLength).join('');
  }

  return str;
}
```

**2. sanitizePhoneNumber()**
```javascript
function sanitizePhoneNumber(phone) {
  if (!phone) return '';
  const cleaned = String(phone).replace(/[^0-9]/g, '');
  return cleaned.slice(0, 20); // Limite razoável
}
```

**Análise**:
- ✅ Aceita qualquer tipo (converte para String)
- ✅ Remove tudo exceto dígitos
- ✅ Limite de 20 dígitos (internacional = ~15 dígitos)
- ⚠️ **Aceita phone vazio** → returns `''`

**Edge Cases**:
1. `phone = null` → `!null = true` → return `''` ✅
2. `phone = undefined` → `!undefined = true` → return `''` ✅
3. `phone = 0` → `!0 = true` → return `''` ❌ (zero é phone inválido, mas tratado como falsy)
4. `phone = '+1 (555) 123-4567'` → `'15551234567'` ✅
5. `phone = '12345678901234567890123'` → slice(0, 20) ✅

**Possível Melhor Validação**:
```javascript
function sanitizePhoneNumber(phone) {
  if (phone === null || phone === undefined || phone === '') return '';

  const cleaned = String(phone).replace(/[^0-9]/g, '');

  // Validar comprimento mínimo
  if (cleaned.length < 7) { // Mínimo para número local
    console.warn('Phone number too short:', cleaned);
    return '';
  }

  return cleaned.slice(0, 20);
}
```

**3. extractContactInfo()**
```javascript
function extractContactInfo(value) {
  const contacts = value.contacts || [];
  const contact = contacts[0] || {};

  const name = sanitizeString(
    contact.profile?.name ||
    contact.profile?.Name ||
    contact.name ||
    'Contato Meta'
  );

  const waId = sanitizePhoneNumber(contact.wa_id);

  return { name, waId };
}
```

**Análise**:
- ✅ Múltiplos fallbacks para name
- ✅ Default sensato: 'Contato Meta'
- ⚠️ **Pega apenas primeiro contato**: `contacts[0]`
  - Meta pode enviar múltiplos contatos em um evento?
  - Provavelmente não, mas não validado

**Edge Cases**:
1. `value.contacts = []` → `contact = {}` → name = 'Contato Meta', waId = '' ✅
2. `value.contacts = undefined` → `contacts = []` → mesmo acima ✅
3. `contact.profile.Name` (capital N) → Fallback coberto ✅
4. Múltiplos contatos → Pega primeiro, ignora resto ⚠️

**4. extractMessageText()** - FUNÇÃO COMPLEXA

```javascript
function extractMessageText(message) {
  const messageType = message.type || 'text';
  let text = '';

  try {
    switch (messageType) {
      case 'text':
        text = message.text?.body || '';
        break;

      case 'interactive':
        const interactive = message.interactive || {};
        if (interactive.type === 'list_reply') {
          text = interactive.list_reply?.title ||
                 interactive.list_reply?.description || '';
        } else if (interactive.type === 'button_reply') {
          text = interactive.button_reply?.title ||
                 interactive.button_reply?.id || '';
        }
        break;

      case 'button':
        text = message.button?.text || '';
        break;

      case 'reaction':
        text = message.reaction?.emoji || '';
        break;

      case 'image':
      case 'video':
      case 'audio':
      case 'document':
        text = message[messageType]?.caption ||
               message[messageType]?.filename || '';
        break;

      default:
        text = '';
    }
  } catch (error) {
    console.error('Erro ao extrair texto:', error);
    text = '';
  }

  return text || `[${messageType} sem texto]`;
}
```

**Análise**:
- ✅ Suporta 9+ tipos de mensagem
- ✅ Try-catch para safety
- ✅ Fallback descritivo: `[image sem texto]`
- ✅ Optional chaining em todos acessos

**Tipos de Mensagem Meta WhatsApp**:
- `text` - Mensagem de texto
- `interactive` - Botões/listas interativas
  - `list_reply` - Resposta de lista
  - `button_reply` - Resposta de botão
- `button` - Botão simples
- `reaction` - Reação a mensagem (emoji)
- `image`, `video`, `audio`, `document` - Mídia
- `location` - Localização ❌ NÃO TRATADO
- `contacts` - Cartão de contato ❌ NÃO TRATADO
- `sticker` - Sticker ❌ NÃO TRATADO

**Tipos Não Tratados**:
```javascript
case 'location':
  const loc = message.location || {};
  text = `📍 ${loc.name || 'Localização'} (${loc.latitude}, ${loc.longitude})`;
  break;

case 'contacts':
  const contactCards = message.contacts || [];
  text = contactCards.map(c => c.name?.formatted_name || 'Contato').join(', ');
  break;

case 'sticker':
  text = '[Sticker]';
  break;
```

**Edge Cases**:
1. `messageType = 'unknown_type'` → default → `''` → return `'[unknown_type sem texto]'` ✅
2. `interactive.type = 'nfm_reply'` (novo tipo) → não tratado → text = '' ⚠️
3. Erro no switch → catch → text = '' → return `'[text sem texto]'` ✅

**5. createTimestamp()** - CONVERSÃO DE TEMPO

```javascript
function createTimestamp(messageTimestamp) {
  try {
    const timestampSeconds = Number(messageTimestamp || Date.now() / 1000);
    if (Number.isNaN(timestampSeconds)) {
      return new Date().toISOString();
    }
    return new Date(timestampSeconds * 1000).toISOString();
  } catch (error) {
    return new Date().toISOString();
  }
}
```

**Análise**:
- ✅ Try-catch
- ✅ NaN check
- ✅ Fallback para now()
- ✅ Multiplica por 1000 (Unix timestamp → milliseconds)

**Edge Cases**:
1. `messageTimestamp = undefined` → `Date.now() / 1000` ✅
2. `messageTimestamp = 'abc'` → `Number('abc') = NaN` → `isNaN(NaN) = true` → now() ✅
3. `messageTimestamp = 1609459200` (2021-01-01) → `new Date(1609459200000)` ✅
4. `messageTimestamp = 0` → `new Date(0)` = 1970-01-01 ✅ (mas improvável)
5. `messageTimestamp = -1` → `new Date(-1000)` = 1969 ⚠️ (Permite timestamps negativos)

**Possível Validação**:
```javascript
function createTimestamp(messageTimestamp) {
  try {
    const now = Date.now();
    let timestampMs;

    if (messageTimestamp) {
      const timestampSeconds = Number(messageTimestamp);

      if (Number.isNaN(timestampSeconds)) {
        console.warn('Invalid timestamp, using now()');
        return new Date(now).toISOString();
      }

      timestampMs = timestampSeconds * 1000;

      // Validar range razoável (não no futuro, não antes de 2020)
      const minTimestamp = new Date('2020-01-01').getTime();
      const maxTimestamp = now + 60000; // +1 minuto (clock skew)

      if (timestampMs < minTimestamp || timestampMs > maxTimestamp) {
        console.warn('Timestamp out of range:', new Date(timestampMs).toISOString());
        return new Date(now).toISOString();
      }
    } else {
      timestampMs = now;
    }

    return new Date(timestampMs).toISOString();
  } catch (error) {
    console.error('Timestamp conversion error:', error);
    return new Date().toISOString();
  }
}
```

---

Continuo com os próximos nodes críticos (PostgreSQL, GPT-4, Meta: Enviar Mensagem)?