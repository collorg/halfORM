#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from datetime import datetime
import model

class OidTable(metaclass=model.TableFactory):
    fqtn = 'dpt_info."collorg.core".oid_table'

class BaseTable(metaclass=model.TableFactory):
    fqtn = '"dpt_info"."collorg.core".base_table'

class ViewSession(metaclass=model.TableFactory):
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
    print(model.table('dpt_info.seminaire.session'))
    model.Model('dpt_info').check()

    """profiling"""
    for i in range(1000):
        model.table('dpt_info."collorg.core".base_table')


    """Put a constraint on a Field"""
    bt = model.table('dpt_info."collorg.core".base_table')
    assert bt.cog_fqtn_.is_set is False
    bt.cog_fqtn_.set('collorg.access.access')
    assert bt.cog_fqtn_.is_set is True
    assert bt.cog_fqtn_.get() is bt.cog_fqtn_.value
    assert bt.cog_oid_.is_set is False
    bt.cog_oid_.value = 'd%', 'like'
    assert bt.cog_oid_.is_set is True
    assert bt.cog_oid_.value == 'd%'
    assert bt.cog_oid_.comp == 'like'
    bt.cog_test_.value = None, 'is not'
    try:
        bt.cog_test_.set(None, '!=')
        assert False
    except:
        bt.cog_test_.set(None, 'is')
    assert bt.cog_test_.is_set and bt.cog_test_.value is None
    assert bt.cog_test_.comp == 'is'
    """Put a constraint via Table constructor"""
    now = datetime.now()
    s = model.table('dpt_info.seminaire.session',
              cog_oid_=('d%', 'like'),
              begin_date_=(now, '<'),
              tba_=False)
    assert s.cog_oid_.is_set
    assert s.cog_oid_.value == 'd%'
    assert s.cog_oid_.comp == 'like'
    assert s.begin_date_.is_set
    assert s.begin_date_.value == now
    assert s.begin_date_.comp == '<'
    assert s.tba_.is_set
    assert s.tba_.value is False
    s2 = s()
    print(type(s), type(s2))
    print(id(s.__class__), id(s2.__class__))
#    print(s.__class__, s2.__class__)
#FAILS    assert s.__class__ == s2.__class__
#FAILS TO    assert type(s) == type(s2)
    assert s2.is_set is False
    assert s.tba_.is_set
    """iterate over the extension."""
    for elt in s.select():
        print(elt)
    for field in s.fields:
        print(field.name)
    x = s(**elt)
    for f in x.fields:
        assert f.is_set
    n = s()
    for elt in n.select(cog_oid_=('d%', 'like')):
        print(elt['cog_oid_'])
    for elt in n.select(cog_oid_=('d%', 'like')):
        t = s(**elt)
        print(t.cog_oid_.value)
    for elt in n.select('cog_oid_', cog_oid_=('d%', 'like')):
        print(elt)
    for elt in n.select('cog_oid_', 'cog_fqtn_', cog_oid_=('d%', 'like')):
        print(elt)

def TODO():
    pass
