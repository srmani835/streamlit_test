import streamlit as st
import pandas as pd

import warnings
warnings.filterwarnings('ignore')
import time


def readcsv(csv):
    df = pd.read_csv(csv)
    return df

def convert_df(df):
   return df.to_csv().encode('utf-8')

def combine_df(df1, df2):
    return pd.concat([df1, df2], axis=1)

def progress_bar(timesleep):
    my_bar = st.progress(0)
    for percent_complete in range(100):
        time.sleep(timesleep)
        my_bar.progress(percent_complete + 1)
		
def Prediction(df):
    length=titanic_df.shape
	pred_list=[]
    for i in range(length[0]):
	    c_r=random.randint(0,1)
		pred_list.append(c_r)
	pred_df=pd.DataFrame(pred_list)
	
	return pred_df
	     
	   

def main():

    st.title('   Money Laundering Detection   ')
    st.image('image.jpg',width=None, use_column_width='always')
    st.markdown('Application to detect the irregularities in day to day transactions')
    file = st.file_uploader('Upload your csv file', type='csv')

    if file is not None:
        
        df = readcsv(file)
        initial_df = df.copy(deep = False) 
    
        predictor = Prediction(df)
        
        final_data = combine_df(initial_df, predictor)

        target_file = convert_df(final_data)

        st.caption('Generating the Prediction File, Please wait')
        progress_bar(0.01)
        st.download_button( "Press to Download",target_file, "file.csv", "text/csv", key='download-csv')


if __name__ == '__main__':
    main()
