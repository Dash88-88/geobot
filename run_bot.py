from bot import run_bot
from models import create_tables

if __name__ == '__main__':
    create_tables()
    run_bot()
