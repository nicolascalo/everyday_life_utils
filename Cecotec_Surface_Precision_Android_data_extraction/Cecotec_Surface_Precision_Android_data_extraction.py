# Cecotec Surface Precision Android data extraction

# Script for a Windows device
# This script needs Tesseract 64-bit and Ghostscript 64-bit for Windows to be installed on the computer


# Library loading


import os
from pypdf import PdfReader
import pandas as pd 
import plotnine as p9
import numpy as np
import shutil

# Setting the working directory to the script location 



# Raw data jpg conversion to pdf with OCR

if os.path.isdir('./data_conv_to_pdf') == False:
    os.makedirs('./data_conv_to_pdf')



for image in os.listdir('./data_to_process_jpg'):
    if image.endswith('.jpg'):
        pdf_filename = image.replace('.jpg', '.pdf')
        
        command = f'ocrmypdf ./data_to_process_jpg/{image} ./data_conv_to_pdf/{pdf_filename} --image-dpi 96' # Export from the Surface Precision app is 96 DPI 
        print(f'Converting {image} to {pdf_filename}...')
        os.system(command)
        print(f'Converted {image} to {pdf_filename}\n')



# Data extraction from the resulting pdf files



df_all = pd.DataFrame()  # Initialize an empty DataFrame to store all data

for pdf_file in os.listdir('./data_conv_to_pdf'):
    if pdf_file.endswith('.pdf'):


        pdf= f'./data_conv_to_pdf/{pdf_file}'
        print(f"Processing file: {pdf}")
        reader = PdfReader(pdf)
        page = reader.pages[0]
        text = page.extract_text()
        if not text:
            print(f"No text found in {pdf}. Skipping.")
            continue    

        user = text.split('\n')[0]  # First line is the username
        
        
        print(f"Username: {user}")

        time = text.split('\n')[1].split(sep = ' ')[0]  # Second line is the time/date
        print(f"Time: {time}")

        date  = text.split('\n')[1].split(sep = ' ')[1] 
        print(f"Date: {date}")

        yearmonthday  = date.strip().split('/')
        yearmonthday = f"{yearmonthday[2]}-{yearmonthday[1]}-{yearmonthday[0]}"  # Convert date to 'Year-Month-Day' format
        yearmonthday = yearmonthday.replace(' ', '')  # Remove any spaces in the date string

        print(f"Year-Month-Day: {yearmonthday}")

        df =  pd.DataFrame(text.split('\n')[2:14]) # Create a DataFrame from the text, skipping the first two lines
        df.columns = ['Data']  # Set the column name for the DataFrame
        df.reset_index(drop=True, inplace=True)  # Reset index to have a clean DataFrame
        df['Param'] = df['Data'].str.replace('\\d.*\\d'," ", regex = True).str.replace('\\s+\\S*$',"", regex=True) # Split the 'Data' column to get parameters


        df['Valeur']   = df['Data'].str.extract(r'(\d.*\d)')  # Extract the values from the 'Data' column
        df['Valeur'] = df['Valeur'].str.strip().str.replace(",",".")  # Remove leading/trailing whitespace from 'Valeur'
        df['Param'] = df['Param'].str.strip()  # Remove leading/trailing whitespace
        df['Param'] = df['Param'].str.replace(".","").str.replace(" =","").str.replace(" )","").str.replace(" +"," ", regex=True).str.strip() # Clean up the 'Param' column
        df.drop(columns=['Data'], inplace=True)  # Drop the original 'Data' column
        df['Username'] = user  # Add the username to the DataFrame
        df['Time'] = time  # Add the time to the DataFrame
        df['Date'] = date  # Add the date to the DataFrame
        df['Year-Month-Day'] = yearmonthday  # Add the formatted date to the DataFrame

        
        df_all = pd.concat([df_all, df], ignore_index=True) # Append the current DataFrame to the main DataFrame
        
        # Divide by 10 if IMC > 100

        mask = (df_all['Param'] == 'IMC') & (pd.to_numeric(df_all['Valeur'], errors='coerce') > 100)
        df_all.loc[mask, 'Valeur'] = pd.to_numeric(df_all.loc[mask, 'Valeur'], errors='coerce') / 10

        df_all['Valeur'] = df_all['Valeur'].astype(float)  # Convert 'Valeur' to float for plotting


        # Pivot the table to a wide format
        
        df_all_pivot = df_all.pivot_table(index=['Username', 'Year-Month-Day','Date', 'Time'], columns='Param', values='Valeur', aggfunc='first').sort_values(by=['Username', 'Date', 'Time'])
        df_all_pivot.columns.name = None  # Remove the name of the columns index
        df_all_pivot.reset_index(inplace=True)  # Reset the index of the pivoted DataFrame
        
        
        
        
        
        
        # Sorting of files into folders
        # pdf files
        
        src = pdf

        dest_folder = f'./processed_data/{user}/raw_data_renamed'
        dest_file = f'{user}_{yearmonthday.replace("/","_")}_{time.replace(":","_")}.pdf'
        dest = f'{dest_folder}/{dest_file}'


        if os.path.isdir(dest_folder) == False:
            os.makedirs(dest_folder)
        

            
        os.replace(src, dest)

        # jpg files
        
        src = pdf.replace("data_conv_to_pdf","data_to_process_jpg").replace("pdf","jpg")

    
        dest_folder = f'./processed_data/{user}/raw_data_og'
        dest = src.replace("data_to_process_jpg",f"processed_data/{user}/raw_data_og")

        if os.path.isdir(dest_folder) == False:
            os.makedirs(dest_folder)
                

            
        shutil.copy(src,dest)
        
        
        dest_folder = f'./processed_data/{user}/raw_data_renamed'
        dest_file = f'{user}_{yearmonthday}_{time.replace(":","_")}.jpg'
        dest = f'{dest_folder}/{dest_file}'
        

        os.replace(src, dest)
        
        
        
        
        
            
        print(f"Data from {pdf} processed and added to the DataFrame.\n")



