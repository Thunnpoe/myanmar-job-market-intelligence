const charts = {};
const number = new Intl.NumberFormat("en-US");
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? "").replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));

function isDark(){return document.documentElement.dataset.theme === "dark"}
function cssColor(name){return getComputedStyle(document.documentElement).getPropertyValue(name).trim()}
function chartPalette(){return isDark()
  ? ["#a9c497", "#e5c36b", "#7fa9bd", "#d89679", "#aa98c7", "#9eb77d"]
  : ["#3c4f31", "#c7962f", "#5f8297", "#b86f55", "#796990", "#819b62"]}

function toast(message){
  $("toast").textContent=message;
  $("toast").classList.add("show");
  setTimeout(()=>$("toast").classList.remove("show"),2400);
}

function rangeColors(values){
  const max=Math.max(...values,1);
  const palette=isDark()
    ? ["#a9c497", "#e5c36b", "#7fa9bd", "#d89679"]
    : ["#3c4f31", "#c7962f", "#6f8e9e", "#bd7b61"];
  return values.map(value=>{
    const ratio=value/max;
    return ratio>=.66?palette[0]:ratio>=.33?palette[1]:ratio>=.12?palette[2]:palette[3];
  });
}

const valueLabelPlugin={
  id:"valueLabels",
  afterDatasetsDraw(chart, _args, pluginOptions){
    if(!pluginOptions?.enabled)return;
    const {ctx,chartArea}=chart;
    const values=chart.data.datasets[0].data;
    ctx.save();
    ctx.fillStyle=cssColor("--ink");
    ctx.font='700 11px "DM Sans"';
    ctx.textBaseline="middle";
    chart.getDatasetMeta(0).data.forEach((bar,index)=>{
      const label=number.format(values[index]);
      const width=ctx.measureText(label).width;
      let x=bar.x+8;
      if(x+width>chartArea.right)x=bar.x-width-8;
      ctx.fillText(label,Math.max(chartArea.left+3,x),bar.y);
    });
    ctx.restore();
  }
};

function buildChart(id,type,labels,values,options={}){
  if(charts[id])charts[id].destroy();
  const horizontal=Boolean(options.horizontal);
  const lineColor=isDark()?"#a9c497":"#3c4f31";
  const gridColor=isDark()?"rgba(237,240,232,.09)":"rgba(60,79,49,.07)";
  charts[id]=new Chart($(id),{
    type,
    plugins:[valueLabelPlugin],
    data:{labels,datasets:[{
      data:values,
      backgroundColor:type==="line"?(isDark()?"rgba(169,196,151,.14)":"rgba(60,79,49,.12)"):type==="bar"?rangeColors(values):chartPalette(),
      borderColor:type==="doughnut"?cssColor("--ivory"):lineColor,
      borderWidth:type==="line"?2:type==="doughnut"?2:0,
      borderRadius:type==="bar"?6:0,
      fill:type==="line",
      tension:.32,
      pointRadius:type==="line"?5:3,
      pointHoverRadius:type==="line"?7:4
    }]},
    options:{
      responsive:true,
      maintainAspectRatio:false,
      indexAxis:horizontal?"y":"x",
      layout:{padding:options.showValues?{right:30}:0},
      plugins:{
        valueLabels:{enabled:Boolean(options.showValues)},
        legend:{display:type==="doughnut",position:"bottom",labels:{color:cssColor("--ink"),boxWidth:10,usePointStyle:true,padding:16,font:{family:"DM Sans",size:11}}},
        tooltip:{callbacks:{label:context=>`${context.label}: ${number.format(context.raw)} jobs`}}
      },
      scales:type==="doughnut"?{}:{
        x:{beginAtZero:true,grid:{color:gridColor},ticks:{color:cssColor("--muted"),font:{family:"DM Sans",size:10}}},
        y:{beginAtZero:true,grid:{display:!horizontal,color:gridColor},ticks:{color:cssColor("--muted"),font:{family:"DM Sans",size:10}}}
      }
    }
  });
}

function fillSelect(id,values){
  const select=$(id);
  values.forEach(value=>{
    const option=document.createElement("option");
    option.value=value;
    option.textContent=value;
    select.appendChild(option);
  });
}

async function loadFilters(){
  const response=await fetch("/api/filters");
  if(!response.ok)throw new Error("Could not load filters");
  const data=await response.json();
  fillSelect("industryFilter",data.industries);
  fillSelect("cityFilter",data.cities);
}

function dashboardQuery(){
  const params=new URLSearchParams();
  [["industry","industryFilter"],["city","cityFilter"]].forEach(([key,id])=>{if($(id).value)params.set(key,$(id).value)});
  return params;
}

