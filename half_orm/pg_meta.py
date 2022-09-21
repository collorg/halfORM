"""This module provides the SQL request to extract the metadata of a
PostgreSQL database.
"""

from collections import OrderedDict

def strip_quotes(qrn):
    "Removes all double quotes from the qrn/fqrn"
    return qrn.replace('"', '')

def __get_qrn(fqrn: tuple) -> tuple:
    "Returns the qualified relation name <schema>.<relation> from the fully qualified relation name"
    return fqrn[1:]

def normalize_fqrn(t_fqrn: tuple) -> str:
    """
    Transform the tuple (<db name>, <schema name>, <table name>) in
    "<db name>":"<schema name>"."<table name>".
    Dots are allowed only in the schema name.
    """
    dbname, schemaname, tablename = t_fqrn
    return f'"{dbname}":"{schemaname}"."{tablename}"'

def normalize_qrn(t_qrn):
    """
    qrn is a tuple for the qualified relation name (<schema name>, <talbe name>)
    A schema name can have any number of dots in it.
    A table name can't have a dot in it.
    returns "<schema name>"."<relation name>"
    """
    return '.'.join([f'"{elt}"' for elt in __get_qrn(t_qrn)])

def camel_case(string):
    "Retruns the string transformed to camel case"
    ccname = []
    name = string.lower()
    capitalize = True
    for char in name:
        if not char.isalnum():
            capitalize = True
            continue
        if capitalize:
            ccname.append(char.upper())
            capitalize = False
            continue
        ccname.append(char)
    return ''.join(ccname)

def class_name(qrn):
    "Returns the class name from qrn"
    return camel_case(qrn.replace('"', '').split('.')[-1])

