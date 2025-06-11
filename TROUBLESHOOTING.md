# TROUBLESHOOTING - Raiox AI CLIP Staging

## 🚨 Problemas Recorrentes e Soluções Definitivas

### 1. ERRO: `operator does not exist: vector <-> numeric[]`
**CAUSA:** Bind parameters não são convertidos para tipo vector  
**SOLUÇÃO:** Usar `::vector` no cast: `embedding <-> %(query_vector)s::vector`

### 2. ERRO: `%%(query_vector)s` - Duplicação de %
**CAUSA:** SQLAlchemy escapa automaticamente % para %% com text()  
**SOLUÇÃO:** Usar psycopg2 direto ou sintaxe correta para SQLAlchemy

### 3. ERRO: `permission denied for table implants`
**CAUSA:** Usuário raiox_user sem permissões na tabela  
**SOLUÇÃO:** `GRANT SELECT ON implants TO raiox_user;`

### 4. ERRO: `syntax error at or near ":"`
**CAUSA:** PostgreSQL não aceita sintaxe `:parameter` do SQLAlchemy  
**SOLUÇÃO:** Usar `%s` com psycopg2 ou sintaxe correta

### 5. FUNÇÃO RETORNA LISTA VAZIA `[]`
**CAUSA:** Função find_similar_implants hardcoded para retornar []  
**SOLUÇÃO:** Implementar busca real no PostgreSQL

### 6. ERRO: `connection timeout`
**CAUSA:** Conexão externa ao PostgreSQL bloqueada  
**SOLUÇÃO:** Usar conexão via SSH ou configurar firewall

## ✅ Checklist de Validação Completa

### ANTES DE DECLARAR SUCESSO:
- [ ] Teste end-to-end com imagem real
- [ ] Verificar logs sem erros
- [ ] Validar JSON estruturado retornado
- [ ] Confirmar dados no PostgreSQL
- [ ] Testar busca de similaridade

### PROTOCOLO DE MUDANÇAS:
1. **SEMPRE fazer backup** antes de alterar código
2. **Validar sintaxe** antes de restart
3. **Testar gradualmente** sem quebrar funcionamento
4. **Documentar problemas** encontrados
5. **Preparar rollback** antes de aplicar mudanças

### COMANDOS DE ROLLBACK:
```bash
# Restaurar main.py
cp /opt/raiox-app/app/main.py.backup_YYYYMMDD_HHMMSS /opt/raiox-app/app/main.py
systemctl restart raiox-api

# Verificar status
systemctl status raiox-api
```

## 🔧 Comandos Úteis

### Verificar Serviço
```bash
systemctl status raiox-api
journalctl -u raiox-api -n 20 --no-pager
```

### Testar API
```bash
curl -H "X-Client-ID: test123" \
     -F "file=@imagem.jpg" \
     http://45.55.128.141:8000/upload
```

### Verificar PostgreSQL
```bash
ssh root@159.65.183.73 "sudo -u postgres psql -d raiox -c 'SELECT COUNT(*) FROM implants;'"
```

### Backup de Segurança
```bash
cp /opt/raiox-app/app/main.py /opt/raiox-app/app/main.py.backup_$(date +%Y%m%d_%H%M%S)
```

## 📋 Fluxo de Correção Segura

1. **Identificar problema** nos logs
2. **Criar backup** do arquivo atual
3. **Aplicar correção** pontual
4. **Validar sintaxe** Python
5. **Restart gradual** do serviço
6. **Testar funcionamento** completo
7. **Documentar solução** aplicada

## 🎯 Lições Aprendidas

1. **NÃO declarar "100% funcionando"** sem teste completo
2. **SEMPRE documentar** problemas recorrentes  
3. **VALIDAR fluxo end-to-end** antes de confirmar sucesso
4. **MANTER backups** e planos de rollback
5. **LEMBRAR de edições manuais** anteriores
6. **QUANDO SE MUDA ALGO, SEMPRE PENSA NA VOLTA**

---
**Data:** 11/06/2025  
**Status:** Documentação completa de troubleshooting

