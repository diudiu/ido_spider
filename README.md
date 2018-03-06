#bilei_crawler

### 项目配置

#### Python
  python 2.7 测试成功
	
#### Mongodb
   - 安装mongodb
   - mkdir crawler_db
   - mongod --dbpath crawler_db
   - 命令行里敲入 
    `mongo`
	验证mongo连接成功
	
#### 安装scrapy
	[链接](https://doc.scrapy.org/en/latest/intro/tutorial.html "链接")

#### 配置爬虫数据库
    cp config.py.sample config.py
    修改mongo的地址和端口
#### 开启爬虫命令
	`scrapy crawl ico`
	
	
#### 配置七牛自动文件存储
    修改qiniu.conf 为你自己的版本，配置要上传文件的地址
    配置[qshell](https://github.com/qiniu/qshell)
    `qshell qupload 15 qiniu.conf`  其中15为你想要的线程数
	