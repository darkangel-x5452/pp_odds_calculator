from sklearn.cluster import KMeans
import numpy as np

X = df[['x','y']].to_numpy()
kmeans = KMeans(n_clusters=3, random_state=0).fit(X)
df['cluster'] = kmeans.labels_

fig = px.scatter(df, x='x', y='y', color='cluster', symbol='outcome',
                 title="KMeans Clustering of Points", size_max=15)
fig.show()
