# halfORM API

```python
mymodel = Model('mymodel_init_file')
```

## instanciating a relation
```python
rel_a = mymodel.relation('public.a')
```

## get to know the relation
```python
print(rel_a)
```

## constraining a relation
```python
rel_a.a_field1 = 'something', '!='
```

## transfering constraints from one relation to another
### Get a new relation through a foreign key
```python
rel_b = rel_a.to_b_fkey
rel_c = rel_b.to_c_fkey
rel_c = rel_a.to_b_fkey.to_c_fkey
```

## instanciating a new relation (free of constraint)
```python
rel_a_bis = rel_a()
```

## instanciating a new relation (with constraint)
```python
rel_b = mymodel.relation('my_schema.b', b_field1=('%whatever%', 'like'))
```

### Set a relation through a foreign key
```python
rel_a_bis.to_b_fkey = rel_b
```

## constraining a field with another field
As shown with foreign keys, any field can be constrained by another field:

```pyton
rel_a_ter = rel_a()
rel_a_ter.a_field1 = rel_b.b_field2
```

rel_a_ter contains the elements for which a_field1 value is in b_field2 values given rel_b relation. (ie. a_field1 is in b_field2 values for which b_field1 is like '%whatever%')

## Set operators

```python
rel_a1 = rel_a(a_field1='something')
rel_a2 = rel_a(a_field2=('%whatever%', 'like')
```

### union
```python
rel_a_union = rel_a1 | rel_a2
```

### intersection
```python
rel_a_inter = rel_a1 & rel_a2
```

### symmetric difference
```python
rel_a_xor = rel_a1 ^ rel_a2
```

### difference
```python
rel_a_minus = rel_a1 - rel_a2
```
