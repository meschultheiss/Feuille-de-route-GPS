from function_parts_modales import *
from style_parts_modales import *
st.set_page_config(
    page_title="Panel Lémanique",
    layout="wide",
    initial_sidebar_state="expanded",
)
if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Titre de l'application
st.write('## Panel Lémanique · _Tracking GPS_')

# banner
st.write("_Dernière mise à jour : 27 mars 2024_")

# Introduction
with st.container(border=1):
    col1, col2 = st.columns([5,1])
    # col1.write("Vous trouverez :")
    col1.write("""
        🌱 Parts modales kilométriques pondérées par mode pour les résident·es 
               
        🌱 Inclure les visiteurs non-résident·es 
               
        🌱 Recodage des modes selon MRMT (et niveaux d'aggrégation supplémentaires)
            
        🌱 Rééchantillonnage des jours d’observation et jours non-déplacés / non-detectés
             
        🌱 Sous-échantillonnage des résidents et visiteurs par canton (basé sur le questionnaire)
             
        🌱 Données d'équipement : véhicule principal des répondant·es 
            
        🌱 Statistiques GPS des répondant·es
    """)

# Footer
st.markdown(footer, unsafe_allow_html=True)

# Charger les données
legs_nogeometry, usr_stats = load_data()

st.write('#### Aperçu des données')
# Aperçu de la base legs_nogeometries
st.write("Le fichier étape issu avec les variables nécessaires au calcul des distances par mode et par répondant·es.")
with st.container():
    col1, col2 = st.columns([5, 2])
    col1.dataframe(legs_nogeometry.sample(4))
    
    col2.download_button(
        label="Télécharger les étapes",
        data=legs_nogeometry.to_csv(),
        file_name='legs_nogeometry_encrypted.zip'
        )

# Aperçu de la base user_stats
st.write("Le fichier user_statistics a été généré pour pouvoir calculer les distances moyennes. Notamment le compte des jours non-déplacés et non-détectés y figure, ainsi que les pondérations et bien d'autres variables.")
with st.container():
    col1, col2 = st.columns([5, 2])
    col1.dataframe(usr_stats[['user_id_fors','days_in_range','days_without_track','days_with_track','main_motor','car_in_HH_count']].sample(4))

    col2.download_button(
        label="Télécharger les statistiques utilisateur·ices",
        data=usr_stats.to_csv(),
        file_name='usr_stats.csv',
        mime='text/csv',
        )

st.write('#### Distances moyennes journalières par répondant·es')
st.write("👈 Aide: réglez les paramètres à gauche et lancez les calculs !")

# Logo
# st.sidebar.markdown(style_logo, unsafe_allow_html=True)
# st.sidebar.markdown("![](https://assets.super.so/15749c3c-d748-4e49-bff7-6fc9ec745dc4/images/adbffa1b-9e3c-49f8-9b4e-605d29073f81/IMAGEFichier_102.svg)", unsafe_allow_html=True)
# Title
st.sidebar.title('Module 1 · _parts modales_')

KT = st.sidebar.selectbox('**Sélectionner le canton pour échantillonnage**', ['GE', 'VD', 'Tous'])
weight = st.sidebar.selectbox('**Sélectionner la pondération**', ['wgt_cant_trim_gps','wgt_agg_trim_gps', 'Aucun'])

mode_aggreg = st.sidebar.selectbox("**Sélectionner le niveau d'aggrégation des modes**", 
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
    modal_share = pd.DataFrame(dmd_w.sum()).astype(int).rename(columns={0:"Distances cumulées[mètres]"})

    # Afficher les parts modales
    st.write(dmd_w)
    st.write('### Parts modales kilométriques')
    st.write(modal_share.T)
    
    # @st.cache_data
    with st.container():
        col1, col2 = st.columns([2, 5])
        col1.write("**Parts modales kilométriques** (somme des moyennes pondérées et journalières des distances parcourues par mode)")

        fig = px.pie(modal_share.reset_index(), values="Distances cumulées[mètres]", names='index', hole=.3, color_discrete_sequence=px.colors.sequential.Blugrn)
        col2.plotly_chart(fig, theme="streamlit")

    # Analyze the signal loss
        # Plot des graphiques
    if incl_signal_loss:
        legs_nogeometry_lql = legs_nogeometry[legs_nogeometry.low_quality_legs_1 == 1].copy().reset_index(drop=True)

        dmd_w_lql = calculate_dmd(legs_nogeometry_lql, usr_stats, KT, weight, 
                period_of_tracking, visitors, airplane,incl_signal_loss)
        dmd_w_lql = dmd_aggreg_modes(dmd_w_lql, level=mode_aggreg)
        
        with st.container():
            col1, col2 = st.columns([2, 5])
            col1.write("""
                       **Distribution des pertes de signal** 
                       (Pourcentage des distances potentiellement affecté par mode)
                       """)

            col2.bar_chart((dmd_w_lql / dmd_w).fillna(0).mean(), color=["#dfab9a"])  # Optional


    st.download_button(
        label="Télécharger les données",
        data=modal_share.to_csv(),
        file_name='distances_cum.csv',
        mime='text/csv',
    )
    my_bar.empty()

st.sidebar.write("#")
st.sidebar.divider()
# Adding the footnote using Markdown with CSS
st.sidebar.markdown("""
<span style="font-size: small;">
                    *wgt_cant_trim_gps : redressement au canton <br>
                    *wgt_agg_trim_gps : redressement à l'agglomération
                    </span>
""", unsafe_allow_html=True)