function renderJobsTable(jobs){
  const body=$("jobsTable");
  body.replaceChildren();
  jobs.forEach(job=>{
    const row=document.createElement("tr");
    [job.title,job.company,job.industry||"Not specified",job.city||"Not specified"].forEach(value=>{
      const cell=document.createElement("td");
      cell.textContent=value||"Not specified";
      row.appendChild(cell);
    });
    const action=document.createElement("td");
    const link=document.createElement("a");
    link.href=job.url;
    link.target="_blank";
    link.rel="noopener";
    link.textContent="View ↗";
    action.appendChild(link);
    row.appendChild(action);
    body.appendChild(row);
  });
}

function renderJobCards(containerId,jobs,recommended=false){
  const container=$(containerId);
  if(!jobs.length){
    container.innerHTML='<p class="empty-state">No matching jobs found. Try a broader keyword.</p>';
    return;
  }
  container.innerHTML=jobs.map(job=>`<article class="job-card"><h3>${escapeHTML(job.title)}</h3><p>${escapeHTML(job.company)} · ${escapeHTML(job.city||"Location not specified")}</p><p>${escapeHTML(job.industry||"Industry not specified")}</p>${recommended?`<span class="match">${escapeHTML(job.match_score)}% match</span><p>${escapeHTML((job.reasons||[]).join(" · "))}</p>`:""}<a href="${escapeHTML(job.url)}" target="_blank" rel="noopener">View job ↗</a></article>`).join("");
}

async function loadDashboard(showMessage=false){
  $("refreshButton").disabled=true;
  try{
    const response=await fetch(`/api/dashboard?${dashboardQuery()}`);
    if(!response.ok)throw new Error("Dashboard API unavailable");
    const data=await response.json();
    const metrics=data.metrics;
    $("jobsMetric").textContent=number.format(metrics.jobs);
    $("companiesMetric").textContent=number.format(metrics.companies);
    $("industriesMetric").textContent=number.format(metrics.industries);
    $("citiesMetric").textContent=number.format(metrics.cities);
    $("salaryMetric").textContent=number.format(metrics.salary_disclosed||0);
    $("lastSync").textContent=data.last_sync?new Date(data.last_sync).toLocaleString():"Waiting for first sync";
    $("trendBasis").textContent=data.trend_basis||"Updating as dates become available";
    buildChart("industryChart","bar",data.industries.map(x=>x.industry),data.industries.map(x=>x.jobs),{horizontal:true});
    buildChart("locationChart","bar",data.locations.map(x=>x.city),data.locations.map(x=>x.jobs),{horizontal:true,showValues:true});
    buildChart("skillsChart","bar",data.skills.map(x=>x.skill),data.skills.map(x=>x.jobs),{horizontal:true});
    buildChart("educationChart","doughnut",data.education.map(x=>x.education_level),data.education.map(x=>x.jobs));
    buildChart("experienceChart","doughnut",data.experience.map(x=>x.experience_level),data.experience.map(x=>x.jobs));
    buildChart("salaryChart","bar",data.salary_bands.map(x=>x.band),data.salary_bands.map(x=>x.jobs));
    buildChart("trendChart","line",data.trend.map(x=>x.month),data.trend.map(x=>x.jobs));
    renderJobsTable(data.recent_jobs);
    if(showMessage)toast("Dashboard updated");
  }catch(error){toast(error.message)}finally{$("refreshButton").disabled=false}
}

async function submitGlobalSearch(event){
  event.preventDefault();
  const keyword=$("globalSearchInput").value.trim();
  if(!keyword){toast("Enter a job, skill or company");return}
  const params=dashboardQuery();
  params.set("q",keyword);
  $("searchResultTitle").textContent=`Results for “${keyword}”`;
  $("searchResults").innerHTML='<p class="empty-state">Searching…</p>';
  $("searchDrawer").hidden=false;
  const response=await fetch(`/api/search?${params}`);
  if(!response.ok){toast("Search is unavailable");return}
  const data=await response.json();
  renderJobCards("searchResults",data.jobs);
}

