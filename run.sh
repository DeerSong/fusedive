mkdir -p test

read token < mytoken
echo python fusedive_mem.py test ${token}
python fusedive_mem.py test ${token}
# python fusedive_mem.py test gMLwmsJtyAAAAAAAAAAAatP1HHuliEf5bftZuwLwzTEiV0CqJFsqbqKeLk9FVgqj
