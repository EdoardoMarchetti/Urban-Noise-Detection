import pandas as pd
import altair as alt
import argparse as ap


parser = ap.ArgumentParser()

parser.add_argument('--data_folder', type = str, default='data')
parser.add_argument('--data_file_name', type = str, default='frame_length.csv')
parser.add_argument('--dimension', type = str, default= 'frame_length_in_s')

args = parser.parse_args()

df = pd.read_csv(f'{args.data_folder}/{args.data_file_name}')
other_dimensions = [col for col in df.columns[:-2] if col != args.dimension] 

subtitle = ''
for col in other_dimensions:
    subtitle += f'{col} = {df[col][0]} '


#Accuracy plot
accuracy = alt.Chart(df).encode(
    alt.X(args.dimension, type = 'quantitative'),
    alt.Y('Accuracy', type = 'quantitative', scale = alt.Scale(zero = False)),
)

accuracy = accuracy.properties(
    title = alt.TitleParams(
        text= f'{args.dimension} vs accuracy',
        subtitle = f'{subtitle}',
        subtitleColor= 'grey'
    )
)

accuracy = (accuracy.mark_line() + accuracy.mark_point()+ alt.Chart().mark_rule().encode(y = alt.datum(0.98)))



#Latency plot
latency = alt.Chart(df).encode(
    alt.X(args.dimension, type = 'quantitative'),
    alt.Y('Avg Latency', type = 'quantitative', scale = alt.Scale(zero = False)),
)

latency = latency.properties(
    title = alt.TitleParams(
        text= f'{args.dimension} vs latency',
        subtitle = f'{subtitle}',
        subtitleColor= 'grey'
    )
)

latency = (latency.mark_line() + latency.mark_point())



final_chart = accuracy | latency
final_chart.show()