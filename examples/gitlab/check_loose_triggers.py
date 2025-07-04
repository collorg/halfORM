from half_orm.model import Model

model = Model('gitlab')
# Via half_orm mais avec du SQL brut pour les triggers
triggers_query = """
SELECT DISTINCT trigger_name 
FROM information_schema.triggers 
WHERE trigger_name LIKE '%loose_fk%'
"""
for elt in model.execute_query(triggers_query):
    rel_name = elt['trigger_name'].replace('_loose_fk_trigger', '')
    try:
        model.get_relation_class(f'public.{rel_name}')
    except:
        print(f'❌ {rel_name} (partition?)')
        continue
    print(rel_name)
