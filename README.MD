### 需求
    从linux服务端发送ICMP ping请求到指定地址，记录并监控对应的latency,jitter,packet loss指标数据

### 疑难
    原本想着寻找开源工具方案，而后发现无论是如smokeping工具还是如go-ping库，
    都是默认用mdev(StdDevRtt)作为jitter的值，而jitter的正确计算逻辑应该参考如下：
    https://www.3rdechelon.net/jittercalc.asp
    
![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/73a58992c4ce42b380ebc7d3cfeae27e~tplv-k3u1fbpfcp-watermark.image?)

### 手写
    基于https://github.com/rburkholder/ping.py
    完整项目：https://github.com/davidliao404/ping-exporter
    
### 用法
    python3 ping_exporter_8006.py

### 指标
    
![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/87ae16795a7547f798e8e7262c6dc40e~tplv-k3u1fbpfcp-watermark.image?)
    