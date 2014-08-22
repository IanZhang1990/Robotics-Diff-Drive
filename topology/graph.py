import sys, os, math

from priority_queue import *

class Node:
	def __init__(self, name, group, value = 0):
		self.name  = name;
		self.value = value;
		self.group = group;

#	def __eq__( self, other ):
#		return self.name == other.name and self.value == other.value;

	def same_name_with( self, other ):
		return self.name == other.name;

class Graph:
	def __init__(self):
		self.graphdict = dict();
		'''
		A graph is of this format:

        {
        	'A' : [('B', 1), ('C', 2)],
        	'B' : [('A', 1), ('C', 3)],
        	'C' : [('A', 2), ('B', 3)]
        }

       	     1
        A ------- B
         \       /
        2 \     / 3
           \   /
             C 
		'''  
	############################################################
	########			Utility private methods        #########

	def __get_adj_nodes__(self, node):
		edges = self.graphdict[node];
		nodes = [];
		for edge in edges:
			nodes.append( edge[0] );
		return nodes;

	def __edge_eq__( self, edge1, edge2 ):
		'''determine if two undirected edges are equal'''
		node_eq   = False;
		weight_eq = False;
		if edge1[0] == edge2[0] and edge1[0] == edge2[0]:
			node_eq = True;
		elif edge1[0] == edge2[1] and edge1[1] == edge2[0]:
			node_eq = True;
		if edge1[2] == edge2[2]:
			weight_eq = True;

		return node_eq and weight_eq;


	############################################################
	########			Utility prublic methods        #########
	def copy(self):
		'''return a copy of the graph. Nodes and edges all remain the same memory addresses.
		Only the reference of of graph itself is different. '''
		newgraph  = Graph();
		#all_nodes = self.get_all_nodes();
		all_edges = self.get_all_edges();
		newgraph.add_edges( all_edges );
		return newgraph;

	def size(self):
		'''return the size of the graph. |E|'''
		return len(self.get_all_edges());

	def contains(self, node_or_edge):
		'''determine if an edge or node exist in the graph'''
		if isinstance( node_or_edge, tuple ):	# This is an edge
			# Determine is the two nodes exist
			if not self.graphdict.has_key( node_or_edge[0] ) or not self.graphdict.has_key( node_or_edge[1] ):
				return False;
			edges = self.graphdict[ node_or_edge[0] ];         # get edges associated to the first node of the edge
			for edge in edges:
				if edge[0] == node_or_edge[1] and edge[1] == node_or_edge[2]:
					return True;
			return False;
		else:									# This is a node
			return self.graphdict.has_key( node_or_edge );

	def add_nodes(self, nodelist):
		'''add a list of nodes.'''
		if not isinstance(nodelist, list):
			nodelist = [nodelist];
		for node in nodelist:
			if not self.contains( node ):
				self.graphdict[node] = [];

	def add_edges(self, edgelist):
		'''add a list of edges, An edge is of the format (node1, node2, weight)'''
		if not isinstance(edgelist, list):
			edgelist = [edgelist];

		for edge in edgelist:
			if self.contains( edge ):			# if the edge is already in the graph
				continue;

			node1 = edge[0];	node2 = edge[1];	weight = edge[2];

			if not self.contains( node1 ):	self.add_nodes( node1 );		# add the node if it doesn't exist in the graph
			if not self.contains( node2 ):	self.add_nodes( node2 );

			if (node2, weight) not in self.graphdict[node1]:
				self.graphdict[node1].append( (node2, weight) );

			if (node1, weight) not in self.graphdict[node2]:
				self.graphdict[node2].append( (node1, weight) );

	def get_all_nodes(self):
		'''get all nodes in the graph'''
		return self.graphdict.keys();

	def get_edges_of(self, node):
		'''get edges associated to the node'''
		return self.graphdict[node];

	def get_all_edges(self):
		'''get all edges.'''
		edges = [];
		added_edges = {}; 							# record edges that is already in the list.

		for node in self.graphdict.keys():
			node_edges = self.graphdict[node];		# get the edges of each node.
			for edge in node_edges:
				existing_edge = False;				# determine if the edge is already in the set
				if added_edges.has_key( ( node, edge[0] ) ) or added_edges.has_key( (edge[0], node) ):
					existing_edge = True;
				if not existing_edge:
					edges.append( (node, edge[0], edge[1]) );
					added_edges[ ( node, edge[0] ) ] = 1;
					added_edges[ ( edge[0], node ) ] = 1;

		return edges;


	def share_nodes_with(self, other):
		'''determine if two graphs share same ndoes'''
		othernodes = other.get_all_nodes();
		for node in othernodes:
			if self.graphdict.has_key( node ):
				return True;
		return False;

	def loop_free( self ):
		'''determine if the graph is loop free'''
		return self.num_of_loops() == 0;

	def mergeable_with(self, other):
		'''define two graph to be mergable, if they satisfy both
		1. they share some nodes
		2. the new graph is loop free
		'''
		if self == other:
			return False;
		share_nodes = self.share_nodes_with( other );
		if not share_nodes:
			return False;
		merged_graph = self.merge_with( other );
		new_graph_loop_free = merged_graph.loop_free();
		return share_nodes and new_graph_loop_free;

	def strong_mergeable_with(self, other):
		'''define two graph to be strong mergable, if they satisfy all
		1. they share some nodes
		2. the new graph is loop free
		3. no nodes have neighbors more than 2.
		'''
		if self == other:
			return False;
		share_nodes = self.share_nodes_with( other );
		if not share_nodes:
			return False;
		merged_graph = self.merge_with( other );
		new_graph_loop_free = merged_graph.loop_free();

		nodes = merged_graph.get_all_nodes();
		for node in nodes:
			if len(merged_graph.get_edges_of( node )) > 2:
				return False;

		return share_nodes and new_graph_loop_free;

	'''
	def self_merge_with(self, other):
		''merge the other graph with self. do not return a new graph. self is changed''
		otheredges = other.get_all_edges();
		self.add_edges( otheredges );
		return;'''

	def merge_with( self, other ):
		'''Merge with another graph. return a new graph, while self remain unchanged'''
		selfcopy   = self.copy();
		otheredges = other.get_all_edges();
		selfcopy.add_edges( otheredges );
		return selfcopy;

	############################################################
	########			     Path methods              #########

	def find_one_path(self, start, end, path=[]):
		'''find one path from the start node to the end node. This method is recursive and very inefficient.'''
		path = path +[start];
		if start == end:
			return path;
		elif not self.graphdict.has_key(start) or not self.graphdict.has_key(end):
			return None;

		for edge in self.graphdict[start]:
			node = edge[0];
			if node not in path:
				newpath = self.find_one_path( node, end, path );
				if newpath:
					return newpath;

		return None;

	def find_all_paths(self, start, end, path=[]):
		path = path + [start];
		if start == end:
			return [path];
		if not self.graphdict.has_key(start) or not self.graphdict.has_key(end):
			return [];
		paths = [];
		for edge in self.graphdict[start]:
			node = edge[0];
			if node not in path:
				newpaths = find_all_paths(self.graphdict, node, end, path);
				for newpath in newpaths:
					paths.append(newpath);
		return paths;

	def adjMat(self):
		'''Get the adjacency matrix'''
		nodes = self.graphdict.keys();
		mat = [];
		for node in nodes:
			row = [];
			adjnodes = self.__get_adj_nodes__(node);
			for other in nodes:
				if other == node:		row.append(0);
				elif other in adjnodes:	row.append(1);
				else:					row.append(0);
			mat.append(row);

		return mat;


	############################################################
	########	    Graph Construction and Save        #########

	def loadMat(self, mat):
		'''Load graph from an adjacency matrix (2d)'''
		n = len(mat);
		nodes = [];
		for i in range(0,n):
			nodes.append( Node( str(i), i ) );
		self.add_nodes( nodes );

		edges = [];
		i = 0;
		for row in mat:
			j = 0;
			for elem in row:
				if i != j and elem != 0:
					edges.append( (nodes[i], nodes[j], elem ));
				j+=1;
				pass;
			i+=1;
		self.add_edges( edges );

	def saveJson(self, filename):
		'''Save the graph in a Json file.'''
		jsonfile = open( filename, 'w' );

		nodeStr = "";
		linkStr = "";
		nodes = self.graphdict.keys();
		for node in nodes:
			nodeStr += "\t\t{\"name\":\"" + str(node.name) + "\", \"group\":"+ str(node.group) + ", \"value\":\"" + str(node.value)  +"\"},\n";
			for edge in self.graphdict[node]:
				linkStr += "\t\t{\"source\":"+ str(nodes.index(node)) +",\"target\":" + str(nodes.index(edge[0])) + ",\"value\":"+ str(edge[1]) +"},\n";

		nodeStr = nodeStr[0:-2] + "\n";
		linkStr = linkStr[0:-2] + "\n";

		nodeSection = "\n\t\"nodes\":[\n{0}\t]".format(nodeStr);
		linkSection = "\n\t\"links\":[\n{0}\t]".format(linkStr);

		jsonStr  = "{ "+ nodeSection +","+ linkSection +"\n}";
		#print jsonStr;
		jsonfile.write( jsonStr );
		jsonfile.close();

	def num_of_loops(self):
		'''the number of 1d holes'''
		mat = self.adjMat();
		edge_num = 0;
		for row in mat:
			for elem in row:
				if elem - 1.0 == 0.0:
					edge_num += 1;
		edge_num /= 2;
		vert_num = len(self.graphdict.keys());
		return edge_num - vert_num + 1;




