# TorMon

Monitor Tor relay with Grafana

## Requirements

* A running InfluxDB and Grafana
* Tor control configured with password access

## Install

Configure __.env.container__ by setting your Tor controler and InfluxDB settings.

*TAG_HOST* is the tag hostname of the running container, it can be anything. This will be the selector in Grafana so that you can monitor several Tor instances.

Configure __.env.torid__ with:

    TORCONTROL_PASSWORD=password_to_torcontrol
    TOR_FP=0123456789ABCDEF0123456789ABCDEF01234567

To start TorMon, you can use docker-compose

    docker-compose up -d

The Influxdb database will be created if it does not exists.

At that point, in Grafana, create a __datasource__ of type InfluxDB to point to the new InfluxDB database.

Import dashboard using JSON file located in dashboard/

Select the datasource you just created

## Remarks

__Make sure to not expose your Tor control endpoint!__

TorMon does not use tor controler async features, it relies on several threads polling the controler.

## Screenshot

![2022-04-03-181417_1920x1080_scrot](https://user-images.githubusercontent.com/490053/161437463-cd96d47a-1388-4d8c-88e2-87784475e396.png)
