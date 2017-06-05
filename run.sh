test_dir=test$1
mkdir -p ${test_dir}

read token < mytoken
echo python fusedive_mem.py ${test_dir} ${token}
python fusedive_mem.py ${test_dir} ${token}
# python fusedive_mem.py test gMLwmsJtyAAAAAAAAAAAatP1HHuliEf5bftZuwLwzTEiV0CqJFsqbqKeLk9FVgqj
