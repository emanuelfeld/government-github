import json
import networkx
from networkx.readwrite import json_graph


def file_iterator(fn):
    with open(fn) as infile:
        data = json.load(infile)
        for row in data['results']:
            yield row


def write_graph(graph, graph_type, fn):
    filename = 'gov/graphs/{name}-network.{extension}'.format(name=fn, extension=graph_type)
    if graph_type == 'json':
        data = json_graph.node_link_data(graph)
        with open(filename, 'wb') as outfile:
            json.dump(data, outfile)
    elif graph_type == 'gexf':
        data = networkx.write_gexf(graph, filename)
    print("Saved to: {}".format(filename))


def contribution_graph():
    graph = networkx.Graph()
    for item in file_iterator('gov/data/contributor.json'):
        graph.add_node(item['login_1'], node_type='organization', grouping=item['grouping_1'])
        graph.add_node(item['login_2'], node_type='organization', grouping=item['grouping_2'])
        graph.add_edge(item['login_1'], item['login_2'], weight=int(item['count']))
    write_graph(graph, 'gexf', 'contribution')


def membership_graph():
    graph = networkx.Graph()
    for item in file_iterator('gov/data/member.json'):
        print(item)
        graph.add_node(item['login_1'], node_type='organization', grouping=item['grouping_1'])
        graph.add_node(item['login_2'], node_type='organization', grouping=item['grouping_2'])
        graph.add_edge(item['login_1'], item['login_2'], weight=int(item['count']))
    write_graph(graph, 'gexf', 'member')


def forking_graph():
    graph = networkx.DiGraph()
    for item in file_iterator('gov/data/fork_government.json'):
        graph.add_node(item['forked_from'], node_type='organization', grouping=item['forked_from_grouping'])
        graph.add_node(item['forked_by'], node_type='organization', grouping=item['forked_by_grouping'])
        graph.add_edge(item['forked_from'], item['forked_by'], edge_type="from")
    write_graph(graph, 'gexf', 'fork')


if __name__ == "__main__":
    membership_graph()
    contribution_graph()
    forking_graph()
