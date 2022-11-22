import pandas as pd
import altair as alt
import argparse as ap


df_frame_length = pd.read_csv(f'data/frame_length.csv')
other_dimensions = [col for col in df_frame_length.columns[:-2] if col != 'frame_length_in_s'] 

subtitle = ''
for col in other_dimensions:
    subtitle += f'{col} = {df_frame_length[col][0]} '

#Latency plot
latency = alt.Chart(df_frame_length).encode(
    alt.X('frame_length_in_s', type = 'quantitative'),
    alt.Y('Avg Latency', type = 'quantitative', scale = alt.Scale(zero = False)),
)

latency = latency.properties(
    title = alt.TitleParams(
        text= f'frame_length vs latency',
        subtitle = f'{subtitle}',
        subtitleColor= 'grey'
    )
)

latency = (latency.mark_line() + latency.mark_point())


df_duration = pd.read_csv(f'data/duration_treshold.csv')
other_dimensions = [col for col in df_duration.columns[:-2] if col != 'duration_thres'] 


subtitle = ''
for col in other_dimensions:
    subtitle += f'{col} = {df_duration[col][0]} '


#Accuracy plot
accuracy = alt.Chart(df_duration).encode(
    alt.X('duration_thres', type = 'quantitative'),
    alt.Y('Accuracy', type = 'quantitative', scale = alt.Scale(zero = False)),
)

accuracy = accuracy.properties(
    title = alt.TitleParams(
        text= f'duration_thres vs accuracy',
        subtitle = f'{subtitle}',
        subtitleColor= 'grey'
    )
)

accuracy = (accuracy.mark_line() + accuracy.mark_point())





final_chart = accuracy | latency
final_chart.show()