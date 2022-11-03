import altair as alt
import pandas as pd

from altair_saver import save




data = pd.read_csv('hyperparameters_tuning.txt')
print(list(data.columns[:-2]))


accuracy_vs_latency = alt.Chart(data).mark_point().encode(
    alt.X('Accuracy', title='Accuracy (%)', type = 'quantitative', scale = alt.Scale(domain = (0.87,1.0))),
    alt.Y('Avg Latency', title = 'Avg Latency (ms)', type = 'quantitative', scale = alt.Scale(domain = (9.0,14.0))),
    tooltip=list(data.columns[:-2])
)

accuracy_vs_latency =  accuracy_vs_latency.properties(
    title = 'Accuracy vs Average Latency'
)

#accuracy_vs_latency.interactive().show()



rows = []
columns = []
duration_values = data['duration_thres'].unique()
for i,dur in enumerate(duration_values):
    print(dur)
    accuracy_vs_duration_thresh = alt.Chart(data[data.duration_thres == dur]).mark_line().encode(
        alt.X ('dbFSthres', type = 'quantitative'),
        alt.Y('Accuracy',type ='quantitative', scale = alt.Scale(domain=(0.85,1.0))),
        alt.Color('frame_length_in_s', type = 'nominal')
    )
    latency_vs_duration_thresh = alt.Chart(data[data.duration_thres == dur]).mark_line().encode(
        alt.X ('dbFSthres', type = 'quantitative'),
        alt.Y('Avg Latency', title = 'Avg Latency (ms)', type = 'quantitative', scale = alt.Scale(domain = (9.0,14.0))),
        alt.Color('frame_length_in_s', type = 'nominal')
    )

    row = alt.hconcat(accuracy_vs_duration_thresh, latency_vs_duration_thresh).properties(
        title = alt.TitleParams(text = f'duration_thres (ms) = {dur}'),
    )

    rows.append(row)

alt.hconcat(
    alt.vconcat(*rows[:5]),
    alt.vconcat(*rows[5:])
).show()




