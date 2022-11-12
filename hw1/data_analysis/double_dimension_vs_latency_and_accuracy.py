import pandas as pd
import altair as alt
import argparse as ap


parser = ap.ArgumentParser()

parser.add_argument('--data_folder', type = str, default='data')
parser.add_argument('--data_file_name', type = str, default='frame_length.csv')
parser.add_argument('--dimension', type = str, default= 'frame_length_in_s')
parser.add_argument('--color', type = str, default= '')

args = parser.parse_args()

df = pd.read_csv(f'{args.data_folder}/{args.data_file_name}')
other_dimensions = [col for col in df.columns[:-2] if (col != args.dimension and col != args.color)] 

subtitle = ''
for col in other_dimensions:
    subtitle += f'{col} = {df[col][0]} '


#Accuracy plot
accuracy = alt.Chart(df).encode(
    alt.X(args.dimension, type = 'quantitative'),
    alt.Y('Accuracy', type = 'quantitative', scale = alt.Scale(zero = False)),
    alt.Color(f'{args.color}:N')
)

accuracy = accuracy.properties(
    title = alt.TitleParams(
        text= f'{args.dimension} vs accuracy',
        subtitle = f'{subtitle}',
        subtitleColor= 'grey'
    )
)

rule = alt.Chart().mark_rule().encode(y = alt.datum(0.98))

accuracy = (rule + accuracy.mark_line() + accuracy.mark_point())


#Latency plot
latency = alt.Chart(df).encode(
    alt.X(args.dimension, type = 'quantitative'),
    alt.Y('Avg Latency', type = 'quantitative', scale = alt.Scale(zero = False)),
    alt.Color(f'{args.color}:N')
)

latency = latency.properties(
    title = alt.TitleParams(
        text= f'{args.dimension} vs latency',
        subtitle = f'{subtitle}',
        subtitleColor= 'grey'
    )
)

rule = alt.Chart().mark_rule().encode(y = alt.datum(9))

latency = (rule + latency.mark_line() + latency.mark_point())



final_chart = accuracy | latency
final_chart.show()