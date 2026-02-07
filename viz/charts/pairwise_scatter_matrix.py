# Assuming you have more numeric columns like x, y, z
df['z'] = [5,2,7,3,6,4,8,2,5]

fig = px.scatter_matrix(df, dimensions=['x','y','z'], color='outcome', color_discrete_map=colors,
                        title="Scatter Matrix of Numeric Columns")
fig.show()
