import prometheus_client
from prometheus_client import Gauge,CollectorRegistry,CONTENT_TYPE_LATEST
from flask import Response, Flask ,request,render_template
import ping
import os
import yaml
from concurrent import futures
from prometheus_client import multiprocess
# gevent
from gevent import monkey
from gevent.pywsgi import WSGIServer
monkey.patch_all()
# gevent end

app = Flask(__name__)

REGISTRY = CollectorRegistry(auto_describe=True)
multiprocess.MultiProcessCollector(REGISTRY)
pingResultFileds_tup = ["dest_addr","count","protocol_version","pinger"]
pingPacketLossGauge = Gauge(name="pingPacketLoss",documentation="pingPacketLoss Multiprocess metric",labelnames=pingResultFileds_tup,registry=REGISTRY,multiprocess_mode='livesum')
pingPacketLossPercGauge = Gauge(name="pingPacketLossPerc",documentation="pingPacketLossPerc Multiprocess metric",labelnames=pingResultFileds_tup,registry=REGISTRY,multiprocess_mode='livesum')
pingjitterGauge = Gauge(name="pingJitter",documentation="pingJitter Multiprocess metric",labelnames=pingResultFileds_tup,registry=REGISTRY,multiprocess_mode='livesum')
pingLatencyMinGauge = Gauge(name="pingLatencyMin",documentation="pingLatencyMin Multiprocess metric",labelnames=pingResultFileds_tup,registry=REGISTRY,multiprocess_mode='livesum')
pingLatencyMaxGauge = Gauge(name="pingLatencyMax",documentation="pingLatencyMax Multiprocess metric",labelnames=pingResultFileds_tup,registry=REGISTRY,multiprocess_mode='livesum')
pingLatencyAvgGauge = Gauge(name="pingLatencyAvg",documentation="pingLatencyAvg Multiprocess metric",labelnames=pingResultFileds_tup,registry=REGISTRY,multiprocess_mode='livesum')

@app.route("/metrics")
def getPingResult():
    count = int(request.args.get('count'))
    src_addr = request.args.get('src_addr')
    pinger =  request.args.get('pinger')
    dest_addr = request.args.get('target')
    protocol_version = request.args.get('protocol_version')
    curPath=os.path.dirname(os.path.realpath(__file__))
    yaml1=os.path.join(curPath,"target_8006.yml")
    f1=open(yaml1,'r', encoding="utf-8") #打开yaml文件
    d1=yaml.load(f1, Loader=yaml.FullLoader) #使用load方法加载
    f1.close
    targets = d1[0]['targets']
    # ping_result_dict = {}
    # ping_result_dict = ping.ping(count=count,src_addr=src_addr,dest_addr=dest_addr,protocol_version=protocol_version)


    with futures.ThreadPoolExecutor(max_workers=256) as executor:
        to_do = []
        for t in targets:
            future = executor.submit(ping.ping,dest_addr=t,count=count)
            to_do.append(future)
        results = []
        for future in futures.as_completed(to_do):	# 等待完成
            res = future.result()	# 接收结果
            results.append(res)
            # print("Already Finished", res)
            
        # print(results)
        executor.shutdown()
    
    for ping_result_dict in results:
        pingPacketLossGauge.labels(ping_result_dict["dst"],count,protocol_version,pinger).set(ping_result_dict['packet_loss'])
        pingPacketLossPercGauge.labels(ping_result_dict["dst"],count,protocol_version,pinger).set(ping_result_dict['packet_loss_perc'])
        pingjitterGauge.labels(ping_result_dict["dst"],count,protocol_version,pinger).set(ping_result_dict['jitter'])
        pingLatencyMinGauge.labels(ping_result_dict["dst"],count,protocol_version,pinger).set(ping_result_dict['latency_min'])
        pingLatencyMaxGauge.labels(ping_result_dict["dst"],count,protocol_version,pinger).set(ping_result_dict['latency_max'])
        pingLatencyAvgGauge.labels(ping_result_dict["dst"],count,protocol_version,pinger).set(ping_result_dict['latency_avg'])
    
    return Response(prometheus_client.generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)

@app.route('/')
def index():
    return render_template('form.html')

if __name__ == "__main__":
    # app.run(debug=False,host='0.0.0.0', port=8006)
    http_server = WSGIServer(('', 8006), app)
    http_server.serve_forever()
