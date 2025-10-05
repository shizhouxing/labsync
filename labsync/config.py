import os
import json
import appdirs

user_data_dir = appdirs.user_data_dir('labsync')
if not os.path.exists(user_data_dir):
    os.makedirs(user_data_dir)

config_file = os.path.join(user_data_dir, 'config.json')

# Define prompts for each config key
CONFIG_PROMPTS = {
    'checkpoint_path': 'Enter the path where checkpoints are stored:',
}

def load_config():
    """Load configuration from file, return empty dict if doesn't exist."""
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save configuration to file."""
    with open(config_file, 'w') as f:
        json.dump(config, indent=4, fp=f)

def get_config_value(key):
    """Get a config value, prompting user if it doesn't exist."""
    config = load_config()

    if key not in config:
        if key not in CONFIG_PROMPTS:
            raise ValueError(f'Unknown config key: {key}')

        print(CONFIG_PROMPTS[key])
        value = input().strip()
        config[key] = value
        save_config(config)

    value = config[key]

    if key.endswith('_path') or key.endswith('_dir'):
        value = os.path.expanduser(value)

    return value
