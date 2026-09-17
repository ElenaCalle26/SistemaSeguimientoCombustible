import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertTriangle,
  Building2,
  Car,
  CheckCircle2,
  LogOut,
  Plus,
  ShieldCheck,
  Save,
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

  /*
  if (token) {
    headers.Authorization = "Bearer $token";
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  */
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
  const [email, setEmail] = useState('admin@fueltrack.local');
  const [password, setPassword] = useState('Cambiar123!');
  const [error, setError] = useState('');

  const submit = async event => {
    event.preventDefault();
    setError('');
    try {
      const token = await request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem('token', token.access_token);
      await onLogin();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <main className="login">
      <section>
        <div className="brand">
          <Activity /> FuelTrack
        </div>
        <h1>Control con criterio.</h1>
        <p>Seguimiento centralizado de operaciones de carguío con información sintética.</p>
        <div className="demo-list">
          <button type="button" className="demo-chip" onClick={() => { setEmail('admin@fueltrack.local'); setPassword('Cambiar123!'); }}>
            Admin
          </button>
          <button type="button" className="demo-chip" onClick={() => { setEmail('operador@fueltrack.local'); setPassword('Operador123!'); }}>
            Operador
          </button>
          <button type="button" className="demo-chip" onClick={() => { setEmail('supervisor@fueltrack.local'); setPassword('Supervisor123!'); }}>
            Supervisor
          </button>
        </div>
      </section>

      <form onSubmit={submit}>
        <h2>Bienvenido</h2>
        <label>
          Correo
          <input value={email} onChange={event => setEmail(event.target.value)} type="email" />
        </label>
        <label>
          Contraseña
          <input value={password} onChange={event => setPassword(event.target.value)} type="password" />
        </label>
        {error && <small className="error">{error}</small>}
        <button type="submit">Ingresar</button>
        <small>Demo: admin@fueltrack.local / operador@fueltrack.local / supervisor@fueltrack.local</small>
      </form>
    </main>
  );
}

