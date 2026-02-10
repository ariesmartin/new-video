-- =====================================================
-- Fix: Simplified RLS Policies for story_plans and content_reviews
-- 不依赖 project_members 表，仅使用 projects.user_id
-- =====================================================

-- story_plans: 仅项目所有者和管理员可访问
CREATE POLICY "Project owner can view story_plans" 
ON story_plans FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = story_plans.project_id
        AND projects.user_id = auth.uid()
    )
);

CREATE POLICY "Project owner can insert story_plans" 
ON story_plans FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = story_plans.project_id
        AND projects.user_id = auth.uid()
    )
);

CREATE POLICY "Project owner can update story_plans" 
ON story_plans FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = story_plans.project_id
        AND projects.user_id = auth.uid()
    )
);

CREATE POLICY "Project owner can delete story_plans" 
ON story_plans FOR DELETE USING (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = story_plans.project_id
        AND projects.user_id = auth.uid()
    )
);

-- content_reviews: 仅项目所有者和管理员可访问
CREATE POLICY "Project owner can view content_reviews" 
ON content_reviews FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = content_reviews.project_id
        AND projects.user_id = auth.uid()
    )
);

CREATE POLICY "Project owner can insert content_reviews" 
ON content_reviews FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = content_reviews.project_id
        AND projects.user_id = auth.uid()
    )
);

CREATE POLICY "Project owner can update content_reviews" 
ON content_reviews FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = content_reviews.project_id
        AND projects.user_id = auth.uid()
    )
);

-- 服务角色绕过策略 (用于后端服务)
CREATE POLICY "Service role can access all story_plans"
ON story_plans FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all content_reviews"
ON content_reviews FOR ALL USING (auth.role() = 'service_role');

-- 完成
