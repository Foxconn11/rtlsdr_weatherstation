#!/bin/bash
while true
do
rtl_433 -d :00000999 -R 32 -F json | python3 wetter.py
sleep 10
done
