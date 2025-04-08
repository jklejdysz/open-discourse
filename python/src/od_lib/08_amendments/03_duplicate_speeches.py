import numpy as np
import re
from tqdm import tqdm

import os
import od_lib.definitions.path_definitions as path_definitions
import pandas as pd
from datetime import datetime

speeches = pd.read_csv(os.path.join(path_definitions.DATABASE, "speeches_revised.csv"))

speeches['speech_content']=speeches['speech_content'].apply(str)
speeches.speech_content.fillna(" ", inplace=True)
speeches['length'] = speeches['speech_content'].str.split().apply(len)

speeches_agr = speeches.groupby(['electoral_term', 'session', 'date'])['length'].sum().reset_index()
speeches_agr.describe()

speeches_agr.shape
speeches_agr['electoral_term_cat'] = (speeches_agr['electoral_term'] % 2) == 0
speeches_agr = speeches_agr.astype({"electoral_term_cat":'category'})

#plt.figure(figsize=(20,7) )
#sns.scatterplot(x ='date', y='length', data=speeches_agr, hue='electoral_term_cat', s=10,ec=None)

speeches_agr[speeches_agr.length > 300000]


outliers = speeches[(speeches.electoral_term == 17) & (speeches.session == 250)]
outliers = speeches[(speeches.electoral_term == 16) & (speeches.session == 250)]
outliers = speeches.copy() # earlier the variable 'dupl' was created due to reference issues

outliers.columns.tolist()
outliers['speech_content_beginning'] = outliers['speech_content'].str[:150]

outliers.sort_values(by = ['electoral_term', 'session', 'politician_id', 'date', 'speech_content_beginning', 'length'],
                    ascending = False, inplace = True)

dupl = outliers.duplicated(subset=['electoral_term', 'session', 'politician_id', 'date', 'speech_content_beginning'], keep='first').reset_index(drop=True)


outliers['dupl'] = dupl.tolist()
outliers.sort_values(by = 'id', ascending = True, inplace = True)

outliers.head(50)

tab = outliers[(outliers.dupl>0) & (outliers.length > 20)].groupby(['electoral_term', 'session'])['dupl'].sum()
id_to_remove = outliers['id'][(outliers.session == 250) & (outliers.electoral_term== 17) & (outliers.dupl == True)]
# same len id_to_remove as before

speeches['drop_dupl'] = ~speeches['id'].isin(id_to_remove)
speeches.columns

speeches.to_csv(os.path.join(path_definitions.DATABASE, "speeches_revised.csv"), index = False)

speeches[speeches.politician_id==-1].groupby(['electoral_term']).count()
speeches.count()
#speeches_prev = pd.read_csv(os.path.join(path_definitions.DATABASE, "speeches_revised copy.csv"))

#speeches_prev.groupby(['electoral_term'])['id'].count() - speeches.groupby(['electoral_term'])['id'].count()

#sum(speeches[speeches.electoral_term<20]['id']!=speeches_prev[speeches.electoral_term<20]['id'])
