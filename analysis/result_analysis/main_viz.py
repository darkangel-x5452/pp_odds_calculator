import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


class ResultsViz:
    def __init__(self):
        self.data_fp = "data/results/outcome_results.parquet"
        self.combined_df: pd.DataFrame
        self.result_col = "Result"
        self.competition_name_col = "competition_name"
        self.sport_genre_col = "sport_genre"
        self.home_result_col = "home_result"

    def read_data(self) -> pd.DataFrame:

        combined_df = pd.read_parquet(self.data_fp)

        combined_df = combined_df.sort_values("start_time_aest")
        self.combined_df = (
            combined_df
            # combined_df[combined_df["Odds"] < 2.0]
            # combined_df[combined_df["Odds"] >= 2.0]
            # combined_df  # [combined_df["home_full_name"] == combined_df["odds_on"]]
        )
        return combined_df

    def plot_data(self):
        self.fig = make_subplots(
            rows=3,
            cols=2,
            # subplot_titles=(
            #     "📈 Time Series – Stock Prices",
            #     "📉 Close Price (Area)",
            #     "📊 Monthly Revenue by Category (Stacked Bar)",
            #     "🌡️  Correlation Heatmap",
            # ),
            # row_heights=[0.30, 0.30, 0.40],
            vertical_spacing=0.1,
            horizontal_spacing=0.02,
            specs=[
                [{"colspan": 2}, None],  # row 1
                [{"type": "xy"}, {"type": "domain"}],  # row 2
                [{"secondary_y": 2}, {"type": "xy"}],  # row 1
            ],
        )

        self.bar_chart_cat(data_input=self.combined_df, group_by=self.competition_name_col, position=[1, 1])
        self.bar_chart_cat(data_input=self.combined_df, group_by=self.sport_genre_col, position=[2, 1])
        self.tree_map_build(data_input=self.combined_df, position=[2, 2])
        self._timeseries_win_loss(data_input=self.combined_df, position=[3,1])
        self._graph_probability_data(data_input=self.combined_df.dropna(subset="probability"), position=[3,2])
        
        
        self.fig.update_layout(
            title="Percentage of",
            barmode="stack",  # stacked
            template="plotly_dark",
        )

        self.fig.show()

    def _timeseries_win_loss(self, data_input: pd.DataFrame, position: list[int]):
        datetime_col = "timestamp_aest"
        result = self.result_col
        credit_val = "Credit"
        lost_val = "Lost"
        results = [credit_val, lost_val, "Refund"]

        data_input[datetime_col] = pd.to_datetime(data_input[datetime_col])

        daily_counts = (
            data_input.groupby([pd.Grouper(key=datetime_col, freq="D"), result])
            .size()
            .unstack(fill_value=0)
            .reset_index()
            .sort_values(datetime_col)
        )

        for col in results:
            if col not in daily_counts.columns:
                daily_counts[col] = 0

        # total decisive outcomes only
        daily_counts["total_win_loss"] = daily_counts[credit_val] + daily_counts[lost_val]

        # win percentage, excluding refunds from denominator
        daily_counts["win_pct"] = (
            daily_counts[credit_val] / daily_counts["total_win_loss"]
        ).where(daily_counts["total_win_loss"] > 0) * 100

        # bottom: stacked bars
        for result_name in results:
            self.fig.add_trace(
                go.Bar(
                    x=daily_counts[datetime_col],
                    y=daily_counts[result_name],
                    name=result_name,
                    opacity=0.7,
                ),
                row=position[0], col=position[1], secondary_y=False
            )

        self.fig.add_trace(
            go.Scatter(
                x=daily_counts[datetime_col],
                y=daily_counts["win_pct"],
                mode="lines+markers",
                name="Win %",
                line=dict(width=3)
            ),
            row=position[0], col=position[1], secondary_y=True
        )

        self.fig.update_xaxes(title_text="Date", row=position[0], col=position[1])
        self.fig.update_yaxes(title_text="Count", row=position[0], col=position[1], secondary_y=False)
        self.fig.update_yaxes(title_text="Win %", range=[0, 100], secondary_y=True, row=position[0], col=position[1])


    def _graph_probability_data(self, data_input: pd.DataFrame, position: list[int]) -> pd.DataFrame:
        row_pos = position[0]
        col_pos = position[1]

        data_pd = data_input.copy()

        x = "probability"
        y = "Odds"
        colour = self.result_col

        # cleaner filtering than .where(...)
        data_pd = data_pd.dropna(subset=[x, y, colour])
        data_pd = data_pd[data_pd[x] != 0]

        centroids = data_pd.groupby(colour)[[x, y]].mean().reset_index()

        category_colors = {
            "Lost": "red",
            "Credit": "green"
        }

        # add one scatter trace per category into subplot position (3,2)
        for category_value in data_pd[colour].unique():
            plot_df = data_pd[data_pd[colour] == category_value]

            plot_colour = category_colors.get(category_value, "grey")

            self.fig.add_trace(
                go.Scatter(
                    x=plot_df[x],
                    y=plot_df[y],
                    mode="markers",
                    name=str(category_value),
                    marker=dict(
                        size=20,
                        color=plot_colour
                    ),
                    customdata=plot_df[[x, y, colour]],
                    hovertemplate=(
                        f"{x}: %{{x}}<br>"
                        f"{y}: %{{y}}<br>"
                        f"{colour}: %{{customdata[2]}}<extra></extra>"
                    )
                ),
                row=row_pos,
                col=col_pos
            )

        # add centroid markers
        for _, row_data in centroids.iterrows():
            plot_colour = category_colors.get(row_data[colour], "grey")

            self.fig.add_trace(
                go.Scatter(
                    x=[row_data[x]],
                    y=[row_data[y]],
                    mode="markers",
                    marker=dict(
                        symbol="x",
                        size=25,
                        color=plot_colour,
                        line=dict(width=2)
                    ),
                    name=f"Centroid {row_data[colour]}",
                    hovertemplate=(
                        f"{colour}: {row_data[colour]}<br>"
                        f"{x}: %{{x}}<br>"
                        f"{y}: %{{y}}<extra></extra>"
                    )
                ),
                row=row_pos,
                col=col_pos
            )

        self.fig.update_xaxes(title_text=x,
                row=row_pos,
                col=col_pos)
        self.fig.update_yaxes(title_text=y,
                row=row_pos,
                col=col_pos)
        return data_input

    def bar_chart_cat(self, data_input: pd.DataFrame, group_by: str, position: list):
        # group_by = self.sport_genre_col

        sport_result_pcts = pd.crosstab(
            data_input[group_by],
            data_input[self.result_col],
            normalize="index",
        ).mul(100)
        sport_result_pcts = sport_result_pcts.reset_index().rename(
            columns={"index": group_by}
        )
        sport_result_pcts = sport_result_pcts.sort_values(
            "Credit", ascending=False
        ).set_index(group_by)
        for cat_b_val in sport_result_pcts.columns:
            print(cat_b_val)
            self.fig.add_trace(
                go.Bar(
                    x=sport_result_pcts.index,  # cat_a values → x-axis
                    y=sport_result_pcts[cat_b_val],  # count_col values → y-axis
                    name=cat_b_val,  # cat_b label → legend / colour
                ),
                row=position[0],
                col=position[1],
            )


    

    def tree_map_build(self, data_input: pd.DataFrame, position: list[int, int]):
        # Build treemap labels/parents by stacking parent rows + child rows
        data_graph = data_input
        percentage_col = "percentage"
        out = (
            data_graph.groupby(self.competition_name_col)[self.result_col]
            .value_counts(dropna=False)
            .rename("count")
            .reset_index()
        )

        # total rows per competition
        out["total_count"] = out.groupby(self.competition_name_col)["count"].transform(
            "sum"
        )

        # percentage of each result within each competition
        out[percentage_col] = out["count"] / out["total_count"] * 100

        # only keep Credit rows
        df_tree = out[out[self.result_col] == "Credit"].copy()

        # optional: avoid string "nan" issues in hover
        df_tree[self.competition_name_col] = df_tree[self.competition_name_col].fillna(
            "Missing"
        )

        # root node
        root_label = "Credit"

        labels = [root_label] + df_tree[self.competition_name_col].tolist()
        parents = [""] + [root_label] * len(df_tree)

        # give unique ids to avoid ambiguity
        ids = [root_label] + [
            f"{root_label}|{comp}" for comp in df_tree[self.competition_name_col]
        ]

        customdata = np.column_stack(
            [
                df_tree["count"],
                df_tree["total_count"],
                df_tree["percentage"].round(2),
            ]
        ).tolist()

        color_vals = np.log1p(df_tree["total_count"])  # log(1 + x)

        self.fig.add_trace(
            go.Treemap(
                ids=ids,
                labels=labels,
                parents=parents,
                values=df_tree["percentage"].tolist(),  # size by percentage
                customdata=customdata,
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Credit count: %{customdata[0]}<br>"
                    "Competition total: %{customdata[1]}<br>"
                    "Credit % within competition: %{customdata[2]}%<br>"
                    "<extra></extra>"
                ),
                texttemplate="<b>%{label}</b><br>%{value:.2f}%",
                tiling=dict(packing="squarify"),
                marker=dict(
                    # colors=df_tree["total_count"].tolist(),   # color by total_count
                    colors=color_vals,
                    colorscale="RdYlGn",
                    cmin=color_vals.min(),
                    cmax=color_vals.max(),
                    showscale=True,
                    colorbar=dict(title="Competition Total"),
                ),
                name="Treemap",
            ),
            row=position[0],
            col=position[1],
        )


def run_app():
    # Tree map of win percent, total count, by sport genre
    # Tree map of win percent, total count, by competition name
    # Bar Stack of win percent, by sport genre
    # Bar Stack of win percent, by competition name
    # Table of home verse all results, showing if home has higher percent win
    # Timeseries of wins/losses each day
    # Filter by Favour >50% and <50%

    rv = ResultsViz()
    rv.read_data()
    rv.plot_data()


if __name__ == "__main__":
    run_app()
