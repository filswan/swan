import toml


def read_config(_config_path=None):
    if _config_path is None:
        _config_path = './config.toml'

    # script_dir = os.path.dirname(__file__)
    # file_path = os.path.join(script_dir, config_path)
    _config = toml.load(_config_path)

    return _config
