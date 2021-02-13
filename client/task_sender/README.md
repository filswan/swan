### Install requirements

At dir client/task_sender, run

    pip install -r requirements.txt 

### Config

Edit config.toml

- **output_dir:** dir to move files to, as static resources for downloading
- **download_url_prefix:** domain name and path to add before the file name
- **is_public:** task is public [true/false]
- **is_verified:** deals in this task are going to be sent as verified [true/false]
- **generate_md5:** generate md5 for miners to verify the integrity of files [true/false] (time consuming)
- **api_key & access_token:** acquire from swan -> my profile

### Run

    python3 swan_task_sender.py input_dir task_name [config_path]

- **input_dir:**    all files in this fold (not in subforlders) will be used
- **config_path (optional):** use external config file (default: client/task_sender)