
# fusedive
$ git clone https://github.com/mengcz13/fusedive.git

$ pip install -r requirements.txt

# 测试用token: gMLwmsJtyAAAAAAAAAAAatP1HHuliEf5bftZuwLwzTEiV0CqJFsqbqKeLk9FVgqj
$ python fusedive_mem.py /path/to/mount/point gMLwmsJtyAAAAAAAAAAAatP1HHuliEf5bftZuwLwzTEiV0CqJFsqbqKeLk9FVgqj

** 运行 **
run.sh为封装好的脚本文件，可以运行一下脚本启动本项目：
$ ./run.sh


** Ubuntu 运行问题 **

> No file/directory in /tmp/...

$ sudo apt install libfuse-dev


> fatal error : Python.h : No such file or directory

$ sudo apt install python3-dev


> fatal error: attr/xattr.h: No such file or directory

$ sudo apt install libattr1-dev


> timeout : 需要翻墙,python 添加socks5包

$ pip install requests[socks]

修改172, 173行的socks5代理服务器地址,服务器配置参考如下

	proxies = {
		    'http': 'socks5://user:pass@host:port',
		    'https': 'socks5://user:pass@host:port'
	}

