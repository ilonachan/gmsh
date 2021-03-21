import ezconf

# top-level defaults
ezconf.from_dict({
    'db': {
        'main': {
            'location': 'sqlite:///db/gmsh.sqlite'
        },
        'playground': {
            'location': 'sqlite:///db/playground.sqlite'
        }
    }
})

# read user config directory
ezconf.from_directory('config')

# read environment variables
ezconf.from_env_mapping({
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
