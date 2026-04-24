
import React, { useState, useEffect } from 'react';
import { 
  FileText, Upload, Download, CheckCircle, User, Car, ArrowRight,
  Loader2, AlertCircle, FileSearch, FolderOpen, DollarSign,
  ExternalLink, ShieldCheck, FileType, Image as ImageIcon
} from 'lucide-react';

const apiKey = ""; 

const DOC_TYPES = [
  { id: 'permiso', label: 'Permiso de Circulación', required: true },
  { id: 'ficha', label: 'Ficha Técnica', required: true },
  { id: 'dni_comprador', label: 'DNI Comprador', required: true },
  { id: 'dni_vendedor', label: 'DNI Vendedor', required: true },
  { id: 'contrato', label: 'Contrato Compra-Venta', required: true }
];

const BASE_TEMPLATES = [
  { id: 'mandato', name: '1-FIRMAR AMBOS MANDATO.pdf' },
  { id: 'dgt', name: '1-FIRMAR AMBOS NOTIFICACION TRAFICO DGT.pdf' },
  { id: '001mp', name: '1-FIRMAR COMPRADOR MANDATO modelo 001MP (NUEVO).pdf' }
];

export default function App() {
  const [files, setFiles] = useState({});
  const [loading, setLoading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [provision, setProvision] = useState("150");
  const [status, setStatus] = useState({ type: '', msg: '' });

  const handleFileChange = (id, e) => {
    const file = e.target.files[0];
    if (file) setFiles(prev => ({ ...prev, [id]: file }));
  };

  const showStatus = (type, msg) => {
    setStatus({ type, msg });
    setTimeout(() => setStatus({ type: '', msg: '' }), 8000);
  };

  const processOCR = async () => {
    if (!files['dni_comprador'] || !files['permiso']) {
      showStatus('error', 'Sube el DNI del Comprador y el Permiso para el análisis.');
      return;
    }
    setLoading(true);
    try {
      const toBase64 = (file) => new Promise((r) => {
        const reader = new FileReader();
        reader.onload = () => r(reader.result.split(',')[1]);
        reader.readAsDataURL(file);
      });

      const [dniB64, permB64] = await Promise.all([toBase64(files['dni_comprador']), toBase64(files['permiso'])]);

      const prompt = `Analiza DNI y Permiso de Circulación. Extrae:
      - Del DNI: Nombre y Apellidos (separados) y NIF.
      - Del Permiso: Matrícula (A), Fecha Matr. (B), Marca (D.1), Modelo (D.3).
      IMPORTANTE: Devuelve solo el JSON puro.
      JSON: { "nombre": "", "apellidos": "", "dni_numero": "", "matricula": "", "marca_modelo": "", "fecha_matriculacion": "" }`;

      const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }, 
            { inlineData: { mimeType: files['dni_comprador'].type, data: dniB64 } },
            { inlineData: { mimeType: files['permiso'].type, data: permB64 } }
          ]}]
        })
      });

      const res = await resp.json();
      const rawText = res.candidates[0].content.parts[0].text.replace(/```json|```/g, '').trim();
      setExtractedData(JSON.parse(rawText));
      showStatus('success', 'Datos extraídos correctamente. Ipar Artekaritza (Correduría) lista.');
    } catch (e) {
      showStatus('error', 'Error en el escaneo IA. Intenta con fotos más claras.');
    } finally { setLoading(false); }
  };

  const loadScripts = async () => {
    const scripts = [
      "https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js",
      "https://unpkg.com/docx@7.1.0/build/index.js"
    ];
    for (const src of scripts) {
      if (!document.querySelector(`script[src="${src}"]`)) {
        const s = document.createElement('script');
        s.src = src;
        document.head.appendChild(s);
        await new Promise(r => s.onload = r);
      }
    }
  };

  const generateWordDoc = async () => {
    const docx = window.docx;
    const permisoImg = files['permiso'];
    
    // Convertimos la imagen a un Uint8Array de forma segura
    const arrayBuffer = await permisoImg.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);

    // Determinar extensión correcta para docx.js
    const imgType = permisoImg.type.includes('png') ? docx.ImageRun.PNG : docx.ImageRun.JPG;

    const doc = new docx.Document({
      sections: [{
        properties: {
            page: {
                margin: { top: 720, right: 720, bottom: 720, left: 720 }
            }
        },
        children: [
          // Logo e Identidad (Header visual)
          new docx.Paragraph({
            children: [
              new docx.TextRun({ text: "IPAR", bold: true, size: 48, color: "0f172a" }),
              new docx.TextRun({ text: " ARTEKARITZA", bold: true, size: 48, color: "2563eb" }),
            ],
            alignment: docx.AlignmentType.CENTER,
          }),
          new docx.Paragraph({ 
            children: [new docx.TextRun({ text: "ASEGUROAK - CORREDURÍA DE SEGUROS", size: 24, bold: true, color: "64748b" })],
            alignment: docx.AlignmentType.CENTER 
          }),
          new docx.Paragraph({ 
            children: [new docx.TextRun({ text: "Gestión Especializada de Vehículos", size: 18, italic: true })],
            alignment: docx.AlignmentType.CENTER,
            spacing: { after: 400 }
          }),
          
          new docx.Paragraph({
            children: [new docx.TextRun({ text: "RECIBÍ DE DOCUMENTACIÓN ORIGINAL", bold: true, underline: {}, size: 28 })],
            alignment: docx.AlignmentType.CENTER,
            spacing: { after: 400 }
          }),

          new docx.Paragraph({
            children: [
              new docx.TextRun({ text: `IPAR ARTEKARITZA S.L., en su condición de Correduría de Seguros, recibe de D/Dña. `, size: 24 }),
              new docx.TextRun({ text: `${extractedData.nombre} ${extractedData.apellidos}`.toUpperCase(), bold: true, size: 24 }),
              new docx.TextRun({ text: `, con D.N.I. `, size: 24 }),
              new docx.TextRun({ text: extractedData.dni_numero, bold: true, size: 24 }),
              new docx.TextRun({ text: `, el documento original correspondiente al PERMISO DE CIRCULACIÓN para proceder a la tramitación de la transferencia del vehículo:`, size: 24 }),
            ],
            spacing: { line: 360, after: 300 }
          }),

          new docx.Table({
            width: { size: 100, type: docx.WidthType.PERCENTAGE },
            rows: [
                new docx.TableRow({
                    children: [
                        new docx.TableCell({ 
                            children: [new docx.Paragraph({ children: [new docx.TextRun({ text: "MATRÍCULA:", bold: true, size: 24 })] })],
                            shading: { fill: "f1f5f9" },
                            margins: { top: 100, bottom: 100, left: 100 }
                        }),
                        new docx.TableCell({ 
                            children: [new docx.Paragraph({ children: [new docx.TextRun({ text: extractedData.matricula.toUpperCase(), bold: true, size: 28, color: "2563eb" })] })],
                            margins: { top: 100, bottom: 100, left: 100 }
                        }),
                    ]
                }),
                new docx.TableRow({
                    children: [
                        new docx.TableCell({ 
                            children: [new docx.Paragraph({ children: [new docx.TextRun({ text: "MARCA / MODELO:", bold: true, size: 24 })] })],
                            shading: { fill: "f1f5f9" },
                            margins: { top: 100, bottom: 100, left: 100 }
                        }),
                        new docx.TableCell({ 
                            children: [new docx.Paragraph({ children: [new docx.TextRun({ text: extractedData.marca_modelo.toUpperCase(), size: 24 })] })],
                            margins: { top: 100, bottom: 100, left: 100 }
                        }),
                    ]
                })
            ],
            spacing: { after: 400 }
          }),

          new docx.Paragraph({
            children: [
                new docx.TextRun({ text: `Asimismo, se hace entrega de la cantidad de `, size: 24 }),
                new docx.TextRun({ text: `${provision} €`, bold: true, size: 26, color: "059669" }),
                new docx.TextRun({ text: ` en concepto de provisión de fondos para los gastos derivados de la gestión.`, size: 24 })
            ],
            spacing: { after: 600 }
          }),

          new docx.Paragraph({ 
            text: `Errenteria, a ${new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })}`, 
            alignment: docx.AlignmentType.RIGHT,
            spacing: { after: 400 }
          }),

          new docx.Paragraph({
            children: [new docx.TextRun({ text: "Firma y Sello de la Correduría:", size: 18, italic: true, color: "64748b" })],
            spacing: { after: 1200 }
          }),

          new docx.Paragraph({
            children: [new docx.TextRun({ text: "ANEXO: COPIA DEL PERMISO DE CIRCULACIÓN ESCANEADO", bold: true, size: 20, color: "2563eb" })],
            spacing: { before: 400, after: 200 },
            border: { bottom: { color: "2563eb", space: 1, value: "single", size: 12 } }
          }),

          // Inserción de la imagen mejorada
          new docx.Paragraph({
            children: [
              new docx.ImageRun({
                data: uint8Array,
                transformation: { 
                    width: 500, // Ajustado para margen estándar A4
                    height: 350 
                },
                type: imgType
              })
            ],
            alignment: docx.AlignmentType.CENTER,
            spacing: { before: 200 }
          })
        ],
      }],
    });

    return await docx.Packer.toBlob(doc);
  };

  const handleDownloadAll = async () => {
    setLoading(true);
    try {
      await loadScripts();
      const zip = new window.JSZip();
      const matriculaLimpia = extractedData?.matricula.replace(/ /g, '_') || 'Ipar';
      const folderName = `Tramite_${matriculaLimpia}`;
      const mainFolder = zip.folder(folderName);

      // Generar Word con imagen
      const wordBlob = await generateWordDoc();
      mainFolder.file(`Recibi_Ipar_Artekaritza_${matriculaLimpia}.docx`, wordBlob);

      // Archivos originales
      const origFolder = mainFolder.folder("01_Documentacion_Original");
      for (const [id, file] of Object.entries(files)) {
        const name = DOC_TYPES.find(d => d.id === id).label.replace(/ /g, '_');
        origFolder.file(`${name}.${file.name.split('.').pop()}`, file);
      }

      // Impresos
      const signFolder = mainFolder.folder("02_Impresos_Firma");
      BASE_TEMPLATES.forEach(t => signFolder.file(t.name, "Plantilla oficial para firma física."));

      const content = await zip.generateAsync({ type: "blob" });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(content);
      link.download = `${folderName}.zip`;
      link.click();
      showStatus('success', 'Expediente generado con éxito. Imagen del permiso incluida.');
    } catch (e) {
      console.error(e);
      showStatus('error', 'Error al procesar el Word. Intenta con una imagen JPG estándar.');
    } finally { setLoading(false); }
  };

  const allReady = extractedData && files['permiso'];

  return (
    <div className="min-h-screen bg-slate-100 p-4 md:p-10 font-sans text-slate-900">
      <div className="max-w-6xl mx-auto">
        <header className="mb-10 flex flex-col md:flex-row justify-between items-center bg-white p-8 rounded-3xl shadow-xl border-b-4 border-blue-600 gap-6">
          <div className="flex items-center gap-5">
            <div className="bg-blue-600 p-4 rounded-2xl text-white shadow-lg shadow-blue-200">
              <ShieldCheck size={40} />
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight">Ipar Artekaritza</h1>
              <p className="text-blue-600 font-bold uppercase tracking-widest text-xs">Correduría de Seguros • Errenteria</p>
            </div>
          </div>
          <button 
            onClick={() => window.open("https://www7.gipuzkoa.net/vehiculos/defaultc.asp")} 
            className="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white rounded-xl font-bold hover:bg-blue-700 transition-all shadow-md"
          >
            <ExternalLink size={18} /> Valorador Hacienda
          </button>
        </header>

        {status.msg && (
          <div className={`mb-8 p-5 rounded-2xl border-l-8 flex items-center gap-4 shadow-md animate-in slide-in-from-top-4 ${status.type === 'error' ? 'bg-red-50 border-red-500 text-red-800' : 'bg-emerald-50 border-emerald-500 text-emerald-800'}`}>
            {status.type === 'error' ? <AlertCircle size={24}/> : <CheckCircle size={24}/>} 
            <span className="font-bold text-lg">{status.msg}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          <div className="lg:col-span-7 space-y-8">
            <section className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200">
              <h2 className="text-xl font-black mb-6 flex items-center gap-3 text-slate-700">
                <Upload size={24} className="text-blue-600" /> Documentación
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {DOC_TYPES.map(doc => (
                  <label key={doc.id} className={`flex flex-col p-5 rounded-2xl border-2 border-dashed cursor-pointer transition-all ${files[doc.id] ? 'bg-blue-50 border-blue-500 shadow-inner' : 'bg-slate-50 border-slate-200 hover:border-blue-400'}`}>
                    <input type="file" className="hidden" onChange={(e) => handleFileChange(doc.id, e)} />
                    <span className="text-[10px] font-black text-slate-400 uppercase mb-2 tracking-widest">{doc.label}</span>
                    <span className="text-sm font-bold truncate flex items-center gap-2">
                        {files[doc.id] ? <><CheckCircle size={14} className="text-blue-600"/> {files[doc.id].name}</> : "Añadir archivo..."}
                    </span>
                  </label>
                ))}
              </div>
            </section>

            <section className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200">
              <div className="flex justify-between items-center mb-8">
                <h2 className="text-xl font-black flex items-center gap-3 text-slate-700">
                    <FileSearch size={24} className="text-purple-600" /> Extracción IA
                </h2>
                <button 
                    onClick={processOCR} 
                    disabled={loading || !files['permiso']} 
                    className="bg-purple-600 text-white px-8 py-3 rounded-2xl font-black hover:bg-purple-700 disabled:opacity-40 flex items-center gap-3 shadow-lg shadow-purple-100"
                >
                  {loading ? <Loader2 className="animate-spin" /> : <ArrowRight />} Escanear
                </button>
              </div>
              <div className="grid grid-cols-2 gap-6 bg-slate-50 p-6 rounded-2xl border border-slate-100">
                 <DataField label="Nombre y Apellidos" value={`${extractedData?.nombre || ''} ${extractedData?.apellidos || ''}`} />
                 <DataField label="NIF Comprador" value={extractedData?.dni_numero} />
                 <DataField label="Matrícula" value={extractedData?.matricula} />
                 <DataField label="Marca/Modelo" value={extractedData?.marca_modelo} />
                 <div className="col-span-2 pt-4 border-t border-slate-200">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Provisión de Fondos</label>
                    <div className="relative">
                        <input type="number" value={provision} onChange={(e) => setProvision(e.target.value)} className="w-full bg-white border-2 border-slate-200 p-3 rounded-xl font-black text-blue-700 text-xl outline-none focus:border-blue-500 transition-all" />
                        <span className="absolute right-4 top-3 text-2xl font-bold text-slate-300">€</span>
                    </div>
                 </div>
              </div>
            </section>
          </div>

          <div className="lg:col-span-5">
             <div className="bg-gradient-to-br from-blue-700 to-blue-900 p-10 rounded-[2.5rem] text-white shadow-2xl sticky top-10">
                <div className="flex items-center gap-4 mb-8">
                    <div className="bg-white/20 p-3 rounded-xl"><FileType size={32} /></div>
                    <h2 className="text-2xl font-black">Exportar a Word</h2>
                </div>
                
                <div className="space-y-6 mb-10 text-blue-50">
                    <div className="flex items-start gap-4">
                        <div className="mt-1"><CheckCircle size={18} className="text-emerald-400" /></div>
                        <p className="text-sm">Identidad: **Correduría de Seguros**.</p>
                    </div>
                    <div className="flex items-start gap-4">
                        <div className="mt-1"><ImageIcon size={18} className="text-emerald-400" /></div>
                        <p className="text-sm">Imagen del **Permiso** visible al final del documento.</p>
                    </div>
                    <div className="flex items-start gap-4">
                        <div className="mt-1"><FolderOpen size={18} className="text-emerald-400" /></div>
                        <p className="text-sm">Carpeta organizada con documentos originales e impresos.</p>
                    </div>
                </div>

                <button 
                    onClick={handleDownloadAll} 
                    disabled={loading || !allReady} 
                    className="w-full bg-white text-blue-900 py-5 rounded-2xl font-black text-xl hover:bg-blue-50 transition-all shadow-2xl flex items-center justify-center gap-4 group disabled:opacity-30"
                >
                  {loading ? <Loader2 className="animate-spin" /> : <Download size={28} className="group-hover:translate-y-1 transition-transform" />}
                  GENERAR EXPEDIENTE
                </button>
                
                {!allReady && (
                    <p className="text-center mt-6 text-blue-300 text-xs font-bold uppercase tracking-widest animate-pulse">
                        Escanea los documentos para activar
                    </p>
                )}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DataField({ label, value }) {
  return (
    <div className="flex flex-col bg-white p-3 rounded-xl border border-slate-200">
      <span className="text-[9px] font-black text-slate-400 uppercase tracking-tighter mb-1">{label}</span>
      <span className="text-md font-bold text-slate-800 truncate">{value || '---'}</span>
    </div>
  );
}
