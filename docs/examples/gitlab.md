# Database Exploration with GitLab

Ever wondered what complex real-world databases look like? Let's explore GitLab's schema with halfORM - safely, without touching any data!

> **🚨 IMPORTANT**: This example uses a development GitLab database. 
> **NEVER run schema modifications on production databases!**
> 
> The `ALTER TABLE` command shown is for educational purposes only.

## What This Example Demonstrates

- **Schema exploration** with halfORM CLI
- **Real-world complexity** handling (888 relations)
- **Foreign key analysis** and relationship discovery
- **Database inspection** without touching production data
- **Database patching** (not in production, this is just an example)
- **Custom tooling** with halfORM (fkeys_between.py)

## Initial Discovery: The Scale

GitLab is a perfect example of a complex application. Let's explore its database model.
!!! note
    To realise this exercise, we have restored a snapshot of a Gitlab database locally.

```sh
$ python -m half_orm gitlab
[halfORM] version 0.15.1
📋 Available relations for gitlab:
p "public"."ai_code_suggestion_events"                                     → No description available
p "public"."ai_duo_chat_events"                                            → No description available
[...]
$ python -m half_orm gitlab | grep -E '^r ' | wc -l
812 # relations
$ python -m half_orm gitlab | grep -E '^v ' | wc -l
14  # views
$ python -m half_orm gitlab | grep -E '^p ' | wc -l
53  # partitioned tables
```

That's quite a large model to work with! Let's see which relations have `users` in their name:

```sh
$ python -m half_orm gitlab | grep users
r "public"."approval_group_rules_users"                                    → No description available
r "public"."approval_merge_request_rules_users"                            → No description available
r "public"."approval_project_rules_users"                                  → No description available
r "public"."banned_users"                                                  → No description available
r "public"."import_source_users"                                           → No description available
r "public"."merge_request_diff_commit_users"                               → No description available
r "public"."merge_requests_approval_rules_approver_users"                  → No description available
r "public"."metrics_users_starred_dashboards"                              → No description available
r "public"."namespace_import_users"                                         → No description available
r "public"."organization_users"                                            → No description available
r "public"."pipl_users"                                                    → No description available
r "public"."user_follow_users"                                             → No description available
r "public"."users"                                                         → No description available
r "public"."users_ops_dashboard_projects"                                  → No description available
r "public"."users_security_dashboard_projects"                             → No description available
r "public"."users_star_projects"                                           → No description available
r "public"."users_statistics"                                              → No description available
```

## Deep Dive: Users Table Structure

Let's examine the main `users` table:

```sh
$ python -m half_orm gitlab public.users | less
DATABASE: gitlab
SCHEMA: public
TABLE: users

FIELDS:
- id:                                           (int4) NOT NULL
- email:                                        (varchar) NOT NULL
- encrypted_password:                           (varchar) NOT NULL
- reset_password_token:                         (varchar)
- reset_password_sent_at:                       (timestamp)
- remember_created_at:                          (timestamp)
- sign_in_count:                                (int4)
- current_sign_in_at:                           (timestamp)
- last_sign_in_at:                              (timestamp)
- current_sign_in_ip:                           (varchar)
- last_sign_in_ip:                              (varchar)
- created_at:                                   (timestamp)
- updated_at:                                   (timestamp)
- name:                                         (varchar)
- admin:                                        (bool) NOT NULL
[...]
```

This is quite a large table: 78 columns, 170 relations pointing to it. That means we have 170 entries like these in the Fkeys dictionary:

```
[...]
Fkeys = {
    '': '_reverse_fkey_gitlab_public_abuse_events_user_id',
    '': '_reverse_fkey_gitlab_public_abuse_report_events_user_id',
    '': '_reverse_fkey_gitlab_public_abuse_report_notes_author_id',
    [...]
}
```

## First halfORM Script

We have enough information to start exploring. Let's look at the administrators:

```python
from half_orm.model import Model

gitlab = Model('gitlab')
Users = gitlab.get_relation_class('public.users')
# List the admin names
for admin in Users(admin=True).ho_select('name'):
    print(admin['name'])
```

## Finding Relationships

Now, is there a `projects` table?

