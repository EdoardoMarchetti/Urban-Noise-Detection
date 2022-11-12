from glob import glob
import pandas as pd


df = pd.DataFrame()

for file in glob('data/*'):
    temp_df = pd.read_csv(file)
    temp_df.rename(columns= {'Accuracy': 'accuracy', 'Avg Latency': 'latency'}, inplace= True)
    good_combinations = temp_df[(temp_df['accuracy'] > 0.98) & (temp_df.frame_length_in_s > 0.001)]
    df = pd.concat([df, good_combinations], axis=0, ignore_index= True)



df.drop_duplicates(inplace = True)


print(df)
df.to_csv('combinations/accuracy_gt98.txt', index = False)
print('saved')