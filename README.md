selper
======
这是一个简单的服务进程管理程序。  
作用:  
    系统启动时候，启动系统服务（在其中可以启动程序维护数据、文件检测等服务）。维护系统服务，启动系统服务，关闭系统服务，重启系统服务，重新载入系统服务。  


## 使用方法
* 使用方法将配置文件selper.ini 放入/etc/selper/文件夹下  
* 将selper.py放入/usr/bin文件夹下。  
* 将需要启动的服务进程按照规则写入selper.ini中  
* 对服务进行管理可以使用命令   


## 使用命令
python selper.py xxx(服务) stop  
python selper.py xxx(服务) restart  
python selper.py xxx(服务) reload    
python selper.py xxx(服务) status

