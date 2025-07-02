import gitlab

class Projects(gitlab.model.get_relation_class('public.projects')):
    Fkeys = {
        'creator_fk': 'creator_fk'
    }
