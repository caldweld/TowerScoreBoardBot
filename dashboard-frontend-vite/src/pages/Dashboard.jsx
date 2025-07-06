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
  const [adminMessage, setAdminMessage] = useState('');
  const [progressData, setProgressData] = useState([]);
  const [selectedTier, setSelectedTier] = useState('t1');
  const [progressLoading, setProgressLoading] = useState(false);

  useEffect(() => {
    fetchUserData();
  }, []);

  useEffect(() => {
    if (userData) {
      fetchAllData();
    }
  }, [userData]);

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
      // Fetch all data in parallel
      const [usersRes, statsRes, waveRes, coinsRes, adminsRes] = await Promise.all([
        fetch('http://13.239.95.169:8000/api/users', { credentials: 'include' }),
        fetch('http://13.239.95.169:8000/api/stats/overview', { credentials: 'include' }),
        fetch('http://13.239.95.169:8000/api/leaderboard/wave', { credentials: 'include' }),
        fetch('http://13.239.95.169:8000/api/leaderboard/coins', { credentials: 'include' }),
        fetch('http://13.239.95.169:8000/api/admin/bot-admins', { credentials: 'include' })
      ]);

      if (usersRes.ok) {
        const usersData = await usersRes.json();
        setAllUsers(usersData);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      if (waveRes.ok) {
        const waveData = await waveRes.json();
        setWaveLeaderboard(waveData);
      }

      if (coinsRes.ok) {
        const coinsData = await coinsRes.json();
        setCoinsLeaderboard(coinsData);
      }

      if (adminsRes.ok) {
        const adminsData = await adminsRes.json();
        setBotAdmins(adminsData.admin_ids);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
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

  useEffect(() => {
    if (activeTab === 'progress') {
      fetchProgressData(selectedTier);
    }
  }, [activeTab, selectedTier]);

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
          <span>User ID: {userData?.user_id}</span>
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
        <button 
          className={activeTab === 'admin' ? 'active' : ''} 
          onClick={() => setActiveTab('admin')}
        >
          Admin Controls
        </button>
        <button 
          className={activeTab === 'data' ? 'active' : ''} 
          onClick={() => setActiveTab('data')}
        >
          Data Management
        </button>
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
                <h3>Total Users</h3>
                <p>{stats?.total_users || 0}</p>
              </div>
              <div className="stat-card">
                <h3>Users with Data</h3>
                <p>{stats?.users_with_data || 0}</p>
              </div>
              <div className="stat-card">
                <h3>Bot Status</h3>
                <p className="status-online">{stats?.bot_status || 'Unknown'}</p>
              </div>
              <div className="stat-card">
                <h3>Database</h3>
                <p className="status-online">{stats?.database_status || 'Unknown'}</p>
              </div>
            </div>
            
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
            </div>
            <div className="leaderboard-content">
              {leaderboardType === 'wave' ? (
                <div className="leaderboard-table">
                  <div className="table-header">
                    <span>Rank</span>
                    <span>Player</span>
                    <span>Highest Wave</span>
                    <span>Tier</span>
                  </div>
                  {waveLeaderboard.slice(0, 10).map((entry, index) => (
                    <div key={index} className="table-row">
                      <span className="rank">#{index + 1}</span>
                      <span className="player">{entry.username}</span>
                      <span className="wave">{entry.max_wave}</span>
                      <span className="tier">{entry.tier}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="leaderboard-table">
                  <div className="table-header">
                    <span>Rank</span>
                    <span>Player</span>
                    <span>Highest Coins</span>
                    <span>Tier</span>
                  </div>
                  {coinsLeaderboard.slice(0, 10).map((entry, index) => (
                    <div key={index} className="table-row">
                      <span className="rank">#{index + 1}</span>
                      <span className="player">{entry.username}</span>
                      <span className="coins">{formatNumber(entry.max_coins)}</span>
                      <span className="tier">{entry.tier}</span>
                    </div>
                  ))}
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
              <div className="admin-card">
                <h3>Database</h3>
                <button className="admin-btn">Backup Data</button>
                <button className="admin-btn">Clear Cache</button>
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
              <button className="data-btn">Export All Data</button>
              <button className="data-btn">Import Data</button>
              <button className="data-btn">Clear All Data</button>
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