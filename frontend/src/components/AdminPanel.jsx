import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import api from '../api';

function AdminPanel() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await api.get('/admin/users');
        setUsers(response.data);
      } catch (error) {
        console.error('Error fetching users:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="admin-page">
      <header className="admin-header">
        <h1>Admin Dashboard</h1>
        <div className="admin-actions">
          <button className="sidebar-btn" onClick={() => navigate('/')} style={{marginRight: '10px'}}>Go to Chat</button>
          <button className="logout-btn" onClick={logout}>Logout</button>
        </div>
      </header>
      <div className="admin-panel">
        <h2>User Statistics</h2>
        <table className="users-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Status</th>
            <th>Last Active</th>
            <th>Total Messages</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.username}>
              <td>{user.username}</td>
              <td className={user.is_active ? 'status-active' : 'status-inactive'}>
                {user.is_active ? 'Online' : 'Offline'}
              </td>
              <td>{user.last_active ? new Date(user.last_active).toLocaleString() : 'N/A'}</td>
              <td>{user.total_messages}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}

export default AdminPanel;
