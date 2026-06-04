from supabase_client import supabase
from database import _COMPLAINTS

# Upload all complaints
result = supabase.table("complaints").insert(_COMPLAINTS).execute()

print(f"Uploaded {len(_COMPLAINTS)} complaint categories")
print(result)