import networkx as nx
from typing import Dict, Any, List, Iterable

class GraphManager:
    _instance = None
    @classmethod
    def singleton(cls):
        if not cls._instance:
            cls._instance = GraphManager()
        return cls._instance
    def __init__(self):
        self.G = nx.Graph()
    def rebuild(self, items: List[Dict[str,Any]]):
        from infrastructure.graph_builder import rules_engine as re
        self.G = nx.Graph()
        for it in items:
            self.G.add_node(it["item_id"], **it)
        for i in range(len(items)):
            for j in range(i+1, len(items)):
                a, b = items[i], items[j]
                sc,_ = re.score_pair(a,b)
                if sc>0: self.G.add_edge(a["item_id"], b["item_id"], weight=sc)
        return {"nodes": self.G.number_of_nodes(), "edges": self.G.number_of_edges()}
    def upsert_item(self, item: Dict[str,Any], items: List[Dict[str,Any]]):
        from infrastructure.graph_builder import rules_engine as re
        if self.G.number_of_nodes()==0: return self.rebuild(items)
        self.G.add_node(item["item_id"], **item)
        for other in items:
            if other["item_id"]==item["item_id"]: continue
            sc,_ = re.score_pair(item, other)
            if sc>0: self.G.add_edge(item["item_id"], other["item_id"], weight=sc)
            elif self.G.has_edge(item["item_id"], other["item_id"]):
                self.G.remove_edge(item["item_id"], other["item_id"])
        return {"nodes": self.G.number_of_nodes(), "edges": self.G.number_of_edges()}
    def neighbors(self, item_id: str) -> List[str]:
        return list(self.G.neighbors(item_id)) if item_id in self.G else []
    def all_candidates(self, exclude_ids: Iterable[str]=()) -> List[Dict[str,Any]]:
        ids=set(exclude_ids or [])
        return [data for nid,data in self.G.nodes(data=True) if nid not in ids]
