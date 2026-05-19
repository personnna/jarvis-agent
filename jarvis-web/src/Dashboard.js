import React, { useState, useEffect } from 'react';

const HTTP_URL = 'https://jarvis-ai.xyz';

function WeatherWidget({ text }) {
  const tempMatch = text?.match(/(\d+)°C/);
  const temp = tempMatch ? tempMatch[1] : '--';
  const isRain = text?.toLowerCase().includes('rain');
  const isSun = text?.toLowerCase().includes('sun') || text?.toLowerCase().includes('clear');
  const icon = isRain ? '🌧️' : isSun ? '☀️' : '⛅';
  const shortDesc = text?.split('.')[0] + '.' || '';

  return (
    <div className="dash-widget">
      <div className="dash-widget-label">⚡ ENVIRONMENT</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '8px 0 4px' }}>
        <span style={{ fontSize: 28 }}>{icon}</span>
        <span style={{ fontSize: 48, fontWeight: 200, color: '#fff', letterSpacing: -2, lineHeight: 1 }}>{temp}°</span>
      </div>
      <div style={{ fontSize: 11, color: '#4A9EE0', letterSpacing: '0.08em', marginBottom: 6 }}>📍 Mestre, Italy</div>
      <div style={{ fontSize: 11, color: '#556677', lineHeight: 1.5 }}>{shortDesc}</div>
    </div>
  );
}


