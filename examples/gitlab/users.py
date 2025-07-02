import gitlab

class Users(gitlab.model.get_relation_class('public.users')):
    Fkeys = {
        'projects_rfk': '_reverse_fkey_gitlab_public_projects_creator_id'
    }
