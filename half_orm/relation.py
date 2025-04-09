#-*- coding: utf-8 -*-
# pylint: disable=protected-access, too-few-public-methods, no-member

"""This module is used by the `model <#module-half_orm.model>`_ module
to generate the classes that manipulate the data in your database
with the `Model.get_relation_class <#half_orm.model.Model.get_relation_class>`_
method.


Example:
    >>> from half_orm.model import Model
    >>> model = Model('halftest')
    >>> class Person(model.get_relation_class('actor.person')):
    >>>     # your code goes here

Main methods provided by the class Relation:
- ho_insert: inserts a tuple into the pg table.
- ho_select: returns a generator of the elements of the set defined by
  the constraint on the Relation object. The elements are dictionaries with the
  keys corresponding to the selected columns names in the relation.
  The result is affected by the methods: ho_distinct, ho_order_by, ho_limit and ho_offset
  (see below).
- ho_update: updates the set defined by the constraint on the Relation object
  with the values passed as arguments.
- ho_delete: deletes from the relation the set of elements defined by the constraint
  on the Relation object.
- ho_get: returns the unique element defined by the constraint on the Relation object.
  the element returned if of the type of the Relation object.

The following methods can be chained on the object before a select.

- ho_distinct: ensures that there are no duplicates on the select result.
- ho_order_by: sets the order of the select result.
- ho_limit: limits the number of elements returned by the select method.
- ho_offset: sets the offset for the select method.

"""

import inspect
from dataclasses import dataclass
from functools import wraps
from collections import OrderedDict
from typing import List, Generic, TypeVar, Dict
from keyword import iskeyword

from half_orm import relation_errors
from half_orm.transaction import Transaction
from half_orm.field import Field
from half_orm import utils
from .base_relation import BaseRelation

@dataclass
class DC_Relation: # pragma: no cover
    def __init__(self, **kwargs): ...

    def ho_insert(self, *args: List[str]) -> Dict:
        """Insert a new tuple into the Relation.

        Returns:
            Dict: A dictionary containing the data inserted.

        Example:
            >>> gaston = Person(last_name='La', first_name='Ga', birth_date='1970-01-01').ho_insert()
            >>> print(gaston)
            {'id': 1772, 'first_name': 'Ga', 'last_name': 'La', 'birth_date': datetime.date(1970, 1, 1)}

        Note:
            It is not possible to insert more than one row with the ho_insert method
        """
        ...
    def ho_select(self, *args: List[str]) -> [Dict]:
        """Gets the set of values correponding to the constraint attached to self.
        This method is a generator.

        Arguments:
            *args: the fields names of the returned attributes. If omitted,
                all the fields are returned.

        Yields:
            the result of the query as a list of dictionaries.

        Example:
            >>> for person in Person(last_name=('like', 'La%')).ho_select('id'):
            >>>     print(person)
            {'id': 1772}
        """
        ...

    def ho_update(self, *args, update_all=False, **kwargs) -> [Dict]:
        """Updates the elements defined by self.

        Arguments:
            **kwargs: the values to be updated {[field name:value]}
            *args [Optional]: the list of columns names to return in the dictionary list for the updated elements. If args is ('*', ), returns all the columns values.
            update_all: a boolean that must be set to True if there is no constraint on
            self. Defaults to False.
        """
        ...

    def ho_delete(self, *args, delete_all=False) -> [Dict]:
        """removes all elements from the set that correspond to the constraint.

        Arguments:
            *args [Optional]:
        """
        ...

    def ho_get(self, *args: List[str]) -> 'Relation':
        """The get method allows you to fetch a singleton from the database.
        It garantees that the constraint references one and only one tuple.

        Arguments:
            args (List[str]): list of fields names.\
            If ommitted, all the values of the row retreived from the database\
            are set for the self object.\
            Otherwise, only the values listed in the `args` parameter are set.

        Returns:
            Relation: the object retreived from the database.

        Raises:
            ExpectedOneError: an exception is raised if no or more than one element is found.

        Example:
            >>> gaston = Person(last_name='Lagaffe', first_name='Gaston').ho_get()
            >>> type(gaston) is Person
            True
            >>> gaston.id
            (int4) NOT NULL (id = 1772)
            >>> str(gaston.id)
            '1772'
            >>> gaston.id.value
            1772
        """
        ...

    def ho_is_set(self):
        """Return True if one field at least is set or if self has been
        constrained by at least one of its foreign keys or self is the
        result of a combination of Relations (using set operators).
        """
        ...

    def ho_distinct(self):
        """Set distinct for the SQL request."""
        ...

    def ho_unaccent(self, *fields_names):
        "Sets unaccent for each field listed in fields_names"
        ...

    def ho_order_by(self, _order_):
        """Sets the SQL `order by` according to the "_order_" string passed

        Example :
            personnes.ho_order_by("field1, field2 desc, field3, field4 desc")
        """
        ...

    def ho_limit(self, _limit_):
        """Sets the limit for the next SQL select request."""
        ...

    def ho_offset(self, _offset_):
        """Set the offset for the next SQL select request."""
        ...

    def ho_count(self, limit=0):
        """Returns the number of tuples matching the intention in the relation.
        """
        ...

    def ho_is_empty(self):
        """Returns True if the self is an empty set, False otherwise.
        """
        ...

