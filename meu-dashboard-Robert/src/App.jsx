import { useState, useEffect } from "react";
import Papa from "papaparse";

const SEEDS = ["seed_10", "seed_42", "seed_99"];

const CURSOS = {
  1: "Des. Sistemas", 2: "Edificações", 3: "Eletrônica",
  4: "Eletrotécnica", 5: "Estradas", 6: "Mecânica", 7: "Química"
};

const DISCIPLINAS = {
  1: "Português", 2: "Matemática", 3: "História", 4: "Geografia",
  5: "Artes", 6: "Ed. Física", 7: "Química", 8: "Física",
  9: "Biologia", 10: "Filosofia", 11: "Sociologia", 12: "Inglês", 13: "Espanhol"
};

async function loadCSV(path) {
  const res = await fetch(path);
  const text = await res.text();
  return Papa.parse(text, { header: true, dynamicTyping: true }).data.filter(r => r && Object.keys(r).length > 1);
}

async function loadSeedData(seed) {
  const base = `/dados/${seed}`;
  const [estudantes, matriculas, resumo] = await Promise.all([
    loadCSV(`${base}/estudantes.csv`),
    loadCSV(`${base}/matriculas.csv`),
    loadCSV(`${base}/resumo_frequencia.csv`),
  ]);

  // métricas gerais
  const total = estudantes.length;
  const situacoes = { ATIVO: 0, TRANCADO: 0, EVADIDO: 0 };
  estudantes.forEach(e => { if (situacoes[e.situacao] !== undefined) situacoes[e.situacao]++; });

  const mediaFaltas = resumo.reduce((s, r) => s + r.faltas_totais, 0) / resumo.length;
  const taxaReprovacao = (resumo.filter(r => r.situacao_final === "REPROVADO").length / resumo.length) * 100;

  // faltas por curso
  const matMap = {};
  matriculas.forEach(m => { matMap[m.id_matricula_disciplina] = m.id_estudante; });

  const estMap = {};
  estudantes.forEach(e => { estMap[e.id_estudante] = e.id_curso; });

  const faltasCurso = {};
  const countCurso = {};
  resumo.forEach(r => {
    const estId = matMap[r.id_matricula_disciplina];
    const cursoId = estMap[estId];
    const nome = CURSOS[cursoId];
    if (!nome) return;
    faltasCurso[nome] = (faltasCurso[nome] || 0) + r.faltas_totais;
    countCurso[nome] = (countCurso[nome] || 0) + 1;
  });
  const mediaFaltasCurso = {};
  Object.keys(faltasCurso).forEach(c => {
    mediaFaltasCurso[c] = faltasCurso[c] / countCurso[c];
  });

  // faltas por disciplina
  const matDiscMap = {};
  matriculas.forEach(m => { matDiscMap[m.id_matricula_disciplina] = m.id_disciplina; });

  const faltasDisc = {};
  const countDisc = {};
  const reprovDisc = {};
  resumo.forEach(r => {
    const discId = matDiscMap[r.id_matricula_disciplina];
    const nome = DISCIPLINAS[discId];
    if (!nome) return;
    faltasDisc[nome] = (faltasDisc[nome] || 0) + r.faltas_totais;
    countDisc[nome] = (countDisc[nome] || 0) + 1;
    if (r.situacao_final === "REPROVADO") reprovDisc[nome] = (reprovDisc[nome] || 0) + 1;
  });
  const taxaReprovDisc = {};
  Object.keys(countDisc).forEach(d => {
    taxaReprovDisc[d] = (reprovDisc[d] || 0) / countDisc[d];
  });
  const sortedReprovDisc = Object.fromEntries(
    Object.entries(taxaReprovDisc).sort((a, b) => b[1] - a[1]).slice(0, 7)
  );
  const sortedFaltasDisc = Object.fromEntries(
    Object.entries(faltasDisc).map(([k, v]) => [k, v / countDisc[k]])
      .sort((a, b) => b[1] - a[1]).slice(0, 7)
  );

  // distribuição de faltas (histograma)
  const faixas = [0, 0, 0, 0, 0, 0, 0, 0, 0];
  resumo.forEach(r => {
    const f = r.faltas_totais;
    const i = f <= 5 ? 0 : f <= 10 ? 1 : f <= 15 ? 2 : f <= 20 ? 3 :
              f <= 25 ? 4 : f <= 30 ? 5 : f <= 35 ? 6 : f <= 40 ? 7 : 8;
    faixas[i]++;
  });

  // top risco
  const faltasPorAluno = {};
  const discPorAluno = {};
  const reprovPorAluno = {};
  resumo.forEach(r => {
    const estId = matMap[r.id_matricula_disciplina];
    if (!estId) return;
    faltasPorAluno[estId] = (faltasPorAluno[estId] || 0) + r.faltas_totais;
    discPorAluno[estId] = (discPorAluno[estId] || 0) + 1;
    if (r.situacao_final === "REPROVADO") reprovPorAluno[estId] = (reprovPorAluno[estId] || 0) + 1;
  });

  const topRisco = Object.keys(faltasPorAluno).map(id => {
    const disc = discPorAluno[id] || 1;
    const reprov = reprovPorAluno[id] || 0;
    const faltaMedia = faltasPorAluno[id] / disc;
    const score = ((reprov / disc) * 60 + (faltaMedia / 60) * 40) * 100;
    const est = estMap[id] ? CURSOS[estMap[id]] : "—";
    const nomeEst = estudantes.find(e => e.id_estudante === parseInt(id))?.nome || "—";
    return { id, nome: nomeEst, curso: est, reprovacoes: reprov, faltas_media: faltaMedia, score: Math.min(100, score) };
  }).sort((a, b) => b.score - a.score).slice(0, 20);

  return {
    estudantes: { total, ...situacoes },
    matriculas: matriculas.length,
    media_faltas: mediaFaltas,
    taxa_reprovacao: taxaReprovacao,
    situacao_estudantes: situacoes,
    faltas_por_curso: mediaFaltasCurso,
    disciplinas_reprovacao: sortedReprovDisc,
    faltas_por_disciplina: sortedFaltasDisc,
    dist_faltas: faixas,
    top_risco: topRisco,
  };
}

