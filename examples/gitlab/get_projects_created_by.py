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