# Save the combined DataFrame to a CSV file for each user


for user in list(df_all_pivot['Username'].unique()): 

    df_user = df_all_pivot[df_all_pivot['Username'] == user]
    
    dest_folder = f'./processed_data/{user}/results'
    dest_file = f'{user}_Cecotec_data.csv'
    dest =  f'{dest_folder}/{dest_file}'
    
    if os.path.isdir(dest_folder) == False:
        os.makedirs(dest_folder)
    
    if os.path.isfile(dest):

        df_previous = pd.read_csv(dest).sort_values(["Year-Month-Day","Time"]).drop_duplicates(ignore_index=True)
        df_user = df_user.sort_values(["Year-Month-Day","Time"]).drop_duplicates(ignore_index=True)
        
        df_user_all = pd.concat([df_previous, df_user]).reset_index().sort_values(["Year-Month-Day","Time"]).drop_duplicates(subset=['Username','Year-Month-Day','Time']) # Append the current DataFrame to the main DataFrame        
        
        os.remove(dest)
        
        
        df_user = df_user_all.to_csv(dest, index=False)
        
    
    
    df_user.drop_duplicates().to_csv(dest, index=False)

    
    
    
    print("All data has been processed and saved.\n")  



# Data vizualisation


    print("Starting graphing of the data.")  
    
    
    
    data_plot = pd.melt(df_user, id_vars=['Username', 'Year-Month-Day','Date', 'Time'], var_name = "Param", value_name = "Valeur") # df to long format
    data_plot = data_plot[data_plot['Param'].isin(['Poids kg','IMC'])]   # Filter the DataFrame for 'Poids kg' parameter



    dest_folder = f'./processed_data/{user}/results'
    dest_file = f'{user}_bodyweight_IMC.png'
    dest =  f'{dest_folder}/{dest_file}'
    
    if os.path.isdir(dest_folder) == False:
        os.makedirs(dest_folder)



    plot_bweight_IMC = p9.ggplot(data = data_plot, mapping = p9.aes(x='Year-Month-Day', y='Valeur', color = "Param")) + \
        p9.geom_point() + \
        p9.geom_line(group = 1) + \
        p9.ggtitle('IMC / Weight Over Time', subtitle=user) + \
        p9.xlab('Date') + \
        p9.ylab('IMC / Weight (kg)') + \
        p9.scale_x_datetime() + \
        p9.theme(axis_text_x=p9.element_text(rotation=45, hjust=1)) + \
        p9.facet_wrap('Param', scales='free_y')  # Create separate plots for each parameter

    plot_bweight_IMC.save(filename = dest, width=16, height=9,units="in")





    data_plot = df_all[df_all['Param'].isin(['TGC %', 'TMS %'])].copy()  # Filter for TGC % and TMS %
    data_plot['Valeur'] = data_plot['Valeur'].astype(float)  # Convert 'Valeur' to float for plotting



    plot_bodycomp = p9.ggplot(data = data_plot, mapping = p9.aes(x='Year-Month-Day', y='Valeur', color = "Param")) + \
        p9.geom_point() + \
        p9.geom_line(p9.aes(group='Param')) + \
        p9.ggtitle('Body Composition Over Time', subtitle=user) + \
        p9.xlab('Date') + \
        p9.ylab('%') + \
        p9.scale_x_datetime() + \
        p9.theme(axis_text_x=p9.element_text(rotation=45, hjust=1))


    dest_file = f'{user}_bodycomp.png'
    dest =  f'{dest_folder}/{dest_file}'
    plot_bodycomp.save(filename = dest, width=16, height=9,units="in")


    plot_IMC = p9.ggplot(data = df_all_pivot, mapping = p9.aes(x='Year-Month-Day', y='IMC')) + \
        p9.geom_point() + \
        p9.geom_line(group = 1) + \
        p9.ggtitle('IMC Over Time', subtitle=user) + \
        p9.xlab('Date') + \
        p9.ylab('IMC') + \
        p9.scale_x_datetime() + \
        p9.theme(axis_text_x=p9.element_text(rotation=45, hjust=1))

    dest_file = f'{user}_IMC.png'
    dest =  f'{dest_folder}/{dest_file}'
    plot_IMC.save(filename = dest, width=16, height=9,units="in")
    
    print("Graphing of the data done.")  
    

