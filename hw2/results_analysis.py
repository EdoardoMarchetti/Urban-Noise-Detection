import altair as alt
import pandas as pd
import numpy as np

df = pd.read_csv('team08_hw2_results.csv')
df['median_total_latency'] = df.median_total_latency.apply(lambda x:round(x*1000, 3))


print(df)


base = alt.Chart(df).encode(
    x=alt.X('median_total_latency', title='Latency (ms)', type='quantitative', 
            scale=alt.Scale(domain=[5.35, 5.95])),
    y=alt.Y('accuracy', title='Accuracy', type='quantitative', scale=alt.Scale(domain=[df['accuracy'].min()-0.01, 1.0])),
).transform_filter(
    (alt.datum.zipped_size < 1000)
)

points = base.mark_point().encode(
    size= alt.Size('zipped_size', title='Size (KB)', type='quantitative'),
    tooltip = ['tag','accuracy', 'median_total_latency', 'zipped_size']
)


big_labels = base.mark_text(
    align='center',
    baseline='bottom',
    dx=0,
    dy=-10,
).transform_filter(
    alt.datum.zipped_size > 1000
).encode(
    text='label:N'
)

small_labels = base.mark_text(
    align='center',
    baseline='bottom',
    dx=0,
    dy=-8,
).transform_filter(
    (alt.datum.zipped_size < 1000) & (alt.datum.zipped_size > 40)
).encode(
    text='label:N'
)

final = base.mark_text(
    align='center',
    baseline='bottom',
    dx=0,
    dy=-5,
).transform_filter(
    (alt.datum.tag == 'Final')
).encode(
    text='label:N'
)

dw_ws = base.mark_text(
    align='center',
    baseline='top',
    dx=0,
    dy=+5,
).transform_filter(
    (alt.datum.tag == 'DW+WS')
).encode(
    text='label:N'
)


(points+small_labels+big_labels+final+dw_ws).interactive().show()