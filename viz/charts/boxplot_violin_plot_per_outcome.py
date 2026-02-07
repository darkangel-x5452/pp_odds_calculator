# Boxplot
fig = px.box(df, x='outcome', y='y', color='outcome', color_discrete_map=colors,
             title="Boxplot of Y by Outcome")
fig.show()

# Violin plot
fig = px.violin(df, x='outcome', y='y', color='outcome', box=True, points='all', color_discrete_map=colors,
                title="Violin Plot of Y by Outcome")
fig.show()
