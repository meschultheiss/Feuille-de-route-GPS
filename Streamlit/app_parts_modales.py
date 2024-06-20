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
st.write("_Dernière mise à jour : 19 juin 2024_")
st.write("""Dans le cadre de l’enquête du Panel Lémanique, un suivi gps a été réalisé du 24 avril au 5 juin 2023 auprès de 2806 personnes résidentes de la zone d’étude. 
         Ces données ont été collectées par MotionTag, puis livrées (base brute) sous la forme de géodonnées de deux types : legs et staypoints. 
         Les géodonnées de type legs se rapprochent de l’étape1 de déplacement, tel que renseigné dans le mrmt. 
         Les staypoints se rapprochent des “activités” ou transbordements.
         En suivant la feuille de route établie en concertation avec les partenaires du projet _Panel Lémanique_, **nous présentons ci-dessous les résultats du Module 1 : Parts modales**.
         """)

# Introduction
with st.container(border=1):
    col1, col2 = st.columns([5,1])
    # col1.write("Vous trouverez :")
    col1.write("""
        🌱 Parts modales kilométriques pondérées par mode pour les résident·es 
               
        🌱 Inclure les visiteurs non-résident·es 
               
        🌱 Recodage des modes selon MRMT (et niveaux d'aggrégation supplémentaires)
            
        🌱 Rééchantillonnage des jours d’observation et jours non-déplacés / non-detectés
             
        🌱 Intégrer les filtres de perte de signal
             
        🌱 Sous-échantillonnage des résidents et visiteurs par canton (basé sur le questionnaire)
             
        🌱 Données d'équipement : véhicule principal des répondant·es 
            
        🌱 Statistiques GPS des répondant·es
    """)

# Charger les données
legs_nogeometry = load_data_legs()
usr_stats = load_data_usrstat()

# Sidebar
# Logo
st.sidebar.markdown(style_logo, unsafe_allow_html=True)
st.sidebar.markdown("![](https://assets.super.so/15749c3c-d748-4e49-bff7-6fc9ec745dc4/images/adbffa1b-9e3c-49f8-9b4e-605d29073f81/IMAGEFichier_102.svg)", unsafe_allow_html=True)
# Title
st.sidebar.title('Module 1 · _parts modales_')

# User Interface for user inputs
mode_col = st.sidebar.selectbox("**Sélectionner la colonne des modes de transport (détecté ou confirmé)**", ['detected_mode', 'mode'], index=1)
KT = st.sidebar.selectbox('**Sélectionner le canton pour échantillonnage**', ['GE', 'VD', 'Tous'])
weight = st.sidebar.selectbox('**Sélectionner la pondération**', ['wgt_cant_trim_gps', 'Aucun'])
period_of_tracking = st.sidebar.selectbox("**Sélectionner la période d'observation à considérer**", ['active_days_count', 'days_with_track','days_in_range'], index=2)
mode_aggreg = st.sidebar.selectbox("**Sélectionner le niveau d'aggrégation des modes**", ["Motiontag", "MRMT", "Niveau 1", "Niveau 2"])

bad_users = st.sidebar.checkbox('Inclure les utilisateurs avec mauvais signal récurrent', value=False)
visitors = st.sidebar.checkbox('Inclure les visiteurs', value=False)
airplane = st.sidebar.checkbox('Inclure les étapes en avion', value=False)
incl_signal_loss = st.sidebar.selectbox('Exclure les étapes avec une perte de signal importante (non-recommandé)', ['Non', "0.05 de perte", "0.07 de perte"], index=0)
outliers = st.sidebar.selectbox('**Exclure les distances extrêmes**', ['Quantile95', 'Quantile98', 'Quantile99', 'Aucune'], index=2)



# Footer
st.markdown(footer, unsafe_allow_html=True)

st.write('#### Aperçu des données')
# Aperçu de la base legs_nogeometries
st.markdown("""Le **fichier étape** (ou _legs_) avec les variables nécessaires au calcul des distances par mode et par répondant·es.
   Plusieurs variables ont été ajoutées au fichier de base.
""")
                    
