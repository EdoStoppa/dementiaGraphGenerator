import pandas as pd
from py2neo import Graph, Node, Relationship, Subgraph
import util as u

def add_general(graph: Graph, discourse: Node, row, attributes: list) -> None:
    nodes, rels = [], []

    general = Node(*['Category', 'General_Discourse-Based'])
    nodes.append(general)
    rels.append(Relationship(discourse, 'SUB_CATEGORY', general))

    # Create feature nodes and relationships
    n, r = u.one_to_features(attributes, row, general)
    nodes += n
    rels += r

    graph.create(Subgraph(nodes, rels))

def add_rel(graph: Graph, discourse: Node, row, attributes: list) -> None:
    nodes, rels = [], []

    relations = Node(*['Category', 'Relations'])
    nodes.append(relations)
    rels.append(Relationship(discourse, 'SUB_CATEGORY', relations))

    attrs = list(zip(attributes[:18], attributes[18:36]))

    for pure, ratio in attrs:
        # Create node for section of basic feature
        new_node = Node(*['Category', pure])
        nodes.append(new_node)

        # Create relation between master node and new subnode
        rels.append(Relationship(relations, 'SUB_CATEGORY', new_node))

        # Create feature nodes and relationships
        n, r = u.one_to_features2(['pure', 'ratio'], [pure, ratio], row, new_node)
        nodes += n
        rels += r

    # Add last special node
    typ2tok = Node(*['Category', 'Type_2_Token'])
    nodes.append(typ2tok)
    rels.append(Relationship(relations, 'SUB_CATEGORY', typ2tok))

    new_node = Node(*['Feature', attributes[-1]], **{'value': row[attributes[-1]]})
    nodes.append(new_node)
    rels.append(Relationship(typ2tok, 'IS', new_node))

    graph.create(Subgraph(nodes, rels))

def add_discourse_based(graph: Graph, data_path: str) -> None:
    # Load data into pandas
    data = pd.read_csv(data_path)
    # Get the columns names
    attributes = list(data.columns)[1:]
    
    for index, row in data.iterrows():
        # Printing progress bar
        u.printProgressBar(index+1, len(data), bar_size=40)

        # Get the patient node
        patient = u.get_patient_node(graph, row['id'])
        if patient is None: continue

        # Create a new CATEGORY node and BASE relationship
        discourse = Node(*['Feature_Type', 'Discourse_Based'])
        discourse_rel = Relationship(patient, 'BASIC_CATEGORY', discourse)

        # Add the node and relationship between patient and category
        graph.create(Subgraph([discourse], [discourse_rel]))

        # Add all the energy features in the graph
        add_general(graph, discourse, row, attributes[:3])

        # Add all the MFCC features in the graph
        add_rel(graph, discourse, row, attributes[3:])
