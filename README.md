# TorMon

Monitor tor relay with grafana

## Requirements

  * A running InfluxDB and Grafana
  * Tor control configured with password access

## Install

Configure __.env.container__ for the running container. 

*TAG_HOST* is the tag hostname of the running container, it can be anything. This will be the selector in Grafana so that you can monitor several tor instance.

Configure __.env.torid__ with:

    TORCONTROL_PASSWORD=password_to_torcontrol
    TOR_FP=0123456789ABCDEF0123456789ABCDEF01234567

To start tormon, you can use docker-compose

    docker-compose up -d

The Influxdb database will be created if it does not exists.

At that point, in Grafana, create a __datasource__ of type InfluxDB to point to the new InfluxDB database.

Import dashboard using JSON file located in dashboard/

Select the datasource you just created

## Design

This is a very basic tor to influxdb relay. It does not use tor controler async features, it relies on threads polling the controler.

## Screenshot
