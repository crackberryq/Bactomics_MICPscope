"""Standalone, offline report with category summaries and inspectable evidence."""
import html


def esc(value):
    return html.escape(str(value if value is not None else '—'), quote=True)


def table(rows, columns):
    return '<div class="scroll"><table><thead><tr>' + ''.join(
        '<th scope="col">' + esc(c.replace('_', ' ')) + '</th>' for c in columns
    ) + '</tr></thead><tbody>' + ''.join(
        '<tr>' + ''.join('<td>' + esc(row.get(c, '—')) + '</td>' for c in columns) + '</tr>'
        for row in rows) + '</tbody></table></div>'


def render_report(result):
    proteins = result['proteins']
    catalog = result.get('knowledge_catalog', {})
    categories = catalog.get('categories', [{'id':'unassigned','name':'Protein properties','description':''}])
    sources = {s['id']:s for s in catalog.get('sources', [])}
    linked = sum(p.get('annotation_status') == 'catalog-linked annotation' for p in proteins)
    calculated = sum(p['status'] == 'calculated' for p in proteins)
    summary = []
    sections = []
    for cat in categories:
        rows = [p for p in proteins if p.get('category', 'unassigned') == cat['id']]
        summary.append(dict(category=cat['name'], annotation_records=len(rows),
                            interpretation='Header-derived associations' if rows else 'No assigned annotation; not an absence claim'))
        details = []
        for p in rows:
            refs = ' · '.join('<a href="' + esc(sources[r]['url']) + '">' + esc(r) + '</a>'
                              for r in p.get('references', []) if r in sources)
            metrics = table([p], ['length','status','aliphatic_index','theoretical_pi','gravy',
                                  'instability_index','molecular_weight_da','aromaticity'])
            details.append('<details class="protein"><summary><strong>' + esc(p.get('gene_name', 'unassigned')) +
                           '</strong> · ' + esc(p.get('protein_name', p.get('description'))) +
                           ' <span class="muted">[' + esc(p['protein_id']) + ']</span></summary>' +
                           '<p><b>Function:</b> ' + esc(p.get('function', 'Not supplied')) + '</p>' +
                           '<p><b>Annotation:</b> ' + esc(p.get('annotation_status', 'unassessed')) + ' · ' +
                           esc(p.get('annotation_basis', 'Not assessed')) + '</p>' + metrics +
                           '<p><b>Evidence level:</b> ' + esc(p.get('evidence_level', 'unassessed')) +
                           '<br><b>Literature scope:</b> ' + esc(p.get('literature_scope', 'Not assessed')) + '</p>' +
                           '<p><b>Descriptor interpretation:</b> ' + esc(p.get('instability_class', 'Not assessed')) +
                           '; ' + esc(p.get('hydropathy_class', 'Not assessed')) + '.</p>' +
                           '<p><b>Temperature:</b> ' + esc(p.get('temperature_indication', 'Undetermined')) +
                           '<br><b>Activity pH:</b> ' + esc(p.get('ph_indication', 'Undetermined')) + '</p>' +
                           '<p><b>Input annotation:</b> ' + esc(p.get('description', '')) + '<br><b>Quality:</b> ' +
                           esc(p.get('notes') or 'No residue flags; completeness remains unassessed') + '</p>' +
                           '<p><b>References:</b> ' + (refs or 'No catalog reference assigned') + '</p></details>')
        sections.append('<section class="card category"><h3>' + esc(cat['name']) + '</h3><p>' +
                        esc(cat['description']) + '</p>' + (''.join(details) or
                        '<p class="muted">No assigned records. This is not evidence that the function is absent.</p>') + '</section>')
    evidence_columns = ['sample_id','subject_id','evidence_type','property','value','unit','source','notes']
    evidence = table(result['evidence'], evidence_columns) if result['evidence'] else '<p>No measured or literature observations supplied.</p>'
    bibliography = ''.join('<li id="ref-' + esc(s['id']) + '"><a href="' + esc(s['url']) + '">' +
                           esc(s['title']) + '</a> · ' + esc(s['type']) + '</li>' for s in sources.values())
    prov = result['provenance']
    version = result.get('software_version', 'unknown')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MICP Scope · ''' + esc(result['sample_id']) + '''</title>
