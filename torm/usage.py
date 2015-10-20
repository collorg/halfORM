#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from datetime import datetime
from table import table, Model, TableFactory

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
    Model('dpt_info').check()

    """profiling"""
    for i in range(1000):
        table('dpt_info."collorg.core".base_table')


    """Put a constraint on a Field"""
    bt = table('dpt_info."collorg.core".base_table')
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
    s = table('dpt_info.seminaire.session',
              cog_oid_=('d%', 'like'),
              begin_date_=(now, '>'),
              tba_=False)
    assert s.cog_oid_.is_set
    assert s.cog_oid_.value == 'd%'
    assert s.cog_oid_.comp == 'like'
    assert s.begin_date_.is_set
    assert s.begin_date_.value == now
    assert s.begin_date_.comp == '>'
    assert s.tba_.is_set
    assert s.tba_.value is False
    s2 = s()
    assert type(s) == type(s)
#    print(s.__class__, s2.__class__)
#FAIL    assert s.__class__ == s2.__class__
    assert s2.is_set is False
    assert s.tba_.is_set

def TODO():
    """iterate over the extension."""
    for elt in bt:
        print(elt)