############################################################
########             Partitioning Graph            #########
############################################################

class GraphBreaker(object):
	"""class for break a graph into several loop-free parts"""
	def __init__(self, graph):
		self.origin_graph = graph;

	def break_it(self):
		'''break the graph into several parts, and save them to another non-connected graph'''
		graphs = [];
		self_edges = self.origin_graph.get_all_edges();

		for edge in self_edges:
			graph = Graph();
			graph.add_edges( edge );
			graphs.append( graph );

		return self.merge_graphs( graphs );


	def merge_graphs(self, graphs):
		pq = PriorityQueue();
		for graph in graphs:
			pq.push( graph, graph.size() );
		
		visited = [];
		while pq.size() > 1:
			this_time_popped = [];
			smallest_graph = pq.pop();
			this_time_popped.append(smallest_graph);
			while (smallest_graph in visited) and (not pq.isEmpty()):
				smallest_graph = pq.pop();
				this_time_popped.append( smallest_graph );
			visited.append( smallest_graph );
			for popped in this_time_popped:
				if popped not in visited:
					pq.push( popped, popped.size() );

			choices = [];

			small_size_graphs = pq.get_all();
			#small_size_graphs = pq.get_smalls( smallest_graph.size() ); # Choose all graphs such that 
																		# 1. they have priority no less than current one, and 
																		# 2. when merge with the smallest one they get a same size new graph
			for graph in small_size_graphs:
				if smallest_graph.strong_mergeable_with( graph ):		# test if they are mergeable
					choices.append( graph );

			if len(choices) == 0:									# if no mergeable graph with the smallest one
				pq.push( smallest_graph, smallest_graph.size() );
				continue;

			# Now we have all graphs mergeable with the smallest graph that will produce the same sized new graph
			''' naive strategy'''
			print '--------------'
			print len(graphs), pq.size();
			graphs.remove(smallest_graph);
			graphs.remove( choices[0] );
			pq.remove_task( choices[0] );
			merged_graph = smallest_graph.merge_with( choices[0] );
			graphs.append( merged_graph );
			pq.push( merged_graph, merged_graph.size() );
			print len(graphs), pq.size();

			'''better strategy:
			--------------------------------------------------------------------------
			define 'credit' for a list of graphs as:
			The sum of the number of all mergeable graphs for every graph in the list
			--------------------------------------------------------------------------
			Merging two graphs means decreasing the credit by at least two.
			With more credits, we can merge more graphs in the list.
			So we prefer to merge graphs that results in larger credit. 
			(Or, we prefer to merge graphs that decrease credit least.)
			'''
			
		#################
		### 'graphs' is a list of loop-free graphs. Each cannot merge with another.
		print len(graphs)
		composed_graph = self.compose( graphs );
		return composed_graph; 

	def compose(self, graphs):
		'''graphs are a list of graphs that each share some nodes. 
		We need to compose them into one graph, to be shown in a webpage.
		All nodes remain the same name, but are different now.'''
		def find_same_name( nodes, node ):
			'''Find a node in a list that has the same name with the 'node' '''
			for item in nodes:
				if item.same_name_with( node ):
					return item;

		new_graph = Graph();

		for graph in graphs:
			nodes = graph.get_all_nodes();
			new_nodes = [];
			for node in nodes:
				new_nodes.append( Node(node.name, node.group, node.value));
			edges = graph.get_all_edges();
			new_edges = [];
			for edge in edges:
				corr_node1 = find_same_name( new_nodes, edge[0] );
				corr_node2 = find_same_name( new_nodes, edge[1] );
				new_edges.append( ( corr_node1, corr_node2, edge[2] ) );
			new_graph.add_edges( new_edges );
			
		return new_graph;	


