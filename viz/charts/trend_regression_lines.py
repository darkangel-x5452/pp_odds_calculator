fig = px.scatter(df, x='x', y='y', color='outcome', trendline='ols', color_discrete_map=colors,
                 title="Scatter with Linear Trend Lines")
fig.show()
