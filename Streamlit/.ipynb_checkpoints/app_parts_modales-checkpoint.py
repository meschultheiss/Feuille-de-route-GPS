import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import time

# Charger vos datasets
@st.cache_data
def load_data():
    # Charger vos datasets ici
    legs_nogeometry = pd.read_pickle('data/legs_nogeometry.pkl')
    usr_stats = pd.read_pickle('data/gps_user_statistics.pkl')
    return legs_nogeometry, usr_stats

# Fonction pour calculer les distances par user et mode

#Compute daily modal distances
def get_daily_modal_distances(df):
    
    # Create a copy of the DataFrame to avoid modifying the original
    df = df.copy()
    
    df['length'] = df['length'].astype(float)
    # Group by 'user_id_day', 'previous_mode', and 'previous_leg_id', then sum the distances
    grouped = df.groupby(['user_id_fors', 'user_id_day', 'mode'])['length'].sum().reset_index()

    # Pivot the table to have modes as columns
    pivoted = grouped.pivot_table(
        index=['user_id_fors', 'user_id_day'],
        columns='mode',
        values='length',
        aggfunc='sum'
    ).reset_index()

    # Resample to include missing days and fill NaNs with different values in different columns
    pivoted['date'] = pd.to_datetime(pivoted['user_id_day'].str[-8:])
    # Create a date range covering the entire date range for each ID
    date_ranges = pivoted.groupby('user_id_fors')['date'].agg(['min', 'max']).reset_index()
    date_ranges['legs_date'] = date_ranges.apply(lambda row: pd.date_range(row['min'], row['max'], freq='D'), axis=1)

    # Create a Cartesian product of IDs and date ranges
    cartesian = date_ranges.explode('legs_date').reset_index(drop=True)

    # Complete the original df with a continuous timeline
    pivoted_filled = pd.merge(pivoted, cartesian[['user_id_fors', 'legs_date']], how='outer', left_on=['user_id_fors', 'date'],
                              right_on=['user_id_fors', 'legs_date'])

    # Create 'days_without_track' column and mark as True for added rows, False otherwise
    pivoted_filled['days_without_track'] = pivoted_filled['date'].isnull().astype(int)
    del pivoted_filled['date']

    # Fill missing values in the user_id_day column
    pivoted_filled['user_id_day'] = pivoted_filled.apply(
        lambda row: row['user_id_day'] if not pd.isnull(row['user_id_day'])
        else row['user_id_fors'] + "_" +
             row['legs_date'].strftime('%Y%m%d'),
        axis=1
    )

    # Fill missing values in the modes columns
    # Get the columns that start with 'Mode::'
    modes_columns = [col for col in pivoted_filled.columns if col.startswith('Mode::')]

    # Fill missing values in the 'modes_columns' with 0
    pivoted_filled[modes_columns] = pivoted_filled[modes_columns].fillna(0)

    # Sort the resulting DataFrame
    pivoted_filled.sort_values(by=['user_id_fors', 'legs_date'], inplace=True)

    return pivoted_filled


#Compute daily modal distances
def calculate_dmd(legs_nogeometry, usr_stats, KT, weight, period_of_tracking, visitors):
    # Creating a dictionary mapping user IDs to their corresponding weight values
    # If weight is 'Aucun', map each user ID to the value 1
    if weight == 'Aucun':
        weight_mapping = usr_stats.set_index('user_id_fors').apply(lambda x: 1, axis=1).to_dict()
    else:
        weight_mapping = usr_stats.set_index('user_id_fors')[weight].to_dict()
    
    # Creating a dictionary mapping user IDs to their corresponding period of tracking values
    active_days_mapping = usr_stats.set_index('user_id_fors')[period_of_tracking].to_dict()
    
    # Setting the condition based on the value of KT
    # If KT is not 'Tous', filter data based on the condition KT_home_survey == KT
    # If KT is 'Tous', include all data (no filtering based on KT)
    if KT != 'Tous':
        KT_condition = (legs_nogeometry.KT_home_survey == KT)
    else:
        KT_condition = True

    if visitors == True:
        visit_condition = (legs_nogeometry.activity_in_KT == KT)
        dmd = get_daily_modal_distances(legs_nogeometry.loc[KT_condition | visit_condition])
    else:
        dmd = get_daily_modal_distances(legs_nogeometry.loc[KT_condition])
    
    # Filtering columns that start with 'Mode::' for further calculations
    mode_columns = dmd.filter(like='Mode::')
    
    # Calculating the sum for each 'Mode::' column for each user_id
    sum_mode_per_user = mode_columns.groupby(dmd['user_id_fors']).apply(lambda x: x.sum())
    
    # Weighting the sum of each 'Mode::' column based on user weights and active days
    sum_mode_per_user_w = sum_mode_per_user.mul(sum_mode_per_user.index.map(weight_mapping), axis=0).div(sum_mode_per_user.index.map(active_days_mapping), axis=0).dropna()

    return sum_mode_per_user_w.astype(int)


# Fonction pour ploter l'histogramme et le pie chart
def plot_charts(modal_share):
    # Plot du pie chart avec des couleurs distinctes et une légende
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0','#ffb3e6','#ff6666']
    fig_pie, ax_pie = plt.subplots()
    ax_pie.pie(modal_share, labels=modal_share.index, colors=colors, autopct='%1.1f%%', startangle=90)
    ax_pie.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax_pie.set_title('Parts Modales')

    # Ajouter une légende
    ax_pie.legend(loc='upper right', labels=modal_share.index)
    
    return fig_pie

# Titre de l'application
st.title('Module 1 : Parts Modales du Panel Lémanique')

# Introduction
st.write("""
Parts modales kilométriques par mode pour les résidents et visiteurs de chaque canton en vue du calcul des émissions carbone.
""")

# Charger les données
legs_nogeometry, usr_stats = load_data()

# Sidebar pour les paramètres
st.sidebar.title('Paramètres')

KT = st.sidebar.selectbox('Sélectionner le canton', ['GE', 'VD', 'Tous'])
weight = st.sidebar.selectbox('Sélectionner la pondération', ['wgt_agg_trim_gps', 'wgt_cant_gps', 'wgt_agg_gps', 'wgt_cant_trim_gps', 'Aucun'])
mode_aggreg = st.sidebar.selectbox("Sélectionner l'aggrégation des modes", ["Détail Motiontag", "MRMT"])

visitors = st.sidebar.checkbox('Inclure les visiteurs')
activity = st.sidebar.checkbox('Inclure les jours actifs mais sans déplacement',
                              value=True)
if activity:
    period_of_tracking = 'active_days_count'
else:
    period_of_tracking = 'days_with_track'
#time_of_day = st.sidebar.slider("Heures d'observation:", value=(0, 23))

# Bouton pour calculer les parts modales
if st.sidebar.button('Calculer les parts modales'):
    # Calculer les parts modales
    # Applying conditions and filtering data to get daily modal distances
    dmd_w = calculate_dmd(legs_nogeometry, usr_stats, KT, weight, 
              period_of_tracking, visitors)

    # Calcul des parts modales
    mean_modal_share = dmd_w.mean()
    modal_share = pd.DataFrame(dmd_w.sum()).astype(int)

    # Afficher les parts modales
    st.write('### Distances moyennes journalières par répondant·es')
    st.write(dmd_w)
    st.write('### Parts modales kilométriques')
    st.write(modal_share.rename(columns={0:'Distance_cumulée_metre'}).T)

    # Plot des graphiques
    st.write('### Graphiques')
    fig_pie = plot_charts(mean_modal_share)
    
    st.pyplot(fig_pie)
