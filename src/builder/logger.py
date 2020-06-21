import logging
import sys

def setup_logging():
    log_format ='%(asctime)-15s [%(levelname)5s] [%(name)s] %(message)s'
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    formatter = logging.Formatter(log_format)
    fh = logging.StreamHandler(sys.stdout)
    fh.setFormatter(formatter)
    root.addHandler(fh)
