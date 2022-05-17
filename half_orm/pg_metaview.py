"""This module provides the SQL request to extract the metadata of a
PostgreSQL database.
"""

from collections import OrderedDict

REQUEST = """
SELECT
    a.attrelid AS tableid,
    array_agg( distinct i.inhseqno::TEXT || ':' || i.inhparent::TEXT ) AS inherits,
    c.relkind AS tablekind,
    n.nspname AS schemaname,
    c.relname AS relationname,
    tdesc.description AS tabledescription,
    a.attname AS fieldname,
    a.attnum AS fieldnum,
    adesc.description AS fielddescription,
    a.attndims AS fielddim,
    pt.typname AS fieldtype,
    a.attnum AS fieldnum,
    NOT( a.attislocal ) AS inherited,
    cn_uniq.contype AS uniq,
    cn_uniq.conkey as pkeynum,
    a.attnotnull OR NULL AS notnull,
    cn_pk.contype AS pkey,
    cn_fk.contype AS fkey,
    cn_fk.conname AS fkeyname,
    cn_fk.conkey AS lfkeynum,
    cn_fk.confrelid AS fkeytableid,
    cn_fk.confkey AS fkeynum,
    cn_fk.confupdtype as fkey_confupdtype,
    cn_fk.confdeltype as fkey_confdeltype
FROM
    pg_class c -- table
    LEFT JOIN pg_description tdesc ON
    tdesc.objoid = c.oid AND
    tdesc.objsubid = 0
    LEFT JOIN pg_namespace n ON
    n.oid = c.relnamespace
    LEFT JOIN pg_inherits i ON
    i.inhrelid = c.oid
    LEFT JOIN pg_attribute a ON
    a.attrelid = c.oid
    LEFT JOIN pg_description adesc ON
    adesc.objoid = c.oid AND
    adesc.objsubid = a.attnum
    JOIN pg_type pt ON
    a.atttypid = pt.oid
    LEFT JOIN pg_constraint cn_uniq ON
    cn_uniq.contype = 'u' AND
    cn_uniq.conrelid = a.attrelid AND
    a.attnum = ANY( cn_uniq.conkey )
    LEFT JOIN pg_constraint cn_pk ON
    cn_pk.contype = 'p' AND
    cn_pk.conrelid = a.attrelid AND
    a.attnum = ANY( cn_pk.conkey )
    LEFT JOIN pg_constraint cn_fk ON
    cn_fk.contype = 'f' AND
    cn_fk.conrelid = a.attrelid AND
    a.attnum = ANY( cn_fk.conkey )
WHERE
    n.nspname <> 'pg_catalog'::name AND
    n.nspname <> 'information_schema'::name AND
    ( c.relkind = 'r'::"char" -- table
      OR c.relkind = 'v'::"char" -- view
      OR c.relkind = 'm' -- materialized view
      OR c.relkind = 'f' -- foreign table/view/mat. view
      OR c.relkind = 'p' -- patitioned table
    ) AND
    a.attnum > 0 -- AND
GROUP BY
    a.attrelid,
    n.nspname,
    c.relname,
    tdesc.description,
    c.relkind,
    a.attnum,
    a.attname,
    a.attnum,
    adesc.description,
    a.attndims,
    a.attislocal,
    pt.typname,
    cn_uniq.contype,
    cn_uniq.conkey,
    a.attnotnull,
    cn_pk.contype,
    cn_fk.contype,
    cn_fk.conname,
    cn_fk.conkey,
    cn_fk.confrelid,
    cn_fk.confkey,
    cn_fk.confupdtype,
    cn_fk.confdeltype
ORDER BY
    n.nspname, c.relname, a.attnum
"""

class Meta(dict):
    __d_meta = {}

    @classmethod
    def deja_vu(cls, dbname):
        return dbname in cls.__d_meta

    @classmethod
    def load(cls, dbname, meta):
        cls.__d_meta[dbname] = meta

    def __getitem__(self, key):
        return Meta.__d_meta.__getitem__(key)

    def __setitem__(self, key, val):
        Meta.__d_meta.__setitem__(key, val)

    def __repr__(self):
        dictrepr = dict.__repr__(self.__d_meta)
        return f'{type(self).__name__}({dictrepr})'
  
    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            self.__d_meta[key] = value

