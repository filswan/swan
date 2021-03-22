# Client Tool Guide

This tool is designed for client to complete the process of sending deals through the following steps:

1. Batch generate car files for files under a specified folder.
2. Share the car file via webserver or hard disk.
3. Propose the deals to a specified miner.

## Basic Concept

### Task

In swan project, a task can contain multiple offline deals. There are two basic type of tasks:

- Public Task
    * A public task is a deal set for open bid. After bidder win the bid, the task holder needs to propose the task to the winner.
- Private Task
    * A private task is used to propose deals to a specified miner.

### Offline Deal

The size of an offline deal can be up to 64 GB. It is suggested to create a CSV file contains the following information: 
uuid|miner_id|deal_cid|file_source_url|md5|start_epoch
------------|-------------|-------------|-------------|-------------|-------------
0b89e0cf-f3ec-41a3-8f1e-52b098f0c503|f047419|bafyreid7tw7mcwlj465dqudwanml3mueyzizezct6cm5a7g2djfxjfgxwm|http://download.com/downloads/fil.tar.car| |544835

This CSV file is helpful to enhance the data consistency and rebuild the graph in the future. 
uuid is generated for future index purpose.


## Prerequisite

- lotus node
- python 3.7+
- pip3

## Install python requirements

```shell
pip3 install -r requirements.txt 
```

## Config

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

Main section defines the token used for connecting with Swan platform. This part can be ignored if offline_mode is set to
true in [sender] section

