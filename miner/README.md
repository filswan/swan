## Getting Started
This tool will listen to the new tasks assigned to your miner from the Swan platform, 
and start importing deals automatically once the files are downloaded.

### Prerequisites
    
    sudo apt install python3-pip
    pip3 install -r offline_deals/requirements.txt 
    sudo apt install aria2

### Config

Edit aria2.conf
- **input-file:** Downloads the URIs listed in session
- **save-session:** Save error/unfinished downloads to session on exit.
- **rpc-secret:** Enable JSON-RPC/XML-RPC server. It is strongly recommended to set secret authorization.

Edit config.toml

[main]
- **api_url:** Swan API address. For Swan production, it is "https://api.filswan.com"
- **miner_fid:** Your filecoin Miner ID
- **expected_sealing_time:** The time expected for sealing deals. Deals starting too soon will be rejected.
- **import_interval:** Importing interval between each deal.
- **api_key & access_token:** Acquire from swan -> my profile Guide:https://nebulaai.medium.com/how-to-use-api-key-in-swan-a2ebdb005aa4

[aria2]
- **aria2_download_dir:** Directory where offline deal files will be downloaded to automatically
- **aria2_conf:** Aria2 configuration file
- **aria2_host:** Aria2 server address
- **aria2_port:** Aria2 server port
- **aria2_secret:** Must be consistent with aria2_secret in aria2.conf

### Run
    
    python3 swan_miner_deal_downloader.py
    python3 swan_miner_deal_importer.py
