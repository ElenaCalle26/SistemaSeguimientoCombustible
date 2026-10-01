import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertTriangle,
  Building2,
  Car,
  CheckCircle2,
  FileText,
  LogOut,
  Plus,
  ShieldCheck,
  Save,
  Radio,
  Fuel,
  RefreshCw,
  User,
  AlertCircle,
  Clock,
  Sparkles
} from 'lucide-react';
import './styles.css';

const API = import.meta.env.VITE_API_URL || '';

const asArray = value => {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.items)) return value.items;
  return [];
};

async function request(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = 'Bearer ' + token;
  }

  const response = await fetch(`${API}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = 'No se pudo completar la solicitud';
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // keep the generic message
    }
    throw new Error(detail);
  }

  return response.json();
}

const fmt = value => new Intl.NumberFormat('es-BO', { maximumFractionDigits: 0 }).format(value);
const dateTimeLocal = value => {
  const date = value ? new Date(value) : new Date();
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
};

function Login({ onLogin }) {
  const [email, setEmail] = useState('josephlfamx@gmail.com');
  const [password, setPassword] = useState('Cambiar123!');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async event => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const token = await request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem('token', token.access_token);
      await onLogin();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login">
      <section className="login-hero">
        <div className="brand">
          <div className="brand-icon"><Activity size={20} /></div>
          <div>
            <span>FuelTrack</span>
            <span className="brand-sub">Sistema de Trazabilidad</span>
          </div>
        </div>

        <h1>
          <span>TRAZABILIDAD Y</span>
          <span>MONITOREO DE</span>
          <span>COMBUSTIBLE</span>
        </h1>

        <p>
          Control de carguíos en tiempo real, detección de patrones con tecnología RFID/NFC y análisis multicriterio para estaciones de servicio.
        </p>

        <div className="login-demo-group">
          <p>Accesos Rápidos (Demostración):</p>
          <div className="demo-list">
            <button
              type="button"
              className="demo-chip"
              onClick={() => { setEmail('josephlfamx@gmail.com'); setPassword('Cambiar123!'); }}
            >
              👑 Admin (Joseph)
            </button>
            <button
              type="button"
              className="demo-chip"
              onClick={() => { setEmail('fernandomolloa@gmail.com'); setPassword('Supervisor123!'); }}
            >
              🛡️ Supervisor (Fernando)
            </button>
            <button
              type="button"
              className="demo-chip"
              onClick={() => { setEmail('operador.cristo@fueltrack.local'); setPassword('Operador123!'); }}
            >
              ⛽ Op. Cristo Autogas
            </button>
            <button
              type="button"
              className="demo-chip"
              onClick={() => { setEmail('operador.gasmay@fueltrack.local'); setPassword('Operador123!'); }}
            >
              ⛽ Op. Gas-May
            </button>
            <button
              type="button"
              className="demo-chip"
              onClick={() => { setEmail('operador.volcan@fueltrack.local'); setPassword('Operador123!'); }}
            >
              ⛽ Op. Volcán
            </button>
          </div>
        </div>
      </section>

      <section className="login-form-wrap">
        <h2>Iniciar Sesión</h2>
        <p>Ingresa tus credenciales autorizadas del sistema</p>

        {error && (
          <div className="error-banner">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={submit}>
          <label>
            Correo Electrónico
            <input
              value={email}
              onChange={event => setEmail(event.target.value)}
              type="email"
              autoComplete="username"
              required
              placeholder="tu-correo@gmail.com"
            />
          </label>

          <label>
            Contraseña
            <input
              value={password}
              onChange={event => setPassword(event.target.value)}
              type="password"
              required
            />
          </label>

          <button className="primary" type="submit" disabled={loading}>
            {loading ? 'Verificando...' : 'Acceder al Sistema'}
          </button>
        </form>
      </section>
    </main>
  );
}

const Card = ({ icon: Icon, label, value, accent }) => (
  <article className={`card ${accent || ''}`}>
    <div>
      <span>{label}</span>
      <strong>{fmt(value || 0)}</strong>
    </div>
    <div className="card-icon-wrap">
      <Icon size={22} />
    </div>
  </article>
);

function App() {
  const [user, setUser] = useState(null);
  const [data, setData] = useState(null);
  const [ops, setOps] = useState([]);
  const [cases, setCases] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [stations, setStations] = useState([]);
  const [institutions, setInstitutions] = useState([]);
  const [fuelTypes, setFuelTypes] = useState([]);
  const [view, setView] = useState('Resumen');
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState('');

  // Estado del panel RFID
  const [rfidState, setRfidState] = useState('idle'); // idle | scanning | found | unknown | error
  const [rfidResult, setRfidResult] = useState(null);
  const [rfidInput, setRfidInput] = useState('');
  const [lastRfidTime, setLastRfidTime] = useState(Date.now());

  const [operationForm, setOperationForm] = useState({
    vehicle_id: '',
    station_id: '',
    fuel_type_id: '',
    quantity_liters: '',
    occurred_at: dateTimeLocal(),
    notes: '',
  });
  const [vehicleForm, setVehicleForm] = useState({
    plate: '',
    vehicle_type: '',
    internal_code: '',
  });
  const [stationForm, setStationForm] = useState({
    institution_id: '',
    code: '',
    name: '',
    municipality: 'La Paz',
    address: '',
  });
  const [caseDrafts, setCaseDrafts] = useState({});
  const [vehicleSummary, setVehicleSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState('');
  const [vehicleSearch, setVehicleSearch] = useState('');

  const canManageCatalogs = user?.role === 'ADMIN' || user?.role === 'SUPERVISOR';
  const canManageStations = user?.role === 'ADMIN' || user?.role === 'SUPERVISOR';
  const canCreateOperations = user?.role === 'OPERATOR';
  const canReviewCases = user?.role === 'ADMIN' || user?.role === 'SUPERVISOR';

  const navItems = useMemo(() => {
    const items = ['Resumen', 'Operaciones'];
    if (canManageCatalogs) {
      items.push('Vehículos', 'Estaciones');
    }
    if (canReviewCases) {
      items.push('Casos de revisión', 'Alertas', 'Analítica');
    }
    return items;
  }, [canManageCatalogs, canReviewCases]);

  async function loadApp() {
    setLoading(true);
    setError('');
    try {
      const me = await request('/api/auth/me');
      const requests = [
        request('/api/dashboard'),
        request('/api/operations?page_size=100'),
        request('/api/vehicles?page_size=100'),
        request('/api/stations'),
        request('/api/fuel-types'),
      ];

      if (me.role === 'ADMIN' || me.role === 'SUPERVISOR') {
        requests.push(request('/api/cases?page_size=100'), request('/api/alerts?page_size=100'));
      } else {
        requests.push(Promise.resolve([]), Promise.resolve([]));
      }
      if (me.role === 'ADMIN') requests.push(request('/api/institutions'));

      const [dashboard, operationsPage, vehiclesPage, stationsData, fuelTypesData, casesPage, alertsPage, institutionsData] = await Promise.all(requests);
      const operations = asArray(operationsPage);
      const vehiclesData = asArray(vehiclesPage);
      const stationsList = asArray(stationsData);
      const fuelList = asArray(fuelTypesData);
      const casesData = asArray(casesPage);
      const alertsData = asArray(alertsPage);
      const institutionsList = asArray(institutionsData);

      setUser(me);
      setData({ ...dashboard, recent_operations: asArray(dashboard?.recent_operations) });
      setOps(operations);
      setVehicles(vehiclesData);
      setStations(stationsList);
      setFuelTypes(fuelList);
      setInstitutions(institutionsList);
      setStationForm(prev => ({ ...prev, institution_id: me.institution_id || prev.institution_id }));
      setCases(casesData);
      setAlerts(alertsData);

      setOperationForm(prev => ({
        ...prev,
        vehicle_id: prev.vehicle_id || vehiclesData[0]?.id || '',
        station_id: me.fixed_station_id || stationsList[0]?.id || '',
        fuel_type_id: prev.fuel_type_id || fuelList[0]?.id || '',
      }));
      setCaseDrafts(
        Object.fromEntries(
          (casesData || []).map(item => [
            item.id,
            {
              status: item.status,
              conclusion: item.conclusion || '',
            },
          ]),
        ),
      );
    } catch (err) {
      localStorage.removeItem('token');
      setUser(null);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (localStorage.getItem('token')) {
      loadApp();
    }
  }, []);

  // Polling para actualizaciones automáticas desde el hardware ESP32
  useEffect(() => {
    if (!user || user.role !== 'OPERATOR' || view !== 'Operaciones') return;

    const interval = setInterval(async () => {
      try {
        const data = await request(`/api/rfid/latest?since=${lastRfidTime}`);
        if (data && data.has_new) {
          setLastRfidTime(data.timestamp);
          setRfidResult(data);
          if (data.status === 'UNKNOWN') {
            setRfidState('unknown');
          } else {
            setRfidState('found');
            if (data.status === 'AUTHORIZED' && data.vehicle) {
              const matchedVehicle = vehicles.find(v => v.plate === data.vehicle.plate);
              if (matchedVehicle) {
                setOperationForm(prev => ({ ...prev, vehicle_id: matchedVehicle.id }));
              }
            }
          }
        }
      } catch (err) {
        // Ignorar de forma segura errores de red en segundo plano
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [user, view, lastRfidTime, vehicles]);

  const refresh = async () => {
    await loadApp();
  };

  const showToast = (msg) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(''), 4000);
  };

  const simulateRfidRead = async (uid) => {
    setRfidState('scanning');
    setRfidResult(null);
    try {
      const stationCode = stations.find(s => s.id === user.fixed_station_id)?.code || 'EST-001';
      const result = await request('/api/rfid/read', {
        method: 'POST',
        body: JSON.stringify({
          rfid_uid: uid,
          station_code: stationCode,
          device_id: 'SIMULACION-WEB',
        }),
      });
      setRfidResult(result);
      setRfidState(result.status === 'UNKNOWN' ? 'unknown' : 'found');
      if (result.vehicle && result.status === 'AUTHORIZED') {
        const v = vehicles.find(x => x.plate === result.vehicle.plate);
        if (v) setOperationForm(prev => ({ ...prev, vehicle_id: v.id }));
      }
    } catch (err) {
      setRfidState('error');
      setError(err.message);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setData(null);
    setOps([]);
    setCases([]);
    setAlerts([]);
    setVehicles([]);
    setStations([]);
    setFuelTypes([]);
    setView('Resumen');
    setVehicleSummary(null);
    setVehicleSearch('');
  };

  const createOperation = async event => {
    event.preventDefault();
    setBusy('operation');
    setError('');
    try {
      await request('/api/operations', {
        method: 'POST',
        body: JSON.stringify({
          vehicle_id: operationForm.vehicle_id,
          station_id: user.fixed_station_id || operationForm.station_id,
          fuel_type_id: Number(operationForm.fuel_type_id),
          quantity_liters: Number(operationForm.quantity_liters),
          occurred_at: new Date(operationForm.occurred_at).toISOString(),
          notes: operationForm.notes || null,
        }),
      });
      await refresh();
      showToast('¡Operación de carguío guardada exitosamente!');
      setView('Resumen');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  };

  const createVehicle = async event => {
    event.preventDefault();
    setBusy('vehicle');
    setError('');
    try {
      await request('/api/vehicles', {
        method: 'POST',
        body: JSON.stringify(vehicleForm),
      });
      setVehicleForm({ plate: '', vehicle_type: '', internal_code: '' });
      await refresh();
      showToast('Vehículo registrado correctamente en el padrón');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  };

  const createStation = async event => {
    event.preventDefault();
    setBusy('station');
    setError('');
    try {
      await request('/api/stations', {
        method: 'POST',
        body: JSON.stringify(stationForm),
      });
      setStationForm({ institution_id: user.institution_id || '', code: '', name: '', municipality: 'La Paz', address: '' });
      await refresh();
      showToast('Estación de servicio agregada al sistema');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  };

  const saveCase = async caseId => {
    setBusy(caseId);
    setError('');
    try {
      const draft = caseDrafts[caseId];
      await request(`/api/cases/${caseId}`, {
        method: 'PATCH',
        body: JSON.stringify({
          status: draft.status,
          conclusion: draft.conclusion || null,
        }),
      });
      await refresh();
      showToast('Caso de revisión actualizado');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  };

  const downloadActivityPdf = async () => {
    setBusy('activity-pdf');
    setError('');
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/api/cases-report.pdf`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('No se pudo generar el reporte PDF');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'fueltrack-actividad.pdf';
      link.click();
      URL.revokeObjectURL(url);
      showToast('Reporte PDF descargado con éxito');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  };

  const fetchVehicleSummary = async (vehicleId) => {
    if (vehicleSummary?.vehicle?.id === vehicleId) {
      setVehicleSummary(null);
      return;
    }
    setLoadingSummary(vehicleId);
    try {
      const summary = await request(`/api/vehicles/${vehicleId}/summary`);
      summary.vehicle.id = vehicleId;
      setVehicleSummary(summary);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingSummary('');
    }
  };

  const alertSeverityData = useMemo(() => {
    const counts = alerts.reduce((result, item) => {
      result[item.severity] = (result[item.severity] || 0) + 1;
      return result;
    }, {});
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [alerts]);

  const alertCodeData = useMemo(() => {
    const counts = alerts.reduce((result, item) => {
      result[item.code] = (result[item.code] || 0) + 1;
      return result;
    }, {});
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [alerts]);

  const caseStatusData = useMemo(() => {
    const counts = cases.reduce((result, item) => {
      result[item.status] = (result[item.status] || 0) + 1;
      return result;
    }, {});
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [cases]);

  const stationOperationsData = useMemo(() => {
    const counts = ops.reduce((result, item) => {
      result[item.station] = (result[item.station] || 0) + 1;
      return result;
    }, {});
    return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8);
  }, [ops]);

  const chartTotal = alertSeverityData.reduce((sum, [, value]) => sum + value, 0);
  const chartGradient = alertSeverityData.length
    ? (() => {
        let start = 0;
        const colorsBySeverity = { CRITICAL: '#dc2626', WARNING: '#d97706', INFO: '#2563eb' };
        return alertSeverityData.map(([label, value]) => {
          const end = start + (value / chartTotal) * 360;
          const segment = `${colorsBySeverity[label] || '#64748b'} ${start}deg ${end}deg`;
          start = end;
          return segment;
        }).join(', ');
      })()
    : '#e2e8f0 0deg 360deg';

  if (!user) {
    return <Login onLogin={loadApp} />;
  }

  const getNavIcon = (item) => {
    switch (item) {
      case 'Resumen': return <Activity size={18} />;
      case 'Operaciones': return <Fuel size={18} />;
      case 'Vehículos': return <Car size={18} />;
      case 'Estaciones': return <Building2 size={18} />;
      case 'Casos de revisión': return <ShieldCheck size={18} />;
      case 'Alertas': return <AlertTriangle size={18} />;
      case 'Analítica': return <Sparkles size={18} />;
      default: return <Activity size={18} />;
    }
  };

  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <div className="brand-icon"><Activity size={18} /></div>
          <div>
            <span>FuelTrack</span>
            <span className="brand-sub">Sistema Institucional</span>
          </div>
        </div>

        <nav>
          {navItems.map(item => (
            <button
              className={view === item ? 'active' : ''}
              onClick={() => { setView(item); setError(''); }}
              key={item}
            >
              {getNavIcon(item)}
              <span>{item}</span>
              {item === 'Casos de revisión' && cases.filter(c => c.status === 'PENDING').length > 0 && (
                <span className="nav-badge">{cases.filter(c => c.status === 'PENDING').length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="profile">
          <div className="avatar">{user.full_name?.[0] || 'U'}</div>
          <div className="user-info">
            <span className="user-name">{user.full_name}</span>
            <span className="user-role">{user.role}</span>
          </div>
          <button className="logout-btn" title="Cerrar sesión" onClick={logout}>
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <main className="content">
        <header>
          <div>
            <span className="eyebrow">PANEL DE CONTROL INSTITUCIONAL</span>
            <h1>{view}</h1>
            <p className="muted">
              {user.role === 'OPERATOR'
                ? `Terminal de Estación de Servicio asignada: ${stations.find(s => s.id === user.fixed_station_id)?.name || 'E/S Cristo Autogas'}`
                : 'Supervisión centralizada, bitácora de auditoría y análisis de reglas de despacho.'}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button className="secondary" type="button" onClick={refresh} title="Actualizar datos">
              <RefreshCw size={15} /> Actualizar
            </button>
            {view === 'Operaciones' && canCreateOperations && (
              <button className="primary" onClick={() => document.getElementById('operation-form')?.scrollIntoView({ behavior: 'smooth' })}>
                <Plus size={16} /> Registrar Operación
              </button>
            )}
          </div>
        </header>

        {loading && <p className="muted">Cargando información del servidor...</p>}
        {error && (
          <div className="error-banner">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}
        {successMsg && (
          <div className="success-banner">
            <CheckCircle2 size={18} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* ── Vista Resumen ────────────────────────────────────────────── */}
        {view === 'Resumen' && data && (
          <>
            <section className="cards">
              <Card icon={Activity} label="Operaciones últimas 24h" value={data.operations_today} />
              <Card icon={AlertTriangle} label="Casos por revisar" value={data.pending_cases} accent={data.pending_cases > 0 ? 'warning' : ''} />
              <Card icon={Car} label="Vehículos activos" value={data.active_vehicles} />
              <Card icon={Building2} label="Estaciones activas" value={data.active_stations} />
            </section>

            <section className="panel">
              <div className="panelhead">
                <div>
                  <h2>Actividad Reciente</h2>
                  <p>Últimos registros de abastecimiento ingresados al sistema.</p>
                </div>
                <ShieldCheck size={20} color="#10b981" />
              </div>
              <Operations rows={data.recent_operations} />
            </section>
          </>
        )}

        {/* ── Vista Operaciones ────────────────────────────────────────── */}
        {view === 'Operaciones' && (
          <>
            <section className="panel">
              <div className="panelhead">
                <div>
                  <h2>Historial de Operaciones</h2>
                  <p>Registro ordenado cronológicamente con volúmenes y estaciones.</p>
                </div>
              </div>
              <Operations rows={ops} />
            </section>

            {/* Módulo Lector RFID para Operadores */}
            {canCreateOperations && (
              <section className="panel rfid-panel">
                <div className="panelhead">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Radio size={20} color="var(--primary)" />
                    <div>
                      <h2>Recepción de Hardware RFID / NFC</h2>
                      <p>Lecturas en vivo desde el sensor ESP32 / PN532 o simulación rápida.</p>
                    </div>
                  </div>
                  <span className={`rfid-status ${rfidState}`}>
                    <span className="rfid-status-pulse" />
                    {rfidState === 'idle'     && 'Esperando aproximación de tarjeta...'}
                    {rfidState === 'scanning' && 'Leyendo UID del sensor...'}
                    {rfidState === 'found'    && (rfidResult?.message || 'Vehículo Identificado')}
                    {rfidState === 'unknown'  && 'Tarjeta o UID Desconocido'}
                    {rfidState === 'error'    && 'Error en la lectura'}
                  </span>
                </div>

                <div className="rfid-input-row">
                  <input
                    placeholder="UID RFID — ej: D0:9B:E2:5F"
                    value={rfidInput}
                    onChange={e => setRfidInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && rfidInput.trim() && simulateRfidRead(rfidInput)}
                  />
                  <button
                    className="primary"
                    type="button"
                    onClick={() => simulateRfidRead(rfidInput)}
                    disabled={rfidState === 'scanning' || !rfidInput.trim()}
                  >
                    Consultar UID
                  </button>
                  <button
                    className="secondary"
                    type="button"
                    onClick={() => { setRfidState('idle'); setRfidResult(null); setRfidInput(''); }}
                  >
                    Limpiar
                  </button>
                </div>

                <div className="rfid-quick">
                  <span>Chips de Demostración:</span>
                  {[
                    { uid: 'D0:9B:E2:5F', label: 'SYN-001 (Llavero Azul)' },
                    { uid: 'D0:89:22:5F', label: 'SYN-002 (Tarjeta Blanca)' },
                    { uid: 'CC:21:6B:06', label: 'SYN-003 (Vehículo C)' },
                    { uid: '1C:F8:6B:06', label: 'Chip No Registrado (Chuto)' },
                  ].map(({ uid, label }) => (
                    <button
                      key={uid}
                      className="demo-chip"
                      type="button"
                      onClick={() => { setRfidInput(uid); simulateRfidRead(uid); }}
                    >
                      💳 {label}
                    </button>
                  ))}
                </div>

                {rfidResult && rfidResult.vehicle && (
                  <div className="rfid-card-wrapper">
                    <div className={`rfid-card rfid-${rfidResult.status.toLowerCase()}`}>
                      <div className="rfid-card-header">
                        <span className="rfid-plate-badge">{rfidResult.vehicle.plate}</span>
                        <span className={`tag ${rfidResult.status}`}>{rfidResult.status}</span>
                        <span className="muted" style={{ fontWeight: 600 }}>{rfidResult.message}</span>
                      </div>

                      <dl className="rfid-details">
                        <dt>UID Físico</dt>       <dd style={{ fontFamily: 'var(--font-mono)' }}>{rfidResult.vehicle.rfid_uid}</dd>
                        <dt>Tipo de Vehículo</dt> <dd>{rfidResult.vehicle.vehicle_type || '—'}</dd>
                        <dt>Marca y Modelo</dt>   <dd>{rfidResult.vehicle.synthetic_make_model || '—'} ({rfidResult.vehicle.synthetic_year || '—'})</dd>
                        <dt>Padrón Oficial</dt>   <dd><span className="tag AUTHORIZED">{rfidResult.vehicle.is_active ? 'Habilitado' : 'Inhabilitado'}</span></dd>
                        <dt>Combustibles</dt>     <dd>{rfidResult.allowed_fuels?.map(f => f.name).join(', ') || 'Todos'}</dd>
                      </dl>

                      {rfidResult.alerts?.length > 0 && (
                        <div className="rfid-alerts">
                          {rfidResult.alerts.map((a, i) => (
                            <span key={i} className={`tag ${a.severity}`}>⚠️ {a.code}: {a.message}</span>
                          ))}
                        </div>
                      )}

                      {rfidResult.recent_operations?.length > 0 && (
                        <div className="rfid-history">
                          <b>Historial de Despachos Recientes (Últimas 24h):</b>
                          <ul>
                            {rfidResult.recent_operations.map((op, i) => (
                              <li key={i}>
                                🕒 {new Date(op.occurred_at).toLocaleString('es-BO')} — <b>{op.station}</b> ({op.fuel_type}, {op.quantity_liters} L)
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {rfidResult && !rfidResult.vehicle && (
                  <div className="rfid-card-wrapper">
                    <div className="error-banner">
                      <AlertTriangle size={18} />
                      <span><b>Alerta:</b> El UID escaneado no coincide con ningún vehículo registrado legalmente en el padrón sintético.</span>
                    </div>
                  </div>
                )}
              </section>
            )}

            {/* Formulario de Registro de Operación */}
            {canCreateOperations && (
              <section className="panel" id="operation-form">
                <div className="panelhead">
                  <div>
                    <h2>Registrar Operación de Abastecimiento</h2>
                    <p>Completa los datos de la carga para ingresar la transacción a la bitácora.</p>
                  </div>
                  <Fuel size={20} color="var(--primary)" />
                </div>
                <form className="form-grid" onSubmit={createOperation}>
                  <label>
                    Vehículo Autorizado
                    <select
                      value={operationForm.vehicle_id}
                      onChange={event => setOperationForm(prev => ({ ...prev, vehicle_id: event.target.value }))}
                      required
                    >
                      {vehicles.map(vehicle => (
                        <option key={vehicle.id} value={vehicle.id}>
                          {vehicle.plate} — {vehicle.vehicle_type || 'Vehículo'} (UID: {vehicle.rfid_uid || 'Sin RFID'})
                        </option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Estación de Servicio (Asignada a la Sesión)
                    <input
                      value={stations.find(station => station.id === user.fixed_station_id)?.name || 'Estación en sesión'}
                      disabled
                    />
                  </label>

                  <label>
                    Tipo de Combustible
                    <select
                      value={operationForm.fuel_type_id}
                      onChange={event => setOperationForm(prev => ({ ...prev, fuel_type_id: event.target.value }))}
                      required
                    >
                      {fuelTypes.map(fuel => (
                        <option key={fuel.id} value={fuel.id}>
                          {fuel.name} ({fuel.code})
                        </option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Cantidad en Litros
                    <input
                      type="number"
                      min="0.1"
                      step="0.01"
                      required
                      placeholder="Ej. 45.5"
                      value={operationForm.quantity_liters}
                      onChange={event => setOperationForm(prev => ({ ...prev, quantity_liters: event.target.value }))}
                    />
                  </label>

                  <label>
                    Fecha y Hora de la Operación
                    <input
                      type="datetime-local"
                      required
                      value={operationForm.occurred_at}
                      onChange={event => setOperationForm(prev => ({ ...prev, occurred_at: event.target.value }))}
                    />
                  </label>

                  <label className="full-width">
                    Notas / Observaciones
                    <textarea
                      rows="2"
                      placeholder="Observaciones adicionales (opcional)..."
                      value={operationForm.notes}
                      onChange={event => setOperationForm(prev => ({ ...prev, notes: event.target.value }))}
                    />
                  </label>

                  <div className="section-actions full-width">
                    <button className="primary" type="submit" disabled={busy === 'operation'}>
                      <Save size={16} /> {busy === 'operation' ? 'Guardando Transacción...' : 'Guardar Operación'}
                    </button>
                  </div>
                </form>
              </section>
            )}
            {!canCreateOperations && <p className="muted" style={{ padding: '16px' }}>Tu rol tiene acceso de solo lectura para operaciones.</p>}
          </>
        )}

        {/* ── Vista Vehículos ─────────────────────────────────────────── */}
        {view === 'Vehículos' && canManageCatalogs && (
          <section className="panel">
            <div className="panelhead">
              <div>
                <h2>Padrón de Vehículos Habilitados</h2>
                <p>Lista oficial de placas, códigos internos y UID de chips RFID vinculados.</p>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input 
                  type="text" 
                  placeholder="Buscar por placa..." 
                  value={vehicleSearch} 
                  onChange={e => setVehicleSearch(e.target.value)} 
                  style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                />
              </div>
            </div>
            
            {vehicleSummary && (
              <div className="rfid-card-wrapper" style={{ margin: '0 20px 20px 20px' }}>
                <div className="panelhead" style={{ borderBottom: 'none', padding: '0 0 10px 0' }}>
                  <h3 style={{ margin: 0 }}>Detalle Operativo del Vehículo</h3>
                  <button className="secondary" onClick={() => setVehicleSummary(null)}>Cerrar Detalle</button>
                </div>
                <div className={`rfid-card rfid-${vehicleSummary.status.toLowerCase()}`}>
                  <div className="rfid-card-header">
                    <span className="rfid-plate-badge">{vehicleSummary.vehicle.plate}</span>
                    <span className={`tag ${vehicleSummary.status}`}>{vehicleSummary.status}</span>
                    <span className="muted" style={{ fontWeight: 600 }}>{vehicleSummary.message}</span>
                  </div>

                  <dl className="rfid-details">
                    <dt>UID Físico</dt>       <dd style={{ fontFamily: 'var(--font-mono)' }}>{vehicleSummary.vehicle.rfid_uid || 'Sin asignar'}</dd>
                    <dt>Tipo de Vehículo</dt> <dd>{vehicleSummary.vehicle.vehicle_type || '—'}</dd>
                    <dt>Marca y Modelo</dt>   <dd>{vehicleSummary.vehicle.synthetic_make_model || '—'} ({vehicleSummary.vehicle.synthetic_year || '—'})</dd>
                    <dt>Padrón Oficial</dt>   <dd><span className="tag AUTHORIZED">{vehicleSummary.vehicle.is_active ? 'Habilitado' : 'Inhabilitado'}</span></dd>
                  </dl>

                  {vehicleSummary.alerts?.length > 0 && (
                    <div className="rfid-alerts">
                      {vehicleSummary.alerts.map((a, i) => (
                        <span key={i} className={`tag ${a.severity}`}>⚠️ {a.code}: {a.message}</span>
                      ))}
                    </div>
                  )}

                  {vehicleSummary.recent_operations?.length > 0 && (
                    <div className="rfid-history">
                      <b>Historial de Despachos Recientes:</b>
                      <ul>
                        {vehicleSummary.recent_operations.map((op, i) => (
                          <li key={i}>
                            🕒 {new Date(op.occurred_at).toLocaleString('es-BO')} — <b>{op.station}</b> ({op.fuel_type}, {op.quantity_liters} L)
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {(!vehicleSummary.recent_operations || vehicleSummary.recent_operations.length === 0) && (
                    <div className="rfid-history">
                      <p className="muted">No hay operaciones recientes registradas para este vehículo.</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Placa</th>
                    <th>UID RFID</th>
                    <th>Tipo</th>
                    <th>Estado Padrón</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {vehicles.filter(v => v.plate.toLowerCase().includes(vehicleSearch.toLowerCase())).map(vehicle => (
                    <tr key={vehicle.id} style={{ background: vehicleSummary?.vehicle?.id === vehicle.id ? '#f8fafc' : 'transparent' }}>
                      <td><b style={{ fontFamily: 'var(--font-mono)' }}>{vehicle.plate}</b></td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{vehicle.rfid_uid || <span className="muted">Sin asignar</span>}</td>
                      <td>{vehicle.vehicle_type || '—'}</td>
                      <td>
                        <span className={`tag ${vehicle.is_active ? 'AUTHORIZED' : 'RESTRICTED'}`}>
                          {vehicle.is_active ? 'ACTIVO' : 'INACTIVO'}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="secondary" 
                          onClick={() => fetchVehicleSummary(vehicle.id)}
                          disabled={loadingSummary === vehicle.id}
                        >
                          {loadingSummary === vehicle.id ? 'Cargando...' : (vehicleSummary?.vehicle?.id === vehicle.id ? 'Ocultar' : 'Ver Historial')}
                        </button>
                      </td>
                    </tr>
                  ))}
                  {!vehicles.length && (
                    <tr>
                      <td colSpan="5" className="empty">No existen vehículos cargados en el padrón.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* ── Vista Estaciones ────────────────────────────────────────── */}
        {view === 'Estaciones' && canManageStations && (
          <>
            <section className="panel">
              <div className="panelhead">
                <div>
                  <h2>Estaciones de Servicio Habilitadas</h2>
                  <p>Surtidores participantes autorizados para la comercialización.</p>
                </div>
                <Building2 size={20} color="var(--primary)" />
              </div>
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>Código</th>
                      <th>Nombre de la Estación</th>
                      <th>Municipio</th>
                      <th>Dirección</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stations.map(station => (
                      <tr key={station.id}>
                        <td><b style={{ fontFamily: 'var(--font-mono)' }}>{station.code}</b></td>
                        <td>{station.name}</td>
                        <td>{station.municipality}</td>
                        <td>{station.address || '—'}</td>
                      </tr>
                    ))}
                    {!stations.length && (
                      <tr>
                        <td colSpan="4" className="empty">No existen estaciones registradas.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel">
              <div className="panelhead">
                <div>
                  <h2>Agregar Nueva Estación</h2>
                  <p>Formulario para habilitar una nueva estación de servicio en el padrón.</p>
                </div>
                <Plus size={20} color="var(--primary)" />
              </div>
              <form className="form-grid" onSubmit={createStation}>
                {user.role === 'ADMIN' ? (
                  <label>
                    Institución Propietaria
                    <select
                      value={stationForm.institution_id}
                      onChange={event => setStationForm(prev => ({ ...prev, institution_id: event.target.value }))}
                      required
                    >
                      <option value="">Selecciona una institución</option>
                      {institutions.map(item => (
                        <option key={item.id} value={item.id}>
                          {item.code} - {item.name}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <label>
                    Institución Asignada
                    <input value={`${user.institution_code || ''} - ${user.institution_name || ''}`} readOnly />
                  </label>
                )}
                <label>
                  Código de Estación
                  <input
                    placeholder="Ej. EST-004"
                    value={stationForm.code}
                    onChange={event => setStationForm(prev => ({ ...prev, code: event.target.value }))}
                    required
                  />
                </label>
                <label>
                  Nombre Comercial
                  <input
                    placeholder="Ej. E/S San Pedro S.R.L."
                    value={stationForm.name}
                    onChange={event => setStationForm(prev => ({ ...prev, name: event.target.value }))}
                    required
                  />
                </label>
                <label>
                  Municipio
                  <input
                    value={stationForm.municipality}
                    onChange={event => setStationForm(prev => ({ ...prev, municipality: event.target.value }))}
                    required
                  />
                </label>
                <label className="full-width">
                  Dirección Física
                  <input
                    placeholder="Av. / Calle y número"
                    value={stationForm.address}
                    onChange={event => setStationForm(prev => ({ ...prev, address: event.target.value }))}
                  />
                </label>
                <div className="section-actions full-width">
                  <button className="primary" type="submit" disabled={busy === 'station'}>
                    <Save size={16} /> {busy === 'station' ? 'Guardando...' : 'Guardar Estación'}
                  </button>
                </div>
              </form>
            </section>
          </>
        )}

        {/* ── Vista Alertas ───────────────────────────────────────────── */}
        {view === 'Alertas' && canReviewCases && (
          <section className="panel">
            <div className="panelhead">
              <div>
                <h2>Alertas Operativas Generadas</h2>
                <p>Señales explicables disparadas por el motor de reglas automáticas.</p>
              </div>
              <button className="secondary" type="button" onClick={() => setView('Analítica')}>
                <Activity size={16} /> Ver Dashboard Gráfico
              </button>
            </div>
            <div className="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Severidad</th>
                    <th>Código de Regla</th>
                    <th>Detalle / Explicación del Criterio</th>
                    <th>Fecha y Hora</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map(alert => (
                    <tr key={alert.id}>
                      <td>
                        <span className={`tag ${alert.severity}`}>
                          {alert.severity}
                        </span>
                      </td>
                      <td><b style={{ fontFamily: 'var(--font-mono)' }}>{alert.code}</b></td>
                      <td>{alert.message}</td>
                      <td>{new Date(alert.created_at).toLocaleString('es-BO')}</td>
                    </tr>
                  ))}
                  {!alerts.length && (
                    <tr>
                      <td colSpan="4" className="empty">No se han registrado alertas en este período.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* ── Vista Analítica ─────────────────────────────────────────── */}
        {view === 'Analítica' && canReviewCases && (
          <section className="analytics">
            <div className="analytics-intro">
              <div>
                <span className="eyebrow">CENTRO DE INTELIGENCIA</span>
                <h2>Métricas y Patrones de Alertas</h2>
                <p className="muted">Visualización de distribución de anomalías, casos manuales y despacho por estación.</p>
              </div>
              <button className="secondary" type="button" onClick={() => setView('Alertas')}>
                <AlertTriangle size={16} /> Ver Listado Detallado
              </button>
            </div>

            <div className="analytics-grid">
              <article className="chart-panel">
                <div className="chart-title">
                  <h3>Alertas por Severidad</h3>
                  <span>{alerts.length} eventos</span>
                </div>
                <div className="pie-layout">
                  <div className="pie-chart" style={{ background: `conic-gradient(${chartGradient})` }}>
                    <div>
                      <strong>{alerts.length}</strong>
                      <small>Alertas</small>
                    </div>
                  </div>
                  <div className="chart-legend">
                    {alertSeverityData.map(([label, value]) => (
                      <div key={label}>
                        <span className={`legend-dot ${label.toLowerCase()}`} />
                        <span>{label}</span>
                        <b>{value}</b>
                      </div>
                    ))}
                    {!alertSeverityData.length && <p className="muted">Sin datos disponibles.</p>}
                  </div>
                </div>
              </article>

              <article className="chart-panel">
                <div className="chart-title">
                  <h3>Frecuencia por Regla</h3>
                  <span>Criterios aplicados</span>
                </div>
                <div className="horizontal-bars">
                  {alertCodeData.map(([label, value]) => (
                    <div className="bar-row" key={label}>
                      <div>
                        <span>{label}</span>
                        <b>{value}</b>
                      </div>
                      <div className="bar-track">
                        <i style={{ width: `${(value / (alertCodeData[0]?.[1] || 1)) * 100}%` }} />
                      </div>
                    </div>
                  ))}
                  {!alertCodeData.length && <p className="muted">Sin alertas disparadas.</p>}
                </div>
              </article>

              <article className="chart-panel">
                <div className="chart-title">
                  <h3>Casos por Estado</h3>
                  <span>Resolución humana</span>
                </div>
                <div className="status-bars">
                  {caseStatusData.map(([label, value]) => (
                    <div className="status-bar" key={label}>
                      <div className={`status-fill ${label}`} style={{ height: `${(value / (caseStatusData[0]?.[1] || 1)) * 100}%` }} />
                      <b>{value}</b>
                      <span>{label}</span>
                    </div>
                  ))}
                  {!caseStatusData.length && <p className="muted">Sin casos pendientes.</p>}
                </div>
              </article>

              <article className="chart-panel">
                <div className="chart-title">
                  <h3>Despachos por Estación</h3>
                  <span>Actividad acumulada</span>
                </div>
                <div className="horizontal-bars">
                  {stationOperationsData.map(([label, value]) => (
                    <div className="bar-row" key={label}>
                      <div>
                        <span>{label}</span>
                        <b>{value}</b>
                      </div>
                      <div className="bar-track green">
                        <i style={{ width: `${(value / (stationOperationsData[0]?.[1] || 1)) * 100}%` }} />
                      </div>
                    </div>
                  ))}
                  {!stationOperationsData.length && <p className="muted">Sin operaciones.</p>}
                </div>
              </article>
            </div>
          </section>
        )}

        {/* ── Vista Casos de Revisión ──────────────────────────────────── */}
        {view === 'Casos de revisión' && canReviewCases && (
          <section className="panel">
            <div className="panelhead">
              <div>
                <h2>Bandeja de Casos de Revisión</h2>
                <p>Evaluación humana obligatoria: los criterios indican revisión previa sin aplicar sanciones automáticas.</p>
              </div>
              <button className="primary" type="button" onClick={downloadActivityPdf} disabled={busy === 'activity-pdf'}>
                <FileText size={16} />
                {busy === 'activity-pdf' ? 'Generando Reporte...' : 'Descargar PDF de Bitácora'}
              </button>
            </div>

            <div className="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Placa</th>
                    <th>Prioridad</th>
                    <th>Estado de Revisión</th>
                    <th>Fecha de Registro</th>
                    <th>Conclusión / Justificación</th>
                    <th>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {cases.map(item => {
                    const draft = caseDrafts[item.id] || { status: item.status, conclusion: item.conclusion || '' };
                    return (
                      <tr key={item.id}>
                        <td>
                          <b style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem' }}>{item.plate}</b>
                          <br />
                          <small className="muted">{item.station}</small>
                        </td>
                        <td>
                          <span className={`tag ${item.priority === 'URGENT' ? 'CRITICAL' : 'INFO'}`}>
                            {item.priority === 'URGENT' ? '🔥 URGENTE' : 'NORMAL'}
                          </span>
                        </td>
                        <td>
                          <select
                            style={{ padding: '6px 10px', fontSize: '0.82rem', fontWeight: 600 }}
                            value={draft.status}
                            onChange={event => setCaseDrafts(prev => ({ ...prev, [item.id]: { ...draft, status: event.target.value } }))}
                          >
                            <option value="PENDING">PENDING (Pendiente)</option>
                            <option value="IN_REVIEW">IN_REVIEW (En Revisión)</option>
                            <option value="RESOLVED">RESOLVED (Justificado/Resuelto)</option>
                            <option value="DISMISSED">DISMISSED (Descartado)</option>
                          </select>
                        </td>
                        <td>{new Date(item.created_at).toLocaleString('es-BO')}</td>
                        <td>
                          <input
                            style={{ minWidth: '180px', padding: '6px 10px', fontSize: '0.85rem' }}
                            value={draft.conclusion}
                            onChange={event => setCaseDrafts(prev => ({ ...prev, [item.id]: { ...draft, conclusion: event.target.value } }))}
                            placeholder="Anotar conclusión..."
                          />
                        </td>
                        <td>
                          <button
                            className="secondary"
                            type="button"
                            onClick={() => saveCase(item.id)}
                            disabled={busy === item.id}
                          >
                            <Save size={14} /> {busy === item.id ? 'Guardando...' : 'Guardar'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                  {!cases.length && (
                    <tr>
                      <td colSpan="6" className="empty">No existen casos de revisión generados.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

function Operations({ rows }) {
  return (
    <div className="table-responsive">
      <table>
        <thead>
          <tr>
            <th>Vehículo</th>
            <th>Estación</th>
            <th>Combustible</th>
            <th>Volumen</th>
            <th>Fecha y Hora</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(item => (
            <tr key={item.id}>
              <td><b style={{ fontFamily: 'var(--font-mono)' }}>{item.plate}</b></td>
              <td>{item.station}</td>
              <td><span className="tag">{item.fuel_type}</span></td>
              <td><b>{item.quantity_liters} L</b></td>
              <td>{new Date(item.occurred_at).toLocaleString('es-BO')}</td>
            </tr>
          ))}
          {!rows.length && (
            <tr>
              <td colSpan="5" className="empty">Aún no hay operaciones registradas.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
