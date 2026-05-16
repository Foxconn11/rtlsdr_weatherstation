#!/bin/bash
while true
do
rtl_433 -d :00000999 -R 32 -F json | python3 weather_receiver.py
sleep 10
done
