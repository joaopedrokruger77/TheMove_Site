from supabase_client import supabase

print("Deletando duplicados (IDs 28 a 36)...")
for i in range(28, 37):
    supabase.table('eventos').delete().eq('id', i).execute()

print("Feito.")
