#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from datetime import datetime
from halfORM.model import RelationFactory, relation, Model
from halfORM.relation_interface import Relation

dpt_info = Model(config_file='/etc/halfORM/dpt_info')

class OidTable(metaclass=RelationFactory):
    fqrn = 'dpt_info."collorg.core".oid_table'

class BaseTable(metaclass=RelationFactory):
    fqrn = '"dpt_info"."collorg.core".base_table'

class ViewSession(metaclass=RelationFactory):
    fqrn = 'dpt_info."seminaire.view"."session"'

if __name__ == '__main__':
    """
    OidTable()
    BaseTable()
    ViewSession()
    PgDatabase()
    relation('dpt_info.seminaire.session')
    sys.exit()
    """
#    print(OidTable())
#    print(BaseTable())
#    print(ViewSession())
#    print(relation('dpt_info.seminaire.session'))
#    dpt_info.desc()

    """profiling"""
    for i in range(1000):
        relation('dpt_info."collorg.core".base_table')

    """request with no constraint."""
    bt = relation('dpt_info."collorg.core".data_type')
    count = 0
    for elt in bt.select():
        count += 1
    print(count)
    bt = relation('dpt_info."collorg.core".base_table')
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
    s = relation('dpt_info.seminaire.session',
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
    assert isinstance(s, Relation)
    print(s.__class__, s2.__class__)
#FAILS    assert s.__class__ == s2.__class__
#FAILS TOO    assert type(s) == type(s2)
    assert s2.is_set is False
    assert s.tba.is_set
    """iterate over the extension."""
    print(s.json())
    for field in s.fields:
        print(field.name)
    n = s()
    for elt in n(cog_oid=('d%', 'like')).select():
        print(elt['cog_oid'])
    t = None
    for elt in n(cog_oid=('d%', 'like')).select():
        t = s(**elt)
        print(t.cog_oid.value)
    for f in t.fields:
        assert f.is_set
    for elt in n(cog_oid=('d%', 'like')).select('cog_oid'):
        print(elt)
    for elt in n(cog_oid=('d%', 'like')).select('cog_oid', 'cog_fqtn'):
        print(elt)
    u = s(cog_oid=('d%', 'like'))
    avant = u.count()
    print(avant)
    u.update(cog_test=True)
    v = s(cog_oid=('d%', 'like'), cog_test=True)
    assert v.count() == avant
    v.update(cog_test=False)

    i = relation(
        'dpt_info."collorg.core".oid_table', cog_oid='ab', cog_fqtn='cd')
    i.insert()
    assert i.count() == 1
    i.model.connection.commit()
    i.delete()
    assert i.count() == 0
    i.model.connection.commit()

def TODO():
    pass
