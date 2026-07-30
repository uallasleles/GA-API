import os
import getpass
from dotenv import load_dotenv

load_dotenv() 

#user = os.environ.get("PYTHON_USER", "pythondemo")
username = os.getenv("ORACLEDB_USERNAME")
#pw = os.environ.get("PYTHON_PASSWORD")
password = os.getenv("ORACLEDB_PASSWORD")
#dsn = os.environ.get("PYTHON_CONNECT_STRING", "localhost/freepdb1")
dsn = os.getenv("ORACLEDB_DSN")


if password is None:
    password = getpass.getpass("Enter password for %s: " % username)
