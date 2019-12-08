from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = ("postgresql://pythonweekend:6ZnrgwMizC9LCtn1@sql.pythonweekend.skypicker.com/pythonweekend")
engine = create_engine(DATABASE_URL,echo=True) # show debug information
Session = sessionmaker(bind=engine)

session = Session()