class Relation(BaseRelation):
    """Used as a base class for the classes generated by
    `Model.get_relation_class <#half_orm.model.Model.get_relation_class>`_.

    Args:
        **kwargs: the arguments names must correspond to the columns names of the relation.

    Raises:
        UnknownAttributeError: If the name of an argument doesn't match a column name in the
            relation considered.

    Examples:
        You can generate a class for any relation in your database:
            >>> from half_orm.model import Model
            >>> model = Model('halftest')
            >>> class Person(model.get_relation_class('actor.person')):
            >>>     # your code

        To define a set of data in your relation at instantiation:
            >>> gaston = Person(last_name='Lagaffe', first_name='Gaston')
            >>> all_names_starting_with_la = Person(last_name=('ilike', 'la%'))

        Or to constrain an instantiated object via its\
            `Fields <#half_orm.field.Field>`_:
            >>> person = Person()
            >>> person.birth_date = ('>', '1970-01-01')

        Raises an `UnknownAttributeError <#half_orm.relation_errors.UnknownAttributeError>`_:
            >>> Person(lost_name='Lagaffe')
            [...]UnknownAttributeError: ERROR! Unknown attribute: {'lost_name'}.
    """
    _ho_fields_aliases = {}

    def __init__(self, **kwargs):
        _fqrn = ""
        """The names of the arguments must correspond to the names of the columns in the relation.
        """
        super().__init__(**kwargs)

    #@utils.trace
    def ho_insert(self, *args) -> '[dict]':
        """Insert a new tuple into the Relation.

        Returns:
            [dict]: A singleton containing the data inserted.

        Example:
            >>> gaston = Person(last_name='La', first_name='Ga', birth_date='1970-01-01').ho_insert()
            >>> print(gaston)
            {'id': 1772, 'first_name': 'Ga', 'last_name': 'La', 'birth_date': datetime.date(1970, 1, 1)}

        Note:
            It is not possible to insert more than one row with the insert method
        """
        _ = args and args != ('*',) and self._ho_check_columns(*args)
        query_template = "insert into {} ({}) values ({})"
        self._ho_query_type = 'insert'
        fields_names, values, fk_fields, fk_query, fk_values = self._what()
        what_to_insert = ["%s" for _ in range(len(values))]
        if fk_fields:
            fields_names += fk_fields
            what_to_insert += fk_query
            values += fk_values
        query = query_template.format(self._qrn, ", ".join(fields_names), ", ".join(what_to_insert))
        returning = args or ['*']
        if returning:
            query = self._ho_add_returning(query, *returning)
        with self.__execute(query, tuple(values)) as cursor:
            res = [dict(elt) for elt in cursor.fetchall()] or [{}]
            return res[0]

    #@utils.trace
    def ho_select(self, *args):
        """Gets the set of values correponding to the constraint attached to the object.
        This method is a generator.

        Arguments:
            *args: the fields names of the returned attributes. If omitted,
                all the fields are returned.

        Yields:
            the result of the query as a dictionary.

        Example:
            >>> for person in Person(last_name=('like', 'La%')).ho_select('id'):
            >>>     print(person)
            {'id': 1772}
        """
        self._ho_check_columns(*args)
        query, values = self._ho_prep_select(*args)
        with self.__execute(query, values) as cursor:
            for elt in cursor:
                yield dict(elt)

    #@utils.trace
    def ho_get(self, *args: List[str]) -> 'Relation':
        """The get method allows you to fetch a singleton from the database.
        It garantees that the constraint references one and only one tuple.

        Args:
            args (List[str]): list of fields names.\
            If ommitted, all the values of the row retreived from the database\
            are set for the self object.\
            Otherwise, only the values listed in the `args` parameter are set.

        Returns:
            Relation: the object retreived from the database.

        Raises:
            ExpectedOneError: an exception is raised if no or more than one element is found.

        Example:
            >>> gaston = Person(last_name='Lagaffe', first_name='Gaston').ho_get()
            >>> type(gaston) is Person
            True
            >>> gaston.id
            (int4) NOT NULL (id = 1772)
            >>> str(gaston.id)
            '1772'
            >>> gaston.id.value
            1772
        """
        self._ho_check_columns(*args)
        self.ho_limit(2)
        _count = self.ho_count()
        if _count != 1:
            raise relation_errors.ExpectedOneError(self, _count)
        self._ho_is_singleton = True
        ret = self(**(next(self.ho_select(*args))))
        ret._ho_is_singleton = True
        return ret

    #@utils.trace
    def ho_update(self, *args, update_all=False, **kwargs):
        """
        kwargs represents the values to be updated {[field name:value]}
        The object self must be set unless update_all is True.
        The constraints of self are updated with kwargs.
        """
        if not (self.ho_is_set() or update_all):
            raise RuntimeError(
                f'Attempt to update all rows of {self.__class__.__name__}'
                ' without update_all being set to True!')

        _ = args and args != ('*',) and self._ho_check_columns(*args)
        self._ho_check_columns(*(kwargs.keys()))
        update_args = {key: value for key, value in kwargs.items() if value is not None}
        if not update_args:
            return None # no new value update. Should we raise an error here?

        query_template = "update {} set {} {}"
        what, where, values = self._update_args(**update_args)
        where, values = self._fkey_where(where, values)
        query = query_template.format(self._qrn, what, where)
        if args:
            query = self._ho_add_returning(query, *args)
        with self.__execute(query, tuple(values)) as cursor:
            for field_name, value in update_args.items():
                self._ho_fields[field_name].set(value)
            if args:
                return [dict(elt) for elt in cursor.fetchall()]
        return None

    #@utils.trace
    def ho_delete(self, *args, delete_all=False):
        """Removes a set of tuples from the relation.
        To empty the relation, delete_all must be set to True.
        """
        _ = args and args != ('*',) and self._ho_check_columns(*args)
        if not (self.ho_is_set() or delete_all):
            raise RuntimeError(
                f'Attempt to delete all rows from {self.__class__.__name__}'
                ' without delete_all being set to True!')
        query_template = "delete from {} {}"
        _, values = self._prep_query(query_template)
        self._ho_query_type = 'delete'
        _, where, _ = self._where_args()
        where, values = self._fkey_where(where, values)
        if where:
            where = f" where {where}"
        query = f"delete from {self._qrn} {where}"
        if args:
            query = self._ho_add_returning(query, *args)
        with self.__execute(query, tuple(values)) as cursor:
            if args:
                return [dict(elt) for elt in cursor.fetchall()]
        return None

    #@utils.trace
    def __execute(self, query, values):
        return self._ho_model.execute_query(query, tuple(values))

    def _to_dict_val_comp(self):
        """Returns a dictionary containing the values and comparators of the fields
        that are set."""
        return {key:(field._comp(), field.value) for key, field in
                self._ho_fields.items() if field.is_set()}

    # @utils.trace
    def ho_count(self, *args):
        """Returns the number of tuples matching the intention in the relation.
        """
        self._ho_query = "select"
        query, values = self._ho_prep_select(*args)
        query = f'select count(*) from ({query}) as ho_count'
        return self.__execute(query, values).fetchone()['count']

    def ho_is_empty(self):
        """Returns True if the relation is empty, False otherwise.
        """
        self.ho_limit(1)
        return self.ho_count() == 0

    def __contains__(self, right):
        return (right - self).ho_count() == 0

    def __iter__(self):
        query, values = self._ho_prep_select()
        for elt in self.__execute(query, values):
            yield dict(elt)

    def __next__(self):
        return next(self.ho_select())

    # deprecated. To remove with release 1.0.0

    @utils._ho_deprecated
    def select(self, *args): # pragma: no cover
        return self.ho_select(*args)

    @utils._ho_deprecated
    def insert(self, *args): # pragma: no cover
        return self.ho_insert(*args)

    @utils._ho_deprecated
    def update(self, *args, update_all=False, **kwargs): # pragma: no cover
        return self.ho_update(*args, update_all, **kwargs)

    @utils._ho_deprecated
    def delete(self, *args, delete_all=False): # pragma: no cover
        return self.ho_delete(*args, delete_all)

    @utils._ho_deprecated
    def get(self, *args): # pragma: no cover
        return self.ho_get(*args)

    @utils._ho_deprecated
    def unaccent(self, *fields_names): # pragma: no cover
        return self.ho_unaccent(*fields_names)

    @utils._ho_deprecated
    def order_by(self, _order_): # pragma: no cover
        return self.ho_order_by(_order_)

    @utils._ho_deprecated
    def limit(self, _limit_): # pragma: no cover
        return self.ho_limit(_limit_)

    @utils._ho_deprecated
    def offset(self, _offset_): # pragma: no cover
        return self.ho_offset(_offset_)

    @utils._ho_deprecated
    def count(self, *args): # pragma: no cover
        return self.ho_count(*args)

    @utils._ho_deprecated
    def is_empty(self): # pragma: no cover
        return self.ho_is_empty()

def singleton(fct):
    """Decorator. Enforces the relation to define a singleton.

    _ho_is_singleton is set by Relation.get.
    _ho_is_singleton is unset as soon as a Field is set.
    """
    @wraps(fct)
    def wrapper(self, *args, **kwargs):
        if self._ho_is_singleton:
            return fct(self, *args, **kwargs)
        try:
            self = self.ho_get()
            return fct(self, *args, **kwargs)
        except relation_errors.ExpectedOneError as err:
            raise relation_errors.NotASingletonError(err)
    wrapper.__is_singleton = True
    wrapper.__orig_args = inspect.getfullargspec(fct)
    return wrapper
