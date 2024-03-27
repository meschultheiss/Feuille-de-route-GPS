from function_parts_modales import *
st.set_page_config(
    page_title="Panel Lémanique",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Titre de l'application
st.write('## Panel Lémanique · _Tracking GPS_')

# Introduction
with st.container(border=2):
    st.write("""
        🌱 Parts modales kilométriques par mode pour les résidents et visiteurs de chaque canton
            
        🌱 Véhicule principal répondant·es 
            
        🌱 Statistiques des répondant·es
    """)

# Charger les données
legs_nogeometry, usr_stats = load_data()

# Aperçu de la base legs_nogeometries
st.dataframe(legs_nogeometry.sample(4))

# Aperçu de la base legs_nogeometries
with st.container():
    col1, col2 = st.columns([5, 2])
    col1.dataframe(usr_stats[['user_id_fors','days_in_range','days_with_track','main_motor','car_in_HH_count']].sample(4))

    col2.download_button(
        label="Télécharger tout le fichier user_statistics",
        data=usr_stats.to_csv(),
        file_name='usr_stats.csv',
        mime='text/csv',
        )

st.write('#### Distances moyennes journalières par répondant·es')
st.write("👈 Aide: réglez les paramètres à gauche et lancez les calculs !")

# Sidebar pour les paramètres
st.sidebar.title('Module 1 · _parts modales_')

KT = st.sidebar.selectbox('Sélectionner le canton pour échantillonnage', ['GE', 'VD', 'Tous'])
weight = st.sidebar.selectbox('Sélectionner la pondération', ['wgt_cant_trim_gps','wgt_agg_trim_gps', 'Aucun'])
mode_aggreg = st.sidebar.selectbox("Sélectionner le niveau d'aggrégation des modes", 
                                   ["Motiontag", "MRMT", "Niveau 1", "Niveau 2"])

visitors = st.sidebar.checkbox('Inclure les visiteurs', value=False)
airplane = st.sidebar.checkbox('Inclure les étapes en avion', value=False)
activity = st.sidebar.checkbox('Inclure les jours actifs mais sans déplacement (recommandé)', value=True)
incl_signal_loss = st.sidebar.checkbox('Inclure les étapes avec une perte de signal importante (recommandé)', value=True)

if activity:
    period_of_tracking = 'active_days_count'
else:
    period_of_tracking = 'days_with_track'
#time_of_day = st.sidebar.slider("Heures d'observation:", value=(0, 23))

# Bouton pour calculer les parts modales
if st.sidebar.button('Calculer les parts modales'):
    # Barre de progrès
    progress_text = "Calculs en cours"
    my_bar = st.progress(0, text=progress_text)

    for percent_complete in range(100):
        time.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=progress_text)
    # time.sleep(1)
    # Calculer les parts modales
    # Applying conditions and filtering data to get daily modal distances
    dmd_w = calculate_dmd(legs_nogeometry, usr_stats, KT, weight, 
              period_of_tracking, visitors, airplane,incl_signal_loss)
    dmd_w = dmd_aggreg_modes(dmd_w, level=mode_aggreg)


    # Calcul des parts modales
    mean_modal_share = dmd_w.mean()
    modal_share = pd.DataFrame(dmd_w.sum()).astype(int).rename(columns={0:'Distance_cumulée_metre'})

    # Afficher les parts modales
    st.write(dmd_w)
    st.write('### Parts modales kilométriques')
    st.write(modal_share.T)

    # Plot des graphiques
    st.bar_chart(modal_share.reset_index(), x="index", y='Distance_cumulée_metre', color=["#FF0000"])  # Optional
    
    # @st.cache_data
    fig = px.pie(modal_share.reset_index(), values='Distance_cumulée_metre', names='index', hole=.3, color_discrete_sequence=px.colors.sequential.Blugrn)
    st.plotly_chart(fig, theme="streamlit")


    st.download_button(
        label="Télécharger les données",
        data=modal_share.to_csv(),
        file_name='distances_cum.csv',
        mime='text/csv',
    )
    my_bar.empty()
