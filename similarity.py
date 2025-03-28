import networkx as nx
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def find_similar(news_data, tfidf_matrix, cluster_labels, threshold=0.75):
    edges = []
    graph = nx.DiGraph()
    result_text = str()
    for cluster in set(cluster_labels):
        indices = np.where(cluster_labels == cluster)[0]
        if len(indices) < 2:
            continue

        news_subset = [news_data[i] for i in indices]
        subset_matrix = tfidf_matrix[indices]
        similarities = cosine_similarity(subset_matrix)

        for i in range(len(news_subset)):
            for j in range(i + 1, len(news_subset)):
                if similarities[i, j] > threshold and news_subset[i]["source"] != news_subset[j]["source"]:
                    if news_subset[i]["id"] not in graph.nodes:
                        graph.add_node(news_subset[i]["id"], title=news_subset[i]["title"], text=news_subset[i]["text"],
                                       author=news_subset[i]["author"], date=news_subset[i]["date"],
                                       source=news_subset[i]["source"])

                    if news_subset[j]["id"] not in graph.nodes:
                        graph.add_node(news_subset[j]["id"], title=news_subset[j]["title"], text=news_subset[j]["text"],
                                       author=news_subset[j]["author"], date=news_subset[j]["date"],
                                       source=news_subset[j]["source"])

                    edges.append((news_subset[i]["id"], news_subset[j]["id"], similarities[i, j]))
                    graph.add_edge(news_subset[i]["id"], news_subset[j]["id"], weight=similarities[i, j])
                    result_text += f"{news_subset[i]['title']} → {news_subset[j]['title']} (сходство: {similarities[i, j]:.2f})\n"
    return graph, edges, result_text
