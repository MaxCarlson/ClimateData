import json
import os
from datetime import datetime, date

# Config path
_config_path = 'config.json'

# Config object
_config = None
_config_default = {
  "Database": {
    "Host": "localhost",
    "Name": "postgres",
    "User": "postgres",
    "Password": "PASSWORD",
    "LastUpdated": None
  }
}

# loads configuration from the config file
def config_load():
  global _config
  global _config_default

  # initialize with defaults
  _config = {}
  _config.update(_config_default.copy())

  # if config file doesn't exist, create new with defaults
  if os.path.exists(_config_path):
    with open(_config_path, 'r') as f:
      _config.update(json.load(f))

# saves configuration to config file
def config_save():
  with open(_config_path, 'w') as w:
    w.write(json.dumps(_config, indent=4))

# whether or not the config has the given path
# path is a list of strings
def _config_has(path):
  if _config is None:
    config_load()
  
  # check each string in path
  item = _config
  for field in path:
    if field not in item:
      return False
    item = item[field]
  
  return True

# returns the config value at path or the default value at path
# path is a list of strings
def _config_get(path):
  item = _config if _config_has(path) else _config_default
  for field in path:
    item = item[field]
  
  return item

# sets the config value at path
# path is a list of strings
def _config_set(path, value):
  item = _config
  path_len = len(path)
  for i in range(path_len):
    is_last = i == (path_len-1)
    field = path[i]

    if is_last:
      item[field] = value
    elif field not in item:
      item[field] = {}
    
    item = item[field]


#DATABASE SECTION---------------------------------------------------------------------
def config_get_db_host() -> str:
  return _config_get(["Database", "Host"])
def config_set_db_host(host):
  _config_set(["Database", "Host"], host)

def config_get_db_name() -> str:
  return _config_get(["Database", "Name"])
def config_set_db_name(name):
  _config_set(["Database", "Name"], name)

def config_get_db_user() -> str:
  return _config_get(["Database", "User"])
def config_set_db_user(user):
  _config_set(["Database", "User"], user)

def config_get_db_password() -> str:
  return _config_get(["Database", "Password"])
def config_set_db_password(password):
  _config_set(["Database", "Password"], password)

def config_get_db_last_updated() -> datetime:
  try:
    return datetime.fromisoformat(_config_get(["Database", "LastUpdated"]))
  except:
    return None
def config_set_db_last_updated(last_updated: datetime):
  _config_set(["Database", "LastUpdated"], last_updated.isoformat())
def config_set_db_last_updated_utc_now():
  config_set_db_last_updated(datetime.utcnow())

def config_get_db_connection_string() -> str:
  return f'host={config_get_db_host()} dbname={config_get_db_name()} user={config_get_db_user()} password={config_get_db_password()}'
