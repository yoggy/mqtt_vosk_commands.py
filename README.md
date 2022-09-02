# mqtt_vosk_commands.py
## How to use

```
$ cd ~
$ mkdir work
$ cd work
$ git clone https://github.com/yoggy/mqtt_vosk_commands.git
$ cd mqtt_vosk_commands

$ sudo pip3 install vosk sounddevice pyyaml paho-mqtt

$ curl -O https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip
$ unzip vosk-model-ja-0.22.zip

$ python3 mqtt_vosk_commands.py -l
  0 bcm2835 Headphones: - (hw:0,0), ALSA (0 in, 8 out)
> 1 USB Microphone: Audio (hw:1,0), ALSA (1 in, 0 out)  <--- default sound_device_id
  2 sysdefault, ALSA (0 in, 128 out)
  3 output, ALSA (0 in, 8 out)
  4 dmix, ALSA (0 in, 2 out)
< 5 default, ALSA (0 in, 128 out)

$ cp config.yaml.sample config.yaml
$ vi config.yaml

    mqtt_host: iot.eclipse.org  <--- Please change the variables to your environment.
    mqtt_port: 1883
    mqtt_use_auth: false
    mqtt_username: username
    mqtt_password: password
    mqtt_speach_topic: aquestalk/speach
    
    sound_device_id: 1    <--- sound_device_id
    sampling_rate: 16000
    sampling_block_size: 4000
    
    model_directory: vosk-model-ja-0.22
    
    wake_words:
      - オッケーグーグル
      - アレクサ
    
    sorry_sentence: すみません、よくわかりません。。

$ cp commands.csv.sample commands.csv
$ vi commands.csv

   #コマンド,#応答文,#送信先トピック,#送信メッセージ
   エアコンつけて,エアコンつけます,device/aircon/on,
   エアコン消して,エアコンけします,device/aircon/off,
   扇風機つけて,扇風機つけます,device/atomsocket0001,on
   扇風機消して,扇風機消します,device/atomsocket0001,off

$ python3 mqtt_vosk_commands.py

```

for supervisord settings...

```
$ sudo apt-get install supervisor
$ cd $HOME/work/mqtt_vosk_commands
(check your scrpt path...)
$ sudo cp mqtt_vosk_commands.conf.sample /etc/supervisor/conf.d/mqtt_vosk_commands.conf
$ sudo vi /etc/supervisor/conf.d/mqtt_vosk_commands.conf
(fix path, etc...)

$ sudo supervisorctl update
mqtt_vosk_commands: added process group

$ sudo supervisorctl status
mqtt_vosk_commands        RUNNING    pid 8192, uptime 0:00:30
```

## Reference

  - https://alphacephei.com/vosk/install
  - https://github.com/alphacep/vosk-api/blob/master/python/example/test_microphone.py

## Copyright and license
Copyright (c) 2022 yoggy

Released under the [MIT license](LICENSE)
