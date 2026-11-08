import React, { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('travelsense_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => localStorage.getItem('travelsense_token') || null);
  const [loading, setLoading] = useState(true);

  // Sync / refresh profile on load if token exists
  useEffect(() => {
    const fetchProfile = async () => {
      if (token) {
        try {
          const profile = await authService.getProfile();
          setUser(profile);
          localStorage.setItem('travelsense_user', JSON.stringify(profile));
        } catch (err) {
          console.warn('Token expired or invalid. Logging out.');
          logout();
        }
      }
      setLoading(false);
    };

    fetchProfile();
  }, [token]);

  const login = async (credentials) => {
    const data = await authService.login(credentials);
    const accessToken = data.access_token;
    const userData = data.user;

    setToken(accessToken);
    setUser(userData);
    localStorage.setItem('travelsense_token', accessToken);
    localStorage.setItem('travelsense_user', JSON.stringify(userData));
    return userData;
  };

  const register = async (userData) => {
    const data = await authService.register(userData);
    const accessToken = data.access_token;
    const userObj = data.user;

    setToken(accessToken);
    setUser(userObj);
    localStorage.setItem('travelsense_token', accessToken);
    localStorage.setItem('travelsense_user', JSON.stringify(userObj));
    return userObj;
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (e) {
      // Ignore network errors on logout
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem('travelsense_token');
      localStorage.removeItem('travelsense_user');
    }
  };

  const updateProfile = async (updateData) => {
    const updated = await authService.updateProfile(updateData);
    setUser(updated);
    localStorage.setItem('travelsense_user', JSON.stringify(updated));
    return updated;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        loading,
        login,
        register,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;

