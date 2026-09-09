"""Presentation-only dashboard. All figures are supplied by saved result tables.

The embedded assets keep the existing offline HTML and GitHub Pages contract.
There is no network dependency, model fitting, or change to analytical outputs.
"""

from __future__ import annotations

import json
from html import escape

from .dashboard_font import FONT_FACE, FONT_LICENSE
from .dashboard_theme import JOURNAL_CSS


def render_dashboard(payload: dict, fallback_html: str = "") -> str:
    """Embed JSON safely, including review text containing HTML or script tags."""
    data = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    data = data.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    return (
        PAGE.replace("__JOURNAL_CSS__", JOURNAL_CSS.replace("__FONT_FACE__", FONT_FACE))
        .replace("__FONT_LICENSE__", escape(FONT_LICENSE))
        .replace("__FALLBACK__", fallback_html)
        .replace("__PAYLOAD__", data)
    )


PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Explore human-labeled Phasmophobia reviews, the nuance behind Steam recommendations, and a transparent text-model evaluation.">
<meta name="color-scheme" content="light">
<title>Phasmophobia Review Analysis | Results Dashboard</title>
<style>__JOURNAL_CSS__</style>
</head>
<body data-book-state="closed">
<div id="book-intro" class="book-intro">
 <button type="button" id="open-journal" class="book-trigger" aria-controls="journal-shell" aria-label="Open the Phasmophobia player feedback journal">
  <span class="closed-book" aria-hidden="true">
   <span class="book-leaves"></span>
   <span id="book-cover" class="book-cover">
    <span class="cover-kicker">FIELD NOTES / STEAM REVIEWS</span>
    <span class="cover-title">Phasmophobia</span>
    <span class="cover-subtitle">Player Feedback<br>Journal</span>
    <span class="cover-rule"></span>
    <span class="cover-caption">Recommendations. Opinions. Evidence.</span>
    <span class="cover-author">Orlando Devito<br><small>Independent research</small></span>
   </span>
  </span>
  <span class="open-prompt">Click or tap anywhere to open</span>
 </button>
</div>
<div id="journal-shell" hidden>
<a class="skip" href="#content">Skip to dashboard</a>
<aside class="sidebar" aria-label="Dashboard navigation">
 <a class="brand" href="#overview"><span class="brand-mark" aria-hidden="true">P</span><span><strong>PHASMOPHOBIA</strong><small>Player feedback journal</small></span></a>
 <div class="nav-label">THE STUDY</div>
 <nav class="nav"><a href="#overview" data-view="overview" aria-current="page"><span>01</span>Case summary</a><a href="#players" data-view="players"><span>02</span>Player reports</a><a href="#model" data-view="model"><span>03</span>Model findings</a><a href="#evidence" data-view="evidence"><span>04</span>Review evidence</a></nav>
 <div class="side-bottom"><span class="badge">Research only</span><p>One game. One observed corpus. No population-wide claims.</p><a href="https://github.com/ThatTryHard/phasmophobia-steam-review-analysis">View project on GitHub ↗</a><a href="https://github.com/ThatTryHard/phasmophobia-steam-review-analysis/blob/main/docs/METHODOLOGY.md">Read the methodology ↗</a></div>
