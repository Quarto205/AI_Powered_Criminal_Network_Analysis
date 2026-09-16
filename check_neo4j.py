import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.graph.connection import get_graph_manager
manager = get_graph_manager()
session = manager.get_session()
res = session.run("MATCH (n {case_id: '3b018e46-03ca-59eb-9340-a1ee5c21fa9c'}) RETURN labels(n) as l LIMIT 5")
for record in res:
    print(record['l'])