const Card = ({ icon: Icon, label, value, accent }) => (
  <article className={`card ${accent || ''}`}>
    <div>
      <span>{label}</span>
      <strong>{fmt(value || 0)}</strong>
    </div>
    <Icon size={21} />
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
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState('');

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
      items.push('Casos de revisión', 'Alertas');
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
        request('/api/operations'),
        request('/api/vehicles'),
        request('/api/stations'),
        request('/api/fuel-types'),
      ];

      if (me.role === 'ADMIN' || me.role === 'SUPERVISOR') {
        requests.push(request('/api/cases'), request('/api/alerts'));
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
        vehicle_id: vehiclesData[0]?.id || '',
        station_id: stationsList[0]?.id || '',
        fuel_type_id: fuelList[0]?.id || '',
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

  const refresh = async () => {
    await loadApp();
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
          station_id: operationForm.station_id,
          fuel_type_id: Number(operationForm.fuel_type_id),
          quantity_liters: Number(operationForm.quantity_liters),
          occurred_at: new Date(operationForm.occurred_at).toISOString(),
          notes: operationForm.notes || null,
        }),
      });
      await refresh();
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
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  };

  if (!user) {
    return <Login onLogin={loadApp} />;
  }

  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <Activity /> FuelTrack
        </div>
        <nav>
          {navItems.map(item => (
            <button className={view === item ? 'active' : ''} onClick={() => setView(item)} key={item}>
              {item === 'Resumen' ? <Activity /> : item === 'Operaciones' ? <Car /> : item === 'Vehículos' ? <Car /> : item === 'Estaciones' ? <Building2 /> : <AlertTriangle />}
              {item}
            </button>
          ))}
        </nav>
        <div className="profile">
          <div className="avatar">{user.full_name[0]}</div>
          <div>
            <b>{user.full_name}</b>
            <small>{user.role}</small>
          </div>
          <button title="Salir" onClick={logout}>
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <main className="content">
        <header>
          <div>
            <p className="eyebrow">PANEL DE SEGUIMIENTO</p>
            <h1>{view}</h1>
            <p className="muted">
              {user.role === 'OPERATOR'
                ? 'Vista operativa para registrar y consultar movimientos.'
                : 'Vista de administración y revisión con datos de prueba.'}
            </p>
          </div>
          {view === 'Operaciones' && canCreateOperations && (
            <button className="primary" onClick={() => document.getElementById('operation-form')?.scrollIntoView({ behavior: 'smooth' })}>
              <Plus size={18} /> Registrar operación
            </button>
          )}
        </header>

        {loading && <p className="muted">Cargando datos...</p>}
        {error && <p className="error">{error}</p>}

        {view === 'Resumen' && data && (
          <>
            <section className="cards">
              <Card icon={Activity} label="Operaciones últimas 24h" value={data.operations_today} />
              <Card icon={AlertTriangle} label="Casos por revisar" value={data.pending_cases} accent="warning" />
              <Card icon={Car} label="Vehículos activos" value={data.active_vehicles} />
              <Card icon={Building2} label="Estaciones activas" value={data.active_stations} />
            </section>
            <section className="panel">
              <div className="panelhead">
                <div>
                  <h2>Actividad reciente</h2>
                  <p>Últimas operaciones de carguío registradas.</p>
                </div>
                <ShieldCheck size={22} />
              </div>
              <Operations rows={data.recent_operations} />
            </section>
          </>
        )}

        {view === 'Operaciones' && (
          <>
            <section className="panel">
              <div className="panelhead">
                <div>
                  <h2>Registro de operaciones</h2>
                  <p>Consulta y creación según el rol asignado.</p>
                </div>
              </div>
              <Operations rows={ops} />
            </section>
            {canCreateOperations && (
              <section className="panel form-card" id="operation-form">
                <div className="panelhead">
                  <div>
                    <h2>Registrar operación</h2>
                    <p>Solo operadores y administradores pueden crear movimientos.</p>
                  </div>
                  <Plus size={20} />
                </div>
                <form className="form-grid" onSubmit={createOperation}>
                  <label>
                    Vehículo
                    <select value={operationForm.vehicle_id} onChange={event => setOperationForm(prev => ({ ...prev, vehicle_id: event.target.value }))}>
                      {vehicles.map(vehicle => (
                        <option key={vehicle.id} value={vehicle.id}>
                          {vehicle.plate}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Estación
                    <input value={stations.find(station => station.id === user.fixed_station_id)?.name || 'Estación fijada en la sesión'} disabled />
                  </label>
                  <label>
                    Combustible
                    <select value={operationForm.fuel_type_id} onChange={event => setOperationForm(prev => ({ ...prev, fuel_type_id: event.target.value }))}>
                      {fuelTypes.map(fuel => (
                        <option key={fuel.id} value={fuel.id}>
                          {fuel.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Litros
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={operationForm.quantity_liters}
                      onChange={event => setOperationForm(prev => ({ ...prev, quantity_liters: event.target.value }))}
                    />
                  </label>
                  <label>
                    Fecha y hora
                    <input
                      type="datetime-local"
                      value={operationForm.occurred_at}
                      onChange={event => setOperationForm(prev => ({ ...prev, occurred_at: event.target.value }))}
                    />
                  </label>
                  <label className="full-width">
                    Observaciones
                    <textarea
                      rows="3"
                      value={operationForm.notes}
                      onChange={event => setOperationForm(prev => ({ ...prev, notes: event.target.value }))}
                    />
                  </label>
                  <div className="section-actions full-width">
                    <button className="primary" type="submit" disabled={busy === 'operation'}>
                      <Save size={16} /> {busy === 'operation' ? 'Guardando...' : 'Guardar operación'}
                    </button>
                  </div>
                </form>
              </section>
            )}
            {!canCreateOperations && <p className="muted">Tu rol solo puede consultar operaciones.</p>}
          </>
        )}

        {view === 'Vehículos' && canManageCatalogs && (
          <>
            <section className="panel">
              <div className="panelhead">
                <div>
                  <h2>Vehículos</h2>
                  <p>Administración de unidades habilitadas.</p>
                </div>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Placa</th>
                    <th>Tipo</th>
                    <th>Código interno</th>
                    <th>Activo</th>
                  </tr>
                </thead>
                <tbody>
                  {vehicles.map(vehicle => (
                    <tr key={vehicle.id}>
                      <td><b>{vehicle.plate}</b></td>
                      <td>{vehicle.vehicle_type || '—'}</td>
                      <td>{vehicle.internal_code || '—'}</td>
                      <td>{vehicle.is_active ? 'Sí' : 'No'}</td>
                    </tr>
                  ))}
                  {!vehicles.length && (
                    <tr>
                      <td colSpan="4" className="empty">No existen vehículos.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>

          </>
        )}

        {view === 'Estaciones' && canManageStations && (
          <>
            <section className="panel">
              <div className="panelhead">
                <div>
                  <h2>Estaciones</h2>
                  <p>Administración de estaciones habilitadas.</p>
                </div>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Nombre</th>
                    <th>Municipio</th>
                    <th>Dirección</th>
                  </tr>
                </thead>
                <tbody>
                  {stations.map(station => (
                    <tr key={station.id}>
                      <td><b>{station.code}</b></td>
                      <td>{station.name}</td>
                      <td>{station.municipality}</td>
                      <td>{station.address || '—'}</td>
                    </tr>
                  ))}
                  {!stations.length && (
                    <tr>
                      <td colSpan="4" className="empty">No existen estaciones.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>

            {canManageStations && <section className="panel form-card">
              <div className="panelhead">
                <div>
                  <h2>Crear estación</h2>
                  <p>Disponible para administradores y supervisores.</p>
                </div>
                <Building2 size={20} />
              </div>
              <form className="form-grid" onSubmit={createStation}>
                {user.role === 'ADMIN' ? (
                  <label>
                    Institución
                    <select value={stationForm.institution_id} onChange={event => setStationForm(prev => ({ ...prev, institution_id: event.target.value }))} required>
                      <option value="">Selecciona una institución</option>
                      {institutions.map(item => <option key={item.id} value={item.id}>{item.code} - {item.name}</option>)}
                    </select>
                  </label>
                ) : (
                  <label>
                    Institución asignada
                    <input value={`${user.institution_code || ''} - ${user.institution_name || ''}`} readOnly />
                  </label>
                )}
                <label>
                  Código
                  <input value={stationForm.code} onChange={event => setStationForm(prev => ({ ...prev, code: event.target.value }))} />
                </label>
                <label>
                  Nombre
                  <input value={stationForm.name} onChange={event => setStationForm(prev => ({ ...prev, name: event.target.value }))} />
                </label>
                <label>
                  Municipio
                  <input value={stationForm.municipality} onChange={event => setStationForm(prev => ({ ...prev, municipality: event.target.value }))} />
                </label>
                <label className="full-width">
                  Dirección
                  <input value={stationForm.address} onChange={event => setStationForm(prev => ({ ...prev, address: event.target.value }))} />
                </label>
                <div className="section-actions full-width">
                  <button className="primary" type="submit" disabled={busy === 'station'}>
                    <Save size={16} /> {busy === 'station' ? 'Guardando...' : 'Guardar estación'}
                  </button>
                </div>
              </form>
            </section>}
          </>
        )}

        {view === 'Alertas' && canReviewCases && (
          <section className="panel">
            <div className="panelhead">
              <div>
                <h2>Alertas operativas</h2>
                <p>Señales explicables; el tercer carguío aparece como prioridad crítica.</p>
              </div>
              <AlertTriangle size={22} />
            </div>
            <table>
              <thead><tr><th>Severidad</th><th>Regla</th><th>Mensaje</th><th>Fecha</th></tr></thead>
              <tbody>
                {alerts.map(alert => (
                  <tr key={alert.id}>
                    <td><span className={`tag ${alert.severity}`}>{alert.severity}</span></td>
                    <td>{alert.code}</td>
                    <td>{alert.message}</td>
                    <td>{new Date(alert.created_at).toLocaleString('es-BO')}</td>
                  </tr>
                ))}
                {!alerts.length && <tr><td colSpan="4" className="empty">No existen alertas.</td></tr>}
              </tbody>
            </table>
          </section>
        )}

        {view === 'Casos de revisión' && canReviewCases && (
          <section className="panel">
            <div className="panelhead">
              <div>
                <h2>Seguimiento manual</h2>
                <p>Los criterios indican revisión; no determinan irregularidades ni sanciones.</p>
              </div>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Vehículo</th>
                  <th>Estado</th>
                  <th>Fecha</th>
                  <th>Conclusión</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {cases.map(item => {
                  const draft = caseDrafts[item.id] || { status: item.status, conclusion: item.conclusion || '' };
                  return (
                    <tr key={item.id}>
                      <td><b>{item.plate}</b></td>
                      <td>
                        <select
                          value={draft.status}
                          onChange={event => setCaseDrafts(prev => ({ ...prev, [item.id]: { ...draft, status: event.target.value } }))}
                        >
                          <option value="PENDING">PENDING</option>
                          <option value="IN_REVIEW">IN_REVIEW</option>
                          <option value="RESOLVED">RESOLVED</option>
                          <option value="DISMISSED">DISMISSED</option>
                        </select>
                      </td>
                      <td>{new Date(item.created_at).toLocaleString('es-BO')}</td>
                      <td>
                        <input
                          value={draft.conclusion}
                          onChange={event => setCaseDrafts(prev => ({ ...prev, [item.id]: { ...draft, conclusion: event.target.value } }))}
                          placeholder="Conclusión"
                        />
                      </td>
                      <td>
                        <button className="secondary" type="button" onClick={() => saveCase(item.id)} disabled={busy === item.id}>
                          {busy === item.id ? 'Guardando...' : 'Guardar'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {!cases.length && (
                  <tr>
                    <td colSpan="5" className="empty">No existen casos identificados.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
        )}
      </main>
    </div>
  );
}

function Operations({ rows }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Vehículo</th>
          <th>Estación</th>
          <th>Combustible</th>
          <th>Volumen</th>
          <th>Fecha y hora</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(item => (
          <tr key={item.id}>
            <td><b>{item.plate}</b></td>
            <td>{item.station}</td>
            <td>{item.fuel_type}</td>
            <td>{item.quantity_liters} L</td>
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
  );
}

createRoot(document.getElementById('root')).render(<App />);