function NextUpWidget({ calendarLines }) {
  const next = calendarLines[0];
  if (!next) return null;
  const parts = next.replace('•', '').trim().split('—');
  const time = parts[0]?.trim();
  const title = parts[1]?.trim();
  const hasTravel = title?.toLowerCase().includes('bus') || 
                    title?.toLowerCase().includes('train') || 
                    title?.toLowerCase().includes('milano') || 
                    title?.toLowerCase().includes('venezia');
  
  const destination = title?.includes('Milano') ? 'Milan,Italy' : 
                      title?.includes('Venezia') ? 'Venice,Italy' : 
                      'Mestre,Italy';
  
  const mapsUrl = `https://www.google.com/maps/dir/Mestre,Italy/${destination}`;
  const osmUrl = `https://www.openstreetmap.org/export/embed.html?bbox=12.1,45.4,12.4,45.6&layer=mapnik&marker=45.4964,12.2369`;

  return (
    <div className="dash-widget">
      <div className="dash-widget-label">🚀 NEXT UP</div>
      <div style={{ fontSize: 11, color: '#4A9EE0', marginBottom: 4, letterSpacing: '0.06em' }}>{time}</div>
      <div style={{ fontSize: 15, color: '#fff', marginBottom: 12, lineHeight: 1.4 }}>{title}</div>

      <iframe
        title="map"
        width="100%"
        height="130"
        style={{ 
          border: 'none', 
          borderRadius: 6, 
          marginBottom: 8,
          filter: 'invert(90%) hue-rotate(180deg) saturate(0.8)',
          opacity: 0.7
        }}
        src={osmUrl}
        loading="lazy"
      />

        {hasTravel && ( <a
          
            href={mapsUrl}
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'block',
              textAlign: 'center',
              padding: '8px',
              borderRadius: 6,
              border: '1px solid rgba(74,158,224,0.3)',
              color: '#4A9EE0',
              fontSize: 11,
              letterSpacing: '0.12em',
              textDecoration: 'none',
              background: 'rgba(74,158,224,0.05)',
              marginBottom: 12,
              marginTop: 8
            }}
          >
            ↗ NAVIGATE TO {destination.split(',')[0].toUpperCase()}
          </a>
        )}

      <div style={{ borderTop: '1px solid rgba(74,158,224,0.08)', marginTop: 4, paddingTop: 10 }}>
        <div className="dash-widget-label" style={{ marginBottom: 8 }}>🔔 UPCOMING</div>
        {calendarLines.slice(1, 4).map((e, i) => {
          const p = e.replace('•', '').trim().split('—');
          return (
            <div key={i} style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 10, color: '#4A9EE0', letterSpacing: '0.05em' }}>{p[0]?.trim()}</div>
              <div style={{ fontSize: 11, color: '#778899' }}>{p[1]?.trim()}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ScheduleWidget({ calendarLines }) {
  return (
    <div className="dash-widget">
      <div className="dash-widget-label">📡 SCHEDULE</div>
      <div style={{ fontSize: 10, color: '#2A5A8A', letterSpacing: '0.1em', marginBottom: 10 }}>{calendarLines.length} EVENTS</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {calendarLines.map((e, i) => {
          const parts = e.replace('•', '').trim().split('—');
          const time = parts[0]?.trim();
          const title = parts[1]?.trim();
          return (
            <div key={i} style={{
              display: 'flex', gap: 10, padding: '7px 10px',
              borderRadius: 4, border: '1px solid rgba(255,255,255,0.04)',
              background: 'rgba(255,255,255,0.02)', animation: `fadeIn 0.3s ease ${i * 0.05}s forwards`, opacity: 0
            }}>
              <span style={{ fontSize: 10, color: '#4A9EE0', minWidth: 140, letterSpacing: '0.03em' }}>{time}</span>
              <span style={{ fontSize: 11, color: '#ccc' }}>{title}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function JiraWidget({ jiraLines, onToggleDone }) {
  return (
    <div className="dash-widget">
      <div className="dash-widget-label">🎯 ACTIVE TASKS</div>
      <div style={{ fontSize: 10, color: '#2A5A8A', letterSpacing: '0.1em', marginBottom: 10 }}>{jiraLines.length} OPEN</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {jiraLines.map((t, i) => {
          const parts = t.replace('•', '').trim().split(':');
          const id = parts[0]?.trim();
          const rest = parts.slice(1).join(':').trim();
          const titleParts = rest.split('[');
          const title = titleParts[0]?.trim();
          const jiraUrl = `https://kadyelyer.atlassian.net/browse/${id}`;
          return (
            <a key={i} href={jiraUrl} target="_blank" rel="noreferrer" style={{
              display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px',
              borderRadius: 4, borderLeft: '2px solid #0052CC',
              background: 'rgba(0,82,204,0.05)', textDecoration: 'none',
              animation: `fadeIn 0.3s ease ${i * 0.05}s forwards`, opacity: 0
            }}>
              <span style={{ fontSize: 10, color: '#0052CC', minWidth: 52 }}>{id}</span>
              <span style={{ fontSize: 11, color: '#ccc', flex: 1 }}>{title}</span>
              <span style={{ fontSize: 9, color: '#444', padding: '2px 6px', border: '1px solid #333', borderRadius: 3 }}>TO DO</span>
            </a>
          );
        })}
      </div>
    </div>
  );
}

export default function Dashboard({ onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    setRefreshing(true);
    try {
      const r = await fetch(`${HTTP_URL}/dashboard`);
      const d = await r.json();
      setData(d);
      setLastUpdated(new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }));
    } catch (e) { console.error(e); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#020408', gap: 16 }}>
      <div className="dash-loading-ring" />
      <div style={{ fontSize: 11, color: '#4A9EE0', letterSpacing: '0.2em' }}>INITIALIZING JARVIS</div>
    </div>
  );

  const calendarLines = data?.calendar?.split('\n').filter(l => l.startsWith('•')) || [];
  const jiraLines = data?.jira?.split('\n').filter(l => l.startsWith('•')) || [];

  return (
    <div className="dashboard">
      <div className="dash-header">
        <div>
          <div className="dash-logo">JARVIS</div>
          <div className="dash-logo-sub">LIFE DASHBOARD</div>
        </div>
        <div className="dash-header-right">
          <button onClick={fetchData} className={`dash-refresh ${refreshing ? 'spinning' : ''}`}>↻</button>
          {lastUpdated && <div className="dash-updated">Updated {lastUpdated}</div>}
          <button onClick={onBack} className="dash-back">← JARVIS</button>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', padding: '20px 24px 12px', borderBottom: '1px solid rgba(74,158,224,0.08)' }}>
        <div>
          <div style={{ fontSize: 64, fontWeight: 200, color: '#fff', letterSpacing: -2, lineHeight: 1 }}>{data?.time}</div>
          <div style={{ fontSize: 11, color: '#4A9EE0', letterSpacing: '0.15em', marginTop: 6, textTransform: 'uppercase' }}>{data?.date}</div>
        </div>
        <div style={{ width: 56, height: 56, borderRadius: '50%', border: '1px solid rgba(74,158,224,0.3)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 3 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 8px #22c55e' }} />
          <div style={{ fontSize: 8, color: '#22c55e', letterSpacing: '0.1em' }}>ONLINE</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '0.7fr 1fr 1.3fr 1.3fr', gap: 12, padding: '16px 24px', alignItems: 'start' }}>
        <WeatherWidget text={data?.weather} />
        <NextUpWidget calendarLines={calendarLines} />
        <ScheduleWidget calendarLines={calendarLines} />
        <JiraWidget jiraLines={jiraLines} />
      </div>

      {data?.ai_tip && (
        <div style={{
          margin: '0 24px 24px',
          padding: '14px 16px',
          borderRadius: 8,
          border: '1px solid rgba(74,158,224,0.15)',
          background: 'rgba(74,158,224,0.03)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: 1,
            background: 'linear-gradient(90deg, transparent, rgba(74,158,224,0.4), transparent)'
          }} />
          <div className="dash-widget-label" style={{marginBottom: 8}}>🤖 JARVIS RECOMMENDS</div>
          <div style={{ fontSize: 13, color: '#aabbcc', lineHeight: 1.6, fontStyle: 'italic' }}>
            "{data.ai_tip}"
          </div>
        </div>
      )}
    </div>

    
  );
}