from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector
import numpy as np
from typing import List

Base = declarative_base()

class Implant(Base):
    __tablename__ = "implants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    manufacturer = Column(String)
    type = Column(String)
    image_url = Column(String)
    embedding = Column(Vector(512))  # Dimensão do vetor CLIP
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "manufacturer": self.manufacturer,
            "type": self.type,
            "image_url": self.image_url
        }
