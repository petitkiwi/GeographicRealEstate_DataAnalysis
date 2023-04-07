from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import requests

#%% Importation des divers dataframes

#dataframe 2021
df_2021=pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/817204ac-2202-4b4a-98e7-4184d154d98c",sep="|",decimal=',',dtype={"Code departement" : str,"Code commune" : str,"Code postal" : str,'Code type local' : str})
df_2021=df_2021.dropna(axis=1,how="all")
df_2021=df_2021.dropna(axis=0,how="all")
df_2021["Code departement"]=df_2021["Code departement"].apply(str)
df_2021["Valeur fonciere"]=df_2021["Valeur fonciere"].apply(float)
df_2021["Surface terrain"]=df_2021["Surface terrain"].apply(float)

#nom_region
nom_region=pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/70cef74f-70b1-495a-8500-c089229c0254",sep=',',dtype={'code_departement':str})

#communes
nom_commune=pd.DataFrame(df_2021,columns=["Code commune","Commune","Code departement"]).drop_duplicates(subset = "Commune").dropna()
f=lambda x : str(x) if len(x)==3 else "0"*(3-len(x))+str(x)
nom_commune["Code commune"]=nom_commune["Code departement"]+nom_commune["Code commune"].apply(f)


#%% Création de nouvelles tables

def df_m_p_d():
    df=pd.DataFrame(df_2021,columns=["Code departement","Valeur fonciere","Surface terrain","Nature mutation"]).dropna(axis=0)
    df=df[df["Nature mutation"]=="Vente"]
    
    df["Prix m2"]=(df["Valeur fonciere"]/df["Surface terrain"])
    df.replace([np.inf, -np.inf], np.nan, inplace=True) 
      
    df.dropna(inplace=True)

    #Moyenne en fonction des departements
    moyenne_prix_dep=pd.DataFrame(df.groupby("Code departement").mean("Prix m2"))
    
    #ajout des num de départements en colonnes de moyenne
    moyenne_prix_dep=moyenne_prix_dep.merge(nom_region,left_index=True,right_on="code_departement")
    return moyenne_prix_dep

moyenne_prix_dep=df_m_p_d()

def df_2018():
    df_2018=pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/1be77ca5-dc1b-4e50-af2b-0240147e0346",sep="|",decimal=',',dtype={"Code departement" : str,"Code commune" : str,"Code postal" : str,'Code type local' : str})
    #enleve les colonnes où toutes les données valent NaN
    df_2018=df_2018.dropna(axis=1,how="all")
    df_2018=df_2018.dropna(axis=0,how="all")
    return df_2018
df_2018 = df_2018()

nom_type=pd.DataFrame(df_2021,columns=["Code type local","Type local"]).drop_duplicates(subset = "Code type local").dropna()
#%% Fonctions qui tracent les graphes
def carte_prix_dep():
    polygons = requests.get(
        "https://france-geojson.gregoiredavid.fr/repo/departements.geojson"
    ).json()
    
    
    # generate some data for each region defined in geojson...
    df = moyenne_prix_dep
    #Génération de la carte grâce aux données organisées ci-dessus
    fig1 = px.choropleth(
        df,
        geojson=polygons,
        locations="code_departement",
        color="Prix m2",
        color_continuous_scale="Viridis",
        range_color=(0, 30000),
        scope="europe",
        featureidkey='properties.code'
    )
    fig1.update_geos(fitbounds="locations", visible=False)
    fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig1

def bar_prix_dep():
    fig = px.bar(moyenne_prix_dep, x='nom_departement', y='Prix m2',text="Prix m2",labels={"nom_departement": "Departement", "Prix m2": "Prix m² en euros"})
    fig.update_xaxes(type='category')
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    return fig

