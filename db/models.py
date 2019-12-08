from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Sequence, Column, Integer, String, TEXT, FLOAT
from sqlalchemy.dialects.postgresql import TIMESTAMP

Base = declarative_base()

class Journey(Base):
    __tablename__ = "journeys_vp" # name of the table 
    id = Column(Integer, Sequence("journeys_vp_id"), primary_key=True)
    source = Column(TEXT)
    destination = Column(TEXT)
    departure_datetime = Column(TIMESTAMP)
    arrival_datetime = Column(TIMESTAMP)
    price = Column(FLOAT)
    currency = Column(String(3))
