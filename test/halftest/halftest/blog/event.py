# hop release: 0.1.0a0
# pylint: disable=wrong-import-order, invalid-name, attribute-defined-outside-init

"""The module halftest.blog.event povides the Event class.

WARNING!

This file is part of the halftest package. It has been generated by the
command hop. To keep it in sync with your database structure, just rerun
hop update.

More information on the half_orm library on https://github.com/collorg/halfORM.

DO NOT REMOVE OR MODIFY THE LINES BEGINING WITH:
#>>> PLACE YOUR CODE BELOW...
#<<< PLACE YOUR CODE ABOVE...

MAKE SURE YOUR CODE GOES BETWEEN THESE LINES OR AT THE END OF THE FILE.
hop ONLY PRESERVES THE CODE BETWEEN THESE MARKS WHEN IT IS RUN.
"""

from halftest.db_connector import base_relation_class
from halftest.blog.post import Post as BlogPost
#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!

#<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!

__RCLS = base_relation_class('blog.event')

class Event(BlogPost, __RCLS):
    """
    __RCLS: <class 'half_orm.model.Table_HalftestBlogEvent'>
    This class allows you to manipulate the data in the PG relation:
    TABLE: "halftest":"blog"."event"
    DESCRIPTION:
    The table blog.event contains all the events
    of the blogging system. It inherits blog.post.
    It's just here to illustrate the inheriance in half_orm
    FIELDS:
    - id:                (int4) NOT NULL
    - title:             (text)
    - content:           (text)
    - author_first_name: (text)
    - author_last_name:  (text)
    - author_birth_date: (date)
    - begin:             (timestamp)
    - end:               (timestamp)
    - location:          (text)

    PRIMARY KEY (id)
    FOREIGN KEY:
    - author: ("author_birth_date", "author_first_name", "author_last_name")
     ↳ "halftest":"actor"."person"(first_name, last_name, birth_date)

    To use the foreign keys as direct attributes of the class, copy/paste the Fkeys bellow in
    your code as a class attribute and replace the empty string(s) key(s) with the alias you
    want to use. The aliases must be unique and different from any of the column names. Empty
    string keys are ignored.

    Fkeys = {
        '': 'author',
    }
    """
    #>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
    Fkeys = {
        'author': 'author'
    }
    #<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
