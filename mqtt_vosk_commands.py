#!/usr/bin/env python3
#
# mqtt_vosk_commands.py - voice recognition commands like google home?
#
#   referenced code -> https://github.com/alphacep/vosk-api/blob/master/python/example/test_microphone.py
#

import os
import sys
import argparse
import json
import yaml
import time
import csv
import vosk
import queue
import sounddevice as sd
import paho.mqtt.client as mqtt

os.chdir(os.path.dirname(__file__))

# https://qiita.com/yohm/items/e95950a5d3eba8915e99
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)
sys.stdin = os.fdopen(sys.stdin.fileno(), 'r', buffering=1)

import logging
logging.basicConfig(stream=sys.stdout, encoding='utf-8', level=logging.DEBUG, format="%(asctime)s : %(levelname)s : %(message)s")

# for Raspberry Pi LED indicator
os.system("echo none | sudo tee /sys/class/leds/led0/trigger >/dev/null")
os.system("echo 0 | sudo tee /sys/class/leds/led0/brightness >/dev/null")

#
# command lists
#
with open('commands.csv') as f:
    reader = csv.reader(f)
    command_list = [row for row in reader]

logging.debug(command_list)

#
# for sound capture
#
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        logging.error(status, file=sys.stderr)
    q.put(bytes(indata))

#
# argparse
#
def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-l', '--list-devices', action='store_true', help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
args = parser.parse_args(remaining)

#
# MQTT
#
with open('config.yaml') as f:
    config = yaml.safe_load(f)

mqtt_client = mqtt.Client(client_id='mqtt-vosk-test', clean_session=True)
if config["mqtt_use_auth"] == True:
    mqtt_client.username_pw_set(config["mqtt_username"], config["mqtt_password"])
mqtt_client.connect(config["mqtt_host"], port=config["mqtt_port"], keepalive=60)
mqtt_client.loop_start()

#
# main
#
try:
    model = vosk.Model(config["model_directory"])

    with sd.RawInputStream(samplerate=int(config["sampling_rate"]),
                            blocksize=int(config["sampling_block_size"]),
                            device=int(config["sound_device_id"]),
                            dtype='int16',
                            channels=1, callback=callback):

            logging.debug("#### Start voice recognition!! ####")

            rec = vosk.KaldiRecognizer(model, int(config["sampling_rate"]))

            command_mode = False
            st = 0.0

            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result["text"].replace(' ', '')

                    if len(text) == 0:
                        continue

                    logging.debug(f"detect text={text}")

                    
                    if command_mode == False:
                        wake_words = [s for s in config["wake_words"] if s in text]
                        if len(wake_words) > 0:
                            # detect wake word
                            st = time.time()
                            command_mode = True
                            os.system("echo 1 | sudo tee /sys/class/leds/led0/brightness >/dev/null")
                            logging.debug(f"detect wake_word! enter command mode...")
                            #mqtt_client.publish(config["mqtt_speach_topic"], "はい") この声を拾ってしまうみたい…
                        else:
                            logging.debug(f"cannot detect wake_word...")

                    else:
                        for c in command_list:
                            command_text = c[0]
                            response_text = c[1]
                            publish_topic = c[2]
                            publish_message = c[3]

                            if command_text in text:
                                logging.debug(f"accept command as {command_text}, reply={response_text}")

                                mqtt_client.publish(config["mqtt_speach_topic"], c[1])

                                time.sleep(3)

                                if len(publish_topic) > 0:
                                    mqtt_client.publish(publish_topic, publish_message)
                                
                                break
                        else:
                            logging.debug(f"detect unknown command...text={text}")
                            mqtt_client.publish(config["mqtt_speach_topic"], config["sorry_sentence"])

                        command_mode = False
                        os.system("echo 0 | sudo tee /sys/class/leds/led0/brightness >/dev/null")

                if time.time() - st > 7 and command_mode == True:
                    logging.debug("clear command mode")
                    command_mode = False
                    os.system("echo 0 | sudo tee /sys/class/leds/led0/brightness >/dev/null")


except KeyboardInterrupt:
    print('\nDone')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))

