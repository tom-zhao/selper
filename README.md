selper
======
这是一个服务进程管理程序。。
作用:启动进程，关闭进程，重启进程，重新载入进程。
不过这些服务进程需要满足一个最大的条件：
对于服务需要保证自己的业务正确性，当意外重启，不会有影响。

1.使用方法将配置文件selper.ini 放入/etc/selper/文件夹下
2.将selper.py放入/usr/bin文件夹下。
3.将需要启动的服务进程按照规则写入selper.ini中
4.对服务进行管理可以使用命令
selper xxx(服务) stop
selper xxx(服务) restart
selper xxx(服务) reload
service process helper..
