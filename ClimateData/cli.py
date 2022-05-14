import os
import datetime
from preprocess import process_files, create_working_directory, has_processed_files
from database import setup_database, is_database_setup
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
    # or if a month since last update
    last_time_updated = config_get_db_last_updated()
    force_download = last_time_updated is None
    #if not force_download and (datetime.datetime.utcnow() - last_time_updated).days >= 30:
    #  force_download = True

    # preprocess files
    create_working_directory()
    process_files(force_data_redownload= force_download)

    # 
    if not has_processed_files():
      print('Required data has not been processed. This is likely happening because we cannot fetch the data from the internet. Is a website down or do we not have an internet connection?')
    else:
      # build database
      if not is_database_setup():
        setup_database()

      # update db last updated
      if force_download:
        config_set_db_last_updated_utc_now()
        config_save()

      # start UI
      app = App()
      app.mainloop()