class PgMeta:
    meta = Meta()
    def __init__(self, connection, dbname, relations):
        self.__dbname = dbname
        self.__relations = relations
        if not PgMeta.meta.deja_vu(dbname):
            self.__load_metadata(connection)

    def metadata(self, dbname):
        return self.meta[dbname].__metadata

    @property
    def relations(self):
        return self.__relations

    def __load_metadata(self, connection):
        """Loads the metadata by querying the request in the pg_metaview
        module.
        """
        metadata = {}
        byname = metadata['byname'] = OrderedDict()
        byid = metadata['byid'] = {}
        with connection.cursor() as cur:
            cur.execute(REQUEST)
            all_ = [elt for elt in cur.fetchall()]
            for dct in all_:
                table_key = f'''"{self.__dbname}":"{dct['schemaname']}"."{dct['relationname']}"'''
                tableid = dct['tableid']
                description = dct['tabledescription']
                if table_key not in byname:
                    byid[tableid] = {}
                    byid[tableid]['sfqrn'] = table_key
                    byid[tableid]['fields'] = OrderedDict()
                    byid[tableid]['fkeys'] = OrderedDict()
                    byname[table_key] = OrderedDict()
                    byname[table_key]['description'] = description
                    byname[table_key]['fields'] = OrderedDict()
                    byname[table_key]['fkeys'] = OrderedDict()
                    byname[table_key]['fields_by_num'] = OrderedDict()
            for dct in all_:
                tableid = dct['tableid']
                table_key = byid[tableid]['sfqrn']
                fieldname = dct.pop('fieldname')
                fieldnum = dct['fieldnum']
                tablekind = dct.pop('tablekind')
                inherits = [byid[int(elt.split(':')[1])]['sfqrn']
                            for elt in dct.pop('inherits') if elt is not None]
                byname[table_key]['tablekind'] = tablekind
                byname[table_key]['inherits'] = inherits
                byname[table_key]['fields'][fieldname] = dct
                byname[table_key]['fields_by_num'][fieldnum] = dct
                byid[tableid]['fields'][fieldnum] = fieldname
                if (tablekind, table_key) not in self.__relations['list']:
                    self.__relations['list'].append((tablekind, table_key))
            for dct in all_:
                tableid = dct['tableid']
                table_key = byid[tableid]['sfqrn']
                fkeyname = dct['fkeyname']
                if fkeyname and not fkeyname in byname[table_key]['fkeys']:
                    fkeytableid = dct['fkeytableid']
                    ftable_key = byid[fkeytableid]['sfqrn']
                    fields = [byid[tableid]['fields'][num] for num in dct['lfkeynum']]
                    confupdtype = dct['fkey_confupdtype']
                    confdeltype = dct['fkey_confdeltype']
                    ffields = [byid[fkeytableid]['fields'][num] for num in dct['fkeynum']]
                    rev_fkey_name = f'_reverse_fkey_{table_key}.{".".join(fields)}'
                    rev_fkey_name = rev_fkey_name.replace(".", "_").replace(":", "_").replace('"', '')
                    byname[table_key]['fkeys'][fkeyname] = (
                        ftable_key, ffields, fields, confupdtype, confdeltype)
                    byname[ftable_key]['fkeys'][rev_fkey_name] = (table_key, fields, ffields)

        self.__relations['list'].sort()
        self.__metadata = metadata
        PgMeta.meta.load(self.__dbname, self)

    def getFqrn(self, dbname, qtn):
        schema, table = qtn.rsplit('.', 1)
        return f'"{dbname}":"{schema}"."{table}"'

    def has_relation(self, dbname, qtn):
        """Checks if the qtn is a relation in the database

        @qtn is in the form <schema>.<table>
        Returns True if the relation exists, False otherwise.
        Also works for views and materialized views.
        """
        key = self.getFqrn(dbname, qtn)
        return key in self.meta[dbname].__metadata['byname']
