import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

export default function Dashboard() {
  const [userData, setUserData] = useState(null);
  const [allUsers, setAllUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [waveLeaderboard, setWaveLeaderboard] = useState([]);
  const [coinsLeaderboard, setCoinsLeaderboard] = useState([]);
  const [botAdmins, setBotAdmins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [leaderboardType, setLeaderboardType] = useState('wave');
  const [selectedTierForLeaderboard, setSelectedTierForLeaderboard] = useState(1);
  const [tierLeaderboard, setTierLeaderboard] = useState([]);
  const [tierLeaderboardLoading, setTierLeaderboardLoading] = useState(false);
  const [adminMessage, setAdminMessage] = useState('');
  const [progressData, setProgressData] = useState([]);
  const [selectedTier, setSelectedTier] = useState('t1');
  const [progressLoading, setProgressLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState({
    bot: 'checking',
    database: 'checking'
  });
  const NUMERIC_STATS_FIELDS = [
    { value: 'coins_earned', label: 'Coins Earned' },
    { value: 'cash_earned', label: 'Cash Earned' },
    { value: 'stones_earned', label: 'Stones Earned' },
    { value: 'damage_dealt', label: 'Damage Dealt' },
    { value: 'enemies_destroyed', label: 'Enemies Destroyed' },
    { value: 'waves_completed', label: 'Waves Completed' },
    { value: 'upgrades_bought', label: 'Upgrades Bought' },
    { value: 'workshop_upgrades', label: 'Workshop Upgrades' },
    { value: 'workshop_coins_spent', label: 'Workshop Coins Spent' },
    { value: 'research_completed', label: 'Research Completed' },
    { value: 'lab_coins_spent', label: 'Lab Coins Spent' },
    { value: 'free_upgrades', label: 'Free Upgrades' },
    { value: 'interest_earned', label: 'Interest Earned' },
    { value: 'orb_kills', label: 'Orb Kills' },
    { value: 'death_ray_kills', label: 'Death Ray Kills' },
    { value: 'thorn_damage', label: 'Thorn Damage' },
    { value: 'waves_skipped', label: 'Waves Skipped' },
  ];
  const [statsLeaderboard, setStatsLeaderboard] = useState([]);
  const [selectedStatsField, setSelectedStatsField] = useState(NUMERIC_STATS_FIELDS[0].value);
  const [statsLeaderboardLoading, setStatsLeaderboardLoading] = useState(false);

  useEffect(() => {
    fetchUserData();
  }, []);

  useEffect(() => {
    if (userData) {
      fetchAllData();
    }
  }, [userData]);

  // Redirect non-admin users away from admin-only tabs
  useEffect(() => {
    if ((activeTab === 'data' || activeTab === 'admin') && !botAdmins.includes(userData?.user_id)) {
      setActiveTab('overview');
    }
  }, [activeTab, botAdmins, userData]);

  const fetchUserData = async () => {
    try {
      const response = await fetch('http://13.239.95.169:8000/api/auth/me', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setUserData(data);
      } else {
        setError('Failed to fetch user data');
      }
    } catch (err) {
      setError('Error fetching user data');
    } finally {
      setLoading(false);
    }
  };

  const fetchAllData = async () => {
    try {
      // First, try to fetch bot admins to determine user permissions
      let isAdmin = false;
      try {
        const adminsRes = await fetch('http://13.239.95.169:8000/api/admin/bot-admins', { credentials: 'include' });
        if (adminsRes.ok) {
          const adminsData = await adminsRes.json();
          setBotAdmins(adminsData.admin_ids);
          isAdmin = adminsData.admin_ids.includes(userData?.user_id);
        } else {
          // 403 or other error means user is not an admin
          console.log('User is not an admin (403 response)');
          setBotAdmins([]);
        }
      } catch (err) {
        console.log('User is not an admin (network error)');
        setBotAdmins([]);
      }

      // Fetch leaderboard and stats data for all users
      const [waveRes, coinsRes, statsRes] = await Promise.all([
        fetch('http://13.239.95.169:8000/api/leaderboard/wave', { credentials: 'include' }),
        fetch('http://13.239.95.169:8000/api/leaderboard/coins', { credentials: 'include' }),
        fetch('http://13.239.95.169:8000/api/stats/overview', { credentials: 'include' })
      ]);

      if (waveRes.ok) {
        const waveData = await waveRes.json();
        setWaveLeaderboard(waveData);
      }

      if (coinsRes.ok) {
        const coinsData = await coinsRes.json();
        setCoinsLeaderboard(coinsData);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
        setSystemStatus({
          bot: statsData.bot_status,
          database: statsData.database_status
        });
      }

      // If user is admin, fetch additional admin data
      if (isAdmin) {
        const usersRes = await fetch('http://13.239.95.169:8000/api/users', { credentials: 'include' });
        if (usersRes.ok) {
          const usersData = await usersRes.json();
          setAllUsers(usersData);
        }
      } else {
        // For non-admin users, set empty admin data
        setAllUsers([]);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setSystemStatus({
        bot: 'offline',
        database: 'disconnected'
      });
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('http://13.239.95.169:8000/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
      window.location.href = '/';
    } catch (err) {
      console.error('Error logging out:', err);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1e15) return (num / 1e15).toFixed(1) + 'Q';
    if (num >= 1e12) return (num / 1e12).toFixed(1) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toString();
  };

  const handleAdminAction = async (action, discordId = null) => {
    setAdminMessage('');
    try {
      let response;
      if (action === 'add' && discordId) {
        response = await fetch('http://13.239.95.169:8000/api/admin/add-bot-admin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ discord_id: discordId })
        });
      } else if (action === 'remove' && discordId) {
        response = await fetch('http://13.239.95.169:8000/api/admin/remove-bot-admin', {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ discord_id: discordId })
        });
      }

      if (response && response.ok) {
        const data = await response.json();
        setAdminMessage(data.message);
        // Refresh admin list
        const adminsRes = await fetch('http://13.239.95.169:8000/api/admin/bot-admins', { credentials: 'include' });
        if (adminsRes.ok) {
          const adminsData = await adminsRes.json();
          setBotAdmins(adminsData.admin_ids);
        }
      }
    } catch (err) {
      setAdminMessage('Error performing admin action');
    }
  };

  const handleExportData = async (format = 'json') => {
    try {
      const response = await fetch(`http://13.239.95.169:8000/api/export/${format}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.headers.get('content-disposition')?.split('filename=')[1] || `tower_data_export.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('Failed to export data');
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Error exporting data');
    }
  };

  const fetchProgressData = async (tier) => {
    setProgressLoading(true);
    try {
      const response = await fetch(`http://13.239.95.169:8000/api/user/progress?tier=${tier}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const history = await response.json();
        // Format data for Recharts
        const formattedData = history.map(entry => ({
          date: entry.timestamp.slice(0, 10), // YYYY-MM-DD
          wave: entry.wave
        }));
        setProgressData(formattedData);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
    } finally {
      setProgressLoading(false);
    }
  };

  const fetchTierLeaderboard = async (tier) => {
    setTierLeaderboardLoading(true);
    try {
      const response = await fetch(`http://13.239.95.169:8000/api/leaderboard/tier/${tier}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setTierLeaderboard(data);
      }
    } catch (error) {
      console.error('Error fetching tier leaderboard:', error);
    } finally {
      setTierLeaderboardLoading(false);
    }
  };

  const fetchStatsLeaderboard = async (field) => {
    setStatsLeaderboardLoading(true);
    try {
      const response = await fetch(`http://13.239.95.169:8000/api/stats-leaderboard?field=${field}`, { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        setStatsLeaderboard(data);
      }
    } catch (error) {
      setStatsLeaderboard([]);
    } finally {
      setStatsLeaderboardLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'progress') {
      fetchProgressData(selectedTier);
    }
  }, [activeTab, selectedTier]);

  useEffect(() => {
    if (activeTab === 'leaderboard' && leaderboardType === 'tier') {
      fetchTierLeaderboard(selectedTierForLeaderboard);
    }
  }, [activeTab, leaderboardType, selectedTierForLeaderboard]);

  useEffect(() => {
    if (activeTab === 'leaderboard' && leaderboardType === 'stats') {
      fetchStatsLeaderboard(selectedStatsField);
    }
  }, [activeTab, leaderboardType, selectedStatsField]);

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Tower Scoreboard Dashboard</h1>
        <div className="user-info">
          <div className="user-details">
            <span>Name: {allUsers.find(user => user.discordid === userData?.user_id)?.discordname || 'Unknown'}</span>
            <span>User ID: {userData?.user_id}</span>
          </div>
          <button onClick={handleLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <nav className="dashboard-nav">
        <button 
          className={activeTab === 'overview' ? 'active' : ''} 
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={activeTab === 'leaderboard' ? 'active' : ''} 
          onClick={() => setActiveTab('leaderboard')}
        >
          Leaderboard
        </button>
        {botAdmins.includes(userData?.user_id) && (
          <button 
            className={activeTab === 'admin' ? 'active' : ''} 
            onClick={() => setActiveTab('admin')}
          >
            Admin Controls
          </button>
        )}
        {botAdmins.includes(userData?.user_id) && (
          <button 
            className={activeTab === 'data' ? 'active' : ''} 
            onClick={() => setActiveTab('data')}
          >
            Data Management
          </button>
        )}
        <button 
          className={activeTab === 'progress' ? 'active' : ''} 
          onClick={() => setActiveTab('progress')}
        >
          Progress Charts
        </button>
      </nav>

      <main className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="overview-section">
            <h2>System Overview</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Total Members</h3>
                <p>{stats?.total_users || 0}</p>
              </div>
              <div className="stat-card">
                <h3>Bot Status</h3>
                <p className={`status-${systemStatus.bot === 'online' ? 'online' : 'offline'}`}>
                  {systemStatus.bot === 'checking' ? 'Checking...' : systemStatus.bot}
                </p>
              </div>
              <div className="stat-card">
                <h3>Database</h3>
                <p className={`status-${systemStatus.database === 'connected' ? 'online' : 'offline'}`}>
                  {systemStatus.database === 'checking' ? 'Checking...' : systemStatus.database}
                </p>
              </div>
              {botAdmins.includes(userData?.user_id) && (
                <div className="stat-card">
                  <h3>Users with Data</h3>
                  <p>{stats?.users_with_data || 0}</p>
                </div>
              )}
            </div>
            
            {botAdmins.includes(userData?.user_id) ? (
              <div className="recent-users">
                <h3>Recent Users</h3>
                <div className="users-list">
                  {allUsers.slice(0, 5).map((user, index) => (
                    <div key={index} className="user-item">
                      <span className="username">{user.discordname}</span>
                      <span className="tier-count">
                        {Object.values(user.tiers).filter(tier => tier && tier !== 'Wave: 0 Coins: 0').length} tiers
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="welcome-message">
                <h3>Welcome to The Tower Scoreboard!</h3>
                <p>Track your progress across all tiers and compare with other players.</p>
                <p>Use the Progress Charts tab to view your personal statistics.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'leaderboard' && (
          <div className="leaderboard-section">
            <h2>Leaderboard</h2>
            <div className="leaderboard-tabs">
              <button 
                className={`tab-btn ${leaderboardType === 'wave' ? 'active' : ''}`}
                onClick={() => setLeaderboardType('wave')}
              >
                By Wave
              </button>
              <button 
                className={`tab-btn ${leaderboardType === 'coins' ? 'active' : ''}`}
                onClick={() => setLeaderboardType('coins')}
              >
                By Coins
              </button>
              <button 
                className={`tab-btn ${leaderboardType === 'tier' ? 'active' : ''}`}
                onClick={() => setLeaderboardType('tier')}
              >
                By Tier
              </button>
              <button 
                className={`tab-btn ${leaderboardType === 'stats' ? 'active' : ''}`}
                onClick={() => setLeaderboardType('stats')}
              >
                Stats Leaderboard
              </button>
            </div>
            {leaderboardType === 'tier' && (
              <div className="tier-selector">
                <label>Select Tier: </label>
                <select 
                  value={selectedTierForLeaderboard} 
                  onChange={(e) => setSelectedTierForLeaderboard(parseInt(e.target.value))}
                  className="tier-select"
                >
                  {Array.from({length: 18}, (_, i) => (
                    <option key={i+1} value={i+1}>Tier {i+1}</option>
                  ))}
                </select>
              </div>
            )}
            {leaderboardType === 'stats' && (
              <div className="tier-selector">
                <label>Select Stat: </label>
                <select 
                  value={selectedStatsField} 
                  onChange={(e) => setSelectedStatsField(e.target.value)}
                  className="tier-select"
                >
                  {NUMERIC_STATS_FIELDS.map(field => (
                    <option key={field.value} value={field.value}>{field.label}</option>
                  ))}
                </select>
              </div>
            )}
            <div className="leaderboard-content">
              {leaderboardType === 'wave' && (
                <div className="leaderboard-table">
                  <div className="table-header">
                    <span>Rank</span>
                    <span>Player</span>
                    <span>Highest Wave</span>
                    <span>Tier</span>
                  </div>
                  {waveLeaderboard.map((entry, index) => (
                    <div key={index} className="table-row">
                      <span className="rank">#{index + 1}</span>
                      <span className="player">{entry.username}</span>
                      <span className="wave">{entry.max_wave}</span>
                      <span className="tier">{entry.tier}</span>
                    </div>
                  ))}
                </div>
              )}
              
              {leaderboardType === 'coins' && (
                <div className="leaderboard-table">
                  <div className="table-header">
                    <span>Rank</span>
                    <span>Player</span>
                    <span>Highest Coins</span>
                    <span>Tier</span>
                  </div>
                  {coinsLeaderboard.map((entry, index) => (
                    <div key={index} className="table-row">
                      <span className="rank">#{index + 1}</span>
                      <span className="player">{entry.username}</span>
                      <span className="coins">{formatNumber(entry.max_coins)}</span>
                      <span className="tier">{entry.tier}</span>
                    </div>
                  ))}
                </div>
              )}
              
              {leaderboardType === 'tier' && (
                <div className="leaderboard-table">
                  <div className="table-header">
                    <span>Rank</span>
                    <span>Player</span>
                    <span>Wave</span>
                    <span>Coins</span>
                  </div>
                  {tierLeaderboardLoading ? (
                    <div className="loading">Loading tier leaderboard...</div>
                  ) : tierLeaderboard.length > 0 ? (
                    tierLeaderboard.map((entry, index) => (
                      <div key={index} className="table-row">
                        <span className="rank">#{index + 1}</span>
                        <span className="player">{entry.username}</span>
                        <span className="wave">{entry.wave}</span>
                        <span className="coins">{entry.coins_formatted}</span>
                      </div>
                    ))
                  ) : (
                    <div className="no-data">No data available for Tier {selectedTierForLeaderboard}</div>
                  )}
                </div>
              )}
              {leaderboardType === 'stats' && (
                <div className="leaderboard-table">
                  <div className="table-header">
                    <span>Rank</span>
                    <span>Player</span>
                    <span>{NUMERIC_STATS_FIELDS.find(f => f.value === selectedStatsField)?.label || 'Value'}</span>
                  </div>
                  {statsLeaderboardLoading ? (
                    <div className="loading">Loading stats leaderboard...</div>
                  ) : statsLeaderboard.length > 0 ? (
                    statsLeaderboard.map((entry, index) => (
                      <div key={index} className="table-row">
                        <span className="rank">#{index + 1}</span>
                        <span className="player">{entry.username}</span>
                        <span className="wave">{formatNumber(entry.value)}</span>
                      </div>
                    ))
                  ) : (
                    <div className="no-data">No data available for this stat</div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'admin' && (
          <div className="admin-section">
            <h2>Admin Controls</h2>
            {adminMessage && (
              <div className="admin-message">{adminMessage}</div>
            )}
            <div className="admin-grid">
              <div className="admin-card">
                <h3>Bot Management</h3>
                <button className="admin-btn">Restart Bot</button>
                <button className="admin-btn">View Bot Logs</button>
              </div>
              <div className="admin-card">
                <h3>User Management</h3>
                <button className="admin-btn">Add Bot Admin</button>
                <button className="admin-btn">Remove Bot Admin</button>
                <button className="admin-btn" onClick={() => fetchAllData()}>Refresh Data</button>
              </div>
            </div>
            
            <div className="admin-list">
              <h3>Current Bot Admins</h3>
              <div className="admins-list">
                {botAdmins.length > 0 ? (
                  botAdmins.map((adminId, index) => (
                    <div key={index} className="admin-item">
                      <span>ID: {adminId}</span>
                      <button 
                        className="remove-admin-btn"
                        onClick={() => handleAdminAction('remove', adminId)}
                      >
                        Remove
                      </button>
                    </div>
                  ))
                ) : (
                  <p>No bot admins found</p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'data' && (
          <div className="data-section">
            <h2>Data Management</h2>
            <div className="data-controls">
              <button className="data-btn" onClick={() => handleExportData('json')}>Export JSON</button>
              <button className="data-btn" onClick={() => handleExportData('csv')}>Export CSV</button>
            </div>
            <div className="data-preview">
              <h3>User Data Overview</h3>
              <div className="data-table">
                <div className="table-header">
                  <span>Username</span>
                  <span>Tiers with Data</span>
                  <span>Actions</span>
                </div>
                {allUsers.slice(0, 10).map((user, index) => (
                  <div key={index} className="table-row">
                    <span>{user.discordname}</span>
                    <span>
                      {Object.values(user.tiers).filter(tier => tier && tier !== 'Wave: 0 Coins: 0').length}/18
                    </span>
                    <span>
                      <button className="view-btn">View</button>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'progress' && (
          <div className="progress-section">
            <h2>Progress Charts</h2>
            <div className="progress-controls">
              <label>Select Tier: </label>
              <select 
                value={selectedTier} 
                onChange={(e) => setSelectedTier(e.target.value)}
                className="tier-select"
              >
                {Array.from({length: 18}, (_, i) => (
                  <option key={i+1} value={`t${i+1}`}>Tier {i+1}</option>
                ))}
              </select>
            </div>
            
            <div className="chart-container">
              {progressLoading ? (
                <div className="loading">Loading progress data...</div>
              ) : progressData.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={progressData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#fff"
                      tick={{ fill: '#fff' }}
                    />
                    <YAxis 
                      stroke="#fff"
                      tick={{ fill: '#fff' }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#2c2f33', 
                        border: '1px solid #444',
                        color: '#fff'
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="wave" 
                      stroke="#5865f2" 
                      strokeWidth={3}
                      dot={{ fill: '#5865f2', strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6, stroke: '#5865f2', strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="no-data">No progress data available for this tier.</div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
} 