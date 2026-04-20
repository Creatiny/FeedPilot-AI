import os
os.environ['PYTHONPATH'] = '/home/kenny/.openclaw/workspace-feedsales'
import sys
sys.path.insert(0, '/home/kenny/.openclaw/workspace-feedsales')
from src.database.pool import DatabasePool
print("imported ok")
