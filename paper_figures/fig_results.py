import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import numpy as np
for f in ['regular','bold','italic','bolditalic']:
    fm.fontManager.addfont(f'/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-{f}.otf')
plt.rcParams.update({'font.family':'TeX Gyre Pagella','font.size':8,'axes.linewidth':0.6,
  'xtick.major.width':0.6,'ytick.major.width':0.6,'xtick.major.size':2.5,'ytick.major.size':2.5,
  'axes.edgecolor':'#52514e','xtick.color':'#52514e','ytick.color':'#52514e','axes.labelcolor':'#0b0b0b',
  'pdf.fonttype':42})
INK='#0b0b0b'; INK2='#52514e'; GRID='#e4e3df'
C={'GROVE':'#2a78d6','Main-question model':'#1baf7a','gemma4:31b':'#eb6834','qwen3.5:27b':'#8a8984'}
MK={'GROVE':'o','Main-question model':'o','gemma4:31b':'s','qwen3.5:27b':'D'}
# Final set, Fall and protective equipment (PAPER_TABLES_v2.md, posthoc_second_baseline.md)
F1={'GROVE':(0.7021,0.6699,0.7329),'Main-question model':(0.7152,0.6851,0.7457),
    'gemma4:31b':(0.6423,0.6131,0.6698),'qwen3.5:27b':(0.6076,0.5814,0.6333),
    'gemma4:31b signed':(0.6753,0.6411,0.7080),'qwen3.5:27b signed':(0.6582,0.6240,0.6917)}
PR={'GROVE':(0.7283,0.6777),'Main-question model':(0.7638,0.6724),'gemma4:31b':(0.9331,0.4897),'qwen3.5:27b':(0.9311,0.4509)}
PRS={'gemma4:31b signed':(0.7717,0.6003),'qwen3.5:27b signed':(0.7657,0.5772)}
BASE={'gemma4:31b signed':'gemma4:31b','qwen3.5:27b signed':'qwen3.5:27b'}
FF=(0.9665,0.3215)  # GROVE, first-freeze thresholds (post hoc), recall, precision
SIZE={'GROVE':(0.7761,0.7192,0.6538),'Main-question model':(0.8806,0.7389,0.5865),'gemma4:31b':(0.9602,0.9113,0.9231)}
order=['GROVE','Main-question model','gemma4:31b','gemma4:31b signed','qwen3.5:27b','qwen3.5:27b signed']
lab={'gemma4:31b':'gemma4:31b (baseline)','qwen3.5:27b':'qwen3.5:27b (post hoc)','gemma4:31b signed':'gemma4:31b, signed confidence','qwen3.5:27b signed':'qwen3.5:27b, signed confidence'}

fig,axs=plt.subplots(1,3,figsize=(6.9,2.45),gridspec_kw={'width_ratios':[1.25,1,1],'wspace':0.42})
# (a) micro-F1 with intervals
ax=axs[0]
for i,k in enumerate(order):
    y=len(order)-1-i; m,lo,hi=F1[k]; b=BASE.get(k,k)
    ax.plot([lo,hi],[y,y],color=C[b],lw=1.6,solid_capstyle='round',zorder=2)
    if k in BASE: ax.plot(m,y,MK[b],ms=5.5,mfc='white',mec=C[b],mew=1.3,zorder=3)
    else: ax.plot(m,y,MK[b],ms=5.5,color=C[b],mec='white',mew=0.8,zorder=3)
    ax.text(hi+0.006,y,f'{m:.3f}',va='center',ha='left',fontsize=7.5,color=INK)
ax.set_yticks(range(len(order))); ax.set_yticklabels([lab.get(k,k) for k in reversed(order)])
ax.set_xlim(0.56,0.80); ax.set_ylim(-0.6,len(order)-0.4)
ax.tick_params(axis='y',labelsize=7.3)
ax.set_xlabel('Micro-F1, final set (95% interval)')
ax.xaxis.grid(True,color=GRID,lw=0.5); ax.set_axisbelow(True)
for s in ['top','right','left']: ax.spines[s].set_visible(False)
ax.tick_params(axis='y',length=0)
ax.set_title('(a)',loc='left',fontsize=8.5,color=INK,pad=4)
# (b) operating points with iso-F1 curves
ax=axs[1]
r=np.linspace(0.01,1,400)
for f in (0.4,0.5,0.6,0.7,0.8):
    p=f*r/(2*r-f); ok=(p>0)&(p<=1)
    ax.plot(r[ok],p[ok],color=GRID,lw=0.7,zorder=1)
    ax.text(1.008,f/(2-f),f'{f:.1f}',fontsize=6,color=INK2,ha='left',va='center',clip_on=False)
