-- ============================================================
-- SQL SCRIPTS FOR SUPABASE SETUP
-- ============================================================
-- Copy and run these in Supabase SQL Editor
-- Dashboard → SQL Editor → New Query → Paste → Run

-- ============================================================
-- PART 1: ENABLE UUID EXTENSION
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- PART 2: CREATE TABLES
-- ============================================================

-- User Profiles (extends Supabase auth.users)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Communities (for future shared forecasting feature)
CREATE TABLE public.communities (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Community Membership
CREATE TABLE public.community_members (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    community_id UUID REFERENCES public.communities(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(community_id, user_id)
);

-- Surf Session Records
-- Matches all columns from Rotto_Tracker.csv plus user/community fields
CREATE TABLE public.records (
    -- System Fields
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    community_id UUID REFERENCES public.communities(id) ON DELETE SET NULL,
    publicity TEXT NOT NULL DEFAULT 'Private' CHECK (publicity IN ('Private', 'Public', 'Community')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Session Metadata
    date DATE NOT NULL,
    time TIME,
    break TEXT,
    zone TEXT,
    total_score DECIMAL(5, 2),
    
    -- Swell Information
    surfline_primary_swell_size_m DECIMAL(4, 2),  -- "Surfline Primary Swell Size (m)"
    seabreeze_swell_m DECIMAL(4, 2),              -- "Seabreeze Swell (m)"
    swell_period_s INTEGER,                        -- "Swell Period (s)"
    swell_direction DECIMAL(5, 2),                 -- "Swell Direction" (degrees)
    suitable_swell TEXT,                           -- "Suitable Swell?" (Yes/No/Ok/Too Big)
    swell_score INTEGER,                           -- "Swell Score" (0-10)
    final_swell_score INTEGER,                     -- "Final Swell Score" (calculated)
    swell_comments TEXT,                           -- "Swell Comments"
    
    -- Wind Information
    wind_bearing TEXT,                             -- "Wind Bearing" (N/NE/E/SE/S/SW/W/NW)
    wind_speed_kn INTEGER,                         -- "Wind Speed (kn)"
    suitable_wind TEXT,                            -- "Suitable Wind?" (Yes/No/Ok)
    wind_score INTEGER,                            -- "Wind Score" (0-10)
    wind_final_score INTEGER,                      -- "Wind Final Score" (calculated)
    wind_comments TEXT,                            -- "Wind Comments"
    
    -- Tide Information
    tide_reading_m DECIMAL(4, 2),                  -- "Tide Reading (m)"
    tide_direction TEXT,                           -- "Tide Direction" (High/Low/Rising/Falling)
    tide_suitable TEXT,                            -- "Tide Suitable?" (Yes/No/Ok)
    tide_score INTEGER,                            -- "Tide Score" (0-10)
    tide_final_score DECIMAL(4, 2),                -- "Tide Final Score" (calculated)
    tide_comments TEXT,                            -- "Tide Comments"
    
    -- Commentary
    full_commentary TEXT                           -- "Full Commentary" (combined comments)
);

-- ============================================================
-- PART 3: CREATE INDEXES FOR PERFORMANCE
-- ============================================================

-- Records indexes
CREATE INDEX idx_records_user_id ON public.records(user_id);
CREATE INDEX idx_records_community_id ON public.records(community_id);
CREATE INDEX idx_records_publicity ON public.records(publicity);
CREATE INDEX idx_records_date ON public.records(date);
CREATE INDEX idx_records_break ON public.records(break);
CREATE INDEX idx_records_zone ON public.records(zone);
CREATE INDEX idx_records_total_score ON public.records(total_score);

-- Community indexes
CREATE INDEX idx_community_members_user_id ON public.community_members(user_id);
CREATE INDEX idx_community_members_community_id ON public.community_members(community_id);

-- ============================================================
-- PART 4: ENABLE ROW LEVEL SECURITY (RLS)
-- ============================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.communities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.records ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- PART 5: CREATE RLS POLICIES
-- ============================================================

-- PROFILES POLICIES
CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- RECORDS POLICIES

-- Users can insert their own records
CREATE POLICY "Users can insert their own records"
    ON public.records FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Users can view their own private records
CREATE POLICY "Users can view their own private records"
    ON public.records FOR SELECT
    USING (
        user_id = auth.uid() 
        AND publicity = 'Private'
    );

-- Anyone can view public records
CREATE POLICY "Anyone can view public records"
    ON public.records FOR SELECT
    USING (publicity = 'Public');

-- Community members can view community records
CREATE POLICY "Community members can view community records"
    ON public.records FOR SELECT
    USING (
        publicity = 'Community' 
        AND community_id IN (
            SELECT community_id 
            FROM public.community_members 
            WHERE user_id = auth.uid()
        )
    );

-- Users can update their own records
CREATE POLICY "Users can update their own records"
    ON public.records FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Users can delete their own records
CREATE POLICY "Users can delete their own records"
    ON public.records FOR DELETE
    USING (user_id = auth.uid());

-- COMMUNITIES POLICIES
CREATE POLICY "Anyone can view communities"
    ON public.communities FOR SELECT
    USING (true);

CREATE POLICY "Authenticated users can create communities"
    ON public.communities FOR INSERT
    WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Community owners can update their communities"
    ON public.communities FOR UPDATE
    USING (auth.uid() = owner_id);

CREATE POLICY "Community owners can delete their communities"
    ON public.communities FOR DELETE
    USING (auth.uid() = owner_id);

-- COMMUNITY MEMBERS POLICIES
CREATE POLICY "Users can view community memberships"
    ON public.community_members FOR SELECT
    USING (true);

CREATE POLICY "Community owners can add members"
    ON public.community_members FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.communities
            WHERE id = community_id
            AND owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can leave communities or owners can remove"
    ON public.community_members FOR DELETE
    USING (
        user_id = auth.uid() 
        OR EXISTS (
            SELECT 1 FROM public.communities
            WHERE id = community_id
            AND owner_id = auth.uid()
        )
    );

-- ============================================================
-- PART 6: CREATE AUTOMATIC TIMESTAMP TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at 
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communities_updated_at 
    BEFORE UPDATE ON public.communities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_records_updated_at 
    BEFORE UPDATE ON public.records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- PART 7: AUTO-CREATE PROFILE ON USER SIGNUP
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, created_at, updated_at)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- VERIFICATION QUERIES (Optional - run to verify setup)
-- ============================================================

-- Check all tables were created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Check RLS is enabled
-- SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

-- Check policies were created
-- SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public';

-- Check triggers exist
-- SELECT trigger_name, event_object_table FROM information_schema.triggers WHERE trigger_schema = 'public';

-- ============================================================
-- SETUP COMPLETE!
-- ============================================================
-- Next steps:
-- 1. Get your SUPABASE_URL and SUPABASE_KEY from Settings → API
-- 2. Add them to .streamlit/secrets.toml
-- 3. Run: pip install supabase==2.10.0
-- 4. Run: streamlit run superweirdonebud_supabase.py
-- 5. Sign up for an account and start tracking!
