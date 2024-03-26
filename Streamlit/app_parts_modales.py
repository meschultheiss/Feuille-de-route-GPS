from function_parts_modales import *

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

KT = st.sidebar.selectbox('Sélectionner le canton pour échantillonnage', ['GE', 'VD', 'Tous'])
weight = st.sidebar.selectbox('Sélectionner la pondération', ['wgt_cant_trim_gps','wgt_agg_trim_gps', 'Aucun'])
mode_aggreg = st.sidebar.selectbox("Sélectionner le niveau d'aggrégation des modes", 
                                   ["Motiontag", "MRMT", "Niveau 1", "Niveau 2"])

visitors = st.sidebar.checkbox('Inclure les visiteurs', value=False)
airplane = st.sidebar.checkbox('Inclure les étapes en avion', value=False)
activity = st.sidebar.checkbox('Inclure les jours actifs mais sans déplacement', value=True)
incl_signal_loss = st.sidebar.checkbox('Inclure les étapes avec une perte de signal importante', value=True)

if activity:
    period_of_tracking = 'active_days_count'
else:
    period_of_tracking = 'days_with_track'
#time_of_day = st.sidebar.slider("Heures d'observation:", value=(0, 23))

# Aperçu de la base legs_nogeometries
st.write(legs_nogeometry.sample(4))

# Bouton pour calculer les parts modales
if st.sidebar.button('Calculer les parts modales'):
    # Calculer les parts modales
    # Applying conditions and filtering data to get daily modal distances
    dmd_w = calculate_dmd(legs_nogeometry, usr_stats, KT, weight, 
              period_of_tracking, visitors, airplane,incl_signal_loss)
    dmd_w = dmd_aggreg_modes(dmd_w, level=mode_aggreg)


    # Calcul des parts modales
    mean_modal_share = dmd_w.mean()
    modal_share = pd.DataFrame(dmd_w.sum()).astype(int).rename(columns={0:'Distance_cumulée_metre'})

    # Afficher les parts modales
    st.write('### Distances moyennes journalières par répondant·es')
    st.write(dmd_w)
    st.write('### Parts modales kilométriques')
    st.write(modal_share.T)

    # Plot des graphiques
    st.bar_chart(modal_share.reset_index(), x="index", y='Distance_cumulée_metre', color=["#FF0000"])  # Optional

    st.download_button(
        label="Télécharger les données",
        data=modal_share.to_csv(),
        file_name='distances_cum.csv',
        mime='text/csv',
    )