with st.container():
    col1, col2 = st.columns([5, 2])
    
    with col1:
        with st.expander("**Fichier étapes** : description des variables"):
            st.markdown("""
                - **leg_id** : Identifiant de l'étape (segment de trajet).
                - **user_id_day** : Identifiant personne-jour.
                - **user_id_fors** : Identifiant de l'utilisateur dans le système FORS.
                - **type** : Type de l'étape (segment de trajet).
                - **geometry** : Géométrie de l'étape (segment de trajet).
                - **legs_date** : Date des étapes (segments de trajet).
                - **started_at** : Heure de début de l'étape (segment de trajet).
                - **started_at_timezone** : Fuseau horaire de début de l'étape.
                - **finished_at** : Heure de fin de l'étape (segment de trajet).
                - **finished_at_timezone** : Fuseau horaire de fin de l'étape.
                - **length_leg** : Longueur de l'étape (segment de trajet).
                - **detected_mode** : Mode de déplacement détecté.
                - **mode** : Mode de déplacement.
                - **purpose** : But de l'étape (segment de trajet).
                - **confirmed_at** : Heure de confirmation de l'étape.
                - **started_on** : Date de début de l'étape.
                - **misdetected_completely** : Détection complètement erronée.
                - **merged** : Fusionné avec d'autres étapes.
                - **created_at** : Date de création de l'étape.
                - **updated_at** : Date de mise à jour de l'étape.
                - **started_at_in_timezone** : Heure de début dans le fuseau horaire spécifié.
                - **finished_at_in_timezone** : Heure de fin dans le fuseau horaire spécifié.
                - **confirmed_at_in_timezone** : Heure de confirmation dans le fuseau horaire spécifié.
                - **created_at_in_timezone** : Date de création dans le fuseau horaire spécifié.
                - **updated_at_in_timezone** : Date de mise à jour dans le fuseau horaire spécifié.
                - **point_per_linestring** : Points par ligne de la géométrie.
                - **max_signlalloss_meters** : Perte maximale de signal en mètres.
                - **length_leg** : Longueur de l'étape (segment de trajet).
                - **rel_max_signalloss** : Perte de signal relative maximale.
                - **low_quality_legs_1** : Filtre spatial (perte à 5%) - Qualité faible.
                - **low_quality_legs_2** : Filtre spatial (perte à 7%) - Qualité faible.
                - **usr_w_constant_bad_signal** : Utilisateur avec un signal GPS constamment mauvais.
                - **leading_stay_id** : Identifiant de l'activité à destination.
                - **duration** : Durée de l'étape (segment de trajet).
                - **activity_in_KT** : Canton de l'activité à destination.
                - **panel_area** : _True_ si l'activité à destination se passe dans le périmètre du panel.
                - **KT_home_survey** : Canton de résidence de la personne.
            """)

        st.dataframe(legs_nogeometry.head(4))
    
    # with col2:
    #     col2.download_button(
    #         label="Télécharger les étapes",
    #         data=legs_nogeometry.to_csv(),
    #         file_name='legs_nogeometry.zip'
    #     )

# Aperçu de la base user_stats
st.markdown("""
    Le **fichier _user statistics_** a été généré pour pouvoir calculer les distances moyennes. 
    Il recense plusieurs informations importantes sur le suivi GPS des répondant·es.
 """)
with st.container():
    col1, col2 = st.columns([5, 2])

    with col1:
        with st.expander("**Fichier user statistics** : description des variables"):
            st.markdown("""
                - **user_id_fors** : Identifiant de l'utilisateur dans le système FORS.
                - **KT_home_survey** : Canton de résidence de l'utilisateur selon l'enquête.
                - **KT_home_gps** : Canton de résidence de l'utilisateur basé sur les données GPS.
                - **first_activity_date** : Date de la première activité enregistrée.
                - **last_activity_date** : Date de la dernière activité enregistrée.
                - **days_in_range** : Nombre total de jours dans la plage temporelle étudiée.
                - **active_days_count** : Nombre de jours où l'utilisateur a eu au moins une activité / étape enregistrée.
                - **days_without_event** : Nombre de jours sans aucune détection enregistrée.
                - **days_with_track** : Nombre de jours avec au moins une étape disponible.
                - **days_without_track** : Nombre de jours sans aucune étape détectée.
                - **ID_municipality_survey** : Identifiant de la municipalité selon l'enquête.
                - **ID_Agglo_survey** : Identifiant de l'agglomération selon l'enquête.
                - **N_Agglo_survey** : Nombre d'agglomérations identifiées dans l'enquête.
                - **gdr** : Genre de l'utilisateur (sexe).
                - **prof** : Profession de l'utilisateur.
                - **age_fr** : Âge de l'utilisateur en années.
                - **wgt_cant_gps** : Poids appliqué aux données GPS du canton.
                - **wgt_agg_gps** : Poids appliqué aux données GPS de l'agglomération.
                - **wgt_cant_trim_gps** : Poids appliqué aux données GPS du canton après ajustement.
                - **wgt_agg_trim_gps** : Poids appliqué aux données GPS de l'agglomération après ajustement.
                - **main_motor** : Principal moyen de transport de l'utilisateur.
                - **car_in_HH_count** : Nombre de voitures dans le ménage de l'utilisateur.
                - **home_geometry_from_gps** : Géométrie de la résidence de l'utilisateur basée sur les données GPS (EPSG:4326).
                - **home_geometry_from_survey** : Géométrie de la résidence de l'utilisateur basée sur l'enquête (EPSG:4326).
                - **distance_home_gps_survey_m** : Distance entre la résidence de l'utilisateur selon les données GPS et l'enquête (en mètres).
            """)   
        st.dataframe(usr_stats.sample(4))

