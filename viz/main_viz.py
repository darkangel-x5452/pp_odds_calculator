import pandas as pd
import plotly.express as px

if __name__ == "__main__":
    file_path = "/mnt/c/Users/s/Downloads/bet_records_shared - main.csv"
    data_pd = pd.read_csv(file_path, skiprows=5)

    x = "chatgpt_favour"
    y = "win"
    colour = "outcome"
    # colour = "sport"

    data_pd = data_pd.dropna(subset=[x, y, colour]).where(data_pd[x] != 0)
    # data_pd = data_pd.dropna(subset=[x, y, colour]).where(data_pd[y] >= 2.0)
    data_pd = data_pd.dropna(subset=[colour])

    centroids = data_pd.groupby(colour)[[x,y]].mean().reset_index()

    category_colors = {'Loss':'red', 'Won':'green'}
    # Interactive scatter plot
    fig = px.scatter(
        data_pd, 
        x=x, 
        y=y, 
        color=colour,  # color by category
        title='Interactive Scatter Plot',
        labels={x:'X Column', y:'Y Column'},
        size_max=40,        # max marker size
        color_discrete_map=category_colors,  # assign colors manually
        hover_data=[x,y,colour]  # info shown on hover
    )

    fig.add_scatter(
        x=centroids[x],
        y=centroids[y],
        mode='markers',
        marker=dict(symbol='x', size=20, color='black'),
        name='Centroid'
    )
    for i, row in centroids.iterrows():
        if row[colour] not in category_colors:
            plot_colour = "grey"
        else:
            plot_colour = f"{category_colors[row[colour]]}"
            
        fig.add_scatter(
            x=[row[x]],
            y=[row[y]],
            mode='markers',
            marker=dict(symbol='x', size=25, color=plot_colour),
            name=f"Centroid {row[colour]}"
        )
    fig.update_traces(marker=dict(size=20))  # all dots size 20
    fig.show()
