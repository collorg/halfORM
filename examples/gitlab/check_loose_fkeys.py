from half_orm.model import Model

model = Model('gitlab')
# Check the loose foreign keys table
loose_fks = model.get_relation_class("public.loose_foreign_keys_deleted_records")()
print(f"Pending deletions to process: {loose_fks.ho_count()}")

# See what tables are affected
for record in loose_fks.ho_limit(5):
    print(f"Deleted from {record['fully_qualified_table_name']}: ID {record['primary_key_value']}")
