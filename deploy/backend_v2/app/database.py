import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from novel_creator import database as novel_db


def init():
    novel_db.init_db()


def get_db():
    return novel_db.get_db()
