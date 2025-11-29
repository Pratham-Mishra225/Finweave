import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { useAuth } from "./AuthContext";

const DashboardContext = createContext(null);
const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || "http://localhost:8000";

export function DashboardProvider({ children }) {
  const { idToken } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const lastRequestIdRef = useRef(0);

  const refreshDashboard = useCallback(
    async ({ silent = false } = {}) => {
      if (!idToken) {
        setDashboardData(null);
        setLoadingDashboard(false);
        return null;
      }

      const requestId = ++lastRequestIdRef.current;

      if (!silent) {
        setLoadingDashboard(true);
      }

      try {
        const response = await fetch(`${BACKEND_URL}/home/dashboard`, {
          headers: {
            Authorization: `Bearer ${idToken}`,
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch dashboard data");
        }

        const data = await response.json();

        if (requestId === lastRequestIdRef.current) {
          setDashboardData(data);
        }

        return data;
      } catch (error) {
        console.error("Error refreshing dashboard:", error);
        return null;
      } finally {
        if (!silent && requestId === lastRequestIdRef.current) {
          setLoadingDashboard(false);
        }
      }
    },
    [idToken]
  );

  const applyLocalTransaction = useCallback((transaction, action = "add") => {
    if (!transaction) {
      return;
    }

    setDashboardData((prev) => {
      if (!prev) {
        return prev;
      }

      const amount = Number(transaction.amount) || 0;
      const isIncome = transaction.type === "income";
      const balanceAdjustment = isIncome ? amount : -amount;
      const updatedBalance =
        action === "add"
          ? (prev.balance || 0) + balanceAdjustment
          : (prev.balance || 0) - balanceAdjustment;

      const updatedRecent = [
        { ...transaction },
        ...(prev.recent_transactions || []),
      ].slice(0, 5);

      const updatedSpending = { ...(prev.spending_overview || {}) };
      if (!isIncome) {
        updatedSpending.total = (updatedSpending.total || 0) + amount;
      }

      return {
        ...prev,
        balance: updatedBalance,
        recent_transactions: updatedRecent,
        spending_overview: updatedSpending,
      };
    });
  }, []);

  useEffect(() => {
    // Invalidate any pending requests when auth state changes
    lastRequestIdRef.current += 1;

    if (!idToken) {
      setDashboardData(null);
      setLoadingDashboard(false);
    }
  }, [idToken]);

  const value = {
    dashboardData,
    loadingDashboard,
    refreshDashboard,
    applyLocalTransaction,
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboard must be used within a DashboardProvider");
  }
  return context;
}