#     with col2:
#         st.download_button(
#             label="Télécharger les statistiques utilisateur·ices",
#             data=usr_stats.to_csv(),
#             file_name='usr_stats.csv',
#             mime='text/csv',
#         )

st.markdown("""
    ### Les points clés sont les suivants :
    - Un rééchantillonnage temporel a permis de s'assurer de la continuité temporelle de la base et de compter les jours non-actifs entre le début et la fin du suivi et les jours sans déplacement. Il apparaît que 966 / 675 / 295 répondant·es ont au moins 3 / 5 / 10 jours non-détectés.
    - La détermination du Canton de domicile n'est pas évidente. La question 14 du questionnaire vague 1 permet d'obtenir une adresse déclarée, mais une centaine de répondant·es (parmi la base GPS) n'ont pas renseigné ce champ. L'alternative est de déterminer les lieux de domicile sur la base du GPS. Avec cette approche, 266 personnes (env. 10%) n'ont pas le même canton de résidence entre le déclaratif (questionnaire) et l'observé (GPS).
    - Nous pouvons déterminer les distances parcourues moyennes journalières par répondant·es en tenant compte des visiteurs, des étapes en avion, des jours actifs sans déplacement et des pertes de signal.
""")


st.write('#### Distances moyennes journalières par répondant·es')
st.write("👈 Aide: réglez les paramètres à gauche et lancez les calculs !")



# Bouton pour calculer les parts modales

if st.sidebar.button('Calculer les parts modales'):
    # Barre de progrès
    progress_text = "Calculs en cours"
    my_bar = st.progress(0, text=progress_text)

    for percent_complete in range(100):
        time.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    # Calculer les parts modales
    # Applying conditions and filtering data to get daily modal distances
    dmd_w = calculate_dmd(legs_nogeometry, usr_stats, KT, weight, period_of_tracking, bad_users, visitors, airplane, incl_signal_loss, outliers, mode_col)
    dmd_w = dmd_aggreg_modes(dmd_w, level=mode_aggreg)

    # Calcul des parts modales
    mean_modal_share = dmd_w.mean()
    modal_share = pd.DataFrame(dmd_w.sum()).astype(int).rename(columns={0:"Distances journalières cumulées [mètres]"})

    # Description méthodo
    st.write("**Méthode** : Somme des distances de toutes les étapes (par mode et usager) divisé par la période d'observation sélectionnée. La pondération pour redressement est appliquée selon les paramètres sélectionnés.") 

    # Afficher les parts modales
    with st.container():
        col1, col2 = st.columns([5, 2])
        with col1:
            st.write(dmd_w)
        with col2:
            st.download_button(
                label="Télécharger les distances moyennes journalières",
                data=dmd_w.to_csv(),
                file_name='distances_jour_user_pond.csv',
                mime='text/csv',
            )
            st.write(f"Nombre d'utilisateur conservés dans le calcul : {len(dmd_w)}")
    st.write('### Parts modales kilométriques (base étape)')
     # Description méthodo
    st.write("**Méthode** : Distances moyennes journalières cumulées (somme des colonnes du tableau ci-dessus).") 

    st.write(modal_share.T)
    
    with st.container():
        col1, col2 = st.columns([2, 5])
        col1.write("**Parts modales kilométriques** (somme des moyennes pondérées et journalières des distances parcourues par mode)")

        fig = px.pie(modal_share.reset_index(), values="Distances journalières cumulées [mètres]", names='index', hole=.3, color_discrete_sequence=px.colors.sequential.Blugrn)
        col2.plotly_chart(fig, theme="streamlit")

    # Analyze the signal loss
        # Plot des graphiques
    if incl_signal_loss == 'Non':
        legs_nogeometry_lql = legs_nogeometry[legs_nogeometry.low_quality_legs_1 == 1].copy().reset_index(drop=True)

        dmd_w_lql = calculate_dmd(legs_nogeometry_lql, usr_stats, KT, weight, period_of_tracking, bad_users, visitors, airplane, incl_signal_loss, outliers, mode_col)
        dmd_w_lql = dmd_aggreg_modes(dmd_w_lql, level=mode_aggreg)
        
        with st.container():
            col1, col2 = st.columns([2, 5])
            with col1:
                st.write("""
                       **Distribution des pertes de signal** 
                       (Pourcentage des distances potentiellement affecté par mode)
                       """)

            with col2:
                st.bar_chart((dmd_w_lql / dmd_w).fillna(0).mean(), color=["#dfab9a"])  # Optional

    my_bar.empty()

st.sidebar.write("#")
st.sidebar.divider()
# Adding the footnote using Markdown with CSS
st.sidebar.markdown("""
<span style="font-size: small;">
                    *wgt_cant_trim_gps : redressement au canton <br>
                    *wgt_agg_trim_gps : redressement à l'agglomération <br>
                    **Les jours actifs sont les jours avec au moins une activité ou étape detectée. *Days in range* intègre les jours non-detectés (non recommandé).
                    </span>
""", unsafe_allow_html=True)