</aside>
<main id="content" tabindex="-1">
 <div class="topbar"><span>CASE FILE / STEAM REVIEW ANALYSIS</span><span id="window-label">Observed corpus</span></div>
 <section id="overview" class="view" aria-labelledby="overview-title">
  <div class="mast"><div><div class="eyebrow">01 / The research question</div><h1 id="overview-title">Recommended. But what did they say?</h1><p>Do written reviews tell us more than a thumbs up or down? This study reads the text, separates mixed opinions from contradictions, and tests whether a sentiment model can capture those distinctions.</p></div><span class="scope-chip">Observed corpus only</span></div>
  <div class="stats" id="overview-stats"></div>
  <div class="grid"><section class="panel"><div class="panel-head"><div><h2>What the text actually says</h2><p>Sentiment within each Steam recommendation group</p></div><span class="panel-num">FIG. 01</span></div><div id="recommendation-bars"></div><div id="sentiment-legend" class="legend"></div><div id="recommendation-insight" class="insight"></div><details><summary>Read the exact counts and percentages</summary><div id="recommendation-table" class="table-scroll"></div></details></section>
  <section class="panel"><div class="panel-head"><div><h2>Nuance is not contradiction</h2><p>Six distinct relationships across the full corpus</p></div></div><div id="relation-bars"></div><p class="note">Intervals are 95% Wilson intervals. They do not correct unknown sampling bias.</p></section></div>
  <div class="grid equal"><section class="panel"><div class="panel-head"><h2>How to read these categories</h2></div><div class="definition"><i class="swatch" style="--c:var(--amber)"></i><div><strong>Mixed opinion</strong><p>Both praise and criticism. A mixed review can still reasonably recommend the game.</p></div></div><div class="definition"><i class="swatch" style="--c:var(--violet)"></i><div><strong>Hard contradiction</strong><p>Clearly negative text paired with Recommended, or clearly positive text paired with Not Recommended.</p></div></div><div class="definition"><i class="swatch" style="--c:var(--gray)"></i><div><strong>Non-evaluative or insufficient</strong><p>Content without a game evaluation, or too little evidence to infer sentiment. Neither automatically implies disagreement.</p></div></div></section>
  <section class="panel"><div class="panel-head"><div><h2>Human reference, not Steam labels</h2><p>Recommendations were hidden during annotation.</p></div></div><div id="annotation-stats" class="metric-inline"></div><p class="note">Agreement is measured before adjudication. Human disagreement is resolved before the final labels are used in analysis or evaluation.</p><details><summary>Inspect annotation agreement by field</summary><div id="agreement-table" class="table-scroll"></div></details></section></div>
  <div class="scope-note"><strong>Scope matters.</strong><span>The collected review window is not a representative sample of all Phasmophobia or Steam reviews. These are descriptive findings, not evidence that an update caused a change in sentiment.</span></div>
 </section>
 <section id="players" class="view" hidden aria-labelledby="players-title">
  <div class="mast"><div><div class="eyebrow">02 / Player reports</div><h1 id="players-title">What players talk about.</h1><p>Explore the themes and playtime groups behind the recommendations. These are associations within this corpus, not explanations of player psychology.</p></div></div>
  <div class="grid"><section class="panel"><div class="panel-head"><div><h2>Primary themes</h2><p>One human-assigned primary theme per review</p></div><span class="panel-num">FIG. 02</span></div><div class="legend" style="margin:0 0 20px"><span><i class="swatch" style="--c:var(--mint)"></i>Recommended</span><span><i class="swatch" style="--c:var(--red)"></i>Not Recommended</span></div><div id="theme-bars"></div><p class="note">Bar lengths show review counts on a common scale. Theme labels were assigned without seeing the Steam recommendation.</p><details><summary>View source theme counts</summary><div id="theme-table" class="table-scroll"></div></details></section>
  <section class="panel"><div class="panel-head"><div><h2>Recommendation × sentiment</h2><p>Cell shading shows share within the recommendation row.</p></div></div><div class="chart-scroll"><div id="sentiment-matrix" class="heatmap-wrap"></div></div><div id="theme-insight" class="insight warm"></div><p class="note">Update-related text does not establish an update’s causal effect. The study has no controlled before-and-after comparison.</p></section></div>
  <section class="panel full"><div class="panel-head"><div><h2>Opinion composition by playtime</h2><p>Each bar totals 100% of its own group. Compare group sizes as well as percentages.</p></div><span class="panel-num">FIG. 03</span></div><div id="player-bars"></div><div id="relation-legend" class="legend"></div><p class="note">Playtime cutoffs are descriptive choices. Small groups are unstable; alternate cutoffs and duplicate/confidence sensitivity checks are available in the project’s <a href="https://github.com/ThatTryHard/phasmophobia-steam-review-analysis/blob/main/data/processed/sensitivity_results.csv">sensitivity results</a>.</p><details><summary>View group counts and denominators</summary><div id="player-table" class="table-scroll"></div></details></section>
 </section>
 <section id="model" class="view" hidden aria-labelledby="model-title">
  <div class="mast"><div><div class="eyebrow">03 / Model findings</div><h1 id="model-title">Can text recover the nuance?</h1><p>Compare the selected text classifier with transparent baselines on the same eligible locked-test reviews.</p></div><span class="badge">Not production-approved</span></div>
  <div id="model-stats" class="stats"></div>
  <section class="panel full"><div class="panel-head"><div><h2>Locked-test comparison</h2><p>Points are estimates; whiskers show 95% group-bootstrap intervals.</p></div><div class="segmented" role="group" aria-label="Performance metric"><button data-metric="macro_f1" aria-pressed="true">Macro F1</button><button data-metric="accuracy" aria-pressed="false">Accuracy</button><button data-metric="balanced_accuracy" aria-pressed="false">Balanced accuracy</button></div></div><div id="metric-chart" class="chart-scroll" aria-live="polite"></div><div id="model-insight" class="insight"></div><p class="note">Macro F1 gives each sentiment class equal weight. The Steam mapping can only output positive or negative, so it cannot identify mixed or non-evaluative text. The 2,000-resample intervals describe uncertainty, not proof of superiority.</p><details><summary>Inspect metric estimates and intervals</summary><div id="metrics-table" class="table-scroll"></div></details></section>
  <div class="grid equal"><section class="panel"><div class="panel-head"><div><h2>Where the model gets confused</h2><p>Rows: human labels · Columns: predictions</p></div><div class="segmented" role="group" aria-label="Confusion matrix values"><button data-confusion="count" aria-pressed="true">Counts</button><button data-confusion="percent" aria-pressed="false">Row %</button></div></div><div class="chart-scroll"><div id="confusion-matrix" class="heatmap-wrap" aria-live="polite"></div></div><p class="note">Diagonal cells are correct predictions. Off-diagonal cells reveal which classes the model confuses. Human-screened insufficient text is outside this model’s four-class task.</p></section>
  <section class="panel"><div class="panel-head"><div><h2>Performance by class</h2><p>F1 score on the eligible locked test · Scale 0–1</p></div></div><div id="class-bars"></div><p class="note">Support is the number of actual test reviews in each class. Small supports make individual class scores particularly uncertain.</p></section></div>
  <section class="panel full"><div class="panel-head"><div><h2>Selection happened before testing</h2><p>Development-only repeated stratified group cross-validation</p></div></div><div id="cv-table" class="table-scroll"></div><p class="note">The one-standard-error rule selects the least complex eligible text model near the highest CV mean. This is a complexity-control heuristic, not a statistical equivalence test. SD describes variation between repeat means, not independent new datasets.</p></section>
  <section class="panel full"><div class="panel-head"><h2>From corpus to evaluation</h2></div><div id="cohort-steps" class="steps"></div><p class="note">The original split was assigned before annotation. Exact normalized-text groups stay together across development/test and within cross-validation. Do not tune against the published test errors.</p></section>
  <div class="scope-note"><strong>What remains untested</strong><span>Future updates, other games, and production use. No operational abstention threshold has been approved. The model is evaluated only on English reviews judged to contain sufficient text.</span></div>
 </section>
 <section id="evidence" class="view" hidden aria-labelledby="evidence-title">
  <div class="mast"><div><div class="eyebrow">04 / Review evidence</div><h1 id="evidence-title">Read the mistakes, not just the score.</h1><p>A deterministic diagnostic sample of locked-test errors. These examples illustrate failure modes; they are not representative of the corpus.</p></div></div>
  <div class="scope-note" style="margin-bottom:24px"><strong>Selection rule</strong><span>Up to two lowest-confidence errors per human-label/predicted-label pair, with ties broken by review ID. Confidence is the model’s uncalibrated predicted-class probability, not a reliability guarantee.</span></div>
  <div class="evidence-tools"><span id="error-count" class="muted" aria-live="polite"></span><label>Human label<select id="error-filter"><option value="all">All classes</option></select></label></div>
  <div id="error-cards" class="error-grid"></div><div class="pager"><span id="page-status" aria-live="polite"></span><div><button id="prev-errors">Previous</button><button id="next-errors">Next</button></div></div>
  <details><summary>Read the full diagnostic sample as a table</summary><div id="error-table" class="table-scroll"></div></details>
 </section>
 <noscript><section class="panel"><h2>Saved result tables</h2><p>Enable JavaScript for the interactive charts. These tables remain available without it.</p>__FALLBACK__</section></noscript>
 <footer class="footer"><span>Independent Phasmophobia study · Orlando Devito</span><span><a href="https://github.com/ThatTryHard/phasmophobia-steam-review-analysis/blob/main/reports/model_validation.md">Validation report</a> · <a href="https://github.com/ThatTryHard/phasmophobia-steam-review-analysis/releases/tag/v2.0.0">Research release</a></span></footer>
