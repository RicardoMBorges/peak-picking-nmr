"""Experimental 2D NMR cross-peak morphology: paired-lobe proposal engine.

Inputs are candidate peak tables, not raw spectrum. Results are hypotheses,
not validated correlations. Distances are in ppm and deliberately mode-specific.
"""
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

DEFAULTS = {
    "HSQC": dict(h_radius=.055, c_radius=.65, orientation="either"),
    "COSY": dict(h_radius=.065, c_radius=.065, orientation="either"),
    "HMBC": dict(h_radius=.115, c_radius=1.1, orientation="H"),
}

def recognize(candidates, mode="HMBC", h_radius=None, c_radius=None,
              snr_min=3.0, min_scales=2, phase_policy="any"):
    """Return (groups, lobes) with traceable input indices and phase pattern.

    Greedy constrained matching: avoids chain merges; a cluster is bounded
    relative to its strongest seed. Never merge >4 maxima. Sign is preserved.
    phase_policy: any | alternating | same.
    """
    if mode not in DEFAULTS: raise ValueError("Unsupported mode")
    cfg=DEFAULTS[mode]
    hr=float(h_radius or cfg["h_radius"]); cr=float(c_radius or cfg["c_radius"])
    if hr<=0 or cr<=0:raise ValueError("Radii must be positive")
    df=candidates.copy().reset_index(drop=True)
    needed={"H_ppm","C_ppm","smoothed_intensity","snr_proxy","scales_detected"}
    if not needed.issubset(df.columns):raise ValueError(f"Missing columns: {needed-set(df.columns)}")
    if "polarity" not in df:df["polarity"]="positive"
    df["source_index"]=np.arange(len(df))
    df=df[(df.snr_proxy>=snr_min)&(df.scales_detected>=min_scales)].copy()
    df=df.sort_values("smoothed_intensity",ascending=False).reset_index(drop=True)
    xy=df[["H_ppm","C_ppm"]].to_numpy(float)
    signs=np.where(df.polarity.astype(str).str.lower().eq("negative"),-1,1)
    tree=cKDTree(xy/np.array([hr,cr])) if len(df) else None
    used=set();groups=[];lobes=[]
    for i in range(len(df)):
        if i in used:continue
        used.add(i);chosen=[i]
        for j in sorted(tree.query_ball_point(xy[i]/[hr,cr],1.0),
                        key=lambda j:-float(df.iloc[j].smoothed_intensity)):
            if j in used or len(chosen)>=4:continue
            dx=abs(xy[i,0]-xy[j,0]);dy=abs(xy[i,1]-xy[j,1])
            if cfg["orientation"]=="H" and dx < 1.4*dy*hr/cr:continue
            if phase_policy=="alternating" and signs[j]==signs[i]:continue
            if phase_policy=="same" and signs[j]!=signs[i]:continue
            # avoid merging arbitrary neighboring signals via very wide radii
            if dx>hr or dy>cr:continue
            chosen.append(j);used.add(j)
        part=df.iloc[chosen]
        w=np.maximum(part.smoothed_intensity.to_numpy(float),1e-12)
        center=np.average(xy[chosen],axis=0,weights=w)
        phase="mixed" if len(set(signs[chosen]))>1 else ("negative" if signs[i]<0 else "positive")
        if len(chosen)>1:
            coords=xy[chosen];v=coords-coords.mean(axis=0)
            cov=(v.T@v)/len(v);ev,vec=np.linalg.eigh(cov)
            orient=float(np.degrees(np.arctan2(vec[1,-1]/cr,vec[0,-1]/hr)))
            spacing=float(np.linalg.norm((coords.max(axis=0)-coords.min(axis=0))/[hr,cr]))
        else:orient=np.nan;spacing=0.
        gid=len(groups)+1
        groups.append(dict(group_id=gid,H_ppm=center[0],C_ppm=center[1],
            n_lobes=len(chosen),phase_pattern=phase,orientation_deg=orient,
            normalized_span=spacing,H_span_ppm=float(part.H_ppm.max()-part.H_ppm.min()),
            C_span_ppm=float(part.C_ppm.max()-part.C_ppm.min()),
            snr_proxy=float(part.snr_proxy.max()),scales_detected=int(part.scales_detected.max()),
            classification="multilobe_hypothesis" if len(chosen)>1 else "single_maximum"))
        for j in chosen:
            item=df.iloc[j].to_dict();item["group_id"]=gid;lobes.append(item)
    return pd.DataFrame(groups),pd.DataFrame(lobes)