ax.text(1.008,0.80,'F1',fontsize=6.5,color=INK2,ha='left',va='center',clip_on=False)
ax.annotate('',xy=PR['GROVE'],xytext=FF,arrowprops=dict(arrowstyle='->',color=C['GROVE'],lw=0.8,shrinkA=4,shrinkB=5,connectionstyle='arc3,rad=-0.35'),zorder=2)
ax.plot(*FF,'o',ms=5.5,mfc='white',mec=C['GROVE'],mew=1.2,zorder=3)
ax.text(FF[0]+0.005,FF[1]-0.035,'GROVE, first-freeze thresholds',fontsize=6.5,color=INK2,ha='right',va='top')
for k in PR:
    ax.plot(*PR[k],MK[k],ms=5.5,color=C[k],mec='white',mew=0.8,zorder=4)
for k,(rr_,pp_) in PRS.items():
    b=BASE[k]; ax.plot(rr_,pp_,MK[b],ms=5.2,mfc='white',mec=C[b],mew=1.3,zorder=4)
ax.text(PRS['gemma4:31b signed'][0]+0.02,PRS['gemma4:31b signed'][1]+0.006,'signed',fontsize=6.5,color=INK2,ha='left',va='center')
ax.text(PRS['qwen3.5:27b signed'][0]+0.02,PRS['qwen3.5:27b signed'][1]-0.008,'signed',fontsize=6.5,color=INK2,ha='left',va='center')
ax.text(PR['GROVE'][0]-0.015,PR['GROVE'][1]+0.035,'GROVE',fontsize=7,color=INK,ha='right')
ax.text(PR['Main-question model'][0]+0.012,PR['Main-question model'][1]+0.035,'Main-question',fontsize=7,color=INK,ha='left')
ax.text(PR['gemma4:31b'][0]-0.018,PR['gemma4:31b'][1]+0.004,'gemma4:31b',fontsize=7,color=INK,ha='right',va='center')
ax.text(PR['qwen3.5:27b'][0],PR['qwen3.5:27b'][1]-0.035,'qwen3.5:27b',fontsize=7,color=INK,ha='center',va='top')
ax.set_xlim(0.55,1.0); ax.set_ylim(0.25,0.85)
ax.set_xlabel('Recall'); ax.set_ylabel('Precision')
for s in ['top','right']: ax.spines[s].set_visible(False)
ax.set_title('(b)',loc='left',fontsize=8.5,color=INK,pad=4)
# (c) recall by hazard size
ax=axs[2]
x=np.arange(3)
for k in ['GROVE','Main-question model','gemma4:31b']:
    ax.plot(x,SIZE[k],'-',color=C[k],lw=1.4,zorder=2)
    ax.plot(x,SIZE[k],MK[k],ms=5,color=C[k],mec='white',mew=0.8,zorder=3)
ax.text(2.08,SIZE['GROVE'][2]+0.02,'GROVE',fontsize=7,color=INK,va='center')
ax.text(2.08,SIZE['Main-question model'][2]-0.02,'Main-\nquestion',fontsize=7,color=INK,va='center')
ax.text(2.13,SIZE['gemma4:31b'][2],'gemma4:31b',fontsize=7,color=INK,va='center')
ax.set_xticks(x); ax.set_xticklabels(['< 1%\n(201)','1–10%\n(200)','≥ 10%\n(99)'])
ax.set_xlim(-0.25,2.9); ax.set_ylim(0.5,1.0)
ax.set_xlabel('Hazard size, share of image (images)'); ax.set_ylabel('Recall')
ax.yaxis.grid(True,color=GRID,lw=0.5); ax.set_axisbelow(True)
for s in ['top','right']: ax.spines[s].set_visible(False)
ax.set_title('(c)',loc='left',fontsize=8.5,color=INK,pad=4)
fig.savefig('/home/claude/figs/Figure_results_final.pdf',bbox_inches='tight',pad_inches=0.02)
fig.savefig('/home/claude/figs/Figure_results_final.png',dpi=220,bbox_inches='tight',pad_inches=0.02)
print('ok')