_REQUEST = """
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
    AND (i.inhparent is null or i.inhparent not in (select oid from pg_class where relkind = 'p'))
    AND (cn_fk is null or cn_fk.confrelid not in (select inhrelid from pg_inherits where inhparent in (select oid from pg_class where relkind = 'p')))
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

class _Meta(dict):
    __d_meta = {}

    @classmethod
    def deja_vu(cls, dbname):
        return dbname in cls.__d_meta

    @classmethod
    def register(cls, dbname, meta):
        cls.__d_meta[dbname] = meta

    def __getitem__(self, key):
        return _Meta.__d_meta.__getitem__(key)

    def __setitem__(self, key, val):
        _Meta.__d_meta.__setitem__(key, val)

    def __repr__(self):
        dictrepr = dict.__repr__(self.__d_meta)
        return f'{type(self).__name__}({dictrepr})'
  
    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            self.__d_meta[key] = value

class PgMeta:
    meta = _Meta()
    def __init__(self, connection, reload=False):
        self.__dbname = connection.get_dsn_parameters()['dbname']
        if not PgMeta.meta.deja_vu(self.__dbname) or reload:
            self.__load_metadata(connection)

    def metadata(self, dbname):
        return self.meta[dbname].__metadata

    def relations_list(self, dbname):
        return self.metadata(dbname)['relations_list']

    def __load_metadata(self, connection):
        """Loads the metadata by querying the _REQUEST.
        """
        metadata = {'relations_list': []}
        byname = metadata['byname'] = OrderedDict()
        byid = metadata['byid'] = {}
        with connection.cursor() as cur:
            cur.execute(_REQUEST)
            all_ = [elt for elt in cur.fetchall()]
            for dct in all_:
                table_key = (self.__dbname, dct['schemaname'], dct['relationname'])
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
                byname[table_key]['tableid'] = tableid
                byname[table_key]['tablekind'] = tablekind
                byname[table_key]['inherits'] = inherits
                byname[table_key]['fields'][fieldname] = dct
                byname[table_key]['fields_by_num'][fieldnum] = dct
                byid[tableid]['fields'][fieldnum] = fieldname
                if (tablekind, table_key) not in metadata['relations_list']:
                    metadata['relations_list'].append((tablekind, table_key))
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
                    rev_fkey_name = f'_reverse_fkey_{"_".join(table_key)}.{".".join(fields)}'
                    rev_fkey_name = strip_quotes(rev_fkey_name.replace(".", "_").replace(":", "_"))
                    byname[table_key]['fkeys'][fkeyname] = (
                        ftable_key, ffields, fields, confupdtype, confdeltype)
                    byname[ftable_key]['fkeys'][rev_fkey_name] = (table_key, fields, ffields)

        metadata['relations_list'].sort()
        self.__metadata = metadata
        PgMeta.meta.register(self.__dbname, self)

    def getFqrn(self, dbname, qrn):
        "Returns the Fully qualified relation name (quoted) from the unquoted (qrn)"
        schema, table = qrn.rsplit('.', 1)
        return f'"{dbname}":"{schema}"."{table}"'

    def has_relation(self, dbname, schema, relation):
        """Checks if the qrn is a relation in the database

        @qrn is in the form <schema>.<table>
        Returns True if the relation exists, False otherwise.
        Also works for views and materialized views.
        """
        return (dbname, schema, relation) in self.meta[dbname].__metadata['byname']


    def desc(self, dbname):
        """Returns the list of the relations of the model.

        Each line contains:
        - the relation type: 'r' relation, 'v' view, 'm' materialized view,
        - the quoted FQRN (Fully qualified relation name)
          <"db name">:"<schema name>"."<relation name>"
        - the list of the FQRN of the inherited relations.

        If a qualified relation name (<schema name>.<table name>) is
        passed, prints only the description of the corresponding relation.
        """
        ret_val = []
        entry = self.metadata(dbname)['byname']
        for key in entry:
            if key[1].find('half_orm_meta') == 0: continue
            inh = []
            tablekind = entry[key]['tablekind']
            if entry[key]['inherits']:
                inh = [elt for elt in entry[key]['inherits']]
            ret_val.append((tablekind, key, inh))
        return ret_val

    def fields_meta(self, dbname, sfqrn):
        "Retruns the fields metadata for a given sfqrn"
        return self.metadata(dbname)['byname'][sfqrn]['fields']

    def fkeys_meta(self, dbname, sfqrn):
        "Returns the foreign keys metadata for a given sfqrn"
        return self.metadata(dbname)['byname'][sfqrn]['fkeys']

    def relation_meta(self, dbname, fqrn):
        "Returns the relation metadata for a given fqrn"
        return self.metadata(dbname)['byname'][fqrn]

    def str(self, dbname):
        out = []
        entry = self.metadata(dbname)['byname']
        for key in entry:
            if key[1].find('half_orm_meta') == 0: continue
            out.append(f"{entry[key]['tablekind']} {normalize_qrn(key)}")
        return '\n'.join(out)

    def _unique_constraints_list(self, dbname, sfqrn):
        "Returns the unique constraints of the given sfqrn"
        rel_meta_by_name = self.metadata(dbname)['byname'][sfqrn]
        tableid = rel_meta_by_name['tableid']
        rel_meta_by_id = self.metadata(dbname)['byid']
        unique_by_num = []
        for key, value in rel_meta_by_name['fields'].items():
            if value['uniq']:
                t_uniq = tuple(value['pkeynum'])
                if unique_by_num.count(t_uniq) == 0:
                    unique_by_num.append(t_uniq)
        unique = []
        for elt in unique_by_num:
            fields_names = []
            for num in elt:
                fields_names.append(rel_meta_by_id[tableid]['fields'][num])
            unique.append(tuple(fields_names))
        return unique

    def _pkey_constraint(self, dbname, sfqrn):
        "Returns the pkey constraint"
        rel_meta_by_name = self.metadata(dbname)['byname'][sfqrn]
        tableid = rel_meta_by_name['tableid']
        rel_meta_by_id = self.metadata(dbname)['byid']
        pkey_by_num = []
        for key, value in rel_meta_by_name['fields'].items():
            if value['pkey']:
                pkey_by_num.append(value['fieldnum'])
        pkey = []
        for num in pkey_by_num:
            pkey.append(rel_meta_by_id[tableid]['fields'][num])
        return pkey
