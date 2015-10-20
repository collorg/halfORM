#!/usr/bin/env python3
#-*- coding: utf-8 -*-

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


    """Put a constraint on a Field and iterate over the
    extension.
    """
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

def TODO():
    for elt in bt:
        print(elt)
