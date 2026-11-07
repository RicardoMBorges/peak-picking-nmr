from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from morphology import recognize, DEFAULTS

BASE = Path(__file__).resolve().parent
st.set_page_config(page_title='NMR 2D Peak Picker',layout='wide')
st.title('NMR 2D Peak Picker')
st.caption('Protótipo integrado: seleção do experimento e visualizadores experimentais pré-processados')
mode=st.segmented_control('Tipo de espectro', ['HSQC','COSY','HMBC'],default='HMBC',selection_mode='single')
if mode is None: mode='HMBC'
info={
 'HSQC':('IURT21 · HSQC','Heteronuclear: Hessiana multiescala e candidatos por persistência.','HSQC_candidates.csv'),
 'COSY':('IURT26 · COSY','Homonuclear: pares simétricos e diagonal; intensidade máxima ajustável.','COSY_candidates.csv'),
 'HMBC':('IURT21 · HMBC','Heteronuclear de longa distância: sinais positivos/negativos e agrupamento preliminar de lóbulos.','HMBC_correlations.csv')}
name,desc,csv=info[mode]
st.subheader(name)
st.write(desc)
st.warning('A seleção carrega um processamento específico já realizado. Esta versão ainda não recalcula um novo espectro Bruker nem muda dinamicamente o modelo de peak picking sobre um mesmo conjunto de dados.')
html=(BASE/'viewers'/f'{mode}.html').read_text(encoding='utf-8')
components.html(html,height=920,scrolling=True)
with (BASE/'data'/csv).open('rb') as file:
 st.download_button('Baixar resultados '+mode,file,file_name=csv,mime='text/csv')

st.divider()
st.header("Reconhecimento morfológico experimental")
st.caption("Analisa a lista de máximos do espectro selecionado e propõe agrupamentos. Não é ainda um modelo físico da forma de linha nem uma deconvolução.")
source={"HSQC":"HSQC_candidates.csv","COSY":"COSY_candidates.csv","HMBC":"HMBC_lobes.csv"}
cpath=BASE/"data"/source[mode]
if cpath.exists():
    peaks=pd.read_csv(cpath)
    if mode=="COSY":
        peaks=peaks.rename(columns={"H_F2_ppm":"H_ppm","H_F1_ppm":"C_ppm"})
        peaks["polarity"]="positive"
    st.write(f"Candidatos de entrada: {len(peaks)}")
    cfg=DEFAULTS[mode]
    col1,col2,col3,col4=st.columns(4)
    hr=col1.number_input("Janela ¹H (ppm)",min_value=.001,max_value=1.,value=cfg["h_radius"],step=.005,format="%.3f")
    cr=col2.number_input("Janela 2ª dimensão (ppm)",min_value=.001,max_value=10.,value=cfg["c_radius"],step=.05,format="%.3f")
    snr=col3.slider("SNR mínimo",3.,30.,5.,1.)
    policy=col4.selectbox("Padrão de fase",["any","alternating","same"],format_func=lambda x:{"any":"Qualquer","alternating":"Alternância +/-","same":"Mesma fase"}[x])
    scales=st.checkbox("Exigir persistência em ≥2 escalas",value=True)
    try:
        groups,lobes=recognize(peaks,mode,h_radius=hr,c_radius=cr,snr_min=snr,min_scales=2 if scales else 1,phase_policy=policy)
        multi=groups[groups.n_lobes>1]
        st.metric("Hipóteses multilóbulos",len(multi))
        if not multi.empty:
            fig=px.scatter(multi,x="H_ppm",y="C_ppm",color="phase_pattern",size="n_lobes",
                           hover_data=["group_id","orientation_deg","H_span_ppm","C_span_ppm"])
            fig.update_xaxes(autorange="reversed",title="¹H (ppm)")
            fig.update_yaxes(autorange="reversed",title="¹³C (ppm)" if mode!="COSY" else "¹H (ppm)")
            st.plotly_chart(fig,use_container_width=True)
        st.dataframe(multi.head(500),use_container_width=True)
        st.download_button("Exportar hipóteses morfológicas",groups.to_csv(index=False).encode(),file_name=f"{mode}_morphology_groups.csv",mime="text/csv")
        st.download_button("Exportar máximos com IDs de grupos",lobes.to_csv(index=False).encode(),file_name=f"{mode}_morphology_lobes.csv",mime="text/csv")
    except Exception as exc:
        st.error(f"Não foi possível analisar os candidatos: {exc}")
else:
    st.warning(f"Lista de máximos não disponível: {cpath.name}")
