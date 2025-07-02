import gitlab

Users = gitlab.model.get_relation_class('public.users')
# list the admins names
for admin in Users(admin=True).ho_select('name'):
    print(admin['name'])

