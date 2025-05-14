-- Migration file to enable Row Level Security (RLS) on tables
-- This script should be executed in your Supabase SQL editor

-- First, enable RLS on all tables that need it
ALTER TABLE public.journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mood_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stress_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.self_care_activities ENABLE ROW LEVEL SECURITY;

-- Create policies for the users table
-- Policy: Users can only view and edit their own profile
CREATE POLICY "Users can view own profile"
  ON public.users
  FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.users
  FOR UPDATE
  USING (auth.uid() = id);

-- Policy: Allow admins to view all users
CREATE POLICY "Admins can view all users"
  ON public.users
  FOR SELECT
  USING (auth.role() = 'authenticated' AND EXISTS (
    SELECT 1 FROM public.users WHERE id = auth.uid() AND is_superuser = true
  ));

-- Create policies for journal_entries table
-- Policy: Users can only view their own journal entries
CREATE POLICY "Users can view own journal entries"
  ON public.journal_entries
  FOR SELECT
  USING (auth.uid()::text = user_id::text);

-- Policy: Users can only create journal entries for themselves
CREATE POLICY "Users can create own journal entries"
  ON public.journal_entries
  FOR INSERT
  WITH CHECK (auth.uid()::text = user_id::text);

-- Policy: Users can only update/delete their own journal entries
CREATE POLICY "Users can update own journal entries"
  ON public.journal_entries
  FOR UPDATE
  USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own journal entries"
  ON public.journal_entries
  FOR DELETE
  USING (auth.uid()::text = user_id::text);

-- Create policies for mood_logs table
-- Policy: Users can only view their own mood logs
CREATE POLICY "Users can view own mood logs"
  ON public.mood_logs
  FOR SELECT
  USING (auth.uid()::text = user_id::text);

-- Policy: Users can only create mood logs for themselves
CREATE POLICY "Users can create own mood logs"
  ON public.mood_logs
  FOR INSERT
  WITH CHECK (auth.uid()::text = user_id::text);

-- Policy: Users can only update/delete their own mood logs
CREATE POLICY "Users can update own mood logs"
  ON public.mood_logs
  FOR UPDATE
  USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own mood logs"
  ON public.mood_logs
  FOR DELETE
  USING (auth.uid()::text = user_id::text);

-- Create policies for stress_events table
-- Policy: Users can only view their own stress events
CREATE POLICY "Users can view own stress events"
  ON public.stress_events
  FOR SELECT
  USING (auth.uid()::text = user_id::text);

-- Policy: Users can only create stress events for themselves
CREATE POLICY "Users can create own stress events"
  ON public.stress_events
  FOR INSERT
  WITH CHECK (auth.uid()::text = user_id::text);

-- Policy: Users can only update/delete their own stress events
CREATE POLICY "Users can update own stress events"
  ON public.stress_events
  FOR UPDATE
  USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own stress events"
  ON public.stress_events
  FOR DELETE
  USING (auth.uid()::text = user_id::text);

-- Create policies for self_care_activities table
-- Policy: Users can only view their own self-care activities
CREATE POLICY "Users can view own self-care activities"
  ON public.self_care_activities
  FOR SELECT
  USING (auth.uid()::text = user_id::text);

-- Policy: Users can only create self-care activities for themselves
CREATE POLICY "Users can create own self-care activities"
  ON public.self_care_activities
  FOR INSERT
  WITH CHECK (auth.uid()::text = user_id::text);

-- Policy: Users can only update/delete their own self-care activities
CREATE POLICY "Users can update own self-care activities"
  ON public.self_care_activities
  FOR UPDATE
  USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own self-care activities"
  ON public.self_care_activities
  FOR DELETE
  USING (auth.uid()::text = user_id::text); 