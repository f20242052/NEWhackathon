from supabase import create_client

SUPABASE_URL = "https://nmxelnvpvcafbmphcsxs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5teGVsbnZwdmNhZmJtcGhjc3hzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1MzY0ODUsImV4cCI6MjA5NjExMjQ4NX0.l6-ZmaMnhZolHFpR0VM_acMLGHPOyq_SI0YXGcj_r5U"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)