<style>
:root{font-family:system-ui,sans-serif;color:#173443;background:#eef3f5}*{box-sizing:border-box}
body{max-width:1320px;margin:auto;padding:28px}header{background:#123c49;color:white;padding:30px;border-radius:16px}
h1{font-size:36px;margin:8px 0}h2{margin-top:32px}.eyebrow{letter-spacing:3px;color:#88e3ca}
.card{background:white;border:1px solid #ccdce2;border-radius:12px;padding:20px;margin-top:18px}
.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:12px;border-bottom:1px solid #dbe5e9;vertical-align:top}th{background:#e4f1ee}
.muted{color:#526974}a{color:#066e70}nav{display:flex;gap:18px;flex-wrap:wrap;margin:22px 0}
.stats{display:flex;gap:16px;flex-wrap:wrap}.stats span{flex:1;min-width:160px;padding:16px;background:#e4f1ee;border-radius:8px}
.protein{border-top:1px solid #ccdce2;padding:16px 0;overflow-wrap:anywhere}summary{cursor:pointer;line-height:1.6}
input{font:inherit;padding:12px;width:100%;border:1px solid #75949d;border-radius:8px}button{font:inherit;padding:9px 16px;margin:10px 8px 0 0;cursor:pointer}
[hidden]{display:none!important}li{margin:12px 0}p{line-height:1.6}code{overflow-wrap:anywhere}
@media(max-width:600px){body{padding:12px}.card,header{padding:16px}h1{font-size:28px}}
@media print{body{padding:0;background:white}input,button{display:none}.scroll{overflow:visible}details{break-inside:avoid}}
</style></head><body><header><div class="eyebrow">BACTOMICS / MICP SCOPE</div><h1>''' + esc(result['sample_id']) + '''</h1>
<p>Gene context, protein properties & application evidence · ''' + esc(version) + '''</p></header>
<nav aria-label="Report sections"><a href="#overview">Overview</a><a href="#proteins">Genes & proteins</a><a href="#conditions">Temperature & pH</a><a href="#evidence">Evidence</a><a href="#methods">Methods & sources</a></nav>
<section class="card" id="overview"><h2>Overview</h2><div class="stats"><span><b>''' + str(len(proteins)) + '''</b> protein records</span><span><b>''' + str(linked) + '''</b> catalog-linked annotations</span><span><b>''' + str(calculated) + '''</b> calculated descriptors</span></div>
<p>''' + esc(result.get('limitations', '')) + '</p>' + table(summary, ['category','annotation_records','interpretation']) + '''</section>
<section id="proteins"><h2>Genes & proteins</h2><p>Names and functions come from supplied annotation and a cited catalog. These are not sequence-confirmed hits. Expand a record for descriptors, context and references.</p>
<label for="protein-search">Find a gene, protein, function or identifier</label><input id="protein-search" type="search" placeholder="Search annotations…">
<button type="button" id="expand">Expand visible records</button><button type="button" id="collapse">Collapse records</button>
<p id="search-status" role="status" aria-live="polite"></p>''' + ''.join(sections) + '''</section>
<section class="card" id="conditions"><h2>Temperature & pH indications</h2>
<p><b>Best operating temperature: undetermined. Best operating pH: undetermined.</b></p>
<p>Aliphatic index describes side-chain composition and has a reported association with thermostability of globular proteins. The reviewed method supplies no universal cutoff that converts this index into a temperature or temperature range. Thermostability and activity optimum are different measurements.</p>
<p>Theoretical pI estimates the charge-neutral point; it is not an enzyme's activity optimum. GRAVY describes mean hydropathy. The instability-index threshold is a sequence heuristic: below 40 is the stable class, above 40 the unstable class, and exactly 40 is left unclassified here. None establishes formulation stability or shelf life.</p>
<p>Source-linked measured temperature and pH observations can be recorded below with protein/strain identity, assay endpoint and preparation context in notes. Conflicting observations remain visible; values are not averaged or transferred to a different sample.</p></section>
<section class="card" id="evidence"><h2>Application evidence</h2><p>Supplied observations are displayed as recorded and have not been independently verified. A literature value is not automatically applicable to this sample.</p>''' + evidence + '''</section>
<section class="card" id="methods"><h2>Methods & sources</h2>
<p>Biopython ''' + esc(prov.get('biopython_version', 'unknown')) + ''' ProteinAnalysis calculates mass, theoretical pI, GRAVY, instability and aromaticity. Aliphatic index = 100 × [A + 2.9V + 3.9(I + L)] / sequence length, using residue counts. One terminal stop is removed; unsupported residues are flagged without descriptor calculation.</p>
<p>Annotation labels are matched conservatively to catalog gene symbols or product phrases. Ambiguous matches stay unresolved. No homology search, pathway-completeness assessment or gene-expression analysis is performed. Generic function annotations are retained even without a catalog match.</p>
<p>Catalog ''' + esc(catalog.get('catalog_version', 'not recorded')) + ' · ' + esc(catalog.get('scope', '')) + '''</p>
<p>Coverage gaps: ''' + esc('; '.join(catalog.get('coverage_gaps', []))) + '''.</p><ul>''' + bibliography + '''</ul>
<p>Input SHA-256: <code>''' + esc(prov['input_sha256']) + '''</code><br>Catalog SHA-256: <code>''' + esc(prov.get('catalog_sha256', 'not recorded')) + '''</code><br>Generated: ''' + esc(prov['created_utc']) + '''</p></section>
<script type="text/javascript">
const search=document.getElementById('protein-search');
const records=[...document.querySelectorAll('.protein')];
function filter(){const q=search.value.toLocaleLowerCase().trim();let n=0;records.forEach(r=>{r.hidden=!r.textContent.toLocaleLowerCase().includes(q);if(!r.hidden)n++});document.getElementById('search-status').textContent=n+' of '+records.length+' records shown';}
search.addEventListener('input',filter);filter();
document.getElementById('expand').addEventListener('click',()=>records.filter(r=>!r.hidden).forEach(r=>r.open=true));
document.getElementById('collapse').addEventListener('click',()=>records.forEach(r=>r.open=false));
</script></body></html>'''