async function submitRecommendations(event){
  event.preventDefault();
  const payload={target:$("recommendTarget").value,skills:$("recommendSkills").value.split(",").map(x=>x.trim()).filter(Boolean),city:$("recommendCity").value||null,industry:$("industryFilter").value||null,limit:12};
  const response=await fetch("/api/recommendations",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  renderJobCards("recommendationResults",(await response.json()).recommendations,true);
}

async function submitSkillGap(event){
  event.preventDefault();
  const payload={target:$("gapTarget").value,skills:$("gapSkills").value.split(",").map(x=>x.trim()).filter(Boolean)};
  const response=await fetch("/api/skill-gap",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const data=await response.json();
  $("skillGapResults").className="gap-summary";
  $("skillGapResults").innerHTML=`<div class="coverage-score"><strong>${data.coverage}%</strong><span>skill coverage</span><small>${data.sample_jobs} jobs analyzed</small></div><div class="skill-list"><h3>Your matching skills</h3><div class="chips">${data.matched.map(x=>`<span class="chip">${escapeHTML(x)}</span>`).join("")||"None yet"}</div></div><div class="skill-list"><h3>Skills to develop</h3><div class="chips">${data.missing.map(x=>`<span class="chip missing">${escapeHTML(x)}</span>`).join("")||"No major gaps found"}</div></div>`;
}

async function submitDemand(event){
  event.preventDefault();
  const response=await fetch(`/api/demand-predictor?career=${encodeURIComponent($("demandCareer").value)}`);
  const data=await response.json();
  $("demandResults").innerHTML=`<div class="demand-score"><strong>${data.demand_score}</strong><div><b>${escapeHTML(data.outlook)}</b><br>${number.format(data.active_jobs)} active jobs · ${number.format(data.companies)} companies<br>${data.market_share}% of the selected market</div></div><small>${escapeHTML(data.confidence)}</small>`;
}

async function submitComparison(event){
  event.preventDefault();
  const industries=$("comparisonIndustries").value.split(",").map(x=>x.trim()).filter(Boolean).slice(0,4);
  if(industries.length<2){toast("Enter at least two industries");return}
  const response=await fetch("/api/comparison",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({industries})});
  const data=await response.json();
  $("comparisonResults").innerHTML=`<table class="comparison-table"><thead><tr><th>Industry</th><th>Jobs</th><th>Companies</th><th>Top skills</th></tr></thead><tbody>${data.comparison.map(item=>`<tr><td>${escapeHTML(item.industry)}</td><td>${number.format(item.jobs)}</td><td>${number.format(item.companies)}</td><td>${escapeHTML(item.top_skills.join(", ")||"Not enough data")}</td></tr>`).join("")}</tbody></table>`;
}

function setMobileFilters(open){
  $("filterSidebar").classList.toggle("open",open);
  $("filterOverlay").classList.toggle("open",open);
  document.body.style.overflow=open?"hidden":"";
}

function toggleDesktopFilters(){
  if(matchMedia("(max-width:900px)").matches){setMobileFilters(false);return}
  const collapsed=$("filterSidebar").classList.toggle("collapsed");
  document.body.classList.toggle("filters-collapsed",collapsed);
  localStorage.setItem("filtersCollapsed",collapsed);
}

function applyTheme(theme,refreshCharts=false){
  document.documentElement.dataset.theme=theme;
  $("themeToggle").textContent=theme==="dark"?"Sun":"Moon";
  $("themeToggle").setAttribute("aria-label",theme==="dark"?"Switch to light mode":"Switch to dark mode");
  if(refreshCharts)loadDashboard();
}

function initializeActiveNavigation(){
  const links=[...document.querySelectorAll(".topnav a")];
  if(links.length)links[0].classList.add("active");
  const sections=links.map(link=>document.querySelector(link.getAttribute("href"))).filter(Boolean);
  const observer=new IntersectionObserver(entries=>{
    const visible=entries.filter(entry=>entry.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
    if(!visible)return;
    links.forEach(link=>link.classList.toggle("active",link.getAttribute("href")===`#${visible.target.id}`));
  },{rootMargin:"-20% 0px -60% 0px",threshold:[0,.15,.4]});
  sections.forEach(section=>observer.observe(section));
}

document.addEventListener("DOMContentLoaded",async()=>{
  localStorage.removeItem("theme");
  applyTheme("light");
  try{await loadFilters();await loadDashboard()}catch(error){toast(error.message)}
  if(localStorage.getItem("filtersCollapsed")==="true"&&!matchMedia("(max-width:900px)").matches){
    $("filterSidebar").classList.add("collapsed");
    document.body.classList.add("filters-collapsed");
  }
  ["industryFilter","cityFilter"].forEach(id=>$(id).addEventListener("change",()=>loadDashboard()));
  $("refreshButton").addEventListener("click",()=>loadDashboard(true));
  $("clearFilters").addEventListener("click",()=>{["industryFilter","cityFilter"].forEach(id=>$(id).value="");loadDashboard()});
  $("collapseFilters").addEventListener("click",toggleDesktopFilters);
  $("mobileFilterButton").addEventListener("click",()=>setMobileFilters(true));
  $("filterOverlay").addEventListener("click",()=>setMobileFilters(false));
  $("themeToggle").addEventListener("click",()=>applyTheme(isDark()?"light":"dark",true));
  $("globalSearchForm").addEventListener("submit",submitGlobalSearch);
  $("closeSearch").addEventListener("click",()=>$("searchDrawer").hidden=true);
  $("recommendationForm").addEventListener("submit",submitRecommendations);
  $("skillGapForm").addEventListener("submit",submitSkillGap);
  $("demandForm").addEventListener("submit",submitDemand);
  $("comparisonForm").addEventListener("submit",submitComparison);
  document.addEventListener("keydown",event=>{if(event.key==="Escape"){setMobileFilters(false);$("searchDrawer").hidden=true}});
  initializeActiveNavigation();
  setInterval(()=>loadDashboard(),3*60*60*1000);
});
