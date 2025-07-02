#!/usr/bin/env python3
"""
Analyze foreign key relationships between two relations.
Usage: fkeys_between.py <database> <relation1> <relation2>
"""

import sys
from half_orm.model import Model

def find_relationships(relation1, relation2):
    """Find all foreign key relationships between two relations"""
    direct = []
    reverse = []
    
    # Direct: relation1 -> relation2
    for fk_name, fk_rel in relation1()._ho_fkeys.items():
        if fk_rel()._qrn == relation2._qrn:
            direct.append((fk_name, fk_rel))
    
    # Reverse: relation2 -> relation1  
    for fk_name, fk_rel in relation2()._ho_fkeys.items():
        if fk_rel()._qrn == relation1._qrn:
            reverse.append((fk_name, fk_rel))
    
    return direct, reverse

def main():
    if len(sys.argv) != 4:
        print("Usage: fkeys_between.py <database> <relation1> <relation2>")
        print("Example: fkeys_between.py gitlab public.users public.projects")
        sys.exit(1)
    
    dbname, rel1_name, rel2_name = sys.argv[1:]
    
    try:
        database = Model(dbname)
        relation1 = database.get_relation_class(rel1_name)
        relation2 = database.get_relation_class(rel2_name)
        
        direct, reverse = find_relationships(relation1, relation2)
        
        print(f"=== RELATIONSHIPS BETWEEN {rel1_name} AND {rel2_name} ===")
        print(f"\nDirect ({rel1_name} → {rel2_name}):")
        if direct:
            for fk_name, fk_rel in direct:
                print(f"  • {fk_name}")
        else:
            print("  (none)")
            
        print(f"\nReverse ({rel2_name} → {rel1_name}):")
        if reverse:
            for fk_name, fk_rel in reverse:
                print(f"  • {fk_name}")
        else:
            print("  (none)")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
