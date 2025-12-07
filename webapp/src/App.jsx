import React, { useState, useEffect, useMemo } from 'react';
import { Search, LayoutGrid, List, ChevronLeft, ChevronRight, ArrowUpDown, Filter, Download } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  // View State
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'grid'

  // Filter State
  const [filterType, setFilterType] = useState('All');
  const [filterHub, setFilterHub] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');

  // Sort State
  const [sortConfig, setSortConfig] = useState({ key: 'mw', direction: 'desc' });

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  useEffect(() => {
    fetch('/data.json')
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => console.error("Failed to load data", err));
  }, []);

  // Derived Lists
  const types = ['All', ...new Set(data.map(item => item.type))].sort();
  const hubs = ['All', 'North', 'South', 'West', 'Houston'];

  // Filtering Logic
  const filteredData = useMemo(() => {
    return data.filter(item => {
      const matchesType = filterType === 'All' || item.type === filterType;
      const matchesHub = filterHub === 'All' || item.hub === filterHub;
      const searchLower = searchTerm.toLowerCase();
      const matchesSearch = item.name.toLowerCase().includes(searchLower) ||
        item.city.toLowerCase().includes(searchLower) ||
        item.county.toLowerCase().includes(searchLower) ||
        (item.notes && item.notes.toLowerCase().includes(searchLower));
      return matchesType && matchesHub && matchesSearch;
    });
  }, [data, filterType, filterHub, searchTerm]);

  // Sorting Logic
  const sortedData = useMemo(() => {
    let sortableItems = [...filteredData];
    if (sortConfig.key !== null) {
      sortableItems.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [filteredData, sortConfig]);

  // Pagination Logic
  const totalPages = Math.ceil(sortedData.length / itemsPerPage);
  const currentData = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedData.slice(start, start + itemsPerPage);
  }, [sortedData, currentPage]);

  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getBadgeClass = (type) => {
    if (type.includes('Crypto')) return 'badge badge-orange';
    if (type.includes('Manufact') || type.includes('Steel')) return 'badge badge-blue';
    if (type.includes('Refin') || type.includes('Chem')) return 'badge badge-purple';
    if (type.includes('Data')) return 'badge badge-gray';
    if (type.includes('Health')) return 'badge badge-green';
    return 'badge badge-gray';
  };

  const getHubColor = (hub) => {
    switch (hub) {
      case 'North': return 'text-blue-400';
      case 'South': return 'text-green-400';
      case 'West': return 'text-orange-400';
      case 'Houston': return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  if (loading) return (
    <div className="h-screen flex items-center justify-center bg-slate-900 text-slate-400">
      <div className="animate-pulse">Loading Analytics Data...</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-900 flex text-slate-200 font-sans">

      {/* Sidebar Filters */}
      <aside className="w-64 bg-slate-800 border-r border-slate-700 hidden md:flex flex-col h-screen sticky top-0">
        <div className="p-6 border-b border-slate-700">
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Filter size={20} className="text-blue-500" /> Data Filters
          </h1>
        </div>

        <div className="p-6 flex-1 overflow-y-auto space-y-8">
          {/* Hub Filter */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">ERCOT Hub</h3>
            <div className="space-y-2">
              {hubs.map(hub => (
                <label key={hub} className="flex items-center gap-3 cursor-pointer group">
                  <div className={`w-4 h-4 rounded-full border flex items-center justify-center
                    ${filterHub === hub ? 'border-blue-500 bg-blue-500' : 'border-slate-600 bg-slate-900 group-hover:border-slate-500'}`}>
                    {filterHub === hub && <div className="w-2 h-2 bg-white rounded-full" />}
                  </div>
                  <input type="radio" className="hidden" checked={filterHub === hub} onChange={() => { setFilterHub(hub); setCurrentPage(1); }} />
                  <span className={`${filterHub === hub ? 'text-white' : 'text-slate-400 group-hover:text-slate-300'}`}>{hub}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Type Filter */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Industry Sector</h3>
            <div className="space-y-1">
              {types.map(type => (
                <button
                  key={type}
                  onClick={() => { setFilterType(type); setCurrentPage(1); }}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors
                    ${filterType === type ? 'bg-blue-500/10 text-blue-400' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 md:p-8 overflow-x-hidden">

        {/* Top Bar */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h2 className="text-2xl font-bold text-white">Large Load Analytics</h2>
            <p className="text-slate-400 text-sm mt-1">Showing {filteredData.length} facilities across ERCOT</p>
          </div>

          <div className="flex items-center gap-4 w-full md:w-auto">
            <div className="relative flex-1 md:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input
                type="text"
                placeholder="Search name, city, county..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
              />
            </div>

            <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700">
              <button
                onClick={() => setViewMode('table')}
                className={`p-2 rounded ${viewMode === 'table' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                <List size={18} />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                <LayoutGrid size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Top Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="dashboard-panel p-4 rounded-xl">
            <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">Total Mw Load</div>
            <div className="text-2xl font-mono text-white">{(filteredData.reduce((acc, c) => acc + c.mw, 0)).toLocaleString()} <span className="text-sm text-slate-500">MW</span></div>
          </div>
          <div className="dashboard-panel p-4 rounded-xl">
            <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">Facility Count</div>
            <div className="text-2xl font-mono text-white">{filteredData.length}</div>
          </div>
          <div className="dashboard-panel p-4 rounded-xl">
            <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">Avg Load Size</div>
            <div className="text-2xl font-mono text-white">{(filteredData.reduce((acc, c) => acc + c.mw, 0) / (filteredData.length || 1)).toFixed(1)} <span className="text-sm text-slate-500">MW</span></div>
          </div>
          <div className="dashboard-panel p-4 rounded-xl bg-blue-500/10 border-blue-500/20">
            <div className="text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">Export Data</div>
            <button className="flex items-center gap-2 text-sm text-white font-medium hover:underline">
              <Download size={14} /> Download CSV
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="dashboard-panel rounded-xl overflow-hidden min-h-[500px]">

          {/* Table View */}
          {viewMode === 'table' && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-slate-400 uppercase bg-slate-800/50 border-b border-slate-700">
                  <tr>
                    <th className="px-6 py-4 th-sortable" onClick={() => requestSort('name')}>
                      <div className="flex items-center gap-1">Name <ArrowUpDown size={12} /></div>
                    </th>
                    <th className="px-6 py-4 th-sortable" onClick={() => requestSort('type')}>Type</th>
                    <th className="px-6 py-4 th-sortable" onClick={() => requestSort('hub')}>Hub</th>
                    <th className="px-6 py-4 th-sortable" onClick={() => requestSort('city')}>City</th>
                    <th className="px-6 py-4 th-sortable" onClick={() => requestSort('county')}>County</th>
                    <th className="px-6 py-4 th-sortable text-right" onClick={() => requestSort('mw')}>
                      <div className="flex items-center justify-end gap-1"><ArrowUpDown size={12} /> Load (MW)</div>
                    </th>
                    <th className="px-6 py-4 text-slate-500">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {currentData.map((item, idx) => (
                    <tr key={idx} className="table-row">
                      <td className="px-6 py-4 font-medium text-white">{item.name}</td>
                      <td className="px-6 py-4">
                        <span className={getBadgeClass(item.type)}>{item.type}</span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs">
                        <span className={getHubColor(item.hub)}>●</span> {item.hub}
                      </td>
                      <td className="px-6 py-4 text-slate-400">{item.city}</td>
                      <td className="px-6 py-4 text-slate-400">{item.county}</td>
                      <td className="px-6 py-4 text-right font-mono text-white">{item.mw}</td>
                      <td className="px-6 py-4 text-slate-500 truncate max-w-xs" title={item.notes}>{item.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {currentData.length === 0 && <div className="p-8 text-center text-slate-500">No customers found.</div>}
            </div>
          )}

          {/* Grid View */}
          {viewMode === 'grid' && (
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {currentData.map((item, idx) => (
                <div key={idx} className="bg-slate-800/50 border border-slate-700 p-4 rounded-lg hover:border-slate-600 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <span className={getBadgeClass(item.type)}>{item.type}</span>
                    <span className="font-mono text-white font-bold">{item.mw} MW</span>
                  </div>
                  <h3 className="font-semibold text-white mb-1 truncate" title={item.name}>{item.name}</h3>
                  <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
                    <span>{item.city}, {item.county}</span>
                    <span className="w-1 h-1 bg-slate-600 rounded-full"></span>
                    <span className={getHubColor(item.hub)}>{item.hub} Hub</span>
                  </div>
                  <p className="text-xs text-slate-500 line-clamp-2">{item.notes}</p>
                </div>
              ))}
            </div>
          )}

        </div>

        {/* Pagination Controls */}
        <div className="mt-6 flex justify-between items-center text-sm text-slate-400">
          <div>
            Page <span className="text-white font-medium">{currentPage}</span> of <span className="text-white font-medium">{totalPages}</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

      </main>
    </div>
  );
}

export default App;
