#!/usr/bin/python3
import re
import time
import os
import sched
import json
import datetime
from functools import wraps
from threading import Thread
from influxdb import InfluxDBClient
from stem.control import Controller
from stem import ControllerError

tor_controller = None
influx_client = None

influx_host     = os.getenv("INFLUX_HOST")
influx_port     = int(os.getenv("INFLUX_PORT"))
db_name         = os.getenv("INFLUX_DB")
m_tags          = {"host": os.getenv("TAG_HOST")}
fp              = os.getenv("TOR_FP")
torcontrol_host = os.getenv("TORCONTROL_HOST")
torcontrol_port = int(os.getenv("TORCONTROL_PORT"))
torcontrol_pass = os.getenv("TORCONTROL_PASSWORD")

def masync(func):
    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl
    return async_func


def schedule(interval):
    def decorator(func):
        def periodic(scheduler, interval, action, actionargs=()):
            scheduler.enter(interval, 1, periodic,
                            (scheduler, interval, action, actionargs))
            action(*actionargs)

        @wraps(func)
        def wrap(*args, **kwargs):
            scheduler = sched.scheduler(time.time, time.sleep)
            periodic(scheduler, interval, func)
            scheduler.run()
        return wrap
    return decorator

def tor2influx(measurement):
    def decorator(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            try:
                fields = func(*args, **kwargs)
            except ControllerError as e:
                print(f"Couldn't connect to tor:{e}")
            else:
                to_influx(measurement,fields)
        return wrap
    return decorator

def get_flags(s):
    res = re.findall("s (.*)\n", s)
    flags = res[0]
    dflags = {}
    for f in (
        "Authority", "BadExit", "BadDirectory", "Exit", "Fast", "Guard",
        "HSDir", "Named", "NoEdConsensus", "Stable", "StaleDesc", "Running",
            "Unnamed", "Valid", "V2Dir"):
        dflags[f] = 1 if f in flags else 0
    return json.dumps(dflags)


def get_bandwidth(s):
    res = re.findall('Bandwidth=([0-9]*)', s)
    return int(res[0])


def get_currenc_tags():
    pass


def get_time():
    return datetime.datetime.utcnow().isoformat()[:-3] + 'Z'

def tor_auth():
    tor_controller.authenticate(password=torcontrol_pass)

def getinfo(query):
    """
    Normalizes tor response as something usable
    See https://github.com/torproject/torspec/blob/main/control-spec.txt
    """

    for i in range(1,11):
        try:
            tor_auth()
        except BaseException:
            time.sleep(0.2*i)
        else:
            break
    else:
        raise

    resp = tor_controller.get_info(query)
    if query == "network-liveness":
        res = {'down': 0, 'up': 1}.get(resp, -1)
    elif query.startswith("ns/id"):
        res = {
            "flags": get_flags(resp),
            "bandwidth": get_bandwidth(resp)
        }
    elif query in ("traffic/read", "traffic/written", "dormant", "uptime"):
        # Normalize to integers
        res = int(resp)
    elif query == "entry-guards":
        res = resp.replace(" ", ":").replace("\n", ", ")
    else:
        res = resp

    return res

def to_influx(measurement, fields):
    tags = m_tags or get_currenc_tags()
    data = [{
        "measurement": measurement,
        "tags": tags,
        "fields": fields,
        'time': get_time()
    }]
    print(f"{get_time()}: {json.dumps(data)}")
    try:
        influx_client.write_points(data, database=db_name)
    except BaseException as e:
        print(f"Couldn't write measurement '{measurement}' to influxdb: {e}")

@masync
@schedule(5)
@tor2influx("bandwidth")
def high_event():
    return {
        "bytes_read":       getinfo("traffic/read"),
        "bytes_written":    getinfo("traffic/written"),
    }

@masync
@schedule(60)
@tor2influx("stats")
def mid_event():
    return {
        "idormant":         getinfo("dormant"),
        "liveness":         getinfo("network-liveness"),
    }

@masync
@schedule(60*60)
@tor2influx("slowstats")
def low_event():
    srv_auth = getinfo(f"ns/id/{fp}")
    return {
        "srv_bandwidth":    srv_auth['bandwidth'],
        "srv_flags":        srv_auth['flags'],
        "entry_guards":     getinfo("entry-guards"),
        "iuptime":          getinfo("uptime"),
    }

@masync
@schedule(24*60*60)
@tor2influx("conf")
def verylow_event():
    return {
        "version":          getinfo("version"),
        "exit_4":           getinfo("exit-policy/ipv4"),
        "exit_6":           getinfo("exit-policy/ipv6"),
        "exit_full":        getinfo("exit-policy/full"),
    }


def main():
    global tor_controller, influx_client

    try:
        influx_client = InfluxDBClient(host=influx_host, port=influx_port)
    except Exception as e:
        print(f"Could not connect to influxdb on {influx_host}:{influx_port}: {e}")
        exit(1)

    influx_client.create_database(db_name)
#    client.create_retention_policy(name="mine", duration="7d", replication=1)

    try:
        tor_controller = Controller.from_port(address=torcontrol_host, port=torcontrol_port)
    except Exception as e:
        print(f"Could not connect to tor control on {torcontrol_host}:{torcontrol_port}: {e}")
        exit(2)

    try:
        tor_auth()
    except Exception as e:
        print(f"Could not authenticate on tor controler: {e}")
        exit(3)

    high_event()
    mid_event()
    low_event()
    verylow_event()

try:
    main()
except KeyboardInterrupt:
    print("Exit")