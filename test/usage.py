#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from datetime import datetime
from halfORM.model import TableFactory, table, Model

class OidTable(metaclass=TableFactory):
    fqtn = 'dpt_info."collorg.core".oid_table'

class BaseTable(metaclass=TableFactory):
    fqtn = '"dpt_info"."collorg.core".base_table'

class ViewSession(metaclass=TableFactory):
    fqtn = 'dpt_info."seminaire.view"."session"'

if __name__ == '__main__':
    """
    OidTable()
    BaseTable()
    ViewSession()
    PgDatabase()
    table('dpt_info.seminaire.session')
    sys.exit()
    """
    print(OidTable())
    print(BaseTable())
    print(ViewSession())
    print(table('dpt_info.seminaire.session'))
    Model('dpt_info').desc()

    """profiling"""
    for i in range(1000):
        table('dpt_info."collorg.core".base_table')

    """request with no constraint."""
    bt = table('dpt_info."collorg.core".data_type')
    count = 0
    for elt in bt.select():
        count += 1
    print(count)
    bt = table('dpt_info."collorg.core".base_table')
    """Put a constraint on a Field"""
    assert bt.cog_fqtn.is_set is False
    bt.cog_fqtn.set('collorg.access.access')
    assert bt.cog_fqtn.is_set is True
    assert bt.cog_fqtn.get() is bt.cog_fqtn.value
    assert bt.cog_oid.is_set is False
    bt.cog_oid.value = 'd%', 'like'
    assert bt.cog_oid.is_set is True
    assert bt.cog_oid.value == 'd%'
    assert bt.cog_oid.comp == 'like'
    bt.cog_test.value = None, 'is not'
    try:
        bt.cog_test.set(None, '!=')
        assert False
    except:
        bt.cog_test.set(None, 'is')
    assert bt.cog_test.is_set and bt.cog_test.value is None
    assert bt.cog_test.comp == 'is'
    """Put a constraint via Table constructor"""
    now = datetime.now()
    s = table('dpt_info.seminaire.session',
              cog_oid=('d%', 'like'),
              begin_date=(now, '<'),
              tba=False)
    assert s.cog_oid.is_set
    assert s.cog_oid.value == 'd%'
    assert s.cog_oid.comp == 'like'
    assert s.begin_date.is_set
    assert s.begin_date.value == now
    assert s.begin_date.comp == '<'
    assert s.tba.is_set
    assert s.tba.value is False
    s2 = s()
    print(type(s), type(s2))
    print(id(s.__class__), id(s2.__class__))
#    print(s.__class__, s2.__class__)
#FAILS    assert s.__class__ == s2.__class__
#FAILS TOO    assert type(s) == type(s2)
    assert s2.is_set is False
    assert s.tba.is_set
    """iterate over the extension."""
    for elt in s.select():
        print(elt)
    for field in s.fields:
        print(field.name)
    x = s(**elt)
    for f in x.fields:
        assert f.is_set
    n = s()
    for elt in n.select(cog_oid=('d%', 'like')):
        print(elt['cog_oid'])
    for elt in n.select(cog_oid=('d%', 'like')):
        t = s(**elt)
        print(t.cog_oid.value)
    for elt in n.select('cog_oid', cog_oid=('d%', 'like')):
        print(elt)
    for elt in n.select('cog_oid', 'cog_fqtn', cog_oid=('d%', 'like')):
        print(elt)
    u = s(cog_oid=('d%', 'like'))
    avant = u.count()
    print(avant)
    u.update(cog_test=True)
#    u.model.commit()
    v = s(cog_oid=('d%', 'like'), cog_test=True)
    assert v.count() == avant
    v.update(cog_test=False)
#    v.model.commit()

    i = table('dpt_info."collorg.core".oid_table', cog_oid='ab', cog_fqtn='cd')
    i.insert()
    assert i.count() == 1
    i.model.commit()
    i.delete()
    assert i.count() == 0
    i.model.commit()

def TODO():
    pass
