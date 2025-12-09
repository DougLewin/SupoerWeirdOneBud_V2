-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USERS TABLE (extends Supabase auth.users)
-- ============================================================
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- COMMUNITIES TABLE
-- ============================================================
CREATE TABLE public.communities (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- COMMUNITY MEMBERS JUNCTION TABLE
-- ============================================================
CREATE TABLE public.community_members (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    community_id UUID REFERENCES public.communities(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(community_id, user_id)
);

-- ============================================================
-- RECORDS TABLE (surf session tracking)
-- ============================================================
CREATE TABLE public.records (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    community_id UUID REFERENCES public.communities(id) ON DELETE SET NULL,
    publicity TEXT NOT NULL DEFAULT 'Private' CHECK (publicity IN ('Private', 'Public', 'Community')),
    
    -- Session Details
    date DATE NOT NULL,
    time TIME,
    break TEXT,
    zone TEXT,
    total_score DECIMAL(5, 2),
    
    -- Swell Data
    surfline_primary_swell_size_m DECIMAL(4, 2),
    seabreeze_swell_m DECIMAL(4, 2),
    swell_period_s INTEGER,
    swell_direction DECIMAL(5, 2),
    suitable_swell TEXT,
    swell_score INTEGER,
    final_swell_score INTEGER,
    swell_comments TEXT,
    
    -- Wind Data
    wind_bearing TEXT,
    wind_speed_kn INTEGER,
    suitable_wind TEXT,
    wind_score INTEGER,
    wind_final_score INTEGER,
    wind_comments TEXT,
    
    -- Tide Data
    tide_reading_m DECIMAL(4, 2),
    tide_direction TEXT,
    tide_suitable TEXT,
    tide_score INTEGER,
    tide_final_score DECIMAL(4, 2),
    tide_comments TEXT,
    
    -- Commentary
    full_commentary TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================
CREATE INDEX idx_records_user_id ON public.records(user_id);
CREATE INDEX idx_records_community_id ON public.records(community_id);
CREATE INDEX idx_records_publicity ON public.records(publicity);
CREATE INDEX idx_records_date ON public.records(date);
CREATE INDEX idx_records_break ON public.records(break);
CREATE INDEX idx_records_zone ON public.records(zone);
CREATE INDEX idx_records_total_score ON public.records(total_score);
CREATE INDEX idx_community_members_user_id ON public.community_members(user_id);
CREATE INDEX idx_community_members_community_id ON public.community_members(community_id);

-- ============================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.communities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.records ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- PROFILES POLICIES
-- ============================================================
CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- ============================================================
-- RECORDS POLICIES
-- ============================================================

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

-- ============================================================
-- COMMUNITIES POLICIES
-- ============================================================
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

-- ============================================================
-- COMMUNITY MEMBERS POLICIES
-- ============================================================
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

CREATE POLICY "Users can leave communities"
    ON public.community_members FOR DELETE
    USING (user_id = auth.uid() OR EXISTS (
        SELECT 1 FROM public.communities
        WHERE id = community_id
        AND owner_id = auth.uid()
    ));

-- ============================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communities_updated_at BEFORE UPDATE ON public.communities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_records_updated_at BEFORE UPDATE ON public.records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- AUTO-CREATE PROFILE ON USER SIGNUP
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
