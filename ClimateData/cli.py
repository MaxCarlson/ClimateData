import os
from preprocess import process_files, create_working_directory
from database import setup_database
from UI import App
from config import _config_path, config_load, config_save, config_set_db_last_updated_utc_now, config_get_db_last_updated

if __name__ == '__main__':

  # on first boot create config and exit
  if not os.path.exists(_config_path):
    config_load()
    config_save()
 
  else:
    # read config
    config_load()

    # if first time startup, run preprocess and db setup
    if config_get_db_last_updated() is None:

      # preprocess files
      create_working_directory()
      process_files()

      # build database
      setup_database()

      # update db last updated
      config_set_db_last_updated_utc_now()
      config_save()

    # start UI
    app = App()
    app.mainloop()


