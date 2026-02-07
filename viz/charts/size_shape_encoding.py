# Use 'z' to size markers
fig = px.scatter(df, x='x', y='y', color='outcome', size='z', color_discrete_map=colors,
                 title="Scatter Plot with Marker Size Encoding")
fig.show()
