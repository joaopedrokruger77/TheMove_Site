-- 1. Adicionar novas colunas de preferência na tabela usuarios
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS orcamento TEXT;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS regiao TEXT;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS tipo_lugar TEXT;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS companhia TEXT;

-- 2. Adicionar colunas de controle na tabela eventos
ALTER TABLE eventos ADD COLUMN IF NOT EXISTS is_sponsored BOOLEAN DEFAULT FALSE;
ALTER TABLE eventos ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'themove';

-- 3. Marcar todos os eventos criados até agora como patrocinados
UPDATE eventos SET is_sponsored = TRUE;

-- 4. Criar tabela de cache para as recomendações do Gemini
CREATE TABLE IF NOT EXISTS recomendacoes_cache (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    recomendacoes_json JSONB NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(usuario_id)
);

-- 5. Desativar Row Level Security para o cache (acesso livre para a API)
ALTER TABLE recomendacoes_cache DISABLE ROW LEVEL SECURITY;