```sh
$ python -m half_orm gitlab | grep projects
p "public"."projects_visits"                                               → No description available
r "public"."ci_runner_projects"                                            → No description available
r "public"."ci_sources_projects"                                           → No description available
r "public"."ci_subscriptions_projects"                                     → No description available
r "public"."cluster_projects"                                              → No description available
r "public"."deploy_keys_projects"                                          → No description available
r "public"."elasticsearch_indexed_projects"                                → No description available
r "public"."lfs_objects_projects"                                          → No description available
r "public"."merge_requests_approval_rules_projects"                        → No description available
r "public"."projects"                                                      → No description available
r "public"."projects_branch_rules_merge_request_approval_settings"         → No description available
r "public"."projects_branch_rules_squash_options"                          → No description available
r "public"."projects_sync_events"                                          → No description available
r "public"."projects_with_pipeline_variables"                              → No description available
r "public"."trending_projects"                                             → No description available
r "public"."users_ops_dashboard_projects"                                  → No description available
r "public"."users_security_dashboard_projects"                             → No description available
r "public"."users_star_projects"                                           → No description available
```

Great! We have a `"public"."projects"` table.

## Building Analysis Tools

We'd like to know if there are any foreign keys between the `public.users` table and the `public.projects` table. Let's write a script for that:

```python title="fkeys_between.py"
#!/usr/bin/env python3
"""
Analyze foreign key relationships between two relations.
Usage: fkeys_between.py <database> <relation1> <relation2>
"""

import sys
from half_orm.model import Model

def find_relationships(relation1, relation2):
    """Find all foreign key relationships between two relations"""
    direct = []
    reverse = []
    
    # Direct: relation1 -> relation2
    for fk_name, fk_rel in relation1()._ho_fkeys.items():
        if fk_rel()._qrn == relation2._qrn:
            direct.append((fk_name, fk_rel))
    
    # Reverse: relation2 -> relation1  
    for fk_name, fk_rel in relation2()._ho_fkeys.items():
        if fk_rel()._qrn == relation1._qrn:
            reverse.append((fk_name, fk_rel))
    
    return direct, reverse

def main():
    if len(sys.argv) != 4:
        print("Usage: fkeys_between.py <database> <relation1> <relation2>")
        print("Example: fkeys_between.py gitlab public.users public.projects")
        sys.exit(1)
    
    dbname, rel1_name, rel2_name = sys.argv[1:]
    
    try:
        database = Model(dbname)
        relation1 = database.get_relation_class(rel1_name)
        relation2 = database.get_relation_class(rel2_name)
        
        direct, reverse = find_relationships(relation1, relation2)
        
        print(f"=== RELATIONSHIPS BETWEEN {rel1_name} AND {rel2_name} ===")
        print(f"\nDirect ({rel1_name} → {rel2_name}):")
        if direct:
            for fk_name, fk_rel in direct:
                print(f"  • {fk_name}")
        else:
            print("  (none)")
            
        print(f"\nReverse ({rel2_name} → {rel1_name}):")
        if reverse:
            for fk_name, fk_rel in reverse:
                print(f"  • {fk_name}")
        else:
            print("  (none)")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

Let's run our analysis script:

```sh
$ examples/fkeys_between.py gitlab public.users public.projects
=== RELATIONSHIPS BETWEEN public.users AND public.projects ===

Direct (public.users → public.projects):
  • _reverse_fkey_gitlab_public_projects_marked_for_deletion_by_user_id

Reverse (public.projects → public.users):
  • fk_0a31cca0b8
```

## Discovering GitLab's Innovative Schema Design

Interesting! There's only one foreign key from `public.projects` to `public.users`: `fk_0a31cca0b8`. This means there's no foreign key constraint on the `creator_id` column in the `public.projects` relation. At first glance, this seems like a schema issue. In a traditional database, we might add:

```sql
ALTER TABLE projects
    ADD CONSTRAINT creator_fk
    FOREIGN KEY (creator_id)
    REFERENCES users(id);
```

### The Solution: GitLab's Loose Foreign Keys Pattern
But wait! This isn't a bug—it's a brilliant feature! 🚀

!!! note "The mystery of the missing FOREIGN KEY"
    This is not an issue. This is a feature!
    GitLab has a very clever way to store the deleted keys in the table `loose_foreign_keys_deleted_records`:

    ```sql
    -- The loose foreign keys deletion tracking table
    CREATE TABLE public.loose_foreign_keys_deleted_records (
        id bigint NOT NULL,
        partition bigint DEFAULT 197 NOT NULL,
        primary_key_value bigint NOT NULL,           -- ID of deleted record
        status smallint DEFAULT 1 NOT NULL,          -- Processing status  
        created_at timestamp with time zone DEFAULT now() NOT NULL,
        fully_qualified_table_name text NOT NULL,   -- Which table was affected
        consume_after timestamp with time zone DEFAULT now(),
        cleanup_attempts smallint DEFAULT 0,        -- Retry counter
        CONSTRAINT check_1a541f3235 CHECK ((char_length(fully_qualified_table_name) <= 150))
    ) PARTITION BY LIST (partition);

    -- Trigger function to log deletions
    CREATE FUNCTION public.insert_into_loose_foreign_keys_deleted_records() 
    RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        -- Log every deleted FQTN, ID for later cleanup or undelete
        INSERT INTO loose_foreign_keys_deleted_records
            (fully_qualified_table_name, primary_key_value)
        SELECT TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME, old_table.id 
        FROM old_table;
        
        RETURN NULL; -- Trigger is for logging only
    END $$;

    -- Apply trigger to users table
    CREATE TRIGGER users_loose_fk_trigger
        AFTER DELETE ON public.users
        REFERENCING OLD TABLE AS old_table  -- PostgreSQL 10+ feature
        FOR EACH STATEMENT
        EXECUTE FUNCTION public.insert_into_loose_foreign_keys_deleted_records();
    ```

    This mechanism allows them to delay the actual deletion of a row in any table for which
    this function is triggered. It provides several key benefits:

    **🔄 Grace Period for Recovery**: Administrators can restore accidentally deleted users and their associated data within a defined time window.

    **⚡ Performance Optimization**: Deletions don't require checking foreign key constraints across hundreds of tables, making operations faster.

    **🛡️ Data Safety**: Critical data (commits, issues, merge requests) remains accessible even if a user account is deleted, preventing data loss.

    **🧹 Deferred Cleanup**: A background job processes the cleanup queue, distributing the workload over time instead of blocking the deletion operation.

### Exploring This Pattern with halfORM

```python title=""
from half_orm.model import Model

model = Model('gitlab')
# Check the loose foreign keys table
loose_fks = model.get_relation_class("public.loose_foreign_keys_deleted_records")()
print(f"Pending deletions to process: {loose_fks.ho_count()}")

# See what tables are affected
for record in loose_fks.ho_limit(5):
    print(f"Deleted from {record['fully_qualified_table_name']}: ID {record['primary_key_value']}")
```

```sh
$ python check_loose_fkeys.py 
Pending deletions to process: 2
Deleted from public.ci_runners: ID 186
Deleted from public.ci_runners: ID 185
```

## What We Discovered

Through this exploration, we found:

- **888 relations** in GitLab's database - a complex real-world schema
- **78 columns** in the users table with **170 foreign key relationships**
- **Missing constraints as a feature**: `projects.creator_id` deliberately has no foreign key constraint!
- **Analysis tools**: halfORM makes it easy to build custom database analysis scripts

This demonstrates how halfORM can help you:
- 🔍 **Explore** unfamiliar databases quickly
- 🔗 **Analyze** relationships between tables  
- 🛠️ **Build** custom tools for database inspection
- 💡 **Discover** innovative design patterns (like loose foreign keys)

### Key Takeaways

1. **"Missing" constraints can be intentional design decisions** - GitLab's loose foreign keys provide operational flexibility
2. **High-scale applications often break traditional rules** for performance and recovery reasons  
3. **halfORM's introspection helps understand real-world patterns** - even unconventional ones
4. **Database design is about trade-offs** - GitLab chose operational safety and performance over strict consistency
5. **Application-level integrity** can replace database-level constraints when the benefits justify the complexity
6. **Recovery mechanisms** are crucial for production systems where accidental deletions could have catastrophic consequences

This pattern shows why exploring real production databases is so valuable for learning! It reveals how theory meets practice in high-scale, mission-critical applications. 🎓

## Next Steps

Try this approach with your own database:

```bash
# Explore your database
python -m half_orm your_database

# Find tables with 'user' in the name  
python -m half_orm your_database | grep user

# Inspect a specific table
python -m half_orm your_database schema.table_name

# Look for loose foreign key patterns
python -m half_orm your_database | grep loose
```