function AnimatedNumber({ value, decimals = 0, suffix = "" }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const end = parseFloat(value) || 0;
    const duration = 900;
    const steps = duration / 16;
    const step = (end - start) / steps;
    let frame = 0;
    const timer = setInterval(() => {
      frame++;
      start += step;
      if (frame >= steps) { setDisplay(end); clearInterval(timer); }
      else setDisplay(start);
    }, 16);
    return () => clearInterval(timer);
  }, [value]);
  return <span>{display.toFixed(decimals)}{suffix}</span>;
}

function BarChart({ data, color }) {
  const max = Math.max(...Object.values(data), 0.001);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {Object.entries(data).map(([label, val]) => (
        <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 110, fontSize: 11, color: "#94a3b8", textAlign: "right", flexShrink: 0 }}>{label}</div>
          <div style={{ flex: 1, background: "rgba(255,255,255,0.06)", borderRadius: 4, overflow: "hidden", height: 22 }}>
            <div style={{
              width: `${(val / max) * 100}%`, height: "100%", background: color,
              borderRadius: 4, transition: "width 0.8s cubic-bezier(.4,0,.2,1)",
              display: "flex", alignItems: "center", justifyContent: "flex-end", paddingRight: 6
            }}>
              <span style={{ fontSize: 10, color: "rgba(255,255,255,0.85)", fontWeight: 600 }}>
                {val < 1 ? `${(val * 100).toFixed(1)}%` : val.toFixed(1)}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

const BAR_LABELS = ["0-5","6-10","11-15","16-20","21-25","26-30","31-35","36-40","41+"];

function DistFaltas({ dist }) {
  const max = Math.max(...dist, 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 80 }}>
      {dist.map((v, i) => (
        <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
          <div style={{
            width: "100%", height: `${(v / max) * 68}px`,
            background: "linear-gradient(180deg, #38bdf8, #0ea5e9)",
            borderRadius: "3px 3px 0 0", transition: "height 0.8s cubic-bezier(.4,0,.2,1)"
          }} />
          <span style={{ fontSize: 9, color: "#64748b" }}>{BAR_LABELS[i]}</span>
        </div>
      ))}
    </div>
  );
}

function ScoreBadge({ score }) {
  const color = score > 85 ? "#ef4444" : score > 70 ? "#f97316" : "#eab308";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ width: 80, height: 8, background: "rgba(255,255,255,0.08)", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${score}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.9s" }} />
      </div>
      <span style={{ fontSize: 12, color, fontWeight: 700 }}>{score.toFixed(0)}</span>
    </div>
  );
}

