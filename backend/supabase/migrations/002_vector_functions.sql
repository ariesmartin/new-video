-- =====================================================
-- Vector Search Functions
-- =====================================================
-- 用于 RAG 的向量相似度搜索函数
-- =====================================================

-- 项目向量相似度搜索
CREATE OR REPLACE FUNCTION match_project_vectors(
    query_embedding VECTOR(1536),
    match_project_id UUID,
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    node_id UUID,
    text_chunk TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        pv.id,
        pv.node_id,
        pv.text_chunk,
        pv.metadata,
        1 - (pv.embedding <=> query_embedding) AS similarity
    FROM project_vectors pv
    WHERE pv.project_id = match_project_id
      AND 1 - (pv.embedding <=> query_embedding) > match_threshold
    ORDER BY pv.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 语义缓存相似度搜索
CREATE OR REPLACE FUNCTION match_semantic_cache(
    query_embedding VECTOR(1536),
    match_model VARCHAR(100),
    match_threshold FLOAT DEFAULT 0.95,
    match_count INT DEFAULT 1
)
RETURNS TABLE (
    id UUID,
    response TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        sc.id,
        sc.response,
        1 - (sc.prompt_embedding <=> query_embedding) AS similarity
    FROM semantic_cache sc
    WHERE sc.model_name = match_model
      AND 1 - (sc.prompt_embedding <=> query_embedding) > match_threshold
    ORDER BY sc.prompt_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_project_vectors IS 'RAG 向量搜索：在项目上下文中搜索相似文本块';
COMMENT ON FUNCTION match_semantic_cache IS '语义缓存搜索：查找相似 Prompt 的缓存响应';
