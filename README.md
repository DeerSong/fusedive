
# fusedive
> 存储技术基础大作业

## 安装

$ git clone https://github.com/mengcz13/fusedive.git

$ pip install -r requirements.txt

>  测试用token: gMLwmsJtyAAAAAAAAAAAatP1HHuliEf5bftZuwLwzTEiV0CqJFsqbqKeLk9FVgqj

$ python fusedive_mem.py /path/to/mount/point gMLwmsJtyAAAAAAAAAAAatP1HHuliEf5bftZuwLwzTEiV0CqJFsqbqKeLk9FVgqj

## 运行 

run.sh为封装好的脚本文件，可以运行一下脚本启动本项目：

```Bash
$ ./run.sh
```

在此之前，你需要在dropbox/developer创建一个app,并generate一个新的token,放入mytoken文件下。

## Ubuntu 运行问题

1. No file/directory in /tmp/... 

```Bash
$ sudo apt install libfuse-dev
```

2. fatal error : Python.h : No such file or directory

```Bash
$ sudo apt install python3-dev
```

3. fatal error: attr/xattr.h: No such file or directory

```Bash
$ sudo apt install libattr1-dev
```

4. timeout : 需要翻墙,python 添加socks5包

```Bash
$ pip install requests[socks]
```

修改`fusedive_mem.py`的172, 173行的socks5代理服务器地址,服务器配置参考如下

```python
proxies = {
	    'http': 'socks5://user:pass@host:port',
	    'https': 'socks5://user:pass@host:port'
}
```

## 开发人员：

张鹿颂
王龙涛
孟垂正
周先达