from neo4j import GraphDatabase
from typing import List, Dict, Any
from .base import BaseStorage

class Neo4jStorage(BaseStorage):
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add(self, subject: str, predicate: str, obj: str, confidence: float = 1.0):
        with self.driver.session() as session:
            query = """
            MERGE (s:Entity {name: $subject})
            MERGE (o:Entity {name: $object})
            MERGE (s)-[r:FACT {predicate: $predicate}]->(o)
            SET r.confidence = $confidence, r.updated_at = timestamp()
            """
            session.run(query, subject=subject, object=obj, predicate=predicate, confidence=confidence)

    def query(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not keyword: return []
        with self.driver.session() as session:
            query = """
            MATCH (s:Entity)-[r:FACT]->(o:Entity)
            WHERE toLower(s.name) CONTAINS toLower($key) 
               OR toLower(o.name) CONTAINS toLower($key) 
               OR toLower(r.predicate) CONTAINS toLower($key)
            RETURN s.name AS subject, r.predicate AS predicate, o.name AS object, r.confidence AS confidence
            LIMIT $limit
            """
            result = session.run(query, key=keyword, limit=limit)
            return [dict(record) for record in result]

    def clear(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")