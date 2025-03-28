from sklearn.cluster import KMeans


def run_clustering(tfidf_matrix, num_clusters, clustering_method):
    if clustering_method == "K-Means":
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        labels = kmeans.fit_predict(tfidf_matrix)
        return labels
