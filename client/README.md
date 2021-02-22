### Prerequisite

- lotus node
- python 3.7+ 
- pip

### Install python requirements

```
pip install -r requirements.txt 
```

### Config

In config.toml

```
[main]
api_key = ""
access_token = ""
api_url = "https://api.filswan.com"

[web-server]
host = "http://nbai.io"
port = 8080
path = "/download"

[sender]
offline_mode = false
output_dir = "/tmp/tasks"
is_public = true
is_verified = true
generate_md5 = false
wallet = ""
max_price = "0"
start_epoch_hours = 96
```

#### main
Main section define the token used for connect with swan platform, you can ignore this part if offline_mode = true in [sender] section
- **api_key**   Follow instuctions here https://nebulaai.medium.com/how-to-use-api-key-in-swan-a2ebdb005aa4
- **access_token** Follow instuctions here https://nebulaai.medium.com/how-to-use-api-key-in-swan-a2ebdb005aa4
- **api_url:** Default using "https://api.filswan.com"
#### web-server
web-server is the client used for miner download files host on client's web server. When generate the CSV file the downloadable URL is combined in the following format: host+port+path+filename, e.g. http://nbai.io:8080/download/<filename>

#### sender

- **offline_mode:** Default true. Disconnect with filswan.com when it is set to true, you will not be able to create swan task, but you can still create CSV and car Fil for sending deals.
- **output_dir:** Out directory for saving generated cars

- **is_public:** task is public [true/false]
- **is_verified:** deals in this task are going to be sent as verified [true/false]
- **generate_md5:** generate md5 for each car file generated [true/false] (time-consuming)
- **wallet:** the wallet used for sent offline deals
- **max_price:** the max price per GiB/epoch for offline deal
- **start_epoch_hours:** start_epoch for deals in hours from current time

### How to use

##### 1. Generate car file for offline deal 
Command
```
    python3 swan_cli.py task --input input_file_dir --name task_name
```
-	--input  For each file under this directory will be converted to a car file, the generated car file will be located under the output folder defined in config.toml
-	--name  define task name used while creating task in swan platform, default: swan-task-<uuid>

Two CSV files is generated after successfully running the command: swan-task-<uuid>.csv , swan-task-<uuid>-metadata.csv. They are under the output folder defined in config.toml.


swan-task-<uuid>.csv is a CSV generated for post a public task or a task for pre-download in Swan platform 
```
miner_id,deal_cid,file_source_url,md5,start_epoch
```
Output metadata CSV is used for creating proposal in the next step
```
uid,source_file_name,source_file_path,source_file_md5,source_file_url,source_file_size,car_file_name,car_file_path,car_file_md5,car_file_url,car_file_size,deal_cid,data_cid,piece_cid,miner_id,start_epoch
```
[only when offline_mode = false] A task will be created on Swan
##### 2. Send offline deal

To send offline deals to a miner, use the metadata CSV, generated in step 1.

```
    python3 swan_cli.py deal --csv swan-task-<uuid>-metadata.csv  --miner miner_id
```
**--csv (Required):**  file path to the metadata CSV file, mandatory fields: source_file_size, car_file_url, data_cid, piece_cid
**--miner (Required):** target miner id for storage, e.g  f01276

A csv with name swan-task-<uuid>-deals.csv is generated under the output directory, it contains the deal cid and miner id for miner process in Swan, you could re-upload this file to swan platform while assign bid to miner or do a private deal.

