-- ============================================================
-- UPDATE RLS POLICIES FOR PUBLIC/PRIVATE ACCESS CONTROL
-- Migration: Consolidate multiple SELECT policies into one
-- ============================================================

-- Drop old individual SELECT policies
DROP POLICY IF EXISTS "Users can view their own private records" ON public.records;
DROP POLICY IF EXISTS "Anyone can view public records" ON public.records;
DROP POLICY IF EXISTS "Community members can view community records" ON public.records;

-- Create new consolidated SELECT policy
-- This allows authenticated users to view:
-- 1. Their own private records
-- 2. Any public record (from any user)
-- 3. Community records if they're a member
CREATE POLICY "Users can view accessible records"
    ON public.records FOR SELECT
    USING (
        -- Own private records
        (user_id = auth.uid() AND publicity = 'Private')
        OR
        -- All public records
        (publicity = 'Public')
        OR
        -- Community records where user is a member
        (publicity = 'Community' AND community_id IN (
            SELECT community_id 
            FROM public.community_members 
            WHERE user_id = auth.uid()
        ))
    );
