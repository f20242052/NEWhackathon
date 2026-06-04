from supabase_client import supabase

print("Starting test")

result = supabase.table("departments").select("*").execute()

print("Query finished")
print(result.data)