- **api_key & access_token:** Acquire from [Filswan](https://www.filswan.com) -> "My Profile"->"Developer Settings". You
  can also check the [Guide](https://nebulaai.medium.com/how-to-use-api-key-in-swan-a2ebdb005aa4)
- **api_url:** Default: "https://api.filswan.com"

#### web-server

web-server is used to upload generated Car files. Miner will download Car files from this web-server.
The downloadable URL in the CSV file is built with the following format: host+port+path+filename,
e.g. http://nbai.io:8080/download/<filename>

Support for IPFS node will be provided in 0.2.0 release.

#### sender

- **offline_mode:** [true/false] Default false. If it is set to true, you will not be able to create Swan task on filswan.com, but you can still create CSVs and Car Files for sending deals.
- **output_dir:** Output directory for saving generated Car files and CSVs

- **public_deal:** [true/false] Whether deals in the tasks are public deals
- **verified_deal:** [true/false] Whether deals in this task are going to be sent as verified
- **fast_retrieval:** [true/false] Indicates that data should be available for fast retrieval
- **generate_md5:** [true/false] Whether to generate md5 for each car file, note: this is a resource consuming action
- **manually_confirm:** [true/false] Whether to manually confirm each deal before sending
- **wallet:**  Wallet used for sending offline deals
- **max_price:** Max price willing to pay per GiB/epoch for offline deal
- **start_epoch_hours:** start_epoch for deals in hours from current time

## How to use

### Step 1. Generate Car files for offline deal

For both public task and offline task, you need to generate Car files

```shell
python3 swan_cli.py car --input-dir [input_files_dir] --out-dir [car_files_output_dir] 
```

The output will be like:

```shell
INFO:root:Generating car file from: [input_file_dir]/ubuntu-15.04-server-i386.iso.tar
INFO:root:car file Generated: [car_files_output_dir]/ubuntu-15.04-server-i386.iso.tar.car, piece cid: baga6ea4seaqbpggkuxz7gpkm2wf3734gkyna3vb4p7bm3qcbl4gb4jgh22vj2pi, piece size: 15.88 GiB
INFO:root:Generating data CID....
INFO:root:Data CID: bafykbzacebbq4g73e4he32ahyynnamrft2tva2jyjt5fsxfqv76anptmyoajw
INFO:root:Car files output dir: [car_files_output_dir]
INFO:root:Please upload car files to web server.
```
If --out-dir is not provided, then the output directory for the car files will be: output_dir (specified in the configuration file) + a random uuid

For example: /tmp/tasks/7f33a9d6-47d0-4635-b152-5e380733bf09

### Step 2: Upload Car files to webserver

After generate the car files, you need to copy the files to a web-server manually.

### Step 3. Create a task

#### Options 1: Private Task

in config.toml: set public_deal = false

```shell
python3 swan_cli.py task --input-dir [car_files_dir] --out-dir [output_files_dir] --miner [miner_id]
```

The output will be like:
```shell
INFO:root:Swan Client Settings: Public Task: False  Verified Deals: True  Connected to Swan: True CSV/car File output dir: /tmp/tasks/[output_files_dir]
INFO:root:['lotus', 'client', 'deal', '--from', 't3u4othyfcqjiiveolvdczcww3rypxgonz7mnqfvbtf2paklpru5f6csoajdfz5nznqy2kpr4eielsmksyurnq', '--start-epoch', '547212', '--manual-piece-cid', 'baga6ea4seaqcqjelghbfwy2r6fxsffzfv6gs2gyvc75crxxltiscpajfzk6csii', '--manual-piece-size', '66584576', 'bafykbzaceb6dtpjjisy5pzwksrxwfothlmfjtmcjj7itsvw2flpp5co5ikxam', 't01101', '0.000000000000000000', '1051200']
INFO:root:wallet: t3u4othyfcqjiiveolvdczcww3rypxgonz7mnqfvbtf2paklpru5f6csoajdfz5nznqy2kpr4eielsmksyurnq
INFO:root:miner: t01101
INFO:root:price: 0
INFO:root:total cost: 0.000000000000000000
INFO:root:start epoch: 547212
Press Enter to continue...
INFO:root:Deal sent, deal cid: bafyreibnmon4sby7ibwiezcjgjge7mshl3h24vftzkab5fqm4ll2voarna, start epoch: 547212
INFO:root:Swan deal final CSV Generated: /tmp/tasks/[output_files_dir]/swan-client-demo-deals.csv
INFO:root:Refreshing token
INFO:root:Working in Online Mode. A swan task will be created on the filwan.com after process done. 
INFO:root:Metadata CSV Generated: /tmp/tasks/[output_files_dir]/swan-client-demo-metadata.csv
INFO:root:Swan task CSV Generated: /tmp/tasks/[output_files_dir]/swan-client-demo.csv
INFO:root:Creating new Swan task: swan-client-demo
INFO:root:New Swan task Generated.
```

#### Options 2: Public Task

in config.toml: set public_deal = true

1. Generate the public task

```shell
python3 swan_cli.py task --input-dir [car_files_dir] --out-dir [output_files_dir] --name [task_name]
```

**--input-dir (Required)** Each file under this directory will be converted to a Car file, the generated car file will be located
under the output folder defined in config.toml

**--out-dir (optional)** Metadata CSV and Swan task CSV will be generated to the given directory. Default: output_dir specified in config.toml 

**--name (optional)** Given task name while creating task on Swan platform. Default:
swan-task-uuid

Two CSV files are generated after successfully running the command: task-name.csv, task-name-metadata.csv.

[task-name.csv] is a CSV generated for posting a task on Swan platform or transferring to miners directly for offline import

```
miner_id,deal_cid,file_source_url,md5,start_epoch
```

[task-name-metadata.csv] contains more content for creating proposal in the next step

```
uuid,source_file_name,source_file_path,source_file_md5,source_file_url,source_file_size,car_file_name,car_file_path,car_file_md5,car_file_url,car_file_size,deal_cid,data_cid,piece_cid,miner_id,start_epoch
```

2. Propose offline deal after miner win the bid. Client needs to use the metadata CSV generated in the previous step
   for sending the offline deals to the miner.

```
python3 swan_cli.py deal --csv [metada_csv_dir/task-name-metadata.csv] --out-dir [output_files_dir] --miner [miner_id]
```

**--csv (Required):** File path to the metadata CSV file. Mandatory metadata CSV fields: source_file_size, car_file_url, data_cid,
piece_cid

**--out-dir (optional)** Swan deal final CSV will be generated to the given directory. Default: output_dir specified in config.toml

**--miner (Required):** Target miner id, e.g f01276

A csv with name [task-name]-metadata-deals.csv is generated under the output directory, it contains the deal cid and
miner id for miner to process on Swan platform. You could re-upload this file to Swan platform while assign bid to miner or do a
private deal.

The output will be like:

```shell
INFO:root:['lotus', 'client', 'deal', '--from', 'f3ufzpudvsjqyiholpxiqoomsd2svy26jvy4z4pzodikgovkhkp6ioxf5p4jbpnf7tgyg67dny4j75e7og7zeq', '--start-epoch', '544243', '--manual-piece-cid', 'baga6ea4seaqcqjelghbfwy2r6fxsffzfv6gs2gyvc75crxxltiscpajfzk6csii', '--manual-piece-size', '66584576', 'bafykbzaceb6dtpjjisy5pzwksrxwfothlmfjtmcjj7itsvw2flpp5co5ikxam', 'f019104', '0.000000000000000000', '1051200']
INFO:root:wallet: f3ufzpudvsjqyiholpxiqoomsd2svy26jvy4z4pzodikgovkhkp6ioxf5p4jbpnf7tgyg67dny4j75e7og7zeq
INFO:root:miner: f019104
INFO:root:price: 0
INFO:root:total cost: 0.000000000000000000
INFO:root:start epoch: 544243
Press Enter to continue...
INFO:root:Deal sent, deal cid: bafyreicqgsxql7oqkzr7mtwyrhnoedgmzpd5br3er7pa6ooc54ja6jmnkq, start epoch: 544243
INFO:root:Swan deal final CSV /tmp/tasks/[output_files_dir]/task-name-metadata-deals.csv
INFO:root:Refreshing token
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MTQzNzA5ODcsImlhdCI6MTYxNDI4NDU4Nywic3ViIjoiV2pIVkJDYWIxM2FyUURlUldwbkw0QSJ9.Hn8f0z2Ew6DuL2E2ELgpi9_Gj8xrg28S3v31dTUW32s
INFO:root:Updating Swan task.
INFO:root:Swan task updated.
```
