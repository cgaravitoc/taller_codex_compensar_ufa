import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import os from 'node:os';
const runtime=process.env.ARTIFACT_NODE_ROOT || path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node');
const require=createRequire(path.join(runtime,'package.json'));
const {Workbook, SpreadsheetFile}=require('@oai/artifact-tool');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const raw=JSON.parse(await fs.readFile(path.join(root,'tmp/clientes.json'),'utf8'));
const wb=Workbook.create();
const ws=wb.worksheets.add('Clientes');
const values=raw.data.map(row=>row.map((v,i)=>i===1?new Date(v):v));
ws.getRange('A1:M5001').values=[raw.columns,...values];
ws.showGridLines=false;
ws.getRange('A1:M5001').format.font={name:'Arial',size:10};
ws.getRange('A1:M1').format={fill:'#18354A',font:{bold:true,color:'#FFFFFF'},rowHeight:42,wrapText:true};
ws.getRange('A1:M5001').format.columnWidth=20;
ws.getRange('F1:G5001').format.columnWidth=23;
ws.getRange('H1:M5001').format.columnWidth=27;
ws.getRange('B2:B5001').setNumberFormat('yyyy-mm-dd');
ws.getRange('H2:H5001').setNumberFormat('#,##0');
ws.getRange('L2:L5001').setNumberFormat('#,##0');
ws.tables.add('A1:M5001',true,'ClientesSinteticos');
ws.freezePanes.freezeRows(1);
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Clientes!A1:M4',tableMaxRows:4,tableMaxCols:13,maxChars:2000})).ndjson);
const xlsx=await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(path.join(root,'data/clientes.xlsx'));
try {await fs.rename(path.join(root,'data/clientes.xlsx.inspect.ndjson'),path.join(root,'qa/clientes.xlsx.inspect.ndjson'));}
catch(e) {if(e.code!=='ENOENT') throw e;}
for(const [name,range] of [['clientes_inicio','A1:G8'],['clientes_perfil','H1:M8']]){
 const blob=await wb.render({sheetName:'Clientes',range,scale:1.5,format:'png'});
 await fs.writeFile(path.join(root,'qa',`${name}.png`),new Uint8Array(await blob.arrayBuffer()));
}
