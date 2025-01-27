from datetime import datetime
from echoforgeai.core.story import Story
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class StoryState(Base):
    __tablename__ = 'story_states'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String)
    graph_state = Column(JSON)
    character_states = Column(JSON)
    timestamp = Column(DateTime)
    
class StoryRepository:
    def __init__(self, db_url="sqlite:///stories.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    async def save_story(self, story: Story):
        session = self.Session()
        state = StoryState(
            session_id=story.session_id,
            graph_state=story.graph.export_state(),
            character_states={name: c.export_state() for name,c in story.characters.items()},
            timestamp=datetime.now()
        )
        session.add(state)
        session.commit()
