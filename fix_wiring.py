#!/usr/bin/env python3
"""
Script para corrigir fiação do workflow v5.004 → v5.005
Adiciona nó "Merge Contextos" para consolidar inputs paralelos
"""

import json
import uuid

# Ler arquivo original
with open('agt_suporte_gynprog_v5_004.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# ====================================================================
# ADICIONAR NÓ "Merge Contextos"
# ====================================================================

novo_no_merge_contextos = {
    "parameters": {
        "functionCode": """// ====================================================================
// MERGE CONTEXTOS v5.005 - Consolida contextos paralelos
// ====================================================================
// Este nó recebe 4 inputs paralelos e mescla em um único objeto
// para enviar ao GPT-4: Gerar Resposta
//
// Input 0: PostgreSQL: Buscar Memoria
// Input 1: PostgreSQL: Mensagens Recentes
// Input 2: Pinecone: Historico (HTTP)
// Input 3: Pinecone: Knowledge Base (HTTP)
// ====================================================================

const memoria = this.getInputData(0);
const mensagens = this.getInputData(1);
const historico = this.getInputData(2);
const knowledgeBase = this.getInputData(3);

const results = [];

// Processar cada item (geralmente apenas 1)
for (let i = 0; i < memoria.length; i++) {
  const memoriaItem = memoria[i] || { json: {} };
  const mensagensItem = mensagens[i] || { json: [] };
  const historicoItem = historico[i] || { json: {} };
  const kbItem = knowledgeBase[i] || { json: {} };

  // Extrair dados necessários
  const client_id = memoriaItem.json.client_id;
  const message_content = memoriaItem.json.message_content;
  const client_name = memoriaItem.json.client_name;
  const normalized = memoriaItem.json.normalized || {};
  const config = memoriaItem.json.config || {};
  const meta = memoriaItem.json.meta || {};

  // Consolidar contextos
  const contextosConsolidados = {
    client_id: client_id,
    client_name: client_name,
    message_content: message_content,

    // Memória do cliente
    memoria_cliente: memoriaItem.json[0] || null,

    // Mensagens recentes
    mensagens_recentes: Array.isArray(mensagensItem.json)
      ? mensagensItem.json
      : [],

    // Histórico similar (Pinecone)
    historico_similar: historicoItem.json.matches || [],

    // Base de conhecimento (Pinecone)
    knowledge_base: kbItem.json.matches || [],

    // Metadata
    normalized: normalized,
    config: config,
    meta: meta
  };

  results.push({ json: contextosConsolidados });
}

return results;
"""
    },
    "id": str(uuid.uuid4()),
    "name": "Merge Contextos",
    "type": "n8n-nodes-base.function",
    "typeVersion": 1,
    "position": [-100, 288],
    "notesInFlow": "NOVO v5.005: Mescla 4 contextos paralelos antes do GPT-4"
}

# Adicionar o novo nó à lista de nós
workflow['nodes'].append(novo_no_merge_contextos)

# ====================================================================
# ATUALIZAR CONEXÕES
# ====================================================================

# 1. PostgreSQL: Buscar Memoria → Merge Contextos (index 0)
workflow['connections']['PostgreSQL: Buscar Memoria'] = {
    "main": [[{
        "node": "Merge Contextos",
        "type": "main",
        "index": 0
    }]]
}

# 2. PostgreSQL: Mensagens Recentes → Merge Contextos (index 1)
workflow['connections']['PostgreSQL: Mensagens Recentes'] = {
    "main": [[{
        "node": "Merge Contextos",
        "type": "main",
        "index": 1
    }]]
}

# 3. Pinecone: Historico (HTTP) → Merge Contextos (index 2)
workflow['connections']['Pinecone: Historico (HTTP)'] = {
    "main": [[{
        "node": "Merge Contextos",
        "type": "main",
        "index": 2
    }]]
}

# 4. Pinecone: Knowledge Base (HTTP) → Merge Contextos (index 3)
workflow['connections']['Pinecone: Knowledge Base (HTTP)'] = {
    "main": [[{
        "node": "Merge Contextos",
        "type": "main",
        "index": 3
    }]]
}

# 5. Merge Contextos → GPT-4: Gerar Resposta
workflow['connections']['Merge Contextos'] = {
    "main": [[{
        "node": "GPT-4: Gerar Resposta",
        "type": "main",
        "index": 0
    }]]
}

# ====================================================================
# ATUALIZAR PROMPT DO GPT-4 PARA USAR DADOS DO MERGE
# ====================================================================

# Encontrar o nó GPT-4: Gerar Resposta e atualizar o prompt
for node in workflow['nodes']:
    if node['name'] == 'GPT-4: Gerar Resposta':
        # Atualizar content do user role
        node['parameters']['messages']['values'][1]['content'] = """=Mensagem do cliente: {{ $json.message_content }}

Memória do cliente:
{{ $json.memoria_cliente?.conversation_summary || 'Nenhuma memória anterior' }}

Últimas mensagens:
{{ $json.mensagens_recentes.map(m => `${m.direction}: ${m.content}`).join('\\n') || 'Sem histórico recente' }}

Base de conhecimento relevante:
{{ $json.knowledge_base?.slice(0, 3).map(m => m.metadata?.text || '').join('\\n\\n') || 'Nenhum artigo relevante encontrado' }}

Histórico similar:
{{ $json.historico_similar?.slice(0, 2).map(m => m.metadata?.text || '').join('\\n\\n') || 'Sem histórico similar' }}"""

        # Atualizar notes
        node['notesInFlow'] = """FIXED v5.005: Prompt atualizado para usar dados consolidados do Merge Contextos
v5.004: Configurado resource=chat com mensagens e contexto completo
Prompt v2025-02-15
System: Você é um agente de suporte da Gynprog, responde em PT-BR, mantendo tom profissional e empático.
User template: mensagem normalizada, memória do cliente, últimos contatos e trechos da base de conhecimento.
Instruções: confirmar entendimento, citar dados apenas se presentes nas fontes e sinalizar limitações quando ocorrerem."""

# ====================================================================
# ATUALIZAR METADATA
# ====================================================================

workflow['name'] = 'agt_suporte_gynprog_v5.005'
workflow['versionId'] = str(uuid.uuid4())

# ====================================================================
# SALVAR ARQUIVO v5.005
# ====================================================================

with open('agt_suporte_gynprog_v5_005.json', 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("✅ Arquivo v5.005 criado com sucesso!")
print("📝 Alterações:")
print("   1. Adicionado nó 'Merge Contextos' para consolidar 4 inputs paralelos")
print("   2. Corrigido fiação:")
print("      - PostgreSQL: Buscar Memoria → Merge Contextos (index 0)")
print("      - PostgreSQL: Mensagens Recentes → Merge Contextos (index 1)")
print("      - Pinecone: Historico → Merge Contextos (index 2)")
print("      - Pinecone: Knowledge Base → Merge Contextos (index 3)")
print("      - Merge Contextos → GPT-4: Gerar Resposta")
print("   3. Atualizado prompt do GPT-4 para usar dados consolidados")
print("")
print("🎯 Problema resolvido: Agora todos os 4 contextos são passados corretamente ao GPT-4!")