export default function Dashboard() {
  const [seed, setSeed] = useState("seed_10");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setData(null);
    loadSeedData(seed).then(d => { setData(d); setLoading(false); });
  }, [seed]);

  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", fontFamily: "'DM Mono','Fira Code',monospace", padding: "0 0 40px" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@700;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        .card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; padding: 20px; transition: border-color 0.2s; }
        .card:hover { border-color: rgba(56,189,248,0.2); }
        .section-title { font-family: 'Syne',sans-serif; font-size: 13px; font-weight: 700; color: #38bdf8; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 14px; }
        .seed-btn { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #94a3b8; font-family: 'DM Mono',monospace; font-size: 13px; padding: 8px 18px; cursor: pointer; transition: all 0.2s; }
        .seed-btn:hover { border-color: #38bdf8; color: #e2e8f0; }
        .seed-btn.active { background: rgba(56,189,248,0.1); border-color: #38bdf8; color: #38bdf8; }
        .tag { display: inline-block; font-size: 10px; padding: 2px 8px; border-radius: 12px; font-weight: 500; }
        .tag-red { background: rgba(239,68,68,0.15); color: #fca5a5; }
        .tag-orange { background: rgba(249,115,22,0.15); color: #fdba74; }
      `}</style>

      {/* HEADER */}
      <div style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", padding: "24px 32px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 11, color: "#38bdf8", letterSpacing: 3, textTransform: "uppercase", marginBottom: 4 }}>Sistema Acadêmico · IFAL</div>
          <h1 style={{ fontFamily: "'Syne',sans-serif", fontSize: 22, fontWeight: 800, color: "#f1f5f9" }}>Frequência & Desempenho</h1>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {SEEDS.map(s => (
            <button key={s} className={`seed-btn${seed === s ? " active" : ""}`} onClick={() => setSeed(s)}>
              {s.replace("seed_", "Seed ")}
            </button>
          ))}
        </div>
      </div>

      {loading || !data ? (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "60vh", color: "#38bdf8", fontSize: 14 }}>
          Carregando dados da {seed}...
        </div>
      ) : (
        <div style={{ padding: "28px 32px", display: "flex", flexDirection: "column", gap: 24 }}>

          {/* MÉTRICAS */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16 }}>
            {[
              { label: "Estudantes", val: data.estudantes.total, decimals: 0, color: "#38bdf8" },
              { label: "Matrículas", val: data.matriculas, decimals: 0, color: "#818cf8" },
              { label: "Média de faltas", val: data.media_faltas, decimals: 1, color: "#f59e0b" },
              { label: "Taxa reprovação", val: data.taxa_reprovacao, decimals: 1, suffix: "%", color: "#f87171" },
            ].map(({ label, val, decimals, suffix, color }) => (
              <div key={label} className="card">
                <div style={{ fontSize: 11, color: "#64748b", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1.5 }}>{label}</div>
                <div style={{ fontFamily: "'Syne',sans-serif", fontSize: 32, fontWeight: 800, background: `linear-gradient(135deg,${color},${color}88)`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                  <AnimatedNumber value={val} decimals={decimals} suffix={suffix || ""} />
                </div>
              </div>
            ))}
          </div>

          {/* SITUAÇÃO + HISTOGRAMA */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: 16 }}>
            <div className="card">
              <div className="section-title">Situação dos Estudantes</div>
              {Object.entries(data.situacao_estudantes).map(([sit, n]) => {
                const colors = { ATIVO: "#34d399", TRANCADO: "#fbbf24", EVADIDO: "#f87171" };
                const pct = ((n / data.estudantes.total) * 100).toFixed(1);
                return (
                  <div key={sit} style={{ marginBottom: 14 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                      <span style={{ fontSize: 12, color: colors[sit], fontWeight: 500 }}>{sit}</span>
                      <span style={{ fontSize: 12, color: "#94a3b8" }}>{n} <span style={{ color: "#475569" }}>({pct}%)</span></span>
                    </div>
                    <div style={{ height: 6, background: "rgba(255,255,255,0.06)", borderRadius: 3, overflow: "hidden" }}>
                      <div style={{ width: `${pct}%`, height: "100%", background: colors[sit], borderRadius: 3, transition: "width 0.8s" }} />
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="card">
              <div className="section-title">Distribuição de Faltas por Matrícula</div>
              <DistFaltas dist={data.dist_faltas} />
              <div style={{ marginTop: 8, fontSize: 10, color: "#475569", textAlign: "center" }}>número de faltas (faixas)</div>
            </div>
          </div>

          {/* FALTAS POR CURSO + REPROVAÇÃO POR DISCIPLINA */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div className="card">
              <div className="section-title">Média de Faltas por Curso</div>
              <BarChart data={data.faltas_por_curso} color="linear-gradient(90deg,#0ea5e9,#38bdf8)" />
            </div>
            <div className="card">
              <div className="section-title">Taxa de Reprovação por Disciplina</div>
              <BarChart data={data.disciplinas_reprovacao} color="linear-gradient(90deg,#7c3aed,#a78bfa)" />
            </div>
          </div>

          {/* TOP RISCO */}
          <div className="card">
            <div className="section-title">Top 20 Alunos em Risco de Evasão</div>
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1.5fr 70px 90px 130px", gap: 12, padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", marginBottom: 4 }}>
              {["Nome", "Curso", "Reprov.", "Falta média", "Score"].map(h => (
                <span key={h} style={{ fontSize: 10, color: "#475569", textTransform: "uppercase", letterSpacing: 1.5 }}>{h}</span>
              ))}
            </div>
            <div style={{ maxHeight: 420, overflowY: "auto" }}>
              {data.top_risco.map((r, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "2fr 1.5fr 70px 90px 130px", gap: 12, alignItems: "center", padding: "10px 0", borderBottom: i < data.top_risco.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none" }}>
                  <span style={{ fontSize: 13, color: "#e2e8f0", fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{r.nome}</span>
                  <span style={{ fontSize: 11, color: "#64748b" }}>{r.curso}</span>
                  <span className={`tag ${r.reprovacoes >= 3 ? "tag-red" : "tag-orange"}`}>{r.reprovacoes}x</span>
                  <span style={{ fontSize: 12, color: "#94a3b8" }}>{r.faltas_media.toFixed(1)}</span>
                  <ScoreBadge score={r.score} />
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}