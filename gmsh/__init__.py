import gmsh.config

# top-level defaults
gmsh.config.from_dict({
    'db': {
        'main': {
            'location': 'sqlite:///gmsh.sqlite'
        },
        'playground': {
            'location': 'sqlite:///playground.sqlite'
        }
    }
})

# read user config directory
gmsh.config.from_directory('config')

# read environment variables
gmsh.config.from_env_mapping({
    'discord': {
        'bot_token': 'BOT_TOKEN'
    },
    'vault': {
        'vault_key': 'VAULT_KEY'
    },
    'db': {
        'main': {
            'location': 'DB_LOCATION'
        },
        'playground': {
            'location': 'DB_PLAYGROUND_LOCATION'
        }
    }
})
