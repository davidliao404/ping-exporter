import prometheus_client
from prometheus_client import Gauge,CollectorRegistry,CONTENT_TYPE_LATEST
from flask import Response, Flask ,request,render_template
import ping

# gevent
from gevent import monkey
from gevent.pywsgi import WSGIServer
monkey.patch_all()
# gevent end

app = Flask(__name__)

@app.route("/metrics")
def getPingResult():
    count = int(request.args.get('count'))
    src_addr = request.args.get('src_addr')
    pinger =  request.args.get('pinger')
    dest_addr = request.args.get('target')
    protocol_version = request.args.get('protocol_version')

    ping_result_dict = {}
    ping_result_dict = ping.ping(count=count,src_addr=src_addr,dest_addr=dest_addr,protocol_version=protocol_version)

    REGISTRY = CollectorRegistry(auto_describe=False)
    pingResultFileds_tup = ["src_addr","count","protocol_version","pinger"]
    pingPacketLossGauge = Gauge(name="pingPacketLoss",documentation="pingPacketLoss",labelnames=pingResultFileds_tup,registry=REGISTRY)
    pingPacketLossPercGauge = Gauge(name="pingPacketLossPerc",documentation="pingPacketLossPerc",labelnames=pingResultFileds_tup,registry=REGISTRY)
    pingjitterGauge = Gauge(name="pingJitter",documentation="pingJitter",labelnames=pingResultFileds_tup,registry=REGISTRY)
    pingLatencyMinGauge = Gauge(name="pingLatencyMin",documentation="pingLatencyMin",labelnames=pingResultFileds_tup,registry=REGISTRY)
    pingLatencyMaxGauge = Gauge(name="pingLatencyMax",documentation="pingLatencyMax",labelnames=pingResultFileds_tup,registry=REGISTRY)
    pingLatencyAvgGauge = Gauge(name="pingLatencyAvg",documentation="pingLatencyAvg",labelnames=pingResultFileds_tup,registry=REGISTRY)
    pingMOSGauge = Gauge(name="pingMOS",documentation="pingMOS",labelnames=pingResultFileds_tup,registry=REGISTRY)

    pingPacketLossGauge.labels(src_addr,count,protocol_version,pinger).set(ping_result_dict['packet_loss'])
    pingPacketLossPercGauge.labels(src_addr,count,protocol_version,pinger).set(ping_result_dict['packet_loss_perc'])
    pingjitterGauge.labels(src_addr,count,protocol_version,pinger).set(ping_result_dict['jitter'])
    pingLatencyMinGauge.labels(src_addr,count,protocol_version,pinger).set(ping_result_dict['latency_min'])
    pingLatencyMaxGauge.labels(src_addr,count,protocol_version,pinger).set(ping_result_dict['latency_max'])
    pingLatencyAvgGauge.labels(src_addr,count,protocol_version,pinger).set(ping_result_dict['latency_avg'])
    pingMOSGauge.labels(src_addr,count,protocol_version,pinger).set(ping_result_dict['MOS'])
    return Response(prometheus_client.generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)

@app.route('/')
def index():
    return render_template('form.html')

if __name__ == "__main__":
    http_server = WSGIServer(('', 8006), app)
    http_server.serve_forever()