def prix_m2_region():
    polygons = requests.get(
    "https://france-geojson.gregoiredavid.fr/repo/regions.geojson"
    ).json()
    
    #Calcul des moyennes de Pix au mètres carrés par région
    moyenne_prix_reg=pd.DataFrame(moyenne_prix_dep.groupby("code_region").mean("Prix m2"))
    nom_region2=nom_region.drop_duplicates(subset = "code_region")
    #Rajout de la colonne avec les codes
    moyenne_prix_reg=moyenne_prix_reg.merge(nom_region2,left_index=True,right_on="code_region")
    
    # generate some data for each region defined in geojson...
    df = moyenne_prix_reg
    fig = px.choropleth(
        df,
        geojson=polygons,
        locations="code_region",
        color="Prix m2",
        color_continuous_scale="Viridis",
        range_color=(0, 30000),
        #scope="europe",
        featureidkey='properties.code',
        labels={"code_region":"Code de la région","Prix m2":"Prix moyen m²"}
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    return fig

def nb_pieces_par_commune():
    # Determination nb pièces par commune
    df=pd.DataFrame(df_2021,columns=["Commune", "Code type local", "Nombre pieces principales"]).dropna(axis=0)
    df.dropna(inplace=True) 
    df=df[df["Code type local"].isin(['1', '2'])]
    
    #Moyenne en fonction des departements
    moyenne_piece_commune=pd.DataFrame(df.groupby("Commune").mean("Nombre pieces principales"))

    #ajout des num de départements en colonnes de moyenne
    moyenne_piece_commune=moyenne_piece_commune.merge(nom_commune,left_index=True,right_on="Commune")
    return moyenne_piece_commune

def nb_pieces_par_departement():
    df=pd.DataFrame(df_2021,columns=["Code departement","Code type local", "Nombre pieces principales"]).dropna(axis=0)
    df.dropna(inplace=True)
    
    df=df[df["Code type local"].isin(['1', '2'])]
    
    
    #Moyenne en fonction des departements
    moyenne_pieces_dep=pd.DataFrame(df.groupby("Code departement").mean("Nombre pieces principales"))
    
    #ajout des num de départements en colonnes de moyenne
    moyenne_pieces_dep=moyenne_pieces_dep.merge(nom_region,left_index=True,right_on="code_departement")
    
    polygons1 = requests.get(
        "https://france-geojson.gregoiredavid.fr/repo/departements.geojson"
    ).json()
    
    # generate some data for each region defined in geojson...
    df = moyenne_pieces_dep
    fig = px.choropleth(
        df,
        geojson=polygons1,
        locations="code_departement",
        color="Nombre pieces principales",
        color_continuous_scale="Viridis",
        range_color=(3, 4),
        scope="europe",
        hover_name="nom_departement",
        featureidkey='properties.code'
    )
    fig.update_layout(
        title={
            'text': "Nombre de pièces principales par département",
            'y':0.9,
            'x':0.1,
            'xanchor': 'left',
            'yanchor': 'top'})
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

def nb_pieces_par_region():
    df=pd.DataFrame(df_2021,columns=["Code departement","Code type local", "Nombre pieces principales"]).dropna(axis=0)
    df.dropna(inplace=True)
    
    #Moyenne en fonction des departements
    moyenne_pieces_dep=pd.DataFrame(df.groupby("Code departement").mean("Nombre pieces principales"))
    
    moyenne_pieces_dep=moyenne_pieces_dep.merge(nom_region,left_index=True,right_on="code_departement")
    
    moyenne_pieces_reg=pd.DataFrame(moyenne_pieces_dep.groupby("code_region").mean("Nombre pieces principales"))
    nom_region2=nom_region.drop_duplicates(subset = "code_region")
    moyenne_pieces_reg=moyenne_pieces_reg.merge(nom_region2,left_index=True,right_on="code_region")
    
    polygons1 = requests.get(
        "https://france-geojson.gregoiredavid.fr/repo/regions.geojson"
    ).json()
    
    
    # generate some data for each region defined in geojson...
    df = moyenne_pieces_reg
    fig = px.choropleth(
        df,
        geojson=polygons1,
        locations="code_region",
        color="Nombre pieces principales",
        color_continuous_scale="Viridis",
        range_color=(3, 4),
        scope="europe",
        hover_name="nom_region",
        featureidkey='properties.code',
    )
    fig.update_layout(
        title={
            'text': "Nombre de pièces principales par région",
            'y':0.9,
            'x':0.1,
            'xanchor': 'left',
            'yanchor': 'top'})
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

def nb_pieces_par_type_habitation():
    df=pd.DataFrame(df_2021,columns=["Code type local","Nombre pieces principales",]).dropna(axis=0)
    df.dropna(inplace=True)
    df=df[df["Code type local"].isin(['1', '2'])]

    #Moyenne en fonction des departements
    moyenne_pieces_type=pd.DataFrame(df.groupby("Code type local").mean("Nombre pieces principales"))
    
    nom_type=pd.DataFrame(df_2021,columns=["Code type local","Type local"]).drop_duplicates(subset = "Code type local").dropna()
    
    #ajout des num de départements en colonnes de moyenne
    moyenne_pieces_type=moyenne_pieces_type.merge(nom_type,left_index=True,right_on="Code type local")
    
    fig = px.bar(moyenne_pieces_type, x='Code type local', y='Nombre pieces principales',text="Nombre pieces principales",
                 labels={"Code type local": "Type d'habitation", "Nombre pieces principales": "Nombre moyen pieces principales"}, 
                title = "Nombre de pièces principales en fonction du type d'habitation")
    fig.update_xaxes(type='category')
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    return fig

def prix_m2_nb_pieces_principales():
    df=pd.DataFrame(df_2021,columns=["Nombre pieces principales","Valeur fonciere","Surface terrain"]).dropna(axis=0)
    df["Prix m2"]=(df["Valeur fonciere"]/df["Surface terrain"])
    df.replace([np.inf, -np.inf], np.nan, inplace=True) 
      
    df.dropna(inplace=True)
    
    df=df.groupby("Nombre pieces principales").mean('Prix m2')
    df['Nombre pieces principales'] = df.index
    
    
    fig = px.bar(df, x='Nombre pieces principales', y='Prix m2',text="Prix m2",
                 labels={"Nombre pieces principales": "Nombre de pieces principales", "Prix m2": "Prix au mètre carré"}, 
                title = "Nombre de pièces principales en fonction du prix eu mètre carré")
    fig.update_xaxes(type='category')
    fig.update_traces(texttemplate='%{text:z.2s}', textposition='outside')
    fig.show(renderer = 'colab')
    
    return fig

def surf_moyenne_terrain_commune():
    df=pd.DataFrame(df_2021,columns=["Commune", "Surface terrain"]).dropna(axis=0)
    df.dropna(inplace=True) 
    
    #Moyenne en fonction des departements
    moyenne_surface_commune=pd.DataFrame(df.groupby("Commune").mean("Surface terrain"))
    
    #je ne comprends pas pourquoi on a 22 NaN dans la moyenne alors qu'on n'utilise pas de NaN dans df
    #ajout des num de départements en colonnes de moyenne
    moyenne_surface_commune=moyenne_surface_commune.merge(nom_commune,left_index=True,right_on="Commune")
    return moyenne_surface_commune

def surf_moyenne_terrain_dep():
    # Determination de la surface moyenne des terrains
    df=pd.DataFrame(df_2021,columns=["Code departement","Surface terrain"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df.dropna(inplace=True) 
    
    #Moyenne en fonction des departements
    moyenne_surface_dep=pd.DataFrame(df.groupby("Code departement").mean("Surface terrain"))
    
    #je ne comprends pas pourquoi on a 22 NaN dans la moyenne alors qu'on n'utilise pas de NaN dans df
    #c'etait à cause des valeurs infs
    
    #ajout des num de départements en colonnes de moyenne
    moyenne_surface_dep=moyenne_surface_dep.merge(nom_region,left_index=True,right_on="code_departement")
    return moyenne_surface_dep

def surf_moyenne_terrain_region():
    # Determination de la surface moyenne des terrains
    df=pd.DataFrame(df_2021,columns=["Code departement","Surface terrain"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df.dropna(inplace=True) 
    #Moyenne en fonction des departements
    moyenne_surface_dep=pd.DataFrame(df.groupby("Code departement").mean("Surface terrain"))
    
    moyenne_surface_reg=pd.DataFrame(moyenne_surface_dep.groupby("code_region").mean("Surface terrain"))
    nom_region2=nom_region.drop_duplicates(subset = "code_region")
    moyenne_surface_reg=moyenne_surface_reg.merge(nom_region2,left_index=True,right_on="code_region")
    
    polygons1 = requests.get(
        "https://france-geojson.gregoiredavid.fr/repo/regions.geojson"
    ).json()
    
    
    # generate some data for each region defined in geojson...
    df = moyenne_surface_reg
    fig = px.choropleth(
        df,
        geojson=polygons1,
        locations="code_region",
        color="Surface terrain",
        color_continuous_scale="Viridis",
        range_color=(0, 5000),
        scope="europe",
        hover_name="nom_region",
        featureidkey='properties.code',
    )
    fig.update_layout(
        title={
            'text': "Surface de terrain moyenne par région",
            'y':0.9,
            'x':0.1,
            'xanchor': 'left',
            'yanchor': 'top'})
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    return fig

def vf_commune():
    df=pd.DataFrame(df_2021,columns=["Commune", "Valeur fonciere"]).dropna(axis=0)
    df.dropna(inplace=True) 
    
    #Moyenne en fonction des departements
    moyenne_valeur_commune=pd.DataFrame(df.groupby("Commune").mean("Valeur fonciere"))
    
    #je ne comprends pas pourquoi on a 22 NaN dans la moyenne alors qu'on n'utilise pas de NaN dans df
    #ajout des num de départements en colonnes de moyenne
    moyenne_valeur_commune=moyenne_valeur_commune.merge(nom_commune,left_index=True,right_on="Commune")
    return moyenne_valeur_commune
    
def vf_dep():
    df=pd.DataFrame(df_2021,columns=["Code departement","Valeur fonciere"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df.dropna(inplace=True) 
    
    #Moyenne en fonction des departements
    moyenne_valeur_dep=pd.DataFrame(df.groupby("Code departement").sum("Valeur fonciere"))
    
    #ajout des num de départements en colonnes de moyenne
    moyenne_valeur_dep=moyenne_valeur_dep.merge(nom_region,left_index=True,right_on="code_departement")
    return moyenne_valeur_dep
    
def vf_region():
    df=pd.DataFrame(df_2021,columns=["Code departement","Valeur fonciere"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df.dropna(inplace=True) 
    
    #Moyenne en fonction des departements
    moyenne_valeur_dep=pd.DataFrame(df.groupby("Code departement").sum("Valeur fonciere"))
    moyenne_valeur_reg=pd.DataFrame(moyenne_valeur_dep.groupby("code_region").mean("Valeur fonciere"))
    nom_region2=nom_region.drop_duplicates(subset = "code_region")
    moyenne_valeur_reg=moyenne_valeur_reg.merge(nom_region2,left_index=True,right_on="code_region")
    
    polygons1 = requests.get(
        "https://france-geojson.gregoiredavid.fr/repo/regions.geojson"
    ).json()
    
    
    # generate some data for each region defined in geojson...
    df = moyenne_valeur_reg
    fig = px.choropleth(
        df,
        geojson=polygons1,
        locations="code_region",
        color="Valeur fonciere",
        color_continuous_scale="Viridis",
        range_color=(0, 150000000000),
        scope="europe",
        hover_name="nom_region",
        featureidkey='properties.code',
    )
    fig.update_layout(
        title={
            'text': "Valeur fonciere totale par région",
            'y':0.9,
            'x':0.1,
            'xanchor': 'left',
            'yanchor': 'top'})
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

def type_locaux():
    legend = ['Dépendance','Maison','Appartement','Local industriel. commercial ou assimilé']
    fig = go.Figure(data=[go.Pie(values=df_2021['Type local'].value_counts(),labels=legend, 
                                 title = 'Proportion des différents types de locaux')])
    return fig

def type_voie():
    typedevoie = ['Rue','Avenue','Route','Chemin','Boulevard','Allée','Impasse','Place','Résidence']
    fig = go.Figure(data=[go.Pie(values=df_2021['Type de voie'].value_counts(),labels=typedevoie, 
                             title = 'Proportion des différents types de voies',pull=[0, 0, 0, 0.2])])
    return fig

def type_mutation():
    typedevoie = ['Vente','Vente en l''état futur d''achèvement','Echange','Vente terrain à bâtir ','Adjudication','Expropriation']
    fig = go.Figure(data=[go.Pie(values=df_2021['Nature mutation'].value_counts(),labels=typedevoie, 
                             title = 'Proportion des différents types de mutation')])
    return fig

def nb_mutation_2018():
    df_21=pd.DataFrame(df_2021,columns=["Nature mutation"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df_21.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df_21.dropna(inplace=True) 
    df_21 = pd.DataFrame(df_21['Nature mutation'].value_counts())
    df_21['Nature de la mutation'] = df_21.index
    
    df_18=pd.DataFrame(df_2018,columns=["Nature mutation"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df_18.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df_18.dropna(inplace=True) 
    df_18 = pd.DataFrame(df_18['Nature mutation'].value_counts())
    df_18['Nature de la mutation'] = df_18.index
    
    fig = go.Figure(go.Bar(x=df_21['Nature de la mutation'], y=df_21['Nature mutation'], name='2021',))
    fig.add_trace(go.Bar(x=df_18['Nature de la mutation'], y=df_18['Nature mutation'], name='2018'))
    
    fig.update_layout(legend_title_text = "Année", title = "Comparaison du nombre de mutations")
    fig.update_xaxes(title_text="Nature de la mutation")
    fig.update_yaxes(title_text="Nombre de mutations")
    return fig

def prix_m2_locaux_2018():
    df=pd.DataFrame(df_2021,columns=["Valeur fonciere","Code type local","Type local","Surface terrain","Code departement","Commune","Code commune","Code postal"])
    df["Prix m2"]=df["Valeur fonciere"]/df["Surface terrain"]
    df.replace([np.inf, -np.inf], np.nan, inplace=True) 
      
    df.dropna(inplace=True) 
    
    df2=pd.DataFrame(df.groupby("Code type local").mean("Prix m2"))
    groupement_type_21=pd.DataFrame(df2.merge(nom_type,left_index=True,right_on="Code type local"))
    groupement_type_21
    
    df=pd.DataFrame(df_2018,columns=["Valeur fonciere","Code type local","Type local","Surface terrain","Code departement","Commune","Code commune","Code postal"])
    df["Prix m2"]=df["Valeur fonciere"]/df["Surface terrain"]
    df.replace([np.inf, -np.inf], np.nan, inplace=True) 
      
    df.dropna(inplace=True) 
    
    df2=pd.DataFrame(df.groupby("Code type local").mean("Prix m2"))
    groupement_type_18=pd.DataFrame(df2.merge(nom_type,left_index=True,right_on="Code type local"))
    
    fig = go.Figure(go.Bar(x=groupement_type_21['Type local'], y=groupement_type_21['Prix m2'], name='2021'))
    fig.add_trace(go.Bar(x=groupement_type_18['Type local'], y=groupement_type_18['Prix m2'], name='2018'))
    
    fig.update_layout(legend_title_text = "Année", title = "Comparaison des prix au mètre carré par rapport au type de local")
    fig.update_xaxes(title_text="Type de local")
    fig.update_yaxes(title_text="Prix du m^2")
    return fig

def type_locaux_echange_2018():
    df_21=pd.DataFrame(df_2021,columns=["Type local"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df_21.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df_21.dropna(inplace=True) 
    df_21 = pd.DataFrame(df_21['Type local'].value_counts())
    df_21['Type de local'] = df_21.index
    
    df_18=pd.DataFrame(df_2018,columns=["Type local"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df_18.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df_18.dropna(inplace=True) 
    df_18 = pd.DataFrame(df_18['Type local'].value_counts())
    df_18['Type de local'] = df_18.index
    
    fig = go.Figure(go.Bar(x=df_21['Type de local'], y=df_21['Type local'], name='2021'))
    fig.add_trace(go.Bar(x=df_18['Type de local'], y=df_18['Type local'], name='2018'))
    
    fig.update_layout(legend_title_text = "Année", title = "Comparaison des proportions de types de locaux")
    fig.update_xaxes(title_text="Type de local")
    fig.update_yaxes(title_text="Nombre de locaux")
    return fig

def nb_pieces_2018():
    df_21=pd.DataFrame(df_2021,columns=["Nombre pieces principales"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df_21.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df_21.dropna(inplace=True) 
    df_21 = df_21[df_21['Nombre pieces principales']<10]
    df_21 = pd.DataFrame(df_21['Nombre pieces principales'].value_counts())
    df_21['Nombre de pieces principales'] = df_21.index
    
    df_18=pd.DataFrame(df_2018,columns=["Nombre pieces principales"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df_18.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df_18.dropna(inplace=True) 
    df_18 = df_18[df_18['Nombre pieces principales']<10]
    df_18 = pd.DataFrame(df_18['Nombre pieces principales'].value_counts())
    df_18['Nombre de pieces principales'] = df_18.index
    
    fig = go.Figure(go.Bar(x=df_21['Nombre de pieces principales'], y=df_21['Nombre pieces principales'], name='2021'))
    fig.add_trace(go.Bar(x=df_18['Nombre de pieces principales'], y=df_18['Nombre pieces principales'], name='2018'))
    
    fig.update_layout(legend_title_text = "Année", title = "Comparaison du nombre de pièces principales")
    fig.update_xaxes(title_text="Nombre de pieces principales")
    fig.update_yaxes(title_text="Nombre de mutations")
    return fig

def type_voie_2018():
    df_21=pd.DataFrame(df_2021,columns=["Type de voie"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df_21.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df_21.dropna(inplace=True) 
    df_21 = pd.DataFrame(df_21['Type de voie'].value_counts())
    df_21['Type voie'] = df_21.index
    df_21 = df_21[df_21['Type de voie']>6000]
    
    df_18=pd.DataFrame(df_2018,columns=["Type de voie"]).dropna(axis=0)
    #enleve les valeurs infinies du dataset
    df_18.replace([np.inf, -np.inf], np.nan, inplace=True) 
    df_18.dropna(inplace=True) 
    df_18 = pd.DataFrame(df_18['Type de voie'].value_counts())
    df_18['Type voie'] = df_18.index
    df_18 = df_18[df_18['Type de voie']>6000]
    
    fig = go.Figure(go.Bar(x=df_21['Type voie'], y=df_21['Type de voie'], name='2021'))
    fig.add_trace(go.Bar(x=df_18['Type voie'], y=df_18['Type de voie'], name='2018'))
    
    fig.update_layout(legend_title_text = "Année", title = "Comparaison des proportions de vente par rapport au type de voie")
    fig.update_xaxes(title_text="Type de voie")
    fig.update_yaxes(title_text="Nombre de voies")
#%%fonction du django

def fonction1(request):
    template= loader.get_template("fonction1.html")
    context={}
    return HttpResponse(template.render(context,request))

def model1(request):
    template=loader.get_template('fonction1.html')
             
    if request.GET['option']=='1':
        fig=bar_prix_dep()
        plot_html=fig.to_html()        
    if request.GET['option']=='2':
        fig=carte_prix_dep()
        plot_html=fig.to_html();
    if request.GET['option']=='3':
        fig=prix_m2_region()
        plot_html=fig.to_html();
    if request.GET['option']=='4':
        fig=nb_pieces_par_commune()
        plot_html=fig.to_html()        
    if request.GET['option']=='5':
        fig=nb_pieces_par_departement()
        plot_html=fig.to_html();
    if request.GET['option']=='6':
        fig=nb_pieces_par_region()
        plot_html=fig.to_html()        
    if request.GET['option']=='7':
        fig=nb_pieces_par_type_habitation()
        plot_html=fig.to_html();
    if request.GET['option']=='8':
        fig=prix_m2_nb_pieces_principales()
        plot_html=fig.to_html();
    if request.GET['option']=='9':
        fig=surf_moyenne_terrain_commune()
        plot_html=fig.to_html();
    if request.GET['option']=='10':
        fig=surf_moyenne_terrain_dep()
        plot_html=fig.to_html();
    if request.GET['option']=='11':
        fig=surf_moyenne_terrain_region()
        plot_html=fig.to_html();
    if request.GET['option']=='12':
        fig=vf_commune()
        plot_html=fig.to_html();
    if request.GET['option']=='13':
        fig=vf_dep()
        plot_html=fig.to_html();
    if request.GET['option']=='14':
        fig=vf_region()
        plot_html=fig.to_html();
    if request.GET['option']=='15':
        fig=type_locaux()
        plot_html=fig.to_html();
    if request.GET['option']=='16':
        fig=type_voie()
        plot_html=fig.to_html();
    if request.GET['option']=='17':
        fig=type_mutation()
        plot_html=fig.to_html();
    if request.GET['option']=='18':
        fig=nb_mutation_2018()
        plot_html=fig.to_html();
    if request.GET['option']=='19':
        fig=prix_m2_locaux_2018()
        plot_html=fig.to_html();
    if request.GET['option']=='20':
        fig=nb_pieces_2018()
        plot_html=fig.to_html();
    if request.GET['option']=='21':
        fig=type_voie_2018()
        plot_html=fig.to_html();
        
    context={'plot_html':plot_html}
    
    return render(request,'fonction1.html',context)
