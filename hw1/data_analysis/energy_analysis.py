import pandas as pd
import altair as alt
import argparse as ap
import numpy as np

parser = ap.ArgumentParser()

parser.add_argument('--sr', type = int, default= 16000)
parser.add_argument('--frl', type = float, default= 0.04)
parser.add_argument('--frs', type= float, default= 0.04)

args = parser.parse_args()

file = f'energy_data/sr_{args.sr}_frl_{args.frl}_frs_{args.frs}.csv'

df = pd.read_csv(file)


df = df.groupby(by = 'label').mean(0)
df.columns =  np.arange(0, 1, args.frl)
df = df.reset_index()
df = df.melt('label', var_name = 'Time', value_name = 'Energy')
df.sort_values(by = 'label', ascending = False, inplace = True)

bars = alt.Chart(df).mark_bar(opacity=0.7).encode(
    alt.X('Time', title = 'Time(s)', type = 'quantitative'),
    y=alt.Y('Energy:Q', stack=None),
    color=alt.Color("label", scale= alt.Scale(domain = ['silence', 'no_silence'], range = ['red', 'blue']))
).properties(
    title = alt.TitleParams(
        text = 'Energy comparison silence vs no_silence mean frame',
        subtitle= f'sample_rate = {int(args.sr / 1000)} kHz, frame_length = {args.frl} s, frame_step = {args.frs} s',
        subtitleColor= 'grey'
    )
)

rule = alt.Chart().mark_rule(color='black', strokeDash=[10, 10]).encode(y=alt.datum(-120))

(bars+rule).show()