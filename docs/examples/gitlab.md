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

GitLab is a perfect example of a complex application. Let's explore its database model (**not in production, of course**).

```sh
$ python -m half_orm gitlab
[halfORM] version 0.15.1
📋 Available relations for gitlab:
p "public"."ai_code_suggestion_events"                                     → No description available
p "public"."ai_duo_chat_events"                                            → No description available
[...]
$ python -m half_orm gitlab | wc -l
888
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
$ python -m half_orm gitlab public.users
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

This is quite a large table with 78 columns and 170 relations pointing to it. That means we have 170 entries like these in the Fkeys dictionary:

```
[...]
PRIMARY KEY (id)
FOREIGN KEYS:
- _reverse_fkey_gitlab_public_abuse_events_user_id: ("id")
 ↳ "gitlab":"public"."abuse_events"(user_id)
- _reverse_fkey_gitlab_public_abuse_report_events_user_id: ("id")
 ↳ "gitlab":"public"."abuse_report_events"(user_id)
- _reverse_fkey_gitlab_public_abuse_report_notes_author_id: ("id")
 ↳ "gitlab":"public"."abuse_report_notes"(author_id)
[...]
Fkeys = {
    '': '_reverse_fkey_gitlab_public_abuse_events_user_id',
    '': '_reverse_fkey_gitlab_public_abuse_report_events_user_id',
    '': '_reverse_fkey_gitlab_public_abuse_report_notes_author_id',
[...]
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

## Discovering Schema Issues

Interesting! There's only one foreign key from `public.projects` to `public.users`: `fk_0a31cca0b8`. This means there's no foreign key constraint on the `creator_id` column in the `public.projects` relation. Let's fix the schema by adding that constraint (again, **we are not in production here!**):

```sql
ALTER TABLE projects ADD CONSTRAINT creator_fk FOREIGN KEY (creator_id) REFERENCES users(id);
```

Now `fkeys_between.py` shows:

```
=== RELATIONSHIPS BETWEEN public.users AND public.projects ===

Direct (public.users → public.projects):
  • _reverse_fkey_gitlab_public_projects_creator_id
  • _reverse_fkey_gitlab_public_projects_marked_for_deletion_by_user_id

Reverse (public.projects → public.users):
  • creator_fk
  • fk_0a31cca0b8
```

## Building a Project Structure

Now that we have the new foreign key, we can use it in our halfORM scripts.

First, let's create a `gitlab` directory where we'll put all our modules:

```sh
$ mkdir gitlab
$ export PYTHONPATH=$PWD
$ cd gitlab
```

In that directory, we'll create the `__init__.py` file that will handle the model shared between all modules:

```python title="__init__.py"
from half_orm.model import Model

model = Model('gitlab')
```

Let's test the `__init__.py` by reusing the script that lists the administrators:

```python title="admins.py"
import gitlab

Users = gitlab.model.get_relation_class('public.users')
# List the admin names
for admin in Users(admin=True).ho_select('name'):
    print(admin['name'])
```

Now let's create the modules `projects.py` and `users.py`:

```python title="projects.py"
import gitlab

class Projects(gitlab.model.get_relation_class('public.projects')):
    Fkeys = {
        'creator_fk': 'creator_fk'
    }
```

```python title="users.py"
import gitlab

class Users(gitlab.model.get_relation_class('public.users')):
    Fkeys = {
        'projects_rfk': '_reverse_fkey_gitlab_public_projects_creator_id'
    }
```

## Putting It All Together

Now we can use these modules in a practical script:

```python title="get_projects_created_by.py"
#!/usr/bin/env python3
"""
Get all projects created by a specific user.
Usage: get_projects_created_by.py <username>
"""
import sys
from gitlab.users import Users

def main():
    if len(sys.argv) != 2:
        print("Usage: get_projects_created_by.py <username>")
        print("Example: get_projects_created_by.py alice")
        sys.exit(1)

    username = sys.argv[1]

    try:
        user = Users(username=username)
        if user.ho_is_empty():
            print(f"❌ User '{username}' not found")
            sys.exit(1)

        project_count = user.projects_rfk().ho_count()
        projects = user.projects_rfk().ho_order_by('created_at DESC')

        if project_count == 0:
            print(f"📭 User '{username}' has no projects")
        else:
            print(f"📂 Projects created by '{username}' ({project_count} total):")
            for project in projects.ho_select('name', 'created_at'):
                print(f"  • {project['name']} (created: {project['created_at']})")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

Example output:
```sh
$ python get_projects_created_by.py alice
📂 Projects created by 'alice' (3 total):
  • awesome-project (created: 2024-01-15 14:30:00)
  • data-analysis-tool (created: 2024-01-10 09:15:00)  
  • documentation-site (created: 2024-01-05 16:45:00)
```

## What We Discovered

Through this exploration, we found:

- **888 relations** in GitLab's database - a complex real-world schema
- **78 columns** in the users table with **170 foreign key relationships**
- **Missing constraint**: `projects.creator_id` had no foreign key constraint!
- **Analysis tools**: halfORM makes it easy to build custom database analysis scripts

This demonstrates how halfORM can help you:
- 🔍 **Explore** unfamiliar databases quickly
- 🔗 **Analyze** relationships between tables  
- 🛠️ **Build** custom tools for database inspection
- 🐛 **Discover** schema issues (like missing constraints)

## Key Takeaways

- halfORM's CLI is perfect for **database exploration**
- **No prior schema knowledge required** - just start exploring
- **Real databases** often have missing constraints (like creator_id)
- halfORM makes it easy to **build custom analysis tools**
- You can **inspect production schemas safely** without touching data

## Next Steps

Try this approach with your own database:

```bash
# Explore your database
python -m half_orm your_database

# Find tables with 'user' in the name  
python -m half_orm your_database | grep user

# Inspect a specific table
python -m half_orm your_database schema.table_name
```