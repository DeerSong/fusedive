# fusedive
## 配置
测试用token: gMLwmsJtyAAAAAAAAAAAatP1HHuliEf5bftZuwLwzTEiV0CqJFsqbqKeLk9FVgqj  
```
git clone https://github.com/mengcz13/fusedive.git  
pip install -r requirements.txt  
python fusedive_mem.py /path/to/mount/point gMLwmsJtyAAAAAAAAAAAatP1HHuliEf5bftZuwLwzTEiV0CqJFsqbqKeLk9FVgqj
```
### timeout
需要翻墙,python 添加socks5包  
```
$ pip install requests[socks]
```
修改fusedive_mem.py的172, 173行的socks5代理服务器地址,服务器配置参考如下
```
    proxies = {
            'http': 'socks5://user:pass@host:port',
            'https': 'socks5://user:pass@host:port'
    }
```
### fatal error: attr/xattr.h: No such file or directory
```
sudo apt install libattr1-dev  
```
### pyenv 依赖
参考：http://blog.sina.com.cn/s/blog_76923bd80102w9zw.html
```
sudo apt-get install libbz2-dev
sudo apt-get install libssl-dev
sudo apt-get install libreadline6 libreadline6-dev
sudo apt-get install libsqlite3-dev
```
### 加密配置 Install Cryptography
```
pip install cryptography  
```
## 任务
周先达 加密  
张鹿颂 rename + move  
孟垂正 同步本地 云盘文件  
王龙涛 多设备修改时的同步  
