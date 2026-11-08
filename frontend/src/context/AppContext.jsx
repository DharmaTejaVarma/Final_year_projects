import React, { createContext, useContext, useState } from 'react';

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [theme] = useState('dark');

  return (
    <AppContext.Provider value={{ theme }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);