'''
graph = Graph();
matrix = [ [0,1,0,1,1,0],
		   [1,0,1,0,0,1],
		   [0,1,0,1,0,1],
		   [1,0,1,0,1,0],
		   [1,0,0,1,0,1],
		   [0,1,1,0,1,0] ];

matrix2= [ [0,1,0,0,0,1],
		   [1,0,1,0,1,0],
		   [0,1,0,1,0,0],
		   [0,0,1,0,1,0],
		   [0,1,0,1,0,1],
		   [1,0,0,0,1,0] ]

matrix3 = [ [0,1,0,0,0,0,0,1,1,0],
		    [1,0,1,0,0,0,0,0,1,0],
		    [0,1,0,1,0,0,0,0,1,0],
		    [0,0,1,0,1,0,0,0,1,0],
		    [0,0,0,1,0,1,0,0,0,1],
		    [0,0,0,0,1,0,1,0,0,1],
		    [0,0,0,0,0,1,0,1,0,1],
		    [1,0,0,0,0,0,1,0,0,1],
		    [1,1,1,1,0,0,0,0,0,1],
		    [0,0,0,0,1,1,1,1,1,0] ]
graph.loadMat( matrix3);
graph.saveJson('./graph_drawing/data/graph2.json');

graphBreaker = GraphBreaker(graph);
breaked_graph = graphBreaker.break_it();
breaked_graph.saveJson('./graph_drawing/data/broken_graph.json');
'''