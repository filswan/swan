##Getting Started
This tool will listen to the new tasks assigned to your miner from the Swan platform, 
and start importing deals automatically once the files are downloaded.

### Prerequisites

    pip3 install -r requirements.txt 

### Config

Edit config.toml

- **api_url:** Swan API address. For more information please visit https://www.filswan.com/swagger.html
- **miner_fid:** Filecoin Miner ID
- **expected_sealing_time:** The time expected for sealing deals. 
- **import_interval:** Importing interval between each deal.
- **api_key & access_token:** Acquire from swan -> my profile

### Run

    python3 swan_miner_deal_importer.py