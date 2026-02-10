import pandas as pd
import plotly.express as px

class CalculatorMetrics:
    def __init__(self):
        file_path = "/mnt/c/Users/s/Downloads/bet_records_shared - Sheet1 (1).csv"
        data_pd = pd.read_csv(file_path, skiprows=5)
        self.chatgpt_odds_col = "chatgpt_favour"
        sport_col = "sport"
        y = "win"
        colour = "outcome"
        # colour = "sport"

        data_pd = data_pd.dropna(subset=[self.chatgpt_odds_col, y, colour]).where(data_pd[self.chatgpt_odds_col] != 0)
        data_pd = data_pd.where(data_pd[colour] != "Refunded")
        # self.data_pd = data_pd.dropna(subset=[colour]).where(data_pd[sport_col] == "Tennis")
        self.data_pd = data_pd.dropna(subset=[colour])

    def calculate_best_chatgpt_odds(self):
        data_pd = self.data_pd

        # Step 1: Create a numeric win flag
        data_pd['win_flag'] = data_pd['outcome'].apply(lambda x: 1 if x == 'Won' else 0)

        # Step 2: Sort by odds_percentage
        df_sorted = data_pd.sort_values(self.chatgpt_odds_col, ascending=False).reset_index()

        # Step 3: Calculate cumulative wins and losses
        df_sorted['cum_wins'] = df_sorted['win_flag'].cumsum()
        df_sorted['cum_losses'] = (~df_sorted['win_flag'].astype(bool)).cumsum()

        # Step 4: Calculate cumulative win ratio
        df_sorted['win_ratio'] = df_sorted['cum_wins'] / (df_sorted['cum_wins'] + df_sorted['cum_losses'])

        group_means = df_sorted.groupby(self.chatgpt_odds_col)['win_ratio'].mean().reset_index()

        # Step 2: Filter for mean > 0.5
        filtered = group_means[group_means['win_ratio'] >= 0.5]

        # Step 3: Pick the first row
        if not filtered.empty:
            fisrt_hit = filtered.iloc[0]
            threshold_odds = fisrt_hit[self.chatgpt_odds_col]
            print("Threshold odds_percentage for 50/50 win/loss:", threshold_odds)
        else:
            print("No group has mean above 0.5")

    def calculate_chatgpt_odds_count(self):
        group_count = self.data_pd.groupby(self.chatgpt_odds_col)["outcome"].count().reset_index()
        print(group_count[[self.chatgpt_odds_col, "outcome"]])

def run_app():
    cm = CalculatorMetrics()
    cm.calculate_best_chatgpt_odds()
    cm.calculate_chatgpt_odds_count()

if __name__ == "__main__":
    run_app()
    