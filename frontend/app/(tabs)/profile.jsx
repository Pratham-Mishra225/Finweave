import React, { useState, useCallback, useEffect } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  useColorScheme,
  ScrollView,
  Switch,
  Alert,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useAuth } from "../../contexts/AuthContext";
import { useDashboard } from "../../contexts/DashboardContext";
import { useRouter } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Profile() {
  const colorScheme = useColorScheme();
  const [darkModeEnabled, setDarkModeEnabled] = useState(
    colorScheme === "dark"
  );
  const isDark = colorScheme === "dark";
  const { user, signOut, idToken } = useAuth();
  const { dashboardData } = useDashboard();
  const router = useRouter();
  
  // State for profile data
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const theme = {
    background: isDark ? "#0a0a0a" : "#F8F9FA",
    card: isDark ? "#1a1a1a" : "#FFFFFF",
    text: isDark ? "#FFFFFF" : "#001F3F",
    textSecondary: isDark ? "#A0A0A0" : "#6B7280",
    border: isDark ? "#2a2a2a" : "#E5E7EB",
    primary: "#001F3F",
    danger: "#EF4444",
  };

  // Fetch profile data from backend
  const fetchProfileData = useCallback(async (silent = false) => {
    if (!idToken) {
      setLoading(false);
      return;
    }

    if (!silent) {
      setLoading(true);
    }

    try {
      const response = await fetch(`${BACKEND_URL}/profile`, {
        headers: {
          Authorization: `Bearer ${idToken}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch profile data");
      }

      const data = await response.json();
      setProfileData(data);
    } catch (error) {
      console.error("Error fetching profile:", error);
      Alert.alert("Error", "Failed to load profile data. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [idToken]);

  // Refresh on focus
  useFocusEffect(
    useCallback(() => {
      fetchProfileData(true);
    }, [fetchProfileData])
  );

  // Fetch once when authenticated
  useEffect(() => {
    fetchProfileData();
  }, [fetchProfileData]);

  // Pull to refresh
  const onRefresh = async () => {
    setRefreshing(true);
    await fetchProfileData(true);
    setRefreshing(false);
  };

  // Update dark mode preference
  const handleDarkModeToggle = async (value) => {
    setDarkModeEnabled(value);
    
    try {
      const response = await fetch(`${BACKEND_URL}/profile/preferences`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${idToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          dark_mode: value,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to update preferences");
      }

      // Update local state
      setProfileData(prev => ({
        ...prev,
        preferences: {
          ...prev?.preferences,
          dark_mode: value,
        },
      }));
    } catch (error) {
      console.error("Error updating dark mode:", error);
      Alert.alert("Error", "Failed to update preferences. Please try again.");
      setDarkModeEnabled(!value); // Revert
    }
  };

  // Prefer dashboardData.balance as it is the most up-to-date value from the dashboard context.
  // Fall back to profileData.stats.balance if dashboardData is unavailable.
  // If both are missing, default to 0.
  // Ensure these sources are kept in sync elsewhere in the codebase to avoid confusion.
  const balanceValue = dashboardData?.balance ?? profileData?.stats?.balance ?? 0;

  const stats = [
    { label: "Balance", value: `₹${balanceValue.toFixed(0)}` },
    { label: "Goals", value: `${profileData?.stats?.total_goals || 0}` },
    { label: "Transactions", value: `${profileData?.stats?.total_transactions || 0}` },
  ];

  const accountSettings = [
    { icon: "person-outline", label: "Edit Profile", value: null },
    { icon: "mail-outline", label: "Email", value: profileData?.email || user?.email || "user@example.com" },
    { icon: "call-outline", label: "Phone", value: profileData?.phone || "Not set" },
  ];

  const preferenceSettings = [
    { icon: "notifications-outline", label: "Notifications", value: null },
    { icon: "color-palette-outline", label: "Appearance", value: null },
  ];

  const securitySettings = [
    { icon: "lock-closed-outline", label: "Change Password", value: null },
    {
      icon: "shield-checkmark-outline",
      label: "Privacy Settings",
      value: null,
    },
    { icon: "link-outline", label: "Linked Accounts", value: null },
  ];

  const supportSettings = [
    { icon: "help-circle-outline", label: "Help & Support", value: null },
    { icon: "document-text-outline", label: "Privacy Policy", value: null },
  ];

  const handleLogout = async () => {
    Alert.alert(
      "Log Out",
      "Are you sure you want to log out?",
      [
        {
          text: "Cancel",
          style: "cancel",
        },
        {
          text: "Log Out",
          style: "destructive",
          onPress: async () => {
            try {
              await signOut();
              router.replace("/login");
            } catch (error) {
              console.error("Error during logout:", error);
              Alert.alert("Error", "Failed to log out. Please try again.");
            }
          },
        },
      ]
    );
  };

  const renderSettingItem = (item, isLast = false, isDanger = false, onPress = null) => (
    <TouchableOpacity
      key={item.label}
      style={[
        styles.settingItem,
        !isLast && { borderBottomWidth: 1, borderBottomColor: theme.border },
      ]}
      activeOpacity={0.7}
      onPress={onPress}
    >
      <View style={styles.settingLeft}>
        <Ionicons
          name={item.icon}
          size={22}
          color={isDanger ? theme.danger : theme.textSecondary}
        />
        <View style={styles.settingText}>
          <Text
            style={[
              styles.settingLabel,
              { color: isDanger ? theme.danger : theme.text },
            ]}
          >
            {item.label}
          </Text>
          {item.value && (
            <Text style={[styles.settingValue, { color: theme.textSecondary }]}>
              {item.value}
            </Text>
          )}
        </View>
      </View>
      <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            Account
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            Manage your profile & preferences
          </Text>
        </View>
        <View
          style={[
            styles.headerIcon,
            { backgroundColor: isDark ? "#2a2a2a" : "#F0F1F3" },
          ]}
        >
          <Ionicons
            name="person-circle-outline"
            size={28}
            color={theme.primary}
          />
        </View>
      </View>

      {loading ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color={theme.primary} />
        </View>
      ) : (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          <View
            style={[
              styles.userCard,
              { backgroundColor: theme.card, borderColor: theme.border },
            ]}
          >
            <View style={[styles.avatar, { backgroundColor: theme.primary }]}>
              <Text style={styles.avatarText}>
                {profileData?.name?.charAt(0)?.toUpperCase() || 
                 user?.displayName?.charAt(0)?.toUpperCase() || 
                 user?.email?.charAt(0)?.toUpperCase() || "U"}
              </Text>
            </View>
            <Text style={[styles.userName, { color: theme.text }]}>
              {profileData?.name || user?.displayName || user?.email?.split('@')[0] || "User"}
            </Text>
            <Text style={[styles.memberSince, { color: theme.textSecondary }]}>
              {user?.emailVerified ? "Email Verified ✓" : "Email Not Verified"}
            </Text>

          <View style={styles.statsRow}>
            {stats.map((stat, index) => (
              <View key={stat.label} style={styles.statItem}>
                <Text style={[styles.statValue, { color: theme.text }]}>
                  {stat.value}
                </Text>
                <Text
                  style={[styles.statLabel, { color: theme.textSecondary }]}
                >
                  {stat.label}
                </Text>
                {index < stats.length - 1 && (
                  <View
                    style={[
                      styles.statDivider,
                      { backgroundColor: theme.border },
                    ]}
                  />
                )}
              </View>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
            ACCOUNT
          </Text>
          <View
            style={[
              styles.settingCard,
              { backgroundColor: theme.card, borderColor: theme.border },
            ]}
          >
            {accountSettings.map((item, index) =>
              renderSettingItem(item, index === accountSettings.length - 1)
            )}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
            PREFERENCES
          </Text>
          <View
            style={[
              styles.settingCard,
              { backgroundColor: theme.card, borderColor: theme.border },
            ]}
          >
            {preferenceSettings.map((item, index) =>
              renderSettingItem(item, index === preferenceSettings.length - 1)
            )}
            <View style={styles.settingItem}>
              <View style={styles.settingLeft}>
                <Ionicons
                  name="moon-outline"
                  size={22}
                  color={theme.textSecondary}
                />
                <Text style={[styles.settingLabel, { color: theme.text }]}>
                  Dark Mode
                </Text>
              </View>
              <Switch
                value={profileData?.preferences?.dark_mode ?? darkModeEnabled}
                onValueChange={handleDarkModeToggle}
                trackColor={{ false: "#D1D5DB", true: "#001F3F" }}
                thumbColor="#FFFFFF"
              />
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
            SECURITY
          </Text>
          <View
            style={[
              styles.settingCard,
              { backgroundColor: theme.card, borderColor: theme.border },
            ]}
          >
            {securitySettings.map((item, index) =>
              renderSettingItem(item, index === securitySettings.length - 1)
            )}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
            SUPPORT
          </Text>
          <View
            style={[
              styles.settingCard,
              { backgroundColor: theme.card, borderColor: theme.border },
            ]}
          >
            {supportSettings.map((item, index) =>
              renderSettingItem(item, index === supportSettings.length - 1)
            )}
          </View>
        </View>

        <View style={styles.section}>
          <View
            style={[
              styles.settingCard,
              { backgroundColor: theme.card, borderColor: theme.border },
            ]}
          >
            {renderSettingItem(
              { icon: "log-out-outline", label: "Log Out", value: null },
              true,
              true,
              handleLogout
            )}
          </View>
        </View>

        <View style={styles.bottomPadding} />
      </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  headerLeft: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: "700",
    letterSpacing: -0.5,
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    fontWeight: "400",
  },
  headerIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  userCard: {
    alignItems: "center",
    padding: 24,
    borderRadius: 16,
    marginBottom: 24,
    borderWidth: 1,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 28,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  userName: {
    fontSize: 22,
    fontWeight: "700",
    marginBottom: 4,
  },
  memberSince: {
    fontSize: 14,
    fontWeight: "400",
    marginBottom: 20,
  },
  statsRow: {
    flexDirection: "row",
    width: "100%",
    justifyContent: "space-around",
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },
  statItem: {
    alignItems: "center",
    position: "relative",
  },
  statValue: {
    fontSize: 20,
    fontWeight: "700",
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 13,
    fontWeight: "400",
  },
  statDivider: {
    position: "absolute",
    right: -20,
    top: 0,
    bottom: 0,
    width: 1,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "600",
    letterSpacing: 1,
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  settingCard: {
    borderRadius: 16,
    borderWidth: 1,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
  },
  settingItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 16,
    paddingHorizontal: 16,
  },
  settingLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  settingText: {
    marginLeft: 12,
    flex: 1,
  },
  settingLabel: {
    fontSize: 15,
    fontWeight: "500",
  },
  settingValue: {
    fontSize: 13,
    fontWeight: "400",
    marginTop: 2,
  },
  bottomPadding: {
    height: 40,
  },
});