</main>
</div>
<noscript><style>#book-intro{display:none}#journal-shell[hidden]{display:block}body[data-book-state="closed"]{overflow:auto}</style></noscript>
<template id="font-license"><pre>__FONT_LICENSE__</pre></template>
<script type="application/json" id="dashboard-data">__PAYLOAD__</script>
<script>
"use strict";
const D=JSON.parse(document.getElementById("dashboard-data").textContent);
const T=D.tables, $=id=>document.getElementById(id), esc=v=>String(v??"").replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=v=>v!==null&&v!==undefined&&v!==""&&Number.isFinite(Number(v))?Number(v):null;
const fixed=(v,n=3)=>num(v)===null?'—':num(v).toFixed(n), pct=v=>num(v)===null?'—':(100*num(v)).toFixed(1)+'%';
const sum=(xs,key='n')=>xs.reduce((a,x)=>a+(num(x[key])??0),0), records=name=>T[name]||[];
const C={Positive_only:'#41694f',Negative_only:'#994b43',Mixed:'#956a20',Neutral_non_evaluative:'#496c89',Not_applicable:'#736e63'};
const names={Positive_only:'Positive',Negative_only:'Negative',Mixed:'Mixed',Neutral_non_evaluative:'Non-evaluative',Not_applicable:'Insufficient',word_1_2gram_logreg:'Word 1–2 gram + LR',word_unigram_logreg:'Word unigram + LR',char_3_5gram_logreg:'Character 3–5 gram + LR',steam_recommendation_mapping:'Steam recommendation',most_frequent:'Most-frequent class'};
const relations={'Aligned positive':'#41694f','Aligned negative':'#994b43','Qualified / mixed opinion':'#956a20','Non-evaluative text':'#496c89','Insufficient text':'#736e63','Hard contradiction':'#755882'};
const classes=['Positive_only','Negative_only','Mixed','Neutral_non_evaluative'], sentimentKeys=[...classes,'Not_applicable'];
const label=x=>names[x]||String(x??'Unknown').replaceAll('_',' '), reviews=records('review_level.csv'), total=reviews.length, kpis=records('kpi_summary.csv'), matrix=records('recommendation_sentiment_matrix.csv'), metrics=records('model_summary.csv');
const blank=()=>'<p class="blank">Not available in this saved result snapshot.</p>';
function table(id,rows,columns){$(id).innerHTML=rows.length?'<table class="data-table"><thead><tr>'+columns.map(c=>'<th scope="col">'+esc(c[1])+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+columns.map(c=>'<td>'+esc(c[2]?c[2](r[c[0]],r):r[c[0]])+'</td>').join('')+'</tr>').join('')+'</tbody></table>':blank()}
function stat(labelText,value,detail,highlight=false){return '<div class="stat '+(highlight?'highlight':'')+'"><div class="label">'+esc(labelText)+'</div><div class="value">'+esc(value)+'</div><div class="detail">'+esc(detail)+'</div></div>'}
function legend(id,keys,colors,namer=label){$(id).innerHTML=keys.map(k=>'<span><i class="swatch" style="--c:'+colors[k]+'"></i>'+esc(namer(k))+'</span>').join('')}
function stack(rows,key,keys,colors,denom){return '<div class="stack" role="img" aria-label="'+esc(keys.map(k=>{const n=sum(rows.filter(r=>r[key]===k));return label(k)+': '+n+' of '+denom}).join('; '))+'">'+keys.map(k=>{const n=sum(rows.filter(r=>r[key]===k)),p=denom?n/denom:0;return n?'<div class="segment" style="width:'+(100*p)+'%;--c:'+colors[k]+'" title="'+esc(label(k)+': '+n+' / '+denom+' ('+pct(p)+')')+'">'+(p>=.085?esc(pct(p)):'')+'</div>':''}).join('')+'</div>'}
function axis(){return '<div class="axis"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div>'}
const dates=reviews.map(r=>r.review_date?String(r.review_date).slice(0,10):'').filter(Boolean).sort();
function dateLabel(s){const d=new Date(s+'T00:00:00Z');return Number.isNaN(d.getTime())?s:d.toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'})}
if(dates.length)$('window-label').textContent=dateLabel(dates[0])+' to '+dateLabel(dates.at(-1));
const mixed=kpis.find(r=>r.kpi==='Qualified / mixed opinion'), hard=kpis.find(r=>r.kpi==='Hard contradiction'), agree=D.agreement.find(r=>r.field==='sentiment_composition');
$('overview-stats').innerHTML=stat('Reviews in the corpus',total,'Full observed corpus',true)+stat('Qualified / mixed opinion',pct(mixed?.proportion),(mixed?.n??'—')+' / '+total+' reviews')+stat('Hard contradictions',pct(hard?.proportion),(hard?.n??'—')+' / '+total+' reviews')+stat('Sentiment agreement κ',fixed(agree?.cohen_kappa),(agree?.n_double_annotated??'—')+' independently double-coded');
$('recommendation-bars').innerHTML=['Recommended','Not Recommended'].map(rec=>{const rows=matrix.filter(r=>r.recommendation===rec),denom=sum(rows);return '<div class="stack-item"><div class="stack-label"><strong>'+rec+'</strong><small>n = '+denom+' · '+pct(total?denom/total:null)+' of corpus</small></div>'+stack(rows,'sentiment_composition',sentimentKeys,C,denom)+axis()+'</div>'}).join('');
legend('sentiment-legend',sentimentKeys,C);
const recN=sum(matrix.filter(r=>r.recommendation==='Recommended')),recMixed=sum(matrix.filter(r=>r.recommendation==='Recommended'&&r.sentiment_composition==='Mixed'));
$('recommendation-insight').innerHTML='<strong>'+recMixed+' of '+recN+' recommended reviews contain mixed opinions.</strong> A thumbs up can coexist with criticism.';
$('relation-bars').innerHTML=kpis.map(r=>'<div class="relation-row"><div class="bar-label"><span><i class="swatch" style="--c:'+relations[r.kpi]+'"></i> '+esc(r.kpi)+'</span><strong>'+pct(r.proportion)+'<small>'+r.n+' / '+r.denominator+'</small></strong></div><div class="track"><div class="fill" style="width:'+(100*r.proportion)+'%;--c:'+relations[r.kpi]+'"></div></div><div class="bar-foot">95% CI '+pct(r.ci95_lower)+' to '+pct(r.ci95_upper)+'</div></div>').join('');
table('recommendation-table',matrix,[['recommendation','Steam verdict'],['sentiment_composition','Human sentiment',label],['n','Count'],['recommendation_denominator','Group n'],['within_recommendation_proportion','Within group',pct]]);
$('annotation-stats').innerHTML=[['Double-coded',agree?.n_double_annotated??'—'],['Exact sentiment agreement',pct(num(agree?.percent_agreement)===null?null:agree.percent_agreement/100)],['Adjudication rows',D.adjudication_rows??'—']].map(([s,v])=>'<div><strong>'+esc(v)+'</strong><small>'+esc(s)+'</small></div>').join('');
table('agreement-table',D.agreement,[['field','Annotation field',label],['n_double_annotated','Paired n'],['percent_agreement','Exact agreement',v=>fixed(v,2)+'%'],['cohen_kappa','Cohen’s κ',v=>fixed(v)]]);
const themes=records('theme_summary.csv'),themeNames=[...new Set(themes.map(r=>r.primary_theme))].sort((a,b)=>sum(themes.filter(r=>r.primary_theme===b))-sum(themes.filter(r=>r.primary_theme===a)));
const maxTheme=Math.max(1,...themeNames.map(t=>sum(themes.filter(r=>r.primary_theme===t))));
$('theme-bars').innerHTML=themeNames.map(t=>{const rows=themes.filter(r=>r.primary_theme===t),n=sum(rows),yes=sum(rows.filter(r=>r.recommendation==='Recommended')),no=n-yes;return '<div class="relation-row"><div class="bar-label"><span>'+esc(t==='Not_applicable'?'Not applicable (insufficient text)':label(t))+'</span><strong>'+n+'<small>reviews</small></strong></div><div class="track" style="height:14px"><div style="display:flex;width:'+(100*n/maxTheme)+'%;height:100%"><div style="background:var(--mint);width:'+(100*yes/n)+'%" title="'+yes+' Recommended"></div><div style="background:var(--red);width:'+(100*no/n)+'%" title="'+no+' Not Recommended"></div></div></div><div class="bar-foot">'+yes+' recommended · '+no+' not recommended</div></div>'}).join('');
table('theme-table',themes,[['primary_theme','Primary theme',label],['recommendation','Steam verdict'],['n','Count'],['theme_denominator','Theme n'],['within_theme_proportion','Within theme',pct]]);
function heatTable(keys,rowLabels,getN,mode='both') {return '<table class="heatmap"><thead><tr><th scope="col">Human label / prediction</th>'+keys.map(k=>'<th scope="col">'+esc(label(k))+'</th>').join('')+'</tr></thead><tbody>'+rowLabels.map(row=>{const ns=keys.map(k=>getN(row,k)),n=ns.reduce((a,b)=>a+b,0);return '<tr><th scope="row">'+esc(label(row))+'<br><small>n = '+n+'</small></th>'+ns.map(v=>{const p=n?v/n:0;return '<td style="--shade:rgba(77,117,80,'+(p*.43+.035)+')" title="'+v+' / '+n+' ('+pct(p)+')">'+(mode==='percent'?pct(p):v)+(mode==='both'?'<small>'+pct(p)+'</small>':'')+'</td>'}).join('')+'</tr>'}).join('')+'</tbody></table>'}
$('sentiment-matrix').innerHTML=heatTable(sentimentKeys,['Recommended','Not Recommended'],(r,c)=>sum(matrix.filter(x=>x.recommendation===r&&x.sentiment_composition===c))).replace('Human label / prediction','Steam verdict / sentiment');
const update=themes.filter(r=>r.primary_theme==='Update_or_change'),updateNo=sum(update.filter(r=>r.recommendation==='Not Recommended'));
$('theme-insight').innerHTML=update.length?'<strong>'+updateNo+' of '+sum(update)+' update-themed reviews are Not Recommended.</strong> This association is specific to the observed review window.':'No update-theme records are available in this snapshot.';
const players=records('player_relation_summary.csv'),playerKeys=[...new Set(players.map(r=>r.player_group??'Unknown'))];
const groupOrder=['New','Casual','Regular','Veteran','Hardcore'];playerKeys.sort((a,b)=>{const rank=s=>{const i=groupOrder.findIndex(k=>s.startsWith(k));return i<0?99:i};return rank(a)-rank(b)});
$('player-bars').innerHTML=playerKeys.map(g=>{const rows=players.filter(r=>(r.player_group??'Unknown')===g),n=sum(rows);return '<div class="stack-item"><div class="stack-label"><strong>'+esc(g)+'</strong><small>n = '+n+(n<30?' · Small group':'')+'</small></div>'+stack(rows,'recommendation_text_relation',Object.keys(relations),relations,n)+axis()+'</div>'}).join('');legend('relation-legend',Object.keys(relations),relations,k=>k);
table('player-table',players,[['player_group','Playtime group'],['recommendation_text_relation','Relationship'],['n','Count'],['player_group_denominator','Group n'],['within_player_group_proportion','Within group',pct]]);
const selected=D.manifest.selected_model||metrics.find(r=>!['most_frequent','steam_recommendation_mapping'].includes(r.model))?.model;
const overall=metrics.filter(r=>r.class==='overall'),findMetric=(model,metric)=>overall.find(r=>r.model===model&&r.metric===metric),mainF1=findMetric(selected,'macro_f1'),mainAcc=findMetric(selected,'accuracy');
$('model-stats').innerHTML=stat('Locked-test macro F1',fixed(mainF1?.estimate),'95% CI '+fixed(mainF1?.ci95_lower)+' to '+fixed(mainF1?.ci95_upper),true)+stat('Locked-test accuracy',pct(mainAcc?.estimate),'English, sufficient-text reviews')+stat('Eligible test reviews',mainF1?.n_test??'—','From the preassigned test partition')+stat('Development reviews',D.manifest.development_rows??'—',(D.manifest.cv_repeats??'—')+' CV repeats');
function drawMetrics(metric='macro_f1'){
 const order=[selected,'steam_recommendation_mapping','most_frequent'],rows=order.map(m=>findMetric(m,metric)).filter(Boolean);
 document.querySelectorAll('[data-metric]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.metric===metric)));
 if(!rows.length){$('metric-chart').innerHTML=blank();return}
 const x=v=>245+Math.max(0,Math.min(1,v))*490;
 let s='<svg class="plot" viewBox="0 0 920 265" role="img" aria-label="'+esc(label(metric))+' comparison with 95 percent confidence intervals"><title>'+esc(label(metric))+' on the locked test</title>';
 [0,.25,.5,.75,1].forEach(v=>s+='<line class="gridline" x1="'+x(v)+'" x2="'+x(v)+'" y1="12" y2="211"/><text x="'+x(v)+'" y="246" text-anchor="middle">'+v.toFixed(2)+'</text>');
 rows.forEach((r,i)=>{const y=44+i*72,c=i===0?'#41694f':'#746b5d',lo=num(r.ci95_lower),hi=num(r.ci95_upper);s+='<g style="--c:'+c+'"><title>'+esc(label(r.model))+': '+fixed(r.estimate)+', 95% interval '+fixed(lo)+' to '+fixed(hi)+'</title><text class="model-label '+(i===0?'selected-label':'')+'" x="0" y="'+(y+5)+'">'+esc(label(r.model))+'</text>';
 if(lo!==null&&hi!==null)s+='<line class="ci" x1="'+x(lo)+'" x2="'+x(hi)+'" y1="'+y+'" y2="'+y+'"/><line class="ci" x1="'+x(lo)+'" x2="'+x(lo)+'" y1="'+(y-6)+'" y2="'+(y+6)+'"/><line class="ci" x1="'+x(hi)+'" x2="'+x(hi)+'" y1="'+(y-6)+'" y2="'+(y+6)+'"/>';
 s+='<circle cx="'+x(r.estimate)+'" cy="'+y+'" r="7"/><text class="score" x="780" y="'+(y+5)+'">'+fixed(r.estimate)+'</text></g>'});
 $('metric-chart').innerHTML=s+'</svg>';
 const a=findMetric(selected,metric),b=findMetric('steam_recommendation_mapping',metric);
 $('model-insight').innerHTML=a&&b?'<strong>'+fixed(a.estimate)+' vs '+fixed(b.estimate)+' for the Steam baseline.</strong> '+(a.estimate>b.estimate?'The text model has the higher point estimate on this test.':'The text model does not exceed the baseline on this metric.')+' The test is small; these estimates do not establish performance after future updates.':'No paired baseline comparison is available.';
}
drawMetrics();document.querySelectorAll('[data-metric]').forEach(b=>b.addEventListener('click',()=>drawMetrics(b.dataset.metric)));
table('metrics-table',overall,[['model','Model',label],['metric','Metric',label],['estimate','Estimate',v=>fixed(v)],['ci95_lower','95% lower',v=>fixed(v)],['ci95_upper','95% upper',v=>fixed(v)],['n_test','Test n']]);
function confusion(mode='count'){document.querySelectorAll('[data-confusion]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.confusion===mode)));$('confusion-matrix').innerHTML=D.predictions.length?heatTable(classes,classes,(r,c)=>D.predictions.filter(x=>x.sentiment_composition===r&&x.predicted_sentiment===c).length,mode):blank()}
confusion();document.querySelectorAll('[data-confusion]').forEach(b=>b.addEventListener('click',()=>confusion(b.dataset.confusion)));
$('class-bars').innerHTML=classes.map(c=>{const r=metrics.find(x=>x.model===selected&&x.class===c&&x.metric==='f1');if(!r)return '';const support=D.predictions.length?D.predictions.filter(x=>x.sentiment_composition===c).length:D.manifest.test_class_counts?.[c]??'—';return '<div class="relation-row"><div class="bar-label"><span>'+label(c)+'</span><strong>'+fixed(r.estimate)+'<small>n = '+support+'</small></strong></div><div class="track" style="height:13px"><div class="fill" style="--c:'+C[c]+';width:'+(100*r.estimate)+'%"></div></div><div class="bar-foot">95% CI '+fixed(r.ci95_lower)+' to '+fixed(r.ci95_upper)+'</div></div>'}).join('')||blank();
table('cv-table',D.selection,[['model','Candidate',label],['mean_macro_f1','Mean macro F1',v=>fixed(v)],['sd_macro_f1','Repeat SD',v=>fixed(v)],['n_repeats','Repeats'],['selected','Decision',v=>v===true||v==='True'?'Selected':'Not selected']]);
const cohort=D.manifest.development_rows!=null&&D.manifest.locked_test_rows!=null?D.manifest.development_rows+D.manifest.locked_test_rows:null;
$('cohort-steps').innerHTML=[['01 / Corpus',total,'Human-labeled reviews'],['02 / Eligible',cohort??'—','English + sufficient text'],['03 / Development',D.manifest.development_rows??'—','Model selection only'],['04 / Locked test',D.manifest.locked_test_rows??'—','Final evaluation cohort']].map(([title,note,desc])=>'<div class="step"><div class="eyebrow">'+title+'</div><div class="number">'+note+'</div><p>'+desc+'</p></div>').join('');
const errors=records('audit_error_examples.csv');let errorPage=0;const perPage=4;
classes.filter(c=>errors.some(e=>e.actual===c)).forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=label(c);$('error-filter').append(o)});
function renderErrors(){const filter=$('error-filter').value,rows=errors.filter(e=>filter==='all'||e.actual===filter),start=errorPage*perPage;
 $('error-count').textContent=rows.length+' diagnostic examples'+(filter==='all'?'':' in this class');
 $('error-cards').innerHTML=rows.slice(start,start+perPage).map(e=>'<article class="error-card"><div class="error-top"><span>'+esc(e.review_id)+'</span><span class="pill">Locked-test error</span></div><blockquote>'+esc(e.review_text)+'</blockquote><div class="labels"><div><span class="muted">Human label</span><strong style="color:'+C[e.actual]+'">'+esc(label(e.actual))+'</strong></div><div><span class="muted">Model predicted</span><strong style="color:'+C[e.predicted]+'">'+esc(label(e.predicted))+'</strong></div><div><span class="muted">Model confidence</span><strong>'+pct(e.prediction_confidence)+'</strong></div></div></article>').join('')||blank();
 $('page-status').textContent=rows.length?'Showing '+(start+1)+'–'+Math.min(start+perPage,rows.length)+' of '+rows.length:'No examples available';$('prev-errors').disabled=errorPage===0;$('next-errors').disabled=start+perPage>=rows.length;
}
$('error-filter').addEventListener('change',()=>{errorPage=0;renderErrors()});$('prev-errors').addEventListener('click',()=>{if(errorPage>0)errorPage--;renderErrors()});$('next-errors').addEventListener('click',()=>{errorPage++;renderErrors()});renderErrors();
table('error-table',errors,[['review_id','Review'],['actual','Human label',label],['predicted','Model label',label],['prediction_confidence','Uncalibrated confidence',pct],['review_text','Review text']]);
// Motion only changes presentation. Routing and every displayed result remain intact.
const motionPreference=window.matchMedia('(prefers-reduced-motion: reduce)');
const shell=$('journal-shell'),intro=$('book-intro'),openButton=$('open-journal');
let bookState='closed',activeView=null,openingTimer=null,pageAnimation=null;
function finishOpening(){
 if(bookState!=='opening')return;
 clearTimeout(openingTimer);bookState='open';document.body.dataset.bookState='open';
 intro.hidden=true;shell.hidden=false;shell.inert=false;shell.removeAttribute('aria-hidden');
 document.querySelector('[data-view][aria-current="page"]')?.focus({preventScroll:true});
}
function openJournal(){
 if(bookState!=='closed')return;
 bookState='opening';openButton.disabled=true;shell.hidden=false;shell.inert=true;
 shell.setAttribute('aria-hidden','true');document.body.dataset.bookState='opening';
 if(motionPreference.matches){finishOpening();return}
 // Timer also completes the transition if the browser suppresses animation events.
 openingTimer=setTimeout(finishOpening,1250);
}
openButton.addEventListener('click',openJournal);
$('book-cover').addEventListener('animationend',event=>{if(event.animationName==='open-cover')finishOpening()});
motionPreference.addEventListener('change',event=>{if(event.matches){finishOpening();pageAnimation?.cancel()}});
function route(){
 let id=location.hash.slice(1);if(!['overview','players','model','evidence'].includes(id))id='overview';
 const changed=id!==activeView;activeView=id;
 document.querySelectorAll('.view').forEach(section=>section.hidden=section.id!==id);
 document.querySelectorAll('[data-view]').forEach(tab=>{if(tab.dataset.view===id)tab.setAttribute('aria-current','page');else tab.removeAttribute('aria-current')});
 if(changed)pageAnimation?.cancel();
 if(changed&&bookState==='open'&&!motionPreference.matches&&typeof $(id).animate==='function'){
  pageAnimation=$(id).animate([
   {opacity:.35},
   {opacity:1}
  ],{duration:220,easing:'ease-out'});
 }
 if(changed&&bookState==='open'){
  const nav=document.querySelector('.nav');
  if(nav.getBoundingClientRect().top<0)nav.scrollIntoView({block:'start',behavior:'instant'});
 }
}
// Update the URL without the browser's automatic anchor jump on each tab click.
document.querySelectorAll('[data-view]').forEach(tab=>tab.addEventListener('click',event=>{
 if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
 event.preventDefault();
 const hash='#'+tab.dataset.view;
 if(location.hash!==hash)history.pushState(null,'',hash);
 route();
}));
window.addEventListener('popstate',route);
window.addEventListener('hashchange',route);route();
</script>
</body></